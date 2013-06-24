import datetime
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from tastypie import http
from tastypie import fields
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS, NBResource
from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication, Authentication
from tastypie.authorization import Authorization
from tastypie.models import ApiKey
from tastypie.exceptions import NotFound, ImmediateHttpResponse
from swingtime.models import Event, Occurrence, OccurrenceManager
from notes.models import Notes
from doli.models import Entry

class SillyAuthentication(BasicAuthentication):
    def is_authenticated(self, request, **kwargs):
        print request.user.username
        if 'dolimobile' in request.user.username:
          return True

        return False

    # Optional but recommended
    def get_identifier(self, request):
        return request.user.username


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
        authentication = ApiKeyAuthentication()
        filtering = {
            'username': ALL,
        }
        allowed_methods = ['get']


class EntryResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = Entry.objects.all()
        resource_name = 'entry'
        authorization = Authorization()
        filtering = {
            'user': ALL_WITH_RELATIONS,
            'pub_date': ['exact', 'lt', 'lte', 'gte', 'gt'],
        }


class UserSignUpResource(ModelResource):

    class Meta:
        object_class = User
        queryset = User.objects.all()
        allowed_methods = ['post']
        include_resource_uri = False
        resource_name = 'newuser'
        excludes = ['is_active','is_staff','is_superuser']
        authentication = ApiKeyAuthentication()
        authorization = Authorization()

    def obj_create(self, bundle, **kwargs):
        try:
            bundle = super(UserSignUpResource, self).obj_create(bundle, **kwargs)
            bundle.obj.set_password(bundle.data.get('password'))
            bundle.obj.save()
        except IntegrityError, e:
            raise ImmediateHttpResponse(response=http.HttpBadRequest(e.message))

    def dehydrate_title(self, bundle):
        return "User" + bundle.data.get('username') + 'has signed up.'


class NoteResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = Notes.objects.all()
        resource_name = 'notes'
        allowed_methods = ['get', 'post', 'put']
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        filtering = {
            'user' : ALL_WITH_RELATIONS
        }

    def get_object_list(self, request):
        return super(NoteResource, self).get_object_list(request).filter(user=request.user)


''' This class manages the calendar event resource
Note: the events is managed by swingtime Event and Occurrence to get all the information
of the Event.
'''
class EventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        resource_name = 'events'
        allowed_methods = ['get', 'post', 'put']
        authentication = ApiKeyAuthentication()

    def get_object_list(self, request):

        return super(EventResource, self).get_object_list(request).filter(user=request.user)


class ApiTokenResource(ModelResource):
    class Meta:
        queryset = ApiKey.objects.all()
        resource_name = 'token'
        include_resource_uri = False
        fields = ['key']
        detail_allowed_methods = ['get']
        authentication = BasicAuthentication()

    def get_object_list(self, request):
        return super(ApiTokenResource, self).get_object_list(request).filter(user=request.user)

''' #Jing: obj_get might be better performing, need to look what's the issue here later
    def obj_get(self, request=None, **kwargs):
        if kwargs['pk'] != 'auth':
            raise NotImplementedError("Resource not found")

        user = request.user
        if not user.is_active:
            raise NotFound("User not active")

        api_key = ApiKey.objects.get(user=request.user)
        return api_key

'''

class EventOccurrenceResource(NBResource):
    events = fields.ToOneField(EventResource, 'event', full=True)
    class Meta:
        queryset = Occurrence.objects.all()
        manager_filters = ('daily_occurrences')
        resource_name = 'today_events'
        allowed_methods = ['get']
        authentication = ApiKeyAuthentication()

    def get_object_list(self, request):
        dtyear = None
        dtmonth = None
        dtday = None

        if 'dtyear' in request.GET:
            dtyear = request.GET['dtyear']
        if 'dtmonth' in request.GET:
            dtmonth = request.GET['dtmonth']
        if 'dtday' in request.GET:
            dtday = request.GET['dtday']
        if dtyear and dtmonth and dtday:
            try:
                print '%s %s %s user: %s'%(dtyear,dtmonth, dtday, request.user)
                dt = datetime.datetime(int(dtyear), int(dtmonth), int(dtday))
            except ValueError, e:
                return e
        else:
            dt = None

        return super(EventOccurrenceResource, self).get_object_list(request).filter(user=request.user, start_time=dt)
