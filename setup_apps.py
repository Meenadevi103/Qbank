import os

apps = ['core', 'departments', 'subjects', 'papers', 'dashboard']

for app in apps:
    os.makedirs(app, exist_ok=True)
    os.makedirs(os.path.join(app, 'migrations'), exist_ok=True)
    
    with open(os.path.join(app, '__init__.py'), 'w') as f:
        pass
        
    with open(os.path.join(app, 'migrations', '__init__.py'), 'w') as f:
        pass
        
    with open(os.path.join(app, 'admin.py'), 'w') as f:
        f.write("from django.contrib import admin\n")
        
    with open(os.path.join(app, 'apps.py'), 'w') as f:
        f.write(f"from django.apps import AppConfig\n\nclass {app.capitalize()}Config(AppConfig):\n    default_auto_field = 'django.db.models.BigAutoField'\n    name = '{app}'\n")
        
    with open(os.path.join(app, 'models.py'), 'w') as f:
        f.write("from django.db import models\n")
        
    with open(os.path.join(app, 'views.py'), 'w') as f:
        f.write("from django.shortcuts import render\n")
        
    with open(os.path.join(app, 'urls.py'), 'w') as f:
        f.write("from django.urls import path\nfrom . import views\n\napp_name = '%s'\n\nurlpatterns = [\n]\n" % app)

print("Apps created successfully.")
