"""
WSGI configuration for PythonAnywhere
"""

import sys
import os

# Add your project directory to the sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import the Flask app
from main import app as application

# Optional: Configure logging
import logging
logging.basicConfig(stream=sys.stderr)
