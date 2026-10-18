import json

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

    def get_content_json(self):
        value = self.cleaned_data.get("content")
        return json.dumps(
            CONTENT_BLOCK.get_prep_value(value), indent=2, ensure_ascii=False
        )
