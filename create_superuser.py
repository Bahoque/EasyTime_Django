import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'easytime.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='GAVIRIA').exists():
    User.objects.create_superuser('GAVIRIA', 'gaviria@gmail.com', '1234567')
    print("Superuser creado")