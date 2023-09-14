#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


if __name__ == "__main__":
    # Add parent dir to PYTHONPATH to allow `tests_django` import
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        os.environ.setdefault("DJANGO_CONFIGURATION", "Test")
    else:
        os.environ.setdefault("DJANGO_CONFIGURATION", "Development")

    from configurations.management import execute_from_command_line

    execute_from_command_line(sys.argv)
