# wagtail-streamfield-standalone

[![PyPI version](https://img.shields.io/pypi/v/wagtail-streamfield-standalone)](https://pypi.org/project/wagtail-streamfield-standalone/)
![License](https://img.shields.io/pypi/l/wagtail-streamfield-standalone)
![Python versions](https://img.shields.io/pypi/pyversions/wagtail-streamfield-standalone)

Embed Wagtail's StreamField editor into any Django form — outside the Wagtail admin.

Use it when you need the full StreamField editing experience (rich text, images, custom blocks, nested structures) on a front-end page, a custom admin view, or anywhere a `ModelAdmin` or standard Django form lives.

## Why Use This?

Wagtail's StreamField editor is tightly coupled to the Wagtail admin shell. Its CSS (`core.css`) sets global styles on `html` and `body`, its JS bootstraps from a `<script id="wagtail-config">` element, and its overlay widgets (modals, dialogs) are appended directly to `<body>`. Drop the raw `BlockWidget` into a non-admin page and you get broken layouts, missing icons, and JavaScript errors.

`wagtail-streamfield-standalone` solves all of that:

- Wraps the editor in a CSS `@scope` block so Wagtail's styles are contained and cannot leak into your page.
- Inlines the SVG icon sprite so icons render without a separate `icons.js` load.
- Watches `<body>` for dynamically-appended modals and dialogs and re-wraps them in the scope root so scoped styles apply there too.
- Fixes block-chooser popup alignment and Draftail floating toolbar positioning when rendered outside the admin layout.
- Exposes the full JS/CSS stack as standard Django form `media` so it integrates with `{{ form.media }}` and works with tools like django-crispy-forms.

## Requirements

- Python >= 3.10
- Django >= 5.2
- Wagtail >= 8.0
- `django.template.context_processors.request` in your `TEMPLATES` settings

## Installation

```bash
pip install wagtail-streamfield-standalone
```

## Setup

### 1. Add to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...
    "wagtail_streamfield_standalone",
]
```

### 2. Wire up the scoped CSS view

The package serves Wagtail's `core.css` through a view that wraps it in a CSS `@scope` rule. Add its URL conf to your project's `urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    ...
    path(
        "wagtail-streamfield-standalone/",
        include("wagtail_streamfield_standalone.urls"),
    ),
]
```

### 3. Enable the request context processor

The `{% streamfield_wagtail_config %}` template tag needs `request` in the template context. Make sure `django.template.context_processors.request` is listed in `TEMPLATES`:

```python
TEMPLATES = [
    {
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "django.template.context_processors.request",
            ],
        },
    },
]
```

## Usage

### Define the form field

Use `StandaloneBlockField` anywhere you would use Wagtail's `BlockField`:

```python
from django import forms
from wagtail.blocks import CharBlock, RichTextBlock, StreamBlock
from wagtail.images.blocks import ImageChooserBlock

from wagtail_streamfield_standalone.fields import StandaloneBlockField

CONTENT_BLOCK = StreamBlock(
    [
        ("text", CharBlock(label="Text")),
        ("rich_text", RichTextBlock(label="Rich Text")),
        ("image", ImageChooserBlock(label="Image")),
    ]
)


class ContentForm(forms.Form):
    content = StandaloneBlockField(block=CONTENT_BLOCK, required=False)
```

### Render the form in a template

Load the template tag library and follow the load order below:

```django
{% load streamfield_standalone_tags %}
<!DOCTYPE html>
<html lang="en">
<head>
    ...
    {{ form.media.css }}
</head>
<body>
    {% streamfield_wagtail_config %}

    <form method="post">
        {% csrf_token %}
        {{ form.content }}
        <button type="submit">Save</button>
    </form>

    {{ form.media.js }}
</body>
</html>
```

The three placement rules are:

| What | Where | Why |
| --- | --- | --- |
| `{{ form.media.css }}` | Inside `<head>` | Loads scoped `core.css` and StreamField panel styles before the editor renders. |
| `{% streamfield_wagtail_config %}` | Anywhere in `<body>`, once per page | Emits `<script id="wagtail-config">` that Wagtail's JS reads at startup for CSRF token, API URLs, and i18n strings. |
| `{{ form.media.js }}` | Just before `</body>` | Ensures the DOM is ready before Wagtail's vendor bundle and block scripts execute. |

### Read the submitted value

The field's `cleaned_data` value is a Wagtail `StreamValue`. To persist or return it as JSON:

```python
import json
from wagtail.blocks import StreamBlock

CONTENT_BLOCK = StreamBlock([...])

def my_view(request):
    if request.method == "POST":
        form = ContentForm(request.POST)
        if form.is_valid():
            stream_value = form.cleaned_data["content"]
            json_data = json.dumps(
                CONTENT_BLOCK.get_prep_value(stream_value),
                indent=2,
                ensure_ascii=False,
            )
```

To pre-populate the editor from saved JSON, pass the raw list to the field's `initial` or reconstruct the `StreamValue`:

```python
form = ContentForm(initial={"content": saved_json_list})
```

### Using with django-crispy-forms

Crispy forms injects `form.media` inside the `<form>` tag by default, which places scripts before `</body>` is reached and can cause the Wagtail vendor bundle to execute before its dependencies. Disable automatic media injection and render it manually:

```python
helper = FormHelper()
helper.include_media = False
```

Then place `{{ form.media.css }}` and `{{ form.media.js }}` manually as shown above.

## How it works

### CSS scoping

Wagtail's `core.css` is served through the `scoped_core_css` view, which wraps its rules in `@scope (.wagtail-streamfield-standalone) { ... }`. This confines all of Wagtail's styles to the editor wrapper and prevents them from affecting your page's `<html>`, `<body>`, links, headings, or form elements.

`:root {}` variable declarations and `@keyframes` blocks are hoisted outside the `@scope` block — `:root` because `@scope`'s `:root` selector never matches `<html>` (which is an ancestor of the scope root, not a descendant), and `@keyframes` because the CSS spec does not allow them inside `@scope`.

CSS `@scope` is supported in Chrome 118+, Safari 17.4+, and Firefox 128+.

### Modal and dialog scoping

Wagtail's chooser modals and dialog overlays are appended directly to `<body>`, outside the editor's scope root. A `MutationObserver` watches `<body>` for these elements and immediately wraps each one in a `<div class="wagtail-streamfield-standalone">` container so the scoped styles apply inside them too. The wrapper is removed automatically when Wagtail removes the overlay.

### Icon sprite

The SVG icon sprite is loaded inline via an injected `<script>` that replicates Wagtail's `icons.js` logic, so icons render correctly without requiring a `data-icon-url` attribute that Django's `Media` system cannot emit.

## Testing

```bash
tox
```

## Demo Project

A demo Django/Wagtail project is included in the `demo/` directory.

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

From the repo root:

```bash
pip install -r requirements.txt
```

This installs the package in editable mode along with Django and Wagtail.

### 3. Apply database migrations

```bash
python manage.py migrate
```

### 4. Create a superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

### 5. Start the development server

```bash
python manage.py runserver
```

### 6. Log in to the admin

Open your browser and go to [http://localhost:8000/cms/](http://localhost:8000/cms/) and log in with the superuser credentials you created.

### 7. Try out the StreamField

Go to the root page at [http://localhost:8000/](http://localhost:8000/) to see the StreamField in action.

## License

MIT License
