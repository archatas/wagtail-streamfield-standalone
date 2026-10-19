import io

import pytest
from django.contrib.auth import get_user_model

SUPERUSER_USERNAME = "testadmin"
SUPERUSER_PASSWORD = "testpass-secure-1"


@pytest.fixture
def superuser(db):
    User = get_user_model()
    return User.objects.create_superuser(
        username=SUPERUSER_USERNAME,
        password=SUPERUSER_PASSWORD,
    )


@pytest.fixture
def dummy_image(db):
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    from PIL import Image as PILImage
    from wagtail.images import get_image_model

    Image = get_image_model()

    buf = io.BytesIO()
    PILImage.new("RGB", (300, 200), color=(70, 130, 180)).save(buf, format="JPEG")

    # Write the file to storage first so Wagtail can open it from disk during
    # save() to read image dimensions — using ImageFile(buf) directly leaves the
    # buffer at EOF, causing PIL to fail and Wagtail to set width/height=None.
    file_name = default_storage.save(
        "original_images/dummy_test.jpg",
        ContentFile(buf.getvalue()),
    )

    image = Image(title="Dummy Test Image")
    image.file = file_name
    image.save()
    return image


@pytest.fixture
def logged_in_page(page, live_server, superuser):
    """Playwright page pre-authenticated as the test superuser via the Wagtail admin login."""
    page.goto(f"{live_server.url}/cms/login/")
    page.locator('[name="username"]').fill(SUPERUSER_USERNAME)
    page.locator('[name="password"]').fill(SUPERUSER_PASSWORD)
    page.locator('[type="submit"]').click()
    page.wait_for_load_state("networkidle")
    return page
