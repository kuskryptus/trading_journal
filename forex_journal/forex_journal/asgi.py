"""
ASGI config for forex_journal project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import logging
from django.core.asgi import get_asgi_application


# Add this line to configure logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

application = get_asgi_application()

log.debug("ASGI configuration complete.")
