from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

from django.views.generic.simple import direct_to_template

from django.contrib import admin
from doli.api import NoteResource, ApiTokenResource, EventResource, UserResource, EntryResource, UserSignUpResource

from tastypie.api import Api

admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(NoteResource())
v1_api.register(ApiTokenResource())
v1_api.register(EventResource())
v1_api.register(EntryResource())
v1_api.register(UserResource())
v1_api.register(UserSignUpResource())

urlpatterns = patterns("",
    url(r"^$", direct_to_template, {"template": "homepage.html"}, name="home"),
    url(r"^admin/", include(admin.site.urls)),

    url(r"^account/", include("account.urls")),
    url(r"^calendar/", include("swingtime.urls")),
    url(r'^notes/', include('notes.urls')),
    url(r'', include('social_auth.urls')),
    url(r"^accounts/profile/$", direct_to_template, {"template": "homepage.html"}),
    url(r'^api/', include(v1_api.urls)),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
