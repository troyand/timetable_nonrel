#-*- coding: utf-8 -*-

import datetime
import os
import codecs

from collections import namedtuple

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.encoding import smart_str


day_names = {
    1: u'Пн',
    2: u'Вт',
    3: u'Ср',
    4: u'Чт',
    5: u'Пт',
    6: u'Сб',
    7: u'Нд',
}


lesson_times = {
    1: u'08:30-09:50',
    2: u'10:00-11:20',
    3: u'11:40-13:00',
    4: u'13:30-14:50',
    5: u'15:00-16:20',
    6: u'16:30-17:50',
    7: u'18:00-19:20',
}


class University(models.Model):
    name = models.CharField(max_length=255, unique=True)
    abbr = models.CharField(max_length=16, unique=True)

    def __unicode__(self):
        return u'%s' % (
            self.abbr
        )


class Faculty(models.Model):
    university = models.ForeignKey(University)
    name = models.CharField(max_length=255)
    abbr = models.CharField(max_length=16)

    class Meta:
        unique_together = (
            ('university', 'name'),
            ('university', 'abbr'),
        )

    def __unicode__(self):
        return '%s - %s' % (
            self.university.abbr,
            self.abbr,
        )


class Major(models.Model):
    faculty = models.ForeignKey(Faculty)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=16)

    class Meta:
        unique_together = ('faculty', 'name', 'kind')

    def __unicode__(self):
        return u'%s - %s' % (
            self.code,
            self.name,
        )


class AcademicTerm(models.Model):
    ACADEMIC_TERMS = (
        (u'семестр', u'семестр'),
        (u'триместр', u'триместр'),
    )
    SEASONS = (
        (u'осінній', u'осінній'),
        (u'весняний', u'весняний'),
        (u'літній', u'літній'),
    )

    class Week:

        def __init__(self, academic_term, week_number):
            if week_number < 0 or week_number > academic_term.number_of_weeks:
                raise ValueError(u'Invalid week number %d for %s' % (
                    week_number, academic_term)
                )
            self.academic_term = academic_term
            self.week_number = week_number

        def __getitem__(self, key):
            if isinstance(key, int):
                return self.academic_term.start_date + datetime.timedelta(
                    days=7 * (self.week_number - 1) + key)
            else:
                raise AttributeError('Int expected, got %s' % key)

        def __repr__(self):
            return smart_str(
                u'Week #%d of %s' % (
                    self.week_number,
                    self.academic_term
                ))

    def expand_weeks(self, weeks):
        result = []
        for part in weeks.split(','):
            if '-' in part:
                result += range(
                    int(part.split('-')[0]),
                    int(part.split('-')[1]) + 1
                )
            else:
                result += [int(part)]
        if self.tcp_week in result:
            result.remove(self.tcp_week)
        return result

    university = models.ForeignKey(University)
    year = models.IntegerField()
    kind = models.CharField(max_length=16, choices=ACADEMIC_TERMS)
    season = models.CharField(max_length=16, choices=SEASONS)
    number_of_weeks = models.IntegerField()
    tcp_week = models.IntegerField(null=True, blank=True)
    start_date = models.DateField()
    exams_start_date = models.DateField()
    exams_end_date = models.DateField()

    def __unicode__(self):
        return u'%s: %s %s %d-%d навчального року (%d т. із %s)' % (
            self.university,
            self.season,
            self.kind,
            self.year,
            self.year + 1,
            self.number_of_weeks,
            self.start_date,
        )

    def __getitem__(self, key):
        """Week getter, at[5][2] gets the wednesday of 5th week"""
        if isinstance(key, int):
            return self.Week(academic_term=self, week_number=key)
        else:
            raise AttributeError('Int expected, got %s' % key)

    def get_week(self, date):
        """Get the Week object corresponding to the given date"""
        delta = date - self.start_date
        week_number = delta.days / 7 + 1
        if 0 < week_number <= self.number_of_weeks:
            return self.Week(academic_term=self, week_number=week_number)
        else:
            raise ValueError('There is no week #%d in %s' % (
                week_number,
                self,
            ))


class Timetable(models.Model):
    major = models.ForeignKey(Major)
    year = models.IntegerField()
    academic_term = models.ForeignKey(AcademicTerm)

    def __unicode__(self):
        return u'%s %s %d р.н.' % (
            self.major.name,
            self.major.kind,
            self.year,
        )


