import os
import sys

sys.path.insert(0, '/Users/ismailpunnol/e-commerceshoes-copy-5/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
