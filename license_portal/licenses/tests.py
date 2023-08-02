from datetime import timedelta
from typing import List
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now
from licenses.models import Client, License
from licenses.notifications import ExpirationNotificationHandler, NotificationCounter


class TestExpirationNotificationView:

    def test_method_not_allowed_returns_405(self, client):
        response = client.get(reverse('sent-expiration-notifications'))
        assert response.status_code == 405

    @pytest.mark.django_db
    def test_returns_number_of_notifications(self, client):
        response = client.post(reverse('sent-expiration-notifications'))
        assert response.status_code == 200
        assert response.content == b'0'


class TestNotificationCounter:

    def test_update_and_get(self):
        counter = NotificationCounter()
        assert counter.get() == 0
        counter.update(1)
        assert counter.get() == 1


def license_factory(**kwargs) -> License:
    client = Client.objects.get_or_create(
            client_name='name',
            poc_contact_name='content name',
            poc_contact_email='client-poc_contact_email',
            admin_poc=User.objects.get_or_create(username='name')[0],
        )[0]

    return License.objects.get_or_create(
        client=client,
        package=0,
        license_type=0,
        **kwargs
    )[0]


@pytest.fixture
def licenses() -> List[License]:
    license1 = license_factory(expiration_datetime=now() + timedelta(days=7))
    license2 = license_factory(expiration_datetime=now() + timedelta(days=120))
    license3 = license_factory(expiration_datetime=now() + timedelta(days=30))
    return [license1, license2, license3]


@pytest.mark.django_db
class TestExpirationNotificationHandler:

    def test_run(self, licenses):
        counter = NotificationCounter()

        with patch('licenses.notifications.today_is_monday', Mock(return_value=True)), \
                patch('licenses.notifications.ExpirationEmailNotification') as email_handler:
            handler = ExpirationNotificationHandler(counter)
            handler.run()

        email_handler.return_value.send_notification.assert_called_with(
            recipients=['client-poc_contact_email'],
            context={'client': licenses[0].client, 'licenses': licenses}
        )
        assert handler.counter.get() == len(licenses)
