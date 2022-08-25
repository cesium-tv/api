from django.contrib.auth.backends import ModelBackend


class TimcastBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        pass
