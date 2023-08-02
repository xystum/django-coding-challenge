from datetime import timedelta
from typing import Any, Final, List

from django.core.mail import send_mail
from django.db.models import Q
from django.template import Template
from django.template.loader import get_template
from django.utils.timezone import now

from .models import Client

DEFAULT_FROM_EMAIL = 'noreply@email.com'


class EmailNotification:
    """ A convenience class to send email notifications
    """
    subject = None  # type: str
    from_email = DEFAULT_FROM_EMAIL  # type: str
    template_path = None  # type: str

    @classmethod
    def load_template(cls) -> Template:
        """Load the configured template path"""
        return get_template(cls.template_path)

    @classmethod
    def send_notification(cls, recipients: List[str], context: Any):
        """Send the notification using the given context"""
        template = cls.load_template()
        message_body = template.render(context=context)
        send_mail(cls.subject, message_body, cls.from_email, recipients, fail_silently=False)


class NotificationCounter:
    _count: int = 0

    def update(self, number: int) -> None:
        self._count += number

    def get(self) -> int:
        return self._count


GLOBAL_NOTIFICATION_COUNTER: NotificationCounter = NotificationCounter()


class ExpirationEmailNotification(EmailNotification):
    subject = 'Licenses about to expire'
    template_path = 'licenses/expiration_notification.html'


LICENSE_EXPIRATION_NOTIFICATION_DELTA: Final[timedelta] = timedelta(days=120)


def today_is_monday() -> bool:
    return now().weekday() == 0


class ExpirationNotificationHandler:

    CASE_4_MONTHS = Q(expiration_datetime__date=now().date() + LICENSE_EXPIRATION_NOTIFICATION_DELTA)
    CASE_MONDAY = Q(expiration_datetime__date=now().date() + timedelta(days=30))
    CASE_WEEK = Q(expiration_datetime__date=now().date() + timedelta(days=7))

    def __init__(self, counter: NotificationCounter):
        self.counter = counter
        self.is_monday = today_is_monday()

        if not self.is_monday:
            self.CASE_MONDAY = Q()

    def run(self) -> None:
        for client in Client.objects.all().prefetch_related('licenses'):
            licenses = client.licenses.filter(self.CASE_4_MONTHS | self.CASE_MONDAY | self.CASE_WEEK)
            if not licenses:
                return

            notification = ExpirationEmailNotification()
            notification.send_notification(recipients=[client.poc_contact_email],
                                           context=dict(client=client, licenses=list(licenses)))

            self.counter.update(licenses.count())
