"""
Playwright integration tests for the StreamField standalone demo.

Selectors target Wagtail 8's StreamField DOM conventions:
  - .c-sf-add-button      — the "+" button that opens the block-type chooser
  - role="option" (exact) — each block type inside the combobox/listbox chooser panel
  - role="listbox"        — the chooser panel itself; waited on to confirm it closed
  - .modal-dialog         — the image/document chooser overlay

If Wagtail's internal class names change these are the first places to update.
"""

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import Page


@pytest.mark.django_db(transaction=True)
def test_add_all_streamfield_blocks(live_server, logged_in_page, dummy_image):
    page = logged_in_page
    page.goto(f"{live_server.url}/")
    page.wait_for_load_state("networkidle")

    # -- Text block (CharBlock) --
    _add_block(page, "Text")
    page.locator('input[type="text"]').last.fill("Hello from the text block")

    # -- Rich Text block (RichTextBlock / Draftail) --
    _add_block(page, "Rich Text")
    page.locator('[contenteditable="true"]').last.click()
    page.keyboard.type("Hello from the rich text block")

    # -- Image block (ImageChooserBlock) --
    _add_block(page, "Image")
    page.get_by_role("button", name="Choose an image").last.click()
    _select_image_in_chooser(page, dummy_image.title)

    # Submit and verify all three block types appear in the returned JSON
    page.get_by_role("button", name="Save").click()
    page.wait_for_load_state("networkidle")

    submitted_json = page.locator("pre").text_content()
    assert '"type": "text"' in submitted_json
    assert '"type": "rich_text"' in submitted_json
    assert '"type": "image"' in submitted_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_block(page: Page, label: str) -> None:
    """Open the StreamField block-type chooser and select a block type by label."""
    page.locator(".c-sf-add-button").last.click()
    # Wagtail 8 renders the block-type chooser as a combobox/listbox; each type is role="option"
    page.get_by_role("option", name=label, exact=True).click()
    # Wait for the chooser to fully close (including its dismiss animation) before
    # the caller tries to interact with the newly added block's content.
    page.get_by_role("listbox").wait_for(state="hidden")


def _select_image_in_chooser(page: Page, image_title: str) -> None:
    """Wait for the Wagtail image-chooser modal, pick the image, wait for close."""
    # The package's MutationObserver wraps the chooser overlay in the scope root,
    # but the .modal-dialog element itself is still the selector target.
    modal = page.locator(".modal-dialog")
    modal.wait_for(state="visible", timeout=15_000)
    # Wait for the async chooser listing to finish loading before clicking
    page.wait_for_load_state("networkidle")
    modal.get_by_text(image_title).first.click()
    modal.wait_for(state="hidden", timeout=15_000)
