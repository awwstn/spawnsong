from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'spawnsong.views.frontpage', name='frontpage'),

    # For social auth (facebook, twitter etc) uncomment this line
    url(r'', include('social_auth.urls')),

    # Overwise use these lines for username/password auth
    url(r'^login/$', 'django.contrib.auth.views.login',name="login"),
    url(r'^logout/$', 'django.contrib.auth.views.logout',name="logout"),
    
    url(r'^s/([^/]+)/$', 'spawnsong.views.snippet',name="snippet"),
    url(r'^u/([^/]+)/$', 'spawnsong.views.user',name="user"),
    url(r'^upload/$', 'spawnsong.views.upload',name="upload"),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
