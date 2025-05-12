
import re
from django.http import HttpResponseForbidden

class AdminIPRestrictionMiddleware:
    ALLOWED_IPS = ['117.213.202.158','127.0.0.1','10.10.13.250' '::1']  # You can add more IPs here

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Restrict access only for admin pages
        if re.match(r'^/admin/', request.path):
            client_ip = request.META.get('REMOTE_ADDR', '')

            if client_ip not in self.ALLOWED_IPS:
                return HttpResponseForbidden("You are not allowed to access the admin page.")

        response = self.get_response(request)
        return response
