from django.shortcuts import render

from .forms import ContentForm


def index(request):
    submitted_json = None
    if request.method == "POST":
        form = ContentForm(request.POST)
        if form.is_valid():
            submitted_json = form.get_content_json()
    else:
        form = ContentForm()
    return render(
        request,
        "demo_app/index.html",
        {"form": form, "submitted_json": submitted_json},
    )
