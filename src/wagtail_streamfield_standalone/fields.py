import json
from functools import cached_property

import django.forms as forms
from django.utils.html import format_html, mark_safe
from wagtail.blocks.base import BlockField, BlockWidget

# CSS class used as the @scope root. Added to the editor wrapper div and to any
# modal/backdrop wrapper divs created by the MutationObserver at runtime.
SCOPE_CLASS = "wagtail-streamfield-standalone"

# Replicates icons.js logic inline, avoiding the need for a data-icon-url script attribute
# that Django's Media system cannot emit.
_SPRITE_LOADER_TEMPLATE = """
(function(){{
    var u={url};
    var c=document.querySelector("[data-sprite]");
    if(!c)return;
    var ls="localStorage"in window&&null!=window.localStorage;
    function inject(s){{
        if("loading"===document.readyState){{
            document.addEventListener("DOMContentLoaded",function(){{c.innerHTML=s;}},{{once:true}});
        }}else{{c.innerHTML=s;}}
    }}
    if(ls&&localStorage.getItem("wagtail:spriteRevision")===u){{
        inject(localStorage.getItem("wagtail:spriteData")||"");
    }}
    fetch(u).then(function(r){{return r.text();}}).then(function(s){{
        inject(s);
        if(ls)try{{
            localStorage.setItem("wagtail:spriteData",s);
            localStorage.setItem("wagtail:spriteRevision",u);
        }}catch(e){{}}
    }}).catch(function(e){{console.error("Error loading icon sprite:",e);}});
}})();
"""