class TimetableVersion(models.Model):
    timetable = models.ForeignKey(Timetable)
    author = models.ForeignKey(User, related_name='authored')
    date_created = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True)
    approver = models.ForeignKey(
        User, blank=True, null=True, related_name='approved')
    approve_date = models.DateTimeField(blank=True, null=True)

    def parents(self):
        result = []
        version = self
        while version.parent:
            result.append(version.parent)
            version = version.parent
        return result

    def serialize_to_table_rows(self):
        result = []
        items = self.timetableitem_set.all().order_by(
            'day_number', 'lesson_number', 'pk')
        for item in items:
            row = [
                day_names[item.day_number],
                lesson_times[item.lesson_number].split(u'-')[0],
                item.room or u'Ø',
                item.discipline,
                item.group or u'Л',
                item.lecturer or u'Ø',
                item.weeks,
            ]
            result.append(row)
        return result

    def discipline_hours_table_rows(self):
        lessons = items_to_lessons(
            self.timetableitem_set.all(), self.timetable.academic_term)
        discipline_group_map = {}
        for lesson in lessons:
            lecturers, count = discipline_group_map.setdefault(
                lesson.discipline, {}).get(lesson.group, (set(), 0))
            if lesson.lecturer:
                lecturers.add(lesson.lecturer)
            else:
                lecturers.add(u'')
            count += 1
            discipline_group_map[lesson.discipline][
                lesson.group] = (lecturers, count)
        result = []
        for discipline in sorted(discipline_group_map.keys()):
            for group in sorted(discipline_group_map[discipline].keys()):
                lecturers, count = discipline_group_map[discipline][group]
                if lecturers:
                    lecturers = u', '.join(sorted(lecturers))
                else:
                    lecturers = u'Ø'
                result.append(
                    (discipline, group or u'Л', lecturers, unicode(count)))
        return result

    def lecturer_hours_table_rows(self):
        lessons = items_to_lessons(
            self.timetableitem_set.all(), self.timetable.academic_term)
        lecturer_hours_map = {}
        for lesson in lessons:
            lecturer = lesson.lecturer or u'Ø'
            lecturer_hours_map[lecturer] = lecturer_hours_map.get(
                lecturer, 0) + 1
        result = []
        for lecturer in sorted(lecturer_hours_map.keys()):
            result.append((lecturer, unicode(lecturer_hours_map[lecturer])))
        return result

    def room_occupation_table_rows(self):
        lessons = items_to_lessons(
            self.timetableitem_set.all(), self.timetable.academic_term)
        room_occupation_map = {}
        for lesson in lessons:
            room = lesson.room or u'Ø'
            key = (
                room,
                lesson.date.isoweekday(),
                lesson.lesson_number,
            )
            room_occupation_map.setdefault(key, set())
            room_occupation_map[key].add(
                self.timetable.academic_term.get_week(lesson.date).week_number)
        result = []
        for key in sorted(room_occupation_map.keys()):
            room, day_number, lesson_number = key
            result.append((
                room,
                day_names[day_number],
                lesson_times[lesson_number].split(u'-')[0],
                u','.join([unicode(i)
                           for i in sorted(room_occupation_map[key])])
            ))
        return result


class TimetableItem(models.Model):
    timetable_version = models.ForeignKey(TimetableVersion)
    day_number = models.IntegerField(choices=sorted(day_names.items()))
    lesson_number = models.IntegerField(choices=sorted(lesson_times.items()))
    room = models.CharField(max_length=32, null=True, blank=True)
    discipline = models.CharField(max_length=255)
    group = models.CharField(max_length=32, null=True, blank=True)
    lecturer = models.CharField(max_length=64, null=True, blank=True)
    weeks = models.CharField(max_length=64)

    def __unicode__(self):
        return u'%s %s [%s] %s - %s / %s [%s]' % (
            self.get_day_number_display(),
            self.get_lesson_number_display(),
            self.room,
            self.discipline,
            self.group or u'лекція',
            self.lecturer,
            self.weeks,
        )


class RenderLink(models.Model):
    link_hash = models.CharField(max_length=32)
    groups_json = models.TextField()


class Enrollment(models.Model):
    user = models.ForeignKey(User)
    timetable = models.ForeignKey(Timetable)
    discipline = models.CharField(max_length=255)
    group = models.CharField(max_length=32, null=True, blank=True)


Lesson = namedtuple(
    'Lesson', 'date lesson_number room discipline group lecturer')


def items_to_lessons(items, academic_term):
    lessons = []
    for item in items:
        weeks = academic_term.expand_weeks(item.weeks)
        for week in weeks:
            day = academic_term[week][item.day_number - 1]
            lesson = Lesson(
                day,
                item.lesson_number,
                item.room,
                item.discipline,
                item.group,
                item.lecturer,
            )
            lessons.append(lesson)
    return lessons


def load_from_file(fixture_txt):
    full_filename = os.path.join(
        settings.SITE_ROOT, 'university', 'fixtures', fixture_txt)
    with codecs.open(full_filename, 'r', 'utf8') as f:
        result = f.read().splitlines()
    return result

all_lecturers = load_from_file('lecturers.txt')
all_disciplines = load_from_file('disciplines.txt')
all_rooms = load_from_file('rooms.txt')
