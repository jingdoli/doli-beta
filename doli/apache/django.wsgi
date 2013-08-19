import os,sys

apache_configuration = os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)
sys.path.append(workspace)
sys.path.append('/home/doli-beta/doli-beta/doli')

os.environ['DJANGO_SETTINGS_MODULE'] = 'doli.settings'

activate_env=os.path.expanduser("home/ubuntu/.virtualenvs/dolibeta/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
