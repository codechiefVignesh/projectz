"""
WSGI config for online_judge project.
Updated for Vercel deployment.
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to Python path
project_home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_home not in sys.path:
    sys.path.append(project_home)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_judge.settings')

application = get_wsgi_application()

# Vercel requires this
app = application