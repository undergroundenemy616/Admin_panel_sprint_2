import datetime
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _


class BlockUnpaidTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'tenant'):
            if (request.tenant.paid_until is None) or \
                    (request.tenant.paid_until <= datetime.date.today()):
                return HttpResponseForbidden(_('Unpaid'))

        return self.get_response(request)
