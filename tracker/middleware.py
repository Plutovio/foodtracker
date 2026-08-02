from django.contrib.auth import get_user_model, login


class AutoLoginMiddleware:
    """
    Automatically logs in the 'resident' user on every request.
    This removes the need for a login page on this single-user personal app.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            User = get_user_model()
            try:
                user = User.objects.get(username='resident')
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
            except User.DoesNotExist:
                pass
        return self.get_response(request)
