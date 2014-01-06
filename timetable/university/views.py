#-*- coding: utf-8 -*-

import base64
import csv
import difflib
import icalendar
import json
import hashlib

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.datastructures import MultiValueDictKeyError
from django.utils import formats
from django.utils import timezone

from timetable.university.models import *
from timetable.university.utils import get_potential_duplicates, get_disciplines, lessons_to_events, academic_terms_to_events, table_diff_lines


def filter_items_by_enrollments(items, enrollments):
    result = []
    # O(len(items)*len(enrollments)) - may be do smth with maps to speed up
    for item in items:
        for enrollment in enrollments:
            if (item.discipline == enrollment.discipline
                and enrollment.group.startswith(item.group or u'')):
                result.append(item)
                break
    return result

def get_user_lessons(user, academic_term, cache_timeout=30):
    cache_key = 'lessons/%s' % user.username
    lessons = cache.get(cache_key)
    if not lessons:
        enrollments = user.enrollment_set.select_related().all()
        timetable_enrollments_map = {}
        for enrollment in enrollments:
            timetable_enrollments_map.setdefault(
                enrollment.timetable, []).append(enrollment)
        lessons = []
        for timetable, enrollments in timetable_enrollments_map.items():
            items = filter_items_by_enrollments(timetable.items(), enrollments)
            lessons.extend(items_to_lessons(items, academic_term))
        cache.set(cache_key, lessons, cache_timeout)
    return lessons

@login_required
def my(request, week=1):
    week = int(week)
    user = request.user
    # TODO fetch active academic term from global settings
    academic_term = AcademicTerm.objects.order_by('-start_date').all()[0]
    lessons = get_user_lessons(user, academic_term)
    result_table = []
    for date in [academic_term[week][i] for i in range(6)]:
        date_lessons = [l for l in lessons if l.date == date]
        result_date_lessons = []
        for lesson_number in sorted(lesson_times.keys()):
            time_lessons = [l for l in date_lessons if l.lesson_number == lesson_number]
            result_date_lessons.append((lesson_times[lesson_number].split('-')[0],
                                        time_lessons))
        result_table.append((date, result_date_lessons))
    return render_to_response(
            'my.html',
            {
                'table': result_table,
                'active_week': week,
                'academic_term': academic_term,
                'weeks': range(1, academic_term.number_of_weeks + 1),
                },
            context_instance=RequestContext(request)
            )

@login_required
def ical(request):
    user = request.user
    # TODO fetch active academic term from global settings
    academic_term = AcademicTerm.objects.order_by('-start_date').all()[0]
    lessons = get_user_lessons(user, academic_term)
    calendar = icalendar.Calendar()
    calendar.add('prodid', '-//USIC timetable//')
    calendar.add('version', '2.0')
    for event in lessons_to_events(lessons, lesson_times):
        calendar.add_component(event)
    for event in academic_terms_to_events([academic_term]):
        calendar.add_component(event)
    response = HttpResponse(
            calendar.to_ical(),
            mimetype='text/calendar; charset=UTF-8',
            )
    response['Content-Disposition'] = 'attachment; filename=timetable.ics'
    return response

@login_required
def edit_timetable(request, version_id):
    version = get_object_or_404(TimetableVersion, pk=version_id)
    timetable = version.timetable
    items = version.timetableitem_set.values(
            'day_number',
            'lesson_number',
            'room',
            'discipline',
            'group',
            'lecturer',
            'weeks').order_by('day_number', 'lesson_number', 'pk')
    season = timetable.academic_term.season
    season_number = timetable.academic_term.SEASONS.index((season, season)) + 1
    usic_args = (timetable.major.kind,
                 timetable.major.name,
                 timetable.year,
                 season_number,
                 )
    cache_key = 'usic/disciplines/%s/%s/%d/%d' % usic_args
    usic_disciplines = cache.get(cache_key)
    if not usic_disciplines:
        usic_disciplines = get_disciplines(*usic_args)
        cache.set(cache_key, usic_disciplines, 60*60)
    disciplines = sorted(set([i['discipline'] for i in items] + usic_disciplines))
    return render_to_response(
            'starter_template.html',
            {
                'timetable': timetable,
                'version': version,
                'day_names': day_names.items()[:6],
                'lesson_times': lesson_times.items(),
                'number_of_lessons': len(lesson_times),
                'items': json.dumps(list(items), ensure_ascii=False),
                'disciplines': disciplines,
                },
            context_instance=RequestContext(request)
            )

