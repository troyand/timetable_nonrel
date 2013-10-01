from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'timetable.views.home', name='home'),
    url(r'^edit/(?P<timetable_id>\d+)/$', 'timetable.university.views.edit_timetable', name='edit_timetable'),
    url(r'^check-1/(?P<timetable_id>\d+)/$', 'timetable.university.views.check_timetable_1', name='check_timetable_1'),
    url(r'^check-2/(?P<timetable_id>\d+)/$', 'timetable.university.views.check_timetable_2', name='check_timetable_2'),
    url(r'^upload/(?P<timetable_id>\d+)/$', 'timetable.university.views.upload_timetable', name='upload_timetable'),
    url(r'^view/(?P<timetable_id>\d+)/$', 'timetable.university.views.view_timetable', name='view_timetable'),
    url(r'^autocomplete/rooms/$', 'timetable.university.views.autocomplete_rooms'),
    url(r'^autocomplete/disciplines/$', 'timetable.university.views.autocomplete_disciplines'),
    url(r'^autocomplete/lecturers/$', 'timetable.university.views.autocomplete_lecturers'),
    # url(r'^timetable/', include('timetable.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
