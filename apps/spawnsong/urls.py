from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from . import admin as spawnsong_admin

# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'spawnsong.views.frontpage', name='frontpage'),

    # For social auth (facebook, twitter etc) uncomment this line
    url(r'', include('social_auth.urls')),
    

    url(r'^password/change/$',
                  auth_views.password_change,
                  name='password_change'),
    url(r'^password/change/done/$',
                  auth_views.password_change_done,
                  name='password_change_done'),
    url(r'^password/reset/$',
                  auth_views.password_reset,
                  name='password_reset'),
    url(r'^password/reset/done/$',
                  auth_views.password_reset_done,
                  name='password_reset_done'),
    url(r'^password/reset/complete/$',
                  auth_views.password_reset_complete,
                  name='password_reset_complete'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
                  auth_views.password_reset_confirm,
                  name='password_reset_confirm'),
                  
    
    url(r'^accounts/register/$',
        views.RegistrationView.as_view(),
        name='registration_register'),
        
    (r'^accounts/', include('registration.auth_urls')),
                    
    # Overwise use these lines for username/password auth
    url(r'^login/$', 'django.contrib.auth.views.login',name="login"),
    url(r'^logout/$', 'django.contrib.auth.views.logout',name="logout"),
    
    url(r'^s/([^/]+)/$', 'spawnsong.views.snippet',name="snippet"),
    url(r'^s/([^/]+)/upload-full/$', 'spawnsong.views.upload_full',name="snippet-upload-full"),
    url(r'^u/([^/]+)/$', 'spawnsong.views.user',name="user"),
    url(r'^upload/$', 'spawnsong.views.upload',name="upload"),
    url(r'^purchase/$', 'spawnsong.views.purchase',name="purchase"),
    url(r'^download/([^/]+)/([^/]+)/([^/]+)/$', 'spawnsong.views.download_full',name="snippet-download-full"),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(spawnsong_admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()