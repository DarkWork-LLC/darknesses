#!/usr/bin/env python3
import os
import sys
import threading
import time


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "darkness_django.settings.local")
    
    # Check if we're starting the MUD server alongside Django
    args = sys.argv[1:]
    start_mud = '--start-mud' in args or '-m' in args
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        
        # If starting MUD server with Django, do so in a separate thread
        if start_mud:
            mud_thread = threading.Thread(target=_start_mud_soon, daemon=True)
            mud_thread.start()
        
        execute_from_command_line(sys.argv)
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc


def _start_mud_soon():
    """Start the MUD server after a short delay to let Django initialize."""
    import time
    time.sleep(2)  # Small delay
    os.system('python manage.py start_mud_server > /dev/null 2>&1 &')


if __name__ == "__main__":
    main()
