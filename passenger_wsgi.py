import os
import sys

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

# Import WSGI application for Phusion Passenger (cPanel hosting)
from config.wsgi import application
