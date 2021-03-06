from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'timetable.university.views.home', name='home'),
    url(r'^favicon\.ico$', RedirectView.as_view(url='static/icons/favicon.ico')),
    url(r'^info/$', 'timetable.university.views.info'),
    url(r'^accounts/login/$', 'django_usic_sso.views.login', name='login'),
#    url(r'^accounts/login/$', 'timetable.university.auth_debug.login', name='login'),
    url(r'^accounts/logout/$', 'django_usic_sso.views.logout', name='logout'),
#    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^accounts/profile/$', 'timetable.university.views.profile', name='profile'),
    url(r'^my/$', 'timetable.university.views.my'),
    url(r'^my/(?P<week>\d+)/$', 'timetable.university.views.my'),
    url(r'^lecturer/timetable/(?P<lecturer>[^/]*)/$', 'timetable.university.views.lecturer_timetable'),
    url(r'^lecturer/timetable/(?P<lecturer>[^/]*)/(?P<week>\d+)/$', 'timetable.university.views.lecturer_timetable'),
    url(r'^ical/(?P<url>\w+)/$', 'timetable.university.views.ical'),
    url(r'^tt/(?P<timetable_id>\d+)/$', 'timetable.university.views.timetable'),
    url(r'^version/(?P<version_id>\d+)/$', 'timetable.university.views.version'),
    url(r'^version/csv/(?P<version_id>\d+)/$', 'timetable.university.views.csv_export'),
    url(r'^edit/(?P<version_id>\d+)/$', 'timetable.university.views.edit_timetable', name='edit_timetable'),
    url(r'^submit/(?P<version_id>\d+)/$', 'timetable.university.views.submit_timetable', name='submit_timetable'),
    url(r'^upload/(?P<timetable_id>\d+)/$', 'timetable.university.views.upload_timetable', name='upload_timetable'),
    url(r'^compare/(?P<version_left>\d+)/(?P<version_right>\d+)/$', 'timetable.university.views.compare'),
    url(r'^approve/(?P<version_left>\d+)/(?P<version_right>\d+)/$', 'timetable.university.views.approve'),
    url(r'^enroll/(?P<timetable_id>\d+)/(?P<discipline>[^/]+)/(?P<group>[^/]+)/$', 'timetable.university.views.enroll'),
    url(r'^unenroll/(?P<timetable_id>\d+)/(?P<discipline>[^/]+)/(?P<group>[^/]+)/$', 'timetable.university.views.unenroll'),
    url(r'^autocomplete/rooms/$', 'timetable.university.views.autocomplete_rooms'),
    url(r'^autocomplete/disciplines/$', 'timetable.university.views.autocomplete_disciplines'),
    url(r'^autocomplete/lecturers/$', 'timetable.university.views.autocomplete_lecturers'),
    url(r'^list/rooms/$', 'timetable.university.views.list_rooms'),
    url(r'^list/lecturers/$', 'timetable.university.views.list_lecturers'),
    url(r'^list/majors/$', 'timetable.university.views.list_majors'),
    # url(r'^timetable/', include('timetable.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
