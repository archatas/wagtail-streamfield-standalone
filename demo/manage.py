#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Make wagtail_streamfield_standalone importable from the repo root
# without requiring `pip install -e ..` first.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo_project.settings")

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
