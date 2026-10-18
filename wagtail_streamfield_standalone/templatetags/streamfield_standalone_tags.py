from django import template
from django.utils.html import json_script

register = template.Library()


@register.simple_tag(takes_context=True)
def streamfield_wagtail_config(context):
    """
    Render the ``<script id="wagtail-config" type="application/json">`` element
    that Wagtail's vendor.js reads at startup for CSRF token, API URLs, and i18n.

    Must be included exactly once per page that contains a StandaloneBlockField.
    Requires ``django.template.context_processors.request`` in TEMPLATES settings.

    Usage::

        {% load streamfield_standalone_tags %}
        {% streamfield_wagtail_config %}
    """
    from wagtail.admin.templatetags.wagtailadmin_tags import (
        wagtail_config as _get_config,
    )

    try:
        config = _get_config(context)
    except Exception:
        config = {}

    return json_script(config, "wagtail-config")
