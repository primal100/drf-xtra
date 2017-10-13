from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION, DELETION, CHANGE
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.options import get_content_type_for_model
from django.utils.encoding import force_text
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.exceptions import NotFound

class XtraViewSetMixin(object):
    filter_fields = ()
    can_write_object_filter = {}
    can_write_object_exclude = {}
    autocomplete_fields = []
    autocomplete_foreign_keys = {}
    set_field_value_to_current_user_on_create = None
    set_field_value_to_current_user_on_update = None
    fieldset_kwarg = "fieldset"
    autocomplete_page_size = None
    log = None

    @cached_property
    def log_write_entres(self):
        if self.log is None:
            return self.queryset.model._meta.object_name in getattr(settings, "LOG_ENTRIES", [])
        return self.log

    def get_serializer_context(self):
        context = super(XtraViewSetMixin, self).get_serializer_context()
        context['fieldset'] = self.request.query_params.get(self.fieldset_kwarg, None)
        return context

    @list_route(methods=['get'], renderer_classes = (JSONRenderer, BrowsableAPIRenderer))
    def autocomplete(self, request, *args, **kwargs):
        fieldname = request.query_params.get("fieldname", None)
        if fieldname:
            if fieldname in self.get_autocomplete_fields():
               queryset = self.filter_queryset(self.queryset)
               flat = True
               fields = (fieldname,)
            else:
                autocomplete_related = self.get_autocomplete_foreign_keys()
                if fieldname in autocomplete_related.keys():
                    queryset = autocomplete_related[fieldname]['queryset']
                    fieldname = autocomplete_related[fieldname]['related_field']
                    fields = ("pk", fieldname)
                    flat = False
                else:
                    raise NotFound(detail=_('Autocomplete is not allowed for %s field' % fieldname))
        else:
            raise NotFound(detail=_("No 'fieldname' paramater provided"))
        istartswith = request.query_params.get("istartswith", None)
        startswith = request.query_params.get("startswith", None)
        icontains = request.query_params.get("icontains", None)
        contains = request.query_params.get("contains", None)
        if istartswith:
            queryset = queryset.filter(**{"%s__istartswith" % fieldname: istartswith})
        elif startswith:
            queryset = queryset.filter(**{"%s__startswith" % fieldname: startswith})
        elif contains:
            queryset = queryset.filter(**{"%s__contains" % fieldname: contains})
        elif icontains:
            queryset = queryset.filter(**{"%s__icontains" % fieldname: icontains})
        try:
            if not queryset.model._meta._forward_fields_map[fieldname].unique:
                queryset = queryset.distinct()
        except (KeyError, AttributeError):
            queryset = queryset.distinct()
        queryset = queryset.order_by(fieldname).values_list(*fields, flat=flat)
        if self.autocomplete_page_size:
            page_size = self.autocomplete_page_size
        elif self.autocomplete_page_size is None:
            page_size = getattr(self.paginator, "page_size", 100)
        else:
            page_size = None
        if page_size:
            queryset = queryset[0:page_size]
        data = list(queryset)
        return Response(data)

    def get_autocomplete_fields(self):
        return self.autocomplete_fields

    def get_autocomplete_foreign_keys(self):
        return self.autocomplete_foreign_keys

    def can_write_object(self, request):
        return self.can_write_object_filter

    def cannot_write_object(self, request):
        return self.can_write_object_exclude

    def perform_create(self, serializer):
        if self.set_field_value_to_current_user_on_create:
            params = {self.set_field_value_to_current_user_on_create: self.request.user}
            instance = serializer.save(**params)
        else:
            instance = serializer.save()
        if self.log_write_entres:
            self.log_addition(instance, 'added')

    def perform_destroy(self, instance):
        instance.delete()
        if self.log_write_entres:
            self.log_deletion(instance, 'deleted')

    def perform_update(self, serializer):
        if self.set_field_value_to_current_user_on_update:
            params = {self.set_field_value_to_current_user_on_update: self.request.user}
            instance = serializer.save(**params)
        else:
            instance = serializer.save()
        if self.log_write_entres:
            self.log_change(instance, 'changed')

    def log_addition(self, object, message):
        """
        Log that an object has been successfully added.
        The default implementation creates an admin LogEntry object.
        """
        return LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=force_text(object),
            action_flag=ADDITION,
            change_message=message,
        )

    def log_change(self, object, message):
        """
        Log that an object has been successfully changed.
        The default implementation creates an admin LogEntry object.
        """
        return LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=force_text(object),
            action_flag=CHANGE,
            change_message=message,
        )

    def log_deletion(self, object, message):
        """
        Log that an object will be deleted. Note that this method must be
        called before the deletion.
        The default implementation creates an admin LogEntry object.
        """
        return LogEntry.objects.log_action(
            user_id=self.request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=force_text(object),
            action_flag=DELETION,
            change_message=message,
        )