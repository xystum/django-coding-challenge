from django.urls import path

from .views import expiration_notification_view

url_patterns = [
    path('send/', expiration_notification_view, name='sent-expiration-notifications'),
]