# core.css resets box-sizing via:
#   html { box-sizing: border-box }
#   *, *::before, *::after { box-sizing: inherit }
#
# Inside @scope (.wagtail-streamfield-standalone) the html{} rule never matches
# (html is an ancestor of the scope root, never a descendant).  So all elements
# inherit box-sizing from the browser default (content-box), which makes padded
# inputs like the image-chooser search field overflow their containers.
#
# Fix: inject a global <style> that explicitly sets border-box on the scope root
# and all its descendants.  A second rule fixes the combobox option grid whose
# fixed 246 px columns sum to 544 px, overflowing the 512 px Tippy popup.
_CSS_OVERRIDES = (
    # core.css resets box-sizing via html{box-sizing:border-box} + *{box-sizing:inherit}.
    # Inside @scope the html{} rule never matches (html is an ancestor, not a descendant),
    # so all elements inherit content-box from the browser default.  Explicit border-box
    # here fixes padded inputs (e.g. image-chooser search bar) overflowing their wrappers.
    ".wagtail-streamfield-standalone,"
    ".wagtail-streamfield-standalone *,"
    ".wagtail-streamfield-standalone *::before,"
    ".wagtail-streamfield-standalone *::after{"
    "box-sizing:border-box}"
    # Block chooser option grid: fixed 246px columns sum to 544px, overflowing the 512px
    # Tippy popup.  Use flexible columns instead.
    ".wagtail-streamfield-standalone .w-combobox__optgroup{"
    "grid-template-columns:repeat(2,minmax(0,1fr))}"
    # In the Wagtail admin the StreamField editor is nested inside a .w-panel--nested
    # container (the page's "Content" editing panel), so each block's own .w-panel
    # gets margin-bottom:0 via core.css's ".w-panel--nested .w-panel{margin-bottom:0}".
    # In standalone context there is no outer .w-panel--nested, so blocks keep the
    # default margin-bottom:40px, creating excessive vertical gaps.
    # This rule replicates the admin's behaviour.
    ".wagtail-streamfield-standalone .w-panel--nested{margin-bottom:0}"
    # core.css sets --header-gap:1rem on .w-panel at >=50em viewports, making
    # .w-panel__header use margin-inline-start:calc((2*1.5rem+1rem)*-1)=-64px.
    # In the admin an outer content panel absorbs this with matching left padding;
    # in standalone mode there is no such outer panel, so the header bleeds
    # 40-64px past the left edge of the form.  Reset the margin to keep the
    # header flush with its panel.
    ".wagtail-streamfield-standalone .w-panel__header{margin-inline-start:0}"
    # core.css gives .w-panel--nested>.w-panel__content a negative
    # margin-inline-start so its dashed left guide-line bleeds into the outer
    # panel's padding area.  In standalone mode the container has no such
    # padding, so the guide-line overflows the form's left edge.
    # The toggle button (1.5rem = 24px wide) IS the block type icon that users
    # see in the header.  Its centre sits at 0.75rem from the panel left.
    # Set the content margin to 0.75rem so the dashed guide-line passes through
    # that centre, and override the "+" button margin so its own centre (= its
    # left edge + half its 1.5rem width) also falls at 0.75rem from the panel.
    ".wagtail-streamfield-standalone .w-panel--nested>.w-panel__content"
    "{margin-inline-start:0.75rem}"
    ".wagtail-streamfield-standalone .c-sf-add-button"
    "{margin-inline-start:0}"
    # In the admin the block header has margin-inline-start:-64px, so the
    # anchor-prefix (24px) and toggle (24px) are off-screen left and only the
    # type-icon + label appear at the outer panel content left edge.
    # In standalone the margin is 0, so anchor+toggle+heading-margin(16px)=64px
    # of whitespace precedes the label.  Remove the anchor-prefix (a permalink
    # not useful outside the admin) and zero the heading's start margin to
    # bring the label to ~24px from the panel left instead of 64px.
    ".wagtail-streamfield-standalone .w-panel__anchor--prefix{display:none}"
    ".wagtail-streamfield-standalone .w-panel__heading--label{margin-inline-start:0}"
    # core.css caps .w-field__wrapper at max-width:840px.  In the admin the
    # outer panel structure limits field width independently, so this cap is
    # invisible.  In standalone the field wrapper is 918px wide (content 948
    # minus 30px padding) and the 840px cap leaves a 78px gap between the
    # input right edge and the action buttons.  Remove the cap so the input
    # fills its container and aligns with the buttons on the right.
    ".wagtail-streamfield-standalone .w-field__wrapper{max-width:none}"
    # core.css sets .w-header .row{padding-top:2.5rem} (40px) and
    # .w-header>.row{padding-bottom:.625rem} (10px).  With h1 height ~25px,
    # the title centre lands 13px below the dark header bar's visual centre.
    # Equalise to 25px each so the title is centred while the row height
    # (25+25+25=75px) and the header bar dimensions remain unchanged.
    ".wagtail-streamfield-standalone .modal .w-header--merged .row"
    "{padding-top:25px;padding-bottom:25px}"
)

