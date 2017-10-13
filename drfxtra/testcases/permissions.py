from rest_framework.test import APILiveServerTestCase
from ..collect_metadata import get_as_dict
from factory.helpers import build
import os
from django.contrib.auth import get_user_model
from django.template.response import SimpleTemplateResponse
from ..factories import (ActiveUserFactory, StaffUserFactory, SuperuserFactory,
                                    GroupFactory, PermissionFactory, LogEntryFactory, PostFactory)

class Report:
    def __init__(self, user_profile, rows):
        self.user_profile = user_profile
        self.headers = ["Can List Model", "Can Get One", "Can Modify", "Can Delete", "Can Create"]
        self.rows = rows

class PermissionsTestCaseReport(APILiveServerTestCase):
    template_name = "django_shamrock/reports/api_permissions.html"
    user_factories = {'Superuser': SuperuserFactory, 'Staff UserModel': StaffUserFactory,
                        'Regular UserModel': ActiveUserFactory}
    model_factories = {'Regular UserModel': ActiveUserFactory,
                      'Staff UserModel': StaffUserFactory,
                      'Superuser': SuperuserFactory,
                      'Group': GroupFactory,
                      'Permission': PermissionFactory,
                      'Logs': LogEntryFactory,
                       'Posts': PostFactory}
    superuser_factory = SuperuserFactory

    def setUp(self):
        self.superuser = self.superuser_factory(username="admin", password="admin")
        self.client = self.client_class()
        print(self.live_server_url)

    def do_request(self, url, method, **params):
        response = getattr(self.client, method)(url, params)
        if any(response.status_code == code for code in [200, 201, 204]):
            return True
        if any(response.status_code == code for code in [403, 404, 405]):
            return False
        return "Inconclusive: %s" % response.status_code

    def own_user_report(self, user, url):
        own_url = "%s%s/" % (url, user.pk)
        return [
            self.do_request(own_url, "get"),
            self.do_request(own_url, "patch"),
            self.do_request(own_url, "delete")
        ]

    def report_for_model(self, factory, url):
        post_params = build(dict, FACTORY_CLASS=factory)
        post_params.update(getattr(factory, "_rest_params", {}))
        instance = factory()
        instance_url = "%s%s/" % (url, instance.pk)
        return [
            self.do_request(url, "get"),
            self.do_request(instance_url, "get"),
            self.do_request(instance_url, "patch"),
            self.do_request(instance_url, "delete"),
            self.do_request(url, "post", **post_params)
        ]

    def report_for_own_objects(self, user, user_fieldname, factory, url):
        instance = factory(**{user_fieldname: user})
        instance_url = "%s%s/" % (url, instance.pk)
        return [
            self.do_request(instance_url, "get"),
            self.do_request(instance_url, "patch"),
            self.do_request(instance_url, "delete"),
        ]

    def generate_user_report(self, factory, models):
        user = factory()
        user.set_password("0o9i8u7y")
        user.save()
        print(user.username)
        self.client.force_authenticate(user)
        reports = []
        for modelinfo in models:
            modelname = modelinfo['info']['model']['name']
            for k, v in self.model_factories.items():
                if v._meta.model._meta.model_name == modelname:
                    report = [k] + self.report_for_model(v, modelinfo['url'])
                    reports.append(report)
                    for fieldname, field in modelinfo['info']['actions']['GET'].items():
                        if field.get("foreign_key", "") == get_user_model()._meta.object_name:
                            own_obj_report = self.report_for_own_objects(user, fieldname, v, modelinfo['url'])
                            reports.append(["Own %s" % (modelinfo['info']['model']['verbose_name']), "-"] + own_obj_report + ["-"])
        try:
            users_url = [model for model in models if model['info']['model']['name'] == 'user'][0]['url']
            reports.append(["Own UserModel", "-"] + self.own_user_report(user, users_url) + ["-"])
        except KeyError:
            pass
        return reports

    def test_generate_report(self):
        models = get_as_dict(self.superuser)
        reports = []
        for name, factory in self.user_factories.items():
            rows = self.generate_user_report(factory, models)
            report = Report(name, rows)
            reports.append(report)
        response = SimpleTemplateResponse(self.template_name, context={'reports': reports}).render()
        html = response.rendered_content
        file_path = os.path.join(os.getcwd(), "permissions_report.html")
        with open(file_path, "w") as f:
            f.write(html)
        pass

