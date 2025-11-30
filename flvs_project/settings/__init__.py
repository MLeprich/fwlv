"""
Settings Module - loads the correct environment configuration
"""

import os

# Determine environment via DJANGO_SETTINGS_MODULE or environment variable
env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *
