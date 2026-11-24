from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def org_atual(request):
    perfil = getattr(request.user, "perfil", None)
    return perfil.organizacao if perfil else None


def papel_requerido(*papeis):
    def deco(view):
        @wraps(view)
        def wrapper(request, *a, **kw):
            perfil = getattr(request.user, "perfil", None)
            if perfil is None or (papeis and perfil.papel not in papeis):
                raise PermissionDenied
            return view(request, *a, **kw)

        return login_required(login_url="login")(wrapper)

    return deco


class DaEquipe(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, "perfil")
