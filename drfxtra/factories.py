import faker
from django.contrib.auth import get_user_model, models
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from factory import DjangoModelFactory, SubFactory, lazy_attribute, post_generation, lazy_attribute_sequence

fake = faker.Factory.create()

# Get the UserModel
UserModel = get_user_model()

class InactiveUserFactory(DjangoModelFactory):
    first_name = lazy_attribute(lambda o: fake.first_name())
    last_name = lazy_attribute(lambda o: fake.last_name())
    username = lazy_attribute_sequence(lambda o, n: o.first_name + o.last_name + str(n))
    email = lazy_attribute(lambda o: o.username + "@example.com")
    is_active = False
    is_superuser = False
    is_staff = False

    class Meta:
        model = models.User

    _rest_params = {'password1': 'q1w2e3r4', 'password2': 'q1w2e3r4'}

    @post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for item in extracted:
                self.groups.add(item)


    @post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for item in extracted:
                self.permissions.add(item)

class ActiveUserFactory(InactiveUserFactory):
    is_active = True

class StaffUserFactory(ActiveUserFactory):
    is_staff = True

class SuperuserFactory(StaffUserFactory):
    is_superuser = True

class GroupFactory(DjangoModelFactory):
    name = lazy_attribute(lambda o: fake.company())

    class Meta:
        model = models.Group

    @post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for item in extracted:
                self.permissions.add(item)

class PermissionFactory(DjangoModelFactory):
    name = lazy_attribute(lambda o: fake.bs().capitalize())
    codename = lazy_attribute(lambda o: fake.bs().capitalize())
    content_type = ContentType.objects.all().first()

    class Meta:
        model = models.Permission

    _rest_params = {'content_type': ContentType.objects.all().first().id}

    @post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for item in extracted:
                self.groups.add(item)

class LogEntryFactory(DjangoModelFactory):
    action_time = lazy_attribute(lambda o: fake.date_time_this_year())
    user = SubFactory(StaffUserFactory)
    action_flag = 0

    class Meta:
        model = LogEntry