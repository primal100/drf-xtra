from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth import password_validation
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.models import LogEntry
from django.contrib.sites.models import Site
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from django.utils import six
from collections import OrderedDict

# Get the UserModel
UserModel = get_user_model()

class PasswordField(serializers.CharField):

    def __init__(self, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 128)
        kwargs['write_only'] = True
        super(PasswordField, self).__init__(**kwargs)

class PKStringRelatedField(PrimaryKeyRelatedField):
    has_pk_and_string = True
    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([
            (
                item.pk,
                self.display_value(item)
            )
            for item in queryset
        ])

    def use_pk_only_optimization(self):
        return False

    def to_representation(self, value):
        pk_attname = value._meta.pk.attname
        if self.pk_field is not None:
            return {pk_attname: self.pk_field.to_representation(value.pk), 'value': six.text_type(value)(value)}
        return {pk_attname: value.pk, 'value': str(value)}

class XtraModelSerializer(serializers.ModelSerializer):
    fieldsets = {}

    def choose_fields_by_fieldset(self, fields, fieldset_name):
        fieldnames = self.fieldsets.get(fieldset_name)
        if fieldnames:
            fieldset = [f for f in fields if f.field in fieldnames]
        elif fieldset_name == "list":
                fieldset = [f for f in fields if not f.many]
        elif fieldset_name == "writable":
            fieldset = [f for f in fields if not f.read_only]
        elif fieldset_name == "no_related":
            fieldset = [f for f in fields if not f.related]
        elif fieldset_name == "writable_no_related":
            fieldset = [f for f in fields if not f.related and not f.read_only]
        else:
            fieldset = fields
        return fieldset

    def get_fields(self):
        fields = super(XtraModelSerializer, self).get_fields()
        fieldset_name = self.context.get("fieldset", None)
        if fieldset_name:
            fields = self.choose_fields_by_fieldset(fields, fieldset_name)
        return fields

class UserDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
        read_only_fields = ('id', 'email', 'is_staff', 'is_superuser')

class UserSerializer(XtraModelSerializer):

    serializer_related_field = PKStringRelatedField
    is_active = serializers.BooleanField(read_only=False, required=False, initial=True)
    password = PasswordField(required=True)

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 'last_login',
                  'date_joined', 'is_superuser', 'is_staff', 'is_active', 'groups', 'user_permissions')
        read_only_fields = ('id', 'last_login', 'date_joined')
        write_only_fields = ('password')


    def create(self, validated_data):
        return UserModel.objects.create_user(username=validated_data.pop("username"),
                                                    email=validated_data.pop("email"),
                                                    password=validated_data.pop("password"),
                                                    first_name=validated_data.pop("first_name", None),
                                                    last_name = validated_data.pop("last_name", None),
                                                    is_active=validated_data.pop("is_active", False),
                                                    is_staff=validated_data.pop("is_staff", False),
                                                    is_superuser=validated_data.pop("is_superuser", False)
                                                    )

    def validate(self, value):
        data = super(UserSerializer, self).validate(value)
        password = value.pop('password', None)
        if password:
            password_validation.validate_password(password, user=self.instance)
            data['password'] = password
        return data

class UserUpdateSerializer(UserSerializer):
    old_password = PasswordField(required=False, allow_blank=True, allow_null=True)
    password = PasswordField(required=False, allow_blank=True, allow_null=True)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            old_password = validated_data.pop("old_password", None)
            request = self.context.get("request")
            current_user = request.user
            if not current_user.is_superuser and current_user == self.instance and not self.instance.check_password(
                    old_password):
                raise ValidationError(
                    _("The old password given is incorrect."),
                    code='incorrect_password',
                )
            else:
                instance.set_password(password)
        return super(UserSerializer, self).update(instance, validated_data)

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'old_password', 'password', 'email', 'first_name', 'last_name',
                  'is_superuser', 'is_staff', 'is_active', 'groups', 'user_permissions')
        read_only_fields = ('id',)
        write_only_fields = ('old_password', 'password')


class StaffUserSerializer(UserSerializer):

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 'last_login',
                  'date_joined', 'is_superuser', 'is_staff', 'is_active', 'groups', 'user_permissions')
        write_only_fields = ('old_password', 'password')
        read_only_fields = ('id', 'last_login', 'date_joined', 'is_staff', 'is_superuser')

class StaffUserUpdateSerializer(UserUpdateSerializer):
    old_password = PasswordField(required=False, allow_blank=True, allow_null=True)
    password = PasswordField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = UserModel
        fields = (
        'id', 'username', 'old_password', 'password', 'email', 'first_name', 'last_name', 'is_active', 'groups', 'user_permissions')
        read_only_fields = ('id',)
        write_only_fields = ('old_password', 'password')

class RegularUserSerializer(UserSerializer):
    class Meta:
        model = UserModel
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_staff', 'is_superuser', 'is_active')
        read_only_fields = fields

class PermissionsSerializer(serializers.ModelSerializer):
    serializer_related_field = PKStringRelatedField
    class Meta:
        model = Permission
        fields = ('id', 'name', 'content_type', 'codename')

class GroupSerializer(serializers.ModelSerializer):
    serializer_related_field = PKStringRelatedField
    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions')

class LogSerializer(serializers.ModelSerializer):
    serializer_related_field = PKStringRelatedField

    class Meta:
        model = LogEntry
        fields = (
        'id', 'action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message')
        read_only_fields = fields

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ("id", "domain", "name")

class TokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = Token
        fields = ("key", "user", "created")