from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import BasicAuthentication, ApiKeyAuthentication
from tastypie.models import ApiKey
from tastypie.exceptions import NotFound
from doli.models import Entry


class UserResource(ModelResource):
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        excludes = ['email', 'password', 'is_active', 'is_staff', 'is_superuser']
        allowed_methods = ['get']
        authentication = BasicAuthentication()


class EntryResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        queryset = Entry.objects.all()
        resource_name = 'entry'


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
