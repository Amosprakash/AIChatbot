import sys

# Path to your Flask application directory
sys.path.insert(0, 'folder name')

# Path to virtual environment site-packages
venv_site_packages = r'path of the venv file '
sys.path.insert(0, venv_site_packages)

# Import your Flask application
from myapp import app

# Define the WSGI application object
application = app
