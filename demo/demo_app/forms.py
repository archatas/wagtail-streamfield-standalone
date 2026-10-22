import json

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        # Prevent crispy forms from injecting {{ form.media }} inside the <form>
        # tag before core.js is loaded. Media is rendered manually in the template:
        # {{ form.media.css }} in <head> and {{ form.media.js }} before </body>.
        self.helper.include_media = False
        self.helper.layout = Layout(
            Field("content"),
            Submit("submit", "Save"),
        )

    def get_content_json(self):
        value = self.cleaned_data.get("content")
        return json.dumps(
            CONTENT_BLOCK.get_prep_value(value), indent=2, ensure_ascii=False
        )