@login_required
@transaction.commit_on_success
def submit_timetable(request, version_id):
    timetable_version = get_object_or_404(TimetableVersion, pk=version_id)
    new_version = TimetableVersion(
            timetable=timetable_version.timetable,
            author=request.user,
            parent=timetable_version,
            remark=request.POST['remark'],
            )
    new_version.save()
    if request.method == 'POST':
        raw_items = json.loads(request.POST['items'])
        for raw_item in raw_items:
            item = TimetableItem(timetable_version=new_version, **raw_item)
            item.save()
        return HttpResponse(json.dumps({
            'status': 'ok',
            'redirect_url': '/compare/%d/%d/' % (timetable_version.pk, new_version.pk),
            }))


@login_required
def upload_timetable(request, timetable_id):
    timetable = get_object_or_404(Timetable, pk=timetable_id)
    error_message = ''
    if request.method == 'POST':
        try:
            with transaction.commit_on_success():
                new_version = TimetableVersion.objects.create(
                        timetable=timetable,
                        author=request.user,
                        remark=u'Завантажено через csv-файл',
                        )
                day_names_inverse = {day_name.upper():day_number for day_number, day_name in day_names.items()}
                lesson_times_inverse = {lesson_time:lesson_number for lesson_number, lesson_time in lesson_times.items()}
                csv_contents = request.FILES['csv_file']
                for line in csv.reader(csv_contents):
                    row = [e.decode('utf-8') for e in line]
                    day_name, lesson_time, room, discipline, group, lecturer, weeks = row
                    if group == u'0':
                        # legacy lecture group
                        group = ''
                    lecturer = lecturer.strip()
                    if lecturer:
                        candidates = [l for l in all_lecturers if l.startswith(lecturer)]
                        if len(candidates) == 1:
                            lecturer = candidates[0]
                    else:
                        lecturer = None
                    TimetableItem.objects.create(
                            timetable_version=new_version,
                            day_number=day_names_inverse[day_name],
                            lesson_number=lesson_times_inverse[lesson_time],
                            room=room or None,
                            discipline=discipline,
                            group=group,
                            lecturer=lecturer,
                            weeks=weeks,
                            )
                return redirect('/tt/%d' % timetable.pk)
        except MultiValueDictKeyError:
            pass
        except csv.Error, e:
            error_message = u'Помилка обробки csv-файлу: %s' % e
        except ValueError:
            error_message = u'Помилка обробки csv-файлу'
    return render_to_response(
            'upload.html',
            {
                'timetable': timetable,
                'error_message': error_message,
                },
            context_instance=RequestContext(request)
            )

def compare(request, version_left, version_right):
    def label(version):
        return u'%s (%s)' % (formats.localize(
            timezone.localtime(version.create_date), True),
            version.author)
    full_diff = 0
    tt_version_left = get_object_or_404(TimetableVersion, pk=version_left)
    tt_version_right = get_object_or_404(TimetableVersion, pk=version_right)
    diffs = []
    if full_diff:
        diff_kwargs = {
                'context': False,
                }
    else:
        diff_kwargs = {
                'context': True,
                'numlines': 0,
                }
    methods_descriptions = [
        ('serialize_to_table_rows', u'Рядки розкладу'),
        ('discipline_hours_table_rows', u'Години дисциплін'),
        ('lecturer_hours_table_rows', u'Години викладачів'),
        ('room_occupation_table_rows', u'Використання аудиторій'),
    ]
    for method_name, description in methods_descriptions:
        left = getattr(tt_version_left, method_name)()
        right = getattr(tt_version_right, method_name)()
        left_text, right_text = table_diff_lines(
                left, right, full_diff
                )
        diff = '<h3>%s</h3>' % description
        diff += difflib.HtmlDiff().make_table(
                left_text,
                right_text,
                label(tt_version_left),
                label(tt_version_right),
                **diff_kwargs
                )
        diffs.append(diff)
    to_approve = (tt_version_left.timetable.active_version() == tt_version_left
                  and tt_version_left.timetable == tt_version_right.timetable
                  and not tt_version_right.approver
                  #and tt_version_right.author != request.user
                  )

    return render_to_response(
            'diff.html',
            {
                'diffs': diffs,
                'to_approve': to_approve,
                'left_version': tt_version_left,
                'right_version': tt_version_right,
                },
            context_instance=RequestContext(request)
            )
    return HttpResponse(diff.replace(u'Courier', u'monospace'))

