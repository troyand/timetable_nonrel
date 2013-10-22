# Create your views here.

import base64
import csv
import difflib
import icalendar
import json
import hashlib

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.datastructures import MultiValueDictKeyError

from timetable.university.models import *
from timetable.university.utils import get_potential_duplicates, get_disciplines, lessons_to_events, academic_terms_to_events, table_diff_lines


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
    usic_disciplines = get_disciplines(timetable.major.kind,
            timetable.major.name,
            timetable.year,
            season_number,
            )
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

def check_timetable_1(request, version_id):
    timetable_version = get_object_or_404(TimetableVersion, pk=version_id)
    timetable = timetable_version.timetable
    new_version = TimetableVersion(
            timetable=timetable_version.timetable,
            author=User.objects.get(username='webmaster'),
            parent=timetable_version,
            )
    if request.method == 'POST':
        raw_items = json.loads(request.POST['items'])
        items = []
        for raw_item in raw_items:
            item = TimetableItem(timetable_version=new_version, **raw_item)
            items.append(item)
        rooms = sorted(set([i.room for i in items if i.room]))
        labeled_rooms = []
        for room in rooms:
            if room in all_rooms:
                labeled_rooms.append(('success', room))
            else:
                labeled_rooms.append(('warning', room))
        disciplines = sorted(set([i.discipline for i in items]))
        labeled_disciplines = []
        potential_duplicate_disciplines = get_potential_duplicates(disciplines)
        for discipline in disciplines:
            if discipline in all_disciplines:
                labeled_disciplines.append(('success', discipline))
            elif discipline in potential_duplicate_disciplines:
                labeled_disciplines.append(('danger', discipline))
            else:
                labeled_disciplines.append(('warning', discipline))
        lecturers = sorted(set([i.lecturer for i in items if i.lecturer]))
        labeled_lecturers = []
        potential_duplicate_lecturers = get_potential_duplicates(lecturers)
        for lecturer in lecturers:
            if lecturer in all_lecturers:
                labeled_lecturers.append(('success', lecturer))
            elif lecturer in potential_duplicate_lecturers:
                labeled_lecturers.append(('danger', lecturer))
            else:
                labeled_lecturers.append(('warning', lecturer))
        return render_to_response(
                'check.html',
                {
                    'timetable': timetable,
                    'version': timetable_version,
                    'labeled_rooms': labeled_rooms,
                    'labeled_disciplines': labeled_disciplines,
                    'labeled_lecturers': labeled_lecturers,
                    },
                context_instance=RequestContext(request)
                )

def check_timetable_2(request, version_id):
    timetable_version = get_object_or_404(TimetableVersion, pk=version_id)
    timetable = timetable_version.timetable
    new_version = TimetableVersion(
            timetable=timetable_version.timetable,
            author=User.objects.get(username='webmaster'),
            parent=timetable_version,
            )
    if request.method == 'POST':
        raw_items = json.loads(request.POST['items'])
        items = []
        for raw_item in raw_items:
            item = TimetableItem(timetable_version=new_version, **raw_item)
            items.append(item)
        lessons = items_to_lessons(items, timetable.academic_term)
        discipline_group_map = {}
        for lesson in lessons:
            lecturers, count = discipline_group_map.setdefault(lesson.discipline, {}).get(lesson.group, (set(), 0))
            if lesson.lecturer:
                lecturers.add(lesson.lecturer)
            else:
                lecturers.add(u'')
            count += 1
            discipline_group_map[lesson.discipline][lesson.group] = (lecturers, count)
        discipline_group_list = []
        for discipline in sorted(discipline_group_map.keys()):
            # temp local vars
            l_groups_lecturers = []
            l_counts = []
            for group in sorted(discipline_group_map[discipline].keys()):
                lecturers, count = discipline_group_map[discipline][group]
                if lecturers:
                    l_groups_lecturers.append((group, u', '.join(lecturers)))
                l_counts.append(count)
            discipline_group_list.append((discipline, l_groups_lecturers, l_counts))
        return render_to_response(
                'check-2.html',
                {
                    'timetable': timetable,
                    'version': timetable_version,
                    'discipline_group_map': discipline_group_map,
                    'discipline_group_list': discipline_group_list,
                    },
                context_instance=RequestContext(request)
                )

@transaction.commit_on_success
def submit_timetable(request, version_id):
    timetable_version = get_object_or_404(TimetableVersion, pk=version_id)
    new_version = TimetableVersion(
            timetable=timetable_version.timetable,
            author=User.objects.get(username='webmaster'),
            parent=timetable_version,
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


@transaction.commit_on_success
def upload_timetable(request, version_id):
    timetable_version = get_object_or_404(TimetableVersion, pk=version_id)
    timetable = timetable_version.timetable
    if timetable_version.parent:
        raise HttpResponseForbidden('Forbidden')
    if request.method == 'POST':
        try:
            new_version = TimetableVersion.objects.create(
                    timetable=timetable_version.timetable,
                    author=User.objects.get(username='webmaster'),
                    parent=timetable_version,
                    )
            day_names_inverse = {day_name.upper():day_number for day_number, day_name in day_names.items()}
            lesson_times_inverse = {lesson_time:lesson_number for lesson_number, lesson_time in lesson_times.items()}
            csv_contents = request.FILES['csv_file']
            for line in csv.reader(csv_contents):
                row = [e.decode('utf-8') for e in line]
                day_name, lesson_time, room, discipline, group, lecturer, weeks = row
                if group == u'0' or group == u'':
                    # legacy lecture group
                    group = None
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
        except MultiValueDictKeyError:
            pass
    return render_to_response(
            'upload.html',
            {
                'timetable': timetable,
                },
            context_instance=RequestContext(request)
            )

def view_timetable(request, version_id):
    timetable_version = get_object_or_404(TimetableVersion, pk=version_id)
    timetable = timetable_version.timetable
    items = timetable_version.timetableitem_set.all()
    discipline_group_map = {}
    for item in items:
        discipline_group_map.setdefault(item.discipline, set()).add(item.group)
    discipline_group_list = []
    for discipline, groups in sorted(discipline_group_map.items()):
        discipline_group_list.append((discipline, sorted(groups)))
    #academic_term = timetable.academic_term
    #lessons = items_to_lessons(timetable.timetableitem_set.all(), academic_term)
    #for lesson in sorted(lessons):
    #    print '|'.join([unicode(el) for el in lesson])
        #pass
    return render_to_response(
            'view.html',
            {
                'timetable': timetable,
                'version': timetable_version,
                'discipline_group_list': discipline_group_list,
                },
            context_instance=RequestContext(request)
            )

def compare(request, version_left, version_right):
    tt_version_left = get_object_or_404(TimetableVersion, pk=version_left)
    tt_version_right = get_object_or_404(TimetableVersion, pk=version_right)
    left_text, right_text = table_diff_lines(
            tt_version_left.serialize_to_table_rows(),
            tt_version_right.serialize_to_table_rows()
            )
    diff = difflib.HtmlDiff().make_file(
            left_text,
            right_text,
            tt_version_left.date_created,
            tt_version_right.date_created,
            context=True,
            numlines=0,
            )
    return HttpResponse(diff)

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
        version = timetable.timetableversion_set.all().order_by('-date_created')[0]
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
    timetables = Timetable.objects.all()
    return render_to_response(
            'home.html',
            {
                'timetables': timetables,
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
