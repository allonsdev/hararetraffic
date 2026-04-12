import threading
from django.utils.deprecation import MiddlewareMixin
from .models import SiteVisitLog

thread_local = threading.local()

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LogSiteVisitMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log every site visit.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Exclude admin or static/media paths
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None

        user = request.user if request.user.is_authenticated else None
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')

        # Save asynchronously in a separate thread to reduce request time
        def save_log():
            SiteVisitLog.objects.create(
                user=user,
                path=request.path,
                full_path=request.get_full_path(),
                method=request.method,
                ip_address=ip,
                user_agent=user_agent,
                referrer=referrer
            )

        threading.Thread(target=save_log).start()
        return None
    

class SiteVisitMiddleware:
    EXCLUDED_PREFIXES = ('/static/', '/favicon', '/admin/jsi18n/')
 
    def __init__(self, get_response):
        self.get_response = get_response
 
    def __call__(self, request):
        response = self.get_response(request)
 
        # Skip static files and noise
        path = request.path
        if any(path.startswith(p) for p in self.EXCLUDED_PREFIXES):
            return response
 
        try:
            from .models import SiteVisitLog
            SiteVisitLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                path=path,
                full_path=request.get_full_path(),
                method=request.method,
                ip_address=self._get_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                referrer=request.META.get('HTTP_REFERER', '')[:500],
            )
        except Exception:
            pass  # Never let logging break the request cycle
 
        return response
 
    def _get_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')