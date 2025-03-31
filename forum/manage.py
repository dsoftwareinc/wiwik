#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import logging
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    if "--no-logs" in sys.argv:
        print("> Disabling logging levels of CRITICAL and below.")
        sys.argv.remove("--no-logs")
        logging.disable(logging.CRITICAL)

    if "--parallel" in sys.argv:
        import multiprocessing

        multiprocessing.set_start_method("fork")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