# blocks.js gives every "+" add-button a Tippy popup with placement:"bottom"
# (centered).  When the button is near the viewport's left edge the 512 px-wide
# popup would extend off-screen, so Popper's preventOverflow clips it to x=5 —
# visually disconnected from the button.
#
# Fix: change placement to "bottom-start" (left-edge-aligned) on every
# .c-sf-add-button as soon as it appears in the DOM.
#
# The Draftail FloatingToolbar is a Tippy popup with placement:"top" (centered).
# Unlike the block chooser, Draftail's React layer calls setProps({placement:'top'})
# on every render, so we cannot patch the instance persistently.  Instead, we watch
# each [data-tippy-root]'s style attribute.  When Popper clips the toolbar to
# x ≤ 10 px (off-screen left) while the text selection is further right, we add
# a horizontal correction to the transform so the toolbar aligns with the selection.
_BLOCK_CHOOSER_FIX_JS = """
(function(){
    var c=document.currentScript.parentElement;

    function patchBtn(el){
        if(el._tippy&&!el._wssfixed){el._tippy.setProps({placement:'bottom-start'});el._wssfixed=true;}
    }

    var correcting=false;
    function correctToolbar(root){
        if(correcting)return;
        if(!root.querySelector('.Draftail-Tooltip'))return;
        var sel=window.getSelection();
        if(!sel||!sel.rangeCount)return;
        var sr=sel.getRangeAt(0).getBoundingClientRect();
        if(!sr.width)return;
        var rr=root.getBoundingClientRect();
        if(rr.x>10)return;
        var shiftX=sr.x-rr.x;
        if(shiftX<1)return;
        var m=root.style.transform.match(/translate\\((-?[\\d.]+)px,\\s*(-?[\\d.]+)px\\)/);
        if(!m)return;
        correcting=true;
        root.style.transform='translate('+(parseFloat(m[1])+shiftX)+'px,'+m[2]+'px)';
        correcting=false;
    }
    function watchTippyRoot(root){
        correctToolbar(root);
        new MutationObserver(function(){correctToolbar(root);})
            .observe(root,{attributes:true,attributeFilter:['style']});
    }

    function fix(root){
        if(!root||root.nodeType!==1)return;
        var qs=root.querySelectorAll?root.querySelectorAll.bind(root):function(){return[];};
        Array.from(qs('.c-sf-add-button')).forEach(patchBtn);
        if(root.matches&&root.matches('.c-sf-add-button'))patchBtn(root);
        var tRoots=(root.matches&&root.matches('[data-tippy-root]'))?[root]:Array.from(qs('[data-tippy-root]'));
        tRoots.forEach(watchTippyRoot);
    }

    new MutationObserver(function(ms){
        ms.forEach(function(m){
            m.addedNodes.forEach(function(n){setTimeout(function(){fix(n);},0);});
        });
    }).observe(c,{childList:true,subtree:true});
})();
"""

# Several Wagtail overlays are appended directly to <body>, outside
# .wagtail-streamfield-standalone:
#
#  - .modal / .modal-backdrop  (Bootstrap / modal-workflow.js)
#  - .w-dialog                 (Wagtail 8+ Stimulus dialog, teleported by w-teleport)
#  - <dialog>                  (native element, used by some future Wagtail views)
#
# Stamping the scope class on the element itself doesn't work: CSS @scope only
# applies its rules to DESCENDANTS of the scope root, not to the root itself.
#
# Solution: wrap each newly-added overlay in a thin
# <div class="wagtail-streamfield-standalone"> at body level so the overlay is a
# true descendant and all @scope rules apply.  The wrapper is zero-height because
# its only child is position:fixed/absolute, so it has no visual footprint.
#
# Cleanup: w-teleport removes .w-dialog from body when the dialog closes.  A nested
# MutationObserver watches each wrapper and removes it once it becomes childless,
# preventing accumulation of empty divs.
#
# A single shared observer handles multiple widgets on the same page.
_MODAL_SCOPE_OBSERVER_JS = """
if(!window.__wssModalObserver){
    function wssWrap(n){
        if(n.nodeType!==1)return;
        if(!(n.classList.contains("modal")||
             n.classList.contains("modal-backdrop")||
             n.classList.contains("w-dialog")||
             n.tagName==="DIALOG"))return;
        var w=document.createElement("div");
        w.className="wagtail-streamfield-standalone";
        n.parentNode.insertBefore(w,n);
        w.appendChild(n);
        new MutationObserver(function(ms,obs){
            if(!w.children.length){w.remove();obs.disconnect();}
        }).observe(w,{childList:true});
    }
    window.__wssModalObserver=new MutationObserver(function(ms){
        ms.forEach(function(m){m.addedNodes.forEach(wssWrap);});
    });
    window.__wssModalObserver.observe(document.body,{childList:true});
}
"""


