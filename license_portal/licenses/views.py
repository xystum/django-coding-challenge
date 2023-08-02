from django.http import HttpResponse, HttpResponseNotAllowed
from django.http.request import HttpRequest
from django.views.decorators.csrf import csrf_exempt

from .notifications import GLOBAL_NOTIFICATION_COUNTER, ExpirationNotificationHandler


@csrf_exempt
def expiration_notification_view(request: HttpRequest) -> HttpResponse:
    if request.method != 'POST':
        return HttpResponseNotAllowed(permitted_methods=['POST'])

    counter = GLOBAL_NOTIFICATION_COUNTER

    handler = ExpirationNotificationHandler(counter)
    handler.run()

    return HttpResponse(counter.get())
