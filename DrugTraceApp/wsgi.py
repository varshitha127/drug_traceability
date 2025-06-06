import os
import sys
from pathlib import Path

# Add the project directory to the Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DrugTraceApp.settings_prod')

# Import Django's WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 