class StandaloneBlockWidget(BlockWidget):
    """
    BlockWidget subclass that:
    - wraps its output in <div data-streamfield-stream-container>
    - inlines the SVG sprite loader (so icons.js with data-icon-url is not needed)
    - exposes a Media property with the full JS/CSS stack in the correct load order
    """

    def render(self, name, value, attrs=None, renderer=None):
        from wagtail.admin.icons import get_icon_sprite_url

        block_html = super().render(name, value, attrs, renderer)
        sprite_js = _SPRITE_LOADER_TEMPLATE.format(
            url=json.dumps(get_icon_sprite_url())
        )
        return format_html(
            '<div class="wagtail-streamfield-standalone" data-streamfield-stream-container>'
            "<style>{css}</style>"
            "<div data-sprite></div>"
            "<script>{sprite}</script>"
            "<script>{modal_observer}</script>"
            "<script>{chooser_fix}</script>"
            "{block}"
            "</div>",
            css=mark_safe(_CSS_OVERRIDES),
            sprite=mark_safe(sprite_js),
            modal_observer=mark_safe(_MODAL_SCOPE_OBSERVER_JS),
            chooser_fix=mark_safe(_BLOCK_CHOOSER_FIX_JS),
            block=block_html,  # already SafeString from BlockWidget
        )

    @cached_property
    def media(self):
        from django.urls import reverse
        from wagtail.admin.staticfiles import versioned_static

        # js_context.media holds adapter JS/CSS contributed by each block type
        # (e.g. draftail for RichTextBlock, chooser scripts for ImageChooserBlock).
        ctx_media = self.js_context.media

        # Full JS stack matching the Wagtail admin base template load order.
        # icons.js is intentionally omitted — its logic is inlined in render().
        base_js = [
            versioned_static("wagtailadmin/js/vendor/jquery-3.6.0.min.js"),
            versioned_static("wagtailadmin/js/vendor/jquery-ui-1.13.2.min.js"),
            versioned_static("wagtailadmin/js/vendor/bootstrap-transition.js"),
            versioned_static("wagtailadmin/js/vendor/bootstrap-modal.js"),
            versioned_static("wagtailadmin/js/vendor/tag-it.js"),
            versioned_static("wagtailadmin/js/core.js"),
            versioned_static("wagtailadmin/js/vendor.js"),
            versioned_static("wagtailadmin/js/wagtailadmin.js"),
            versioned_static("wagtailadmin/js/modal-workflow.js"),
            # telepath/blocks.js must come after vendor.js (chunk 321) so that
            # window.telepath is initialised before block classes are registered.
            versioned_static("wagtailadmin/js/telepath/blocks.js"),
        ]
        seen_js = set(base_js)
        all_js = list(base_js)
        for js_url in ctx_media._js:
            if js_url not in seen_js:
                all_js.append(js_url)
                seen_js.add(js_url)

        # CSS: scoped core.css (via Django view) + streamfield panel CSS + block CSS.
        scoped_css_url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        extra_css = list(ctx_media._css.get("all", [])) + [
            versioned_static("wagtailadmin/css/panels/streamfield.css"),
        ]
        seen_css = {scoped_css_url}
        all_css = [scoped_css_url]
        for css_url in extra_css:
            if css_url not in seen_css:
                all_css.append(css_url)
                seen_css.add(css_url)

        return forms.Media(js=all_js, css={"all": all_css})


class StandaloneBlockField(BlockField):
    """
    BlockField that uses StandaloneBlockWidget so the full Wagtail JS/CSS
    stack is declared as form media and can be rendered with {{ form.media }}.

    Usage::

        content = StandaloneBlockField(block=my_stream_block, required=False)

    In the template include {{ form.media.css }} in <head>, then once per page::

        {% streamfield_wagtail_config %}

    Then render the field and finish with {{ form.media.js }} before </body>.

    If using django-crispy-forms set ``helper.include_media = False`` to prevent
    the media from being injected inside the form tag before core.js loads.
    """

    def __init__(self, block, **kwargs):
        kwargs.setdefault("widget", StandaloneBlockWidget(block))
        super().__init__(block, **kwargs)
