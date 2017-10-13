from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from rest_framework import viewsets, mixins
from rest_framework.pagination import CursorPagination
from rest_framework.authtoken.models import Token
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from .serializers import (
    UserSerializer, UserUpdateSerializer, StaffUserSerializer, StaffUserUpdateSerializer, RegularUserSerializer,
    GroupSerializer, LogSerializer, SiteSerializer, TokenSerializer, PermissionsSerializer
)
from .permissions import UserPermissions, WriteObjectPermission, IsSuperuser
from rest_framework.permissions import IsAdminUser
from django.contrib.sites.models import Site
from .mixins import XtraViewSetMixin

UserModel = get_user_model()

class UserViewSet(XtraViewSetMixin, viewsets.ModelViewSet):

    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    permission_classes = (UserPermissions, WriteObjectPermission)
    ordering = ('-date_joined',)
    filter_fields = ('username', 'email', 'first_name', 'last_name', 'last_login', 'date_joined', 'is_superuser', 'is_staff', 'is_active')
    ordering_fields = ('id', 'username', 'email', 'first_name', 'last_name', 'last_login', 'date_joined',
                       'is_superuser', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'last_login', 'date_joined')
    autocomplete_fields = ("username", "email", "first_name", "last_name")
    log = True

    def can_write_object(self, request):
        if request.user.is_superuser:
            return {}
        elif request.user.is_staff:
            return {'is_staff': False}
        return {'id': request.user.id}

    def get_serializer_class(self):
        user = self.request.user
        method = self.request.method
        if any(m == method for m in ['PUT', 'PATCH']):
            if user.is_superuser:
                return UserUpdateSerializer
            if user.is_staff:
                return StaffUserUpdateSerializer
        if user.is_superuser:
            return UserSerializer
        if user.is_staff:
            return StaffUserSerializer
        return RegularUserSerializer

    def get_queryset(self):
        user = self.request.user
        if user:
            if user.is_staff:
                return self.queryset
        return self.queryset.filter(is_staff=False)

class LogViewSet(XtraViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows logs to be  viewed, created, updated or deleted.
    """
    queryset = LogEntry.objects.all().order_by('-action_time')
    serializer_class = LogSerializer
    filter_fields = ('user', 'action_time', 'object_id', 'object_repr', 'action_flag', 'change_message')
    ordering_fields = ('action_time',)
    ordering = "-action_time"
    pagination_class = CursorPagination
    permission_classes = (IsAdminUser,)
    page_size = 20
    autocomplete_foreign_keys = {'user':{'queryset': get_user_model().objects.all(), 'related_field': 'username'},
                                 'content_type': {'queryset': ContentType.objects.all(), 'related_field': 'model'}}

class GroupViewSet(XtraViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed, created, updated or deleted.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_fields = ('name',)
    ordering_fields = ('id', 'name')
    ordering = ('id',)
    permission_classes = (IsSuperuser,)
    log = True

class PermissionViewSet(XtraViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed, created, updated or deleted.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionsSerializer
    filter_fields = ('name', 'content_type', 'codename')
    search_fields = ('name', 'codename')
    ordering_fields = ('id', 'name', 'content_type', 'codename')
    ordering = ('id',)
    permission_classes = (IsSuperuser)
    autocomplete_fields = ("name", "codename")
    log = True

class SiteViewSet(XtraViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows sites to be viewed, created, updated or deleted.
    """
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    filter_fields = ('domain', 'name')
    ordering_fields = ('id', 'domain', 'name')
    ordering = ('id',)
    permission_classes = (IsSuperuser,)
    log = True

class TokenViewSet(XtraViewSetMixin, viewsets.ReadOnlyModelViewSet, mixins.DestroyModelMixin, mixins.CreateModelMixin):
    """
    API endpoint that allows tokens to be viewed, created or deleted.
    """
    queryset = Token.objects.all()
    serializer_class = TokenSerializer
    filter_fields = ("key", "user", "created")
    ordering_fields = ('key', 'user', 'created')
    ordering = ('-created',)
    permission_classes = (IsSuperuser,)
    log = True