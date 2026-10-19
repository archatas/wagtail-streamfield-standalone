import posixpath
import re
from pathlib import Path

import wagtail
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import cache_control

SCOPE = ".wagtail-streamfield-standalone"

# The CSS lives at {STATIC_URL}wagtailadmin/css/ in the static tree.
_CSS_STATIC_BASE = "wagtailadmin/css/"

_RELATIVE_URL_RE = re.compile(r"url\((\.\.[^)]+)\)")


def _rewrite_css_urls(content: str) -> str:
    """Rewrite relative url() references to absolute static URLs."""
    static_url = settings.STATIC_URL.rstrip("/")

    def _replace(m: re.Match) -> str:
        resolved = posixpath.normpath(posixpath.join(_CSS_STATIC_BASE, m.group(1)))
        return f"url({static_url}/{resolved})"

    return _RELATIVE_URL_RE.sub(_replace, content)


_CORE_CSS_PATH = (
    Path(wagtail.__file__).parent / "admin/static/wagtailadmin/css/core.css"
)

# Matches :root{...} blocks whose body contains no nested braces.
# Wagtail's :root block only holds --w-* custom properties (fonts, colours, spacing)
# whose values never contain { }, so this regex is sufficient.
_ROOT_BLOCK_RE = re.compile(r":root\{[^{}]+\}")

# Matches @keyframes blocks that may contain nested braces (e.g. 0%{...}to{...}).
# We allow one level of nesting since keyframe bodies like `{transform:rotate(0)}` use
# a single pair of braces — the outer pair for the timeline, inner pairs per stop.
_KEYFRAMES_RE = re.compile(
    r"@keyframes\s+[^{]+\{(?:[^{}]*|\{[^{}]*\})*\}"
)


@cache_control(max_age=86400, public=True)
def scoped_core_css(request):
    """
    Serve wagtail's core.css wrapped in a CSS @scope rule so that its styles
    only apply inside elements matching .wagtail-streamfield-standalone.

    :root{} variable declarations and @keyframes blocks are hoisted outside the
    @scope block:
    - :root{} so --w-* custom properties are globally available (@scope's :root
      never matches <html> because it is an ancestor of the scope root)
    - @keyframes because @keyframes is not valid inside @scope per the CSS spec;
      hoisting them avoids browser-specific parsing behaviour and keeps animations
      working globally.

    @scope is supported in Chrome 118+, Safari 17.4+, Firefox 128+.
    """
    content = _rewrite_css_urls(_CORE_CSS_PATH.read_text(encoding="utf-8"))

    root_blocks = "\n".join(_ROOT_BLOCK_RE.findall(content))
    keyframes_blocks = "\n".join(_KEYFRAMES_RE.findall(content))

    # Remove @keyframes from core.css before wrapping so they are not duplicated
    # inside @scope (where they would be invalid).
    inner = _KEYFRAMES_RE.sub("", content)

    body = f"{root_blocks}\n{keyframes_blocks}\n@scope ({SCOPE}) {{\n{inner}\n}}"
    return HttpResponse(body, content_type="text/css; charset=utf-8")
