from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class IsOwnerOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(obj.created_by == request.user)
