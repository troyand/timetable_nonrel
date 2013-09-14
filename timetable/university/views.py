# Create your views here.

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.datastructures import MultiValueDictKeyError
from django.template.defaultfilters import register as rf

from timetable.university.models import day_names, lesson_times, Timetable, TimetableItem

import csv



@rf.filter(name='lookup')
def lookup(dictionary, index):
    if index in dictionary:
        return dictionary[index]
    return None



def edit_timetable(request, timetable_id):
    timetable = get_object_or_404(Timetable, pk=timetable_id)
    items = timetable.timetableitem_set.all()
    day_lesson_items = {}
    for day_number in day_names:
        day_lesson_items[day_number] = {}
        for lesson_number in lesson_times:
            day_lesson_items[day_number][lesson_number] = []
    for item in items:
        day_lesson_items[item.day_number][item.lesson_number].append(item)
    return render_to_response(
            'starter_template.html',
            {
                'day_names': day_names.items(),
                'lesson_times': lesson_times.items(),
                'number_of_lessons': len(lesson_times),
                'day_lesson_items': day_lesson_items,
                },
            context_instance=RequestContext(request)
            )

def upload_timetable(request, timetable_id):
    timetable = get_object_or_404(Timetable, pk=timetable_id)
    if request.method == 'POST':
        try:
            day_names_inverse = {day_name.upper():day_number for day_number, day_name in day_names.items()}
            lesson_times_inverse = {lesson_time:lesson_number for lesson_number, lesson_time in lesson_times.items()}
            csv_contents = request.FILES['csv_file']
            old_items = list(timetable.timetableitem_set.all())
            for line in csv.reader(csv_contents):
                row = [e.decode('utf-8') for e in line]
                day_name, lesson_time, room, discipline, group, lecturer, weeks = row
                if group == u'0' or group == u'':
                    # legacy lecture group
                    group = None
                TimetableItem.objects.create(
                        timetable=timetable,
                        day_number=day_names_inverse[day_name],
                        lesson_number=lesson_times_inverse[lesson_time],
                        room=room or None,
                        discipline=discipline,
                        group=group,
                        lecturer=lecturer.strip() or None,
                        weeks=weeks,
                        )
            for item in old_items:
                item.delete()
        except MultiValueDictKeyError:
            pass
    return render_to_response(
            'upload.html',
            {
                'timetable': timetable,
                },
            context_instance=RequestContext(request)
            )

def view_timetable(request, timetable_id):
    timetable = get_object_or_404(Timetable, pk=timetable_id)
    academic_term = timetable.academic_term
    lessons = []
    for item in timetable.timetableitem_set.all():
        weeks = academic_term.expand_weeks(item.weeks)
        for week in weeks:
            day = academic_term[week][item.day_number-1]
            lesson = (
                day,
                item.lesson_number,
                item.room,
                item.discipline,
                item.group,
                item.lecturer,
                )
            lessons.append(lesson)
    for lesson in sorted(lessons):
        #print '|'.join([unicode(el) for el in lesson])
        pass
    return render_to_response(
            'upload.html',
            {
                'timetable': timetable,
                },
            context_instance=RequestContext(request)
            )
