from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    # Wagtail admin (needed for image/page chooser modals)
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    # Scoped core.css served by the package
    path(
        "streamfield/",
        include("wagtail_streamfield_standalone.urls", namespace="wagtail_streamfield_standalone"),
    ),
    # Demo
    path("", include("demo_app.urls", namespace="demo_app")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
