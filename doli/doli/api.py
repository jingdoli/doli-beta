import datetime
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, DatabaseError
from django.db import transaction
from django.db import connection

try:
    from django.conf.urls import patterns, url
except ImportError: # Django < 1.4
    from django.conf.urls.defaults import patterns, url
from tastypie import http
from tastypie import fields
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication, Authentication
from tastypie.authorization import Authorization
from tastypie.models import ApiKey
from tastypie.exceptions import NotFound, ImmediateHttpResponse
from tastypie.utils import trailing_slash
from swingtime.models import Event, Occurrence, OccurrenceManager
from notes.models import Notes
from doli.models import Entry

# by Michal migajek Gajek

class NBResource(ModelResource):
    class Meta:        
        abstract = True
        
        # there are three options for specifying filters.
        # it's either a dictionary of 'filter_name': queryset
        # or a tuple of filter names
        # in the second case, if the default_manager attribute is provided
        # the filter name is assumed to be Manager method, 
        # otherwise it's assumed to be QuerySet method
        default_manager = None 
        manager_filters = ()
        
    def prepend_urls(self):
        """ if there are allowed custom Manager methods, add special url for that"""
        return [
                 url(r"^(?P<resource_name>%s)/filtered_list/(?P<filter>\w+)%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('dispatch_list_filtered'), name="api_dispatch_list_filtered"),
        ] if self._meta.manager_filters else []
        
    def dispatch_list_filtered(self, request, **kwargs):
        """ check if the provided filter name is valid, and - if so - proceed to the get_object_list """ 
        mfilter = kwargs.pop('filter')
        filters = self._meta.manager_filters        
        if (isinstance(filters, dict) and not mfilter in filters.keys()) or \
            not mfilter in filters:
                raise Exception('Invalid filter (%s) name provided' % filter)
                
        request.custom_filter = mfilter
        return self.dispatch_list(request)

    def get_object_list(self, request):        
        """ applies custom filtering if the filter name was provided """
        if hasattr(request, 'custom_filter'):
            filters = self._meta.manager_filters
            if isinstance(filters, dict):
                # filter to apply is in fact a name of queryset specified in Resource 
                queryset = filters[request.custom_filter]._clone()
            else:
                # if there's a default_manager, filter is it's method
                # otherwise we assume filter is a method of default QuerySet
                manager_or_queryset = self._meta.default_manager or super(NBResource, self).get_object_list(request)
                method = getattr(manager_or_queryset, request.custom_filter)
                if not method:
                    raise Exception('Manager or QuerySet does not have method named %s' % request.custom_filter)
                
                #FIXME: very, very ugly trick...                
                kwargs = request.GET.dict()
                if 'format' in kwargs.keys():
                    kwargs = deepcopy(kwargs)
                    kwargs.pop('format')
                queryset = method(**kwargs) 
        else:
            queryset = super(NBResource, self).get_object_list(request)
        return queryset

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
	#TODO: Add input validation!!

    def obj_create(self, bundle, **kwargs):
        try:
            bundle = super(UserSignUpResource, self).obj_create(bundle, **kwargs)
            bundle.obj.set_password(bundle.data.get('password'))
            bundle.obj.save()
        except (DatabaseError, IntegrityError), e:
            connection.close()
            self.rollback([bundle])
            raise ImmediateHttpResponse(http.HttpBadRequest("User name or email has already been taken!"))
	except ValueError, e:
            self.rollback([bundle])
            raise ImmediateHttpResponse(http.HttpBadRequest("Invalid input string."))
        except Exception, e:
            self.rollback([bundle])
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