@login_required
def approve(request, version_left, version_right):
    tt_version_left = get_object_or_404(TimetableVersion, pk=version_left)
    tt_version_right = get_object_or_404(TimetableVersion, pk=version_right)
    error = None
    if request.method != 'POST':
        error = u'Некоректний HTTP метод'
    elif 'valid' not in request.POST:
        error = u'Необхідно підтвердити перевірку інформації'
    elif tt_version_right.approver:
        error = u'Цю версію вже затверджено користувачем %s' % tt_version_right.approver
    elif tt_version_left.timetable.active_version() != tt_version_left:
        error = u'База для порівняння не є активною версією'
    elif tt_version_left.timetable != tt_version_right.timetable:
        error = u'Несумісні розклади'
    elif tt_version_right.author == request.user:
        error = u'Заборонено затверджувати власні версії'
    else:
        tt_version_right.approver = request.user
        tt_version_right.approve_date = timezone.now()
        tt_version_right.save()
    return render_to_response(
            'approve.html',
            {
                'error': error,
                'left_version': tt_version_left,
                'right_version': tt_version_right,
                },
            context_instance=RequestContext(request)
            )

def get_link(request):
    if request.method == 'POST':
        groups_json = request.POST['groups']
        link_hash = base64.urlsafe_b64encode(
                hashlib.sha1(groups_json.encode('utf8')).digest()).rstrip('=')
        try:
            RenderLink.objects.get(link_hash=link_hash)
        except RenderLink.DoesNotExist:
            RenderLink.objects.create(link_hash=link_hash, groups_json=groups_json)
        return HttpResponse(link_hash)

def get_lessons_by_link_hash(link_hash):
    render_link = get_object_or_404(RenderLink, link_hash=link_hash)
    group_records = json.loads(render_link.groups_json)
    timetable_map = {}
    for timetable_id, discipline, group in group_records:
        timetable_map.setdefault(timetable_id, []).append((discipline, group))
    lessons = []
    for timetable_id in sorted(timetable_map.keys()):
        timetable = get_object_or_404(Timetable, pk=timetable_id)
        # TODO - add more logic here
        # but for now, just take the latest tt version
        version = timetable.timetableversion_set.all().order_by('-create_date')[0]
        all_items = version.timetableitem_set.all()
        filtered_items = []
        for discipline, group in timetable_map[timetable_id]:
            filtered_items.extend([i for i in all_items if i.discipline == discipline and i.group == group])
        lessons.extend(items_to_lessons(filtered_items, timetable.academic_term))
    return lessons

def get_academic_terms_by_link_hash(link_hash):
    render_link = get_object_or_404(RenderLink, link_hash=link_hash)
    group_records = json.loads(render_link.groups_json)
    timetable_ids = set([i[0] for i in group_records])
    academic_terms = []
    for timetable_id in timetable_ids:
        timetable = get_object_or_404(Timetable, pk=timetable_id)
        academic_terms.append(timetable.academic_term)
    return academic_terms

def render_timetable(request, link_hash):
    lessons = get_lessons_by_link_hash(link_hash)
    lessons.sort(key=lambda i: (i.date, i.lesson_number))
    return render_to_response(
            'render.html',
            {
                'lessons': lessons,
                },
            context_instance=RequestContext(request)
            )

def ical_timetable(request, link_hash):
    lessons = get_lessons_by_link_hash(link_hash)
    academic_terms = get_academic_terms_by_link_hash(link_hash)
    calendar = icalendar.Calendar()
    calendar.add('prodid', '-//USIC timetable//')
    calendar.add('version', '2.0')
    for event in lessons_to_events(lessons, lesson_times):
        calendar.add_component(event)
    for event in academic_terms_to_events(academic_terms):
        calendar.add_component(event)
    response = HttpResponse(
            calendar.to_ical(),
            mimetype='text/calendar; charset=UTF-8',
            )
    response['Content-Disposition'] = 'attachment; filename=timetable.ics'
    return response

def home(request):
    def itemize(d):
        """Convert dict to sorted item list recursively"""
        if not isinstance(d, dict):
            return d
        result_list = []
        for k in sorted(d.keys()):
            result_list.append((k, itemize(d[k])))
        return result_list

    #TODO: add active academic term filtering
    timetables = Timetable.objects.select_related().all()
    faculty_major_kind_tt_map = {}
    for timetable in timetables:
        faculty_major_kind_tt_map.setdefault(
            timetable.major.faculty, {}).setdefault(
                timetable.major.name, {}).setdefault(
                    timetable.major.kind, {}).setdefault(
                        timetable.year, timetable)
    faculty_major_kind_tt_list = itemize(faculty_major_kind_tt_map)
    return render_to_response(
            'jumbo.html',
            {
                'faculty_major_kind_tt_list': faculty_major_kind_tt_list,
                'timetables': timetables,
                'page': 'index',
                },
            context_instance=RequestContext(request)
            )

