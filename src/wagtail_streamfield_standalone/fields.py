from functools import cached_property

import django.forms as forms
from django.utils.html import format_html
from wagtail.blocks.base import BlockField, BlockWidget

# CSS class used as the @scope root. Added to the editor wrapper div and to any
# modal/backdrop wrapper divs created by the MutationObserver at runtime.
SCOPE_CLASS = "wagtail-streamfield-standalone"


class StandaloneBlockWidget(BlockWidget):
    """
    BlockWidget subclass that:
    - wraps its output in <div data-streamfield-stream-container>
    - passes the icon sprite URL via data-sprite-url for sprite-loader.js
    - exposes a Media property with the full JS/CSS stack in the correct load order
    """

    def render(self, name, value, attrs=None, renderer=None):
        from wagtail.admin.icons import get_icon_sprite_url

        block_html = super().render(name, value, attrs, renderer)
        return format_html(
            '<div class="wagtail-streamfield-standalone" data-streamfield-stream-container>'
            '<div data-sprite data-sprite-url="{}"></div>'
            "{}"
            "</div>",
            get_icon_sprite_url(),
            block_html,
        )

    @cached_property
    def media(self):
        from django.templatetags.static import static
        from django.urls import reverse
        from wagtail.admin.staticfiles import versioned_static

        # js_context.media holds adapter JS/CSS contributed by each block type
        # (e.g. draftail for RichTextBlock, chooser scripts for ImageChooserBlock).
        ctx_media = self.js_context.media

        # Full JS stack matching the Wagtail admin base template load order.
        # icons.js is intentionally omitted — its logic is in sprite-loader.js.
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
            static("wagtail-streamfield-standalone/js/sprite-loader.js"),
            static("wagtail-streamfield-standalone/js/modal-scope-observer.js"),
            static("wagtail-streamfield-standalone/js/block-chooser-fix.js"),
        ]
        seen_js = set(base_js)
        all_js = list(base_js)
        for js_url in ctx_media._js:
            if js_url not in seen_js:
                all_js.append(js_url)
                seen_js.add(js_url)

        # CSS: scoped core.css (via Django view) + standalone overrides + block CSS.
        scoped_css_url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        standalone_css_url = static("wagtail-streamfield-standalone/css/standalone.css")
        extra_css = list(ctx_media._css.get("all", [])) + [
            versioned_static("wagtailadmin/css/panels/streamfield.css"),
        ]
        seen_css = {scoped_css_url, standalone_css_url}
        all_css = [scoped_css_url, standalone_css_url]
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
