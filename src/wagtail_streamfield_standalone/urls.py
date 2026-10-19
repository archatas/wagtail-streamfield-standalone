from django.urls import path

from . import views

app_name = "wagtail_streamfield_standalone"

urlpatterns = [
    path("core.css", views.scoped_core_css, name="scoped_core_css"),
]
