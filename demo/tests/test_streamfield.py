"""
Unit tests for wagtail-streamfield-standalone Python functionality.

Covers three modules:
  - fields.py         — StandaloneBlockField / StandaloneBlockWidget
  - views.py          — scoped_core_css view and _rewrite_css_urls helper
  - templatetags/     — streamfield_wagtail_config template tag
"""

import pytest
from django.urls import reverse
from wagtail.blocks import CharBlock, StreamBlock


# ---------------------------------------------------------------------------
# fields.py — StandaloneBlockField / StandaloneBlockWidget
# ---------------------------------------------------------------------------


def _simple_block():
    return StreamBlock([("text", CharBlock())])


class TestStandaloneBlockField:
    def test_uses_standalone_widget_by_default(self):
        from wagtail_streamfield_standalone.fields import (
            StandaloneBlockField,
            StandaloneBlockWidget,
        )

        field = StandaloneBlockField(block=_simple_block())
        assert isinstance(field.widget, StandaloneBlockWidget)

    def test_custom_widget_is_not_overridden(self):
        from wagtail.blocks.base import BlockWidget

        from wagtail_streamfield_standalone.fields import (
            StandaloneBlockField,
            StandaloneBlockWidget,
        )

        block = _simple_block()
        # Django deep-copies widgets, so identity check is wrong — check type instead
        field = StandaloneBlockField(block=block, widget=BlockWidget(block))
        assert type(field.widget) is BlockWidget
        assert not isinstance(field.widget, StandaloneBlockWidget)


@pytest.mark.django_db
class TestStandaloneBlockWidget:
    def test_render_wraps_in_scope_div(self):
        from wagtail_streamfield_standalone.fields import StandaloneBlockWidget

        html = StandaloneBlockWidget(_simple_block()).render("content", None, attrs={})
        assert 'class="wagtail-streamfield-standalone"' in html

    def test_render_includes_stream_container_attr(self):
        from wagtail_streamfield_standalone.fields import StandaloneBlockWidget

        html = StandaloneBlockWidget(_simple_block()).render("content", None, attrs={})
        assert "data-streamfield-stream-container" in html

    def test_render_includes_sprite_placeholder(self):
        from wagtail_streamfield_standalone.fields import StandaloneBlockWidget

        html = StandaloneBlockWidget(_simple_block()).render("content", None, attrs={})
        assert "data-sprite" in html

    def test_media_css_includes_scoped_core_css_url(self):
        from wagtail_streamfield_standalone.fields import StandaloneBlockWidget

        widget = StandaloneBlockWidget(_simple_block())
        scoped_url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        assert scoped_url in widget.media._css.get("all", [])

    def test_media_js_includes_vendor_and_core_and_blocks(self):
        from wagtail_streamfield_standalone.fields import StandaloneBlockWidget

        # Django 6.1+ stores Script objects in _js rather than plain strings
        js = " ".join(str(f) for f in StandaloneBlockWidget(_simple_block()).media._js)
        assert "core.js" in js
        assert "vendor.js" in js
        assert "blocks.js" in js

    def test_media_js_vendor_loaded_before_blocks(self):
        from wagtail_streamfield_standalone.fields import StandaloneBlockWidget

        js_files = [str(f) for f in StandaloneBlockWidget(_simple_block()).media._js]
        vendor_idx = next(i for i, f in enumerate(js_files) if "vendor.js" in f)
        blocks_idx = next(i for i, f in enumerate(js_files) if "blocks.js" in f)
        assert vendor_idx < blocks_idx

    def test_media_js_has_no_duplicates(self):
        from wagtail_streamfield_standalone.fields import StandaloneBlockWidget

        js_files = [str(f) for f in StandaloneBlockWidget(_simple_block()).media._js]
        assert len(js_files) == len(set(js_files))


# ---------------------------------------------------------------------------
# views.py — _rewrite_css_urls helper
# ---------------------------------------------------------------------------


class TestRewriteCSSUrls:
    def test_rewrites_relative_url_reference(self):
        from wagtail_streamfield_standalone.views import _rewrite_css_urls

        result = _rewrite_css_urls("src: url(../fonts/icon.woff)")
        assert "url(../" not in result
        assert "url(" in result

    def test_rewritten_url_uses_static_url_prefix(self):
        from django.conf import settings

        from wagtail_streamfield_standalone.views import _rewrite_css_urls

        result = _rewrite_css_urls("src: url(../fonts/icon.woff)")
        static_base = settings.STATIC_URL.rstrip("/")
        assert f"url({static_base}/" in result

    def test_leaves_non_relative_urls_unchanged(self):
        from wagtail_streamfield_standalone.views import _rewrite_css_urls

        css = "background: url(/static/img/foo.png)"
        assert _rewrite_css_urls(css) == css

    def test_multiple_relative_urls_all_rewritten(self):
        from wagtail_streamfield_standalone.views import _rewrite_css_urls

        css = "a{src:url(../a.woff)} b{src:url(../b.woff)}"
        result = _rewrite_css_urls(css)
        assert "url(../" not in result


# ---------------------------------------------------------------------------
# views.py — scoped_core_css view
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScopedCoreCSSView:
    def test_returns_200_with_css_content_type(self, client):
        url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        response = client.get(url)
        assert response.status_code == 200
        assert "text/css" in response["Content-Type"]

    def test_contains_scope_rule(self, client):
        url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        content = client.get(url).content.decode()
        assert "@scope (.wagtail-streamfield-standalone)" in content

    def test_root_block_hoisted_before_scope(self, client):
        url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        content = client.get(url).content.decode()
        root_pos = content.find(":root{")
        scope_pos = content.find("@scope")
        assert root_pos != -1 and scope_pos != -1
        assert root_pos < scope_pos

    def test_keyframes_hoisted_before_scope(self, client):
        url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        content = client.get(url).content.decode()
        kf_pos = content.find("@keyframes")
        scope_pos = content.find("@scope")
        assert kf_pos != -1 and scope_pos != -1
        assert kf_pos < scope_pos

    def test_no_keyframes_inside_scope_block(self, client):
        url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        content = client.get(url).content.decode()
        scope_pos = content.find("@scope")
        # Everything after "@scope" should contain no @keyframes
        assert "@keyframes" not in content[scope_pos:]

    def test_no_relative_url_references(self, client):
        url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        content = client.get(url).content.decode()
        assert "url(../" not in content

    def test_cache_control_header(self, client):
        url = reverse("wagtail_streamfield_standalone:scoped_core_css")
        response = client.get(url)
        assert "max-age=86400" in response.get("Cache-Control", "")


# ---------------------------------------------------------------------------
# templatetags/streamfield_standalone_tags.py — streamfield_wagtail_config
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestStreamfieldWagtailConfigTag:
    def test_emits_wagtail_config_script_element(self, rf):
        from django.template import Context, Template

        request = rf.get("/")
        template = Template(
            "{% load streamfield_standalone_tags %}"
            "{% streamfield_wagtail_config %}"
        )
        output = template.render(Context({"request": request}))
        assert 'id="wagtail-config"' in output
        assert 'type="application/json"' in output

    def test_does_not_raise_without_request_in_context(self):
        from django.template import Context, Template

        template = Template(
            "{% load streamfield_standalone_tags %}"
            "{% streamfield_wagtail_config %}"
        )
        # Should not raise; the tag catches exceptions from wagtail_config()
        output = template.render(Context({}))
        assert 'id="wagtail-config"' in output
