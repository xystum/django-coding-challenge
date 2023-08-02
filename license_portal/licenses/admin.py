from django.contrib import admin

from .models import Client, License

admin.site.register(License)
admin.site.register(Client)