def info(request):
    return render_to_response(
        'info.html',
        {
        },
        context_instance=RequestContext(request)
    )

def timetable(request, timetable_id):
    timetable = get_object_or_404(Timetable, pk=timetable_id)
    active_version = timetable.active_version()
    all_versions = timetable.versions()
    items = active_version.timetableitem_set.all()
    discipline_group_map = {}
    for item in items:
        if item.group:
            discipline_group_map.setdefault(item.discipline, set()).add(item.group)
    if request.user.is_authenticated():
        user = request.user
        enrollments = Enrollment.objects.filter(user=user, timetable=timetable)
        enrolled_discipline_group_pairs = []
        for enrollment in enrollments:
            enrolled_discipline_group_pairs.append((enrollment.discipline,
                                                    enrollment.group))
    else:
        enrolled_discipline_group_pairs = []
    discipline_group_list = []
    for discipline, groups in sorted(discipline_group_map.items()):
        group_enrolled = []
        for group in sorted(groups):
            group_enrolled.append((
                group, (discipline, group) in enrolled_discipline_group_pairs))
        discipline_group_list.append((discipline, group_enrolled))
    return render_to_response(
            'view.html',
            {
                'timetable': timetable,
                'version': active_version,
                'all_versions': all_versions,
                'discipline_group_list': discipline_group_list,
                },
            context_instance=RequestContext(request)
            )


def version(request, version_id):
    version = get_object_or_404(TimetableVersion, pk=version_id)
    timetable = version.timetable
    active_version = timetable.active_version()
    all_versions = timetable.versions()
    items = version.timetableitem_set.all()
    methods_descriptions = [
        ('serialize_to_table_rows', u'Рядки розкладу'),
        ('discipline_hours_table_rows', u'Години дисциплін'),
        ('lecturer_hours_table_rows', u'Години викладачів'),
        ('room_occupation_table_rows', u'Використання аудиторій'),
    ]
    header_rows = []
    for method_name, description in methods_descriptions:
        rows = getattr(version, method_name)()
        header_rows.append((description, rows))
    return render_to_response(
            'version.html',
            {
                'timetable': timetable,
                'version': version,
                'active_version': active_version,
                'all_versions': all_versions,
                'header_rows': header_rows,
                },
            context_instance=RequestContext(request)
            )


@login_required
def enroll(request, timetable_id, discipline, group):
    user = request.user
    timetable = get_object_or_404(Timetable, pk=timetable_id)
    Enrollment.objects.create(user=user, timetable=timetable,
                              discipline=discipline, group=group)
    cache_key = 'lessons/%s' % user.username
    cache.delete(cache_key)
    return HttpResponse('Ok')

@login_required
def unenroll(request, timetable_id, discipline, group):
    user = request.user
    enrollment = get_object_or_404(Enrollment, user=user, timetable__pk=timetable_id,
                                   discipline=discipline, group=group)
    enrollment.delete()
    cache_key = 'lessons/%s' % user.username
    cache.delete(cache_key)
    return HttpResponse('Ok')

@login_required
def profile(request):
    user = request.user
    enrollments = user.enrollment_set.select_related().all()
    timetable_enrollments_map = {}
    for enrollment in enrollments:
        timetable_enrollments_map.setdefault(
            enrollment.timetable, []).append(enrollment)
    return render_to_response(
        'registration/profile.html',
        {
            'page': 'profile',
            'ical_link': request.build_absolute_uri('/ical/TODO/'),
            'timetable_enrollments_map': timetable_enrollments_map,
        },
        context_instance=RequestContext(request)
    )

def autocomplete(request, dataset, limit=10):
    try:
        query_original = request.GET['query']
        query = query_original.upper()
        result = []
        for item in dataset:
            if item.upper().startswith(query):
                result.append(item)
        json_response = {
                'query': query_original,
                'suggestions': result[:limit],
                'data': result[:limit],
                }
        return HttpResponse(json.dumps(json_response))
    except MultiValueDictKeyError:
        return HttpResponseForbidden('Forbidden')

def autocomplete_rooms(request):
    return autocomplete(request, all_rooms)

def autocomplete_disciplines(request):
    return autocomplete(request, all_disciplines)

def autocomplete_lecturers(request):
    return autocomplete(request, all_lecturers)
