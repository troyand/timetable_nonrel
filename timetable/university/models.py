#-*- coding: utf-8 -*-

import datetime

from django.db import models
from django.utils.encoding import smart_str


lesson_times = {
    1: u'8:30-9:50',
    2: u'10:00-11:20',
    3: u'11:40-13:00',
    4: u'13:30-14:50',
    5: u'15:00-16:20',
    6: u'16:30-17:50',
    7: u'18:00-19:20',
}

day_names = {
        1: u'Пн',
        2: u'Вт',
        3: u'Ср',
        4: u'Чт',
        5: u'Пт',
        6: u'Сб',
        7: u'Нд',
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
            if type(key) == type(1):
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
        if type(key) == type(1):
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


class TimetableItem(models.Model):
    timetable = models.ForeignKey(Timetable)
    day_number = models.IntegerField(choices=sorted(day_names.items()))
    lesson_number = models.IntegerField(choices=sorted(lesson_times.items()))
    room = models.CharField(max_length=32, null=True, blank=True)
    discipline = models.CharField(max_length=255)
    group = models.CharField(max_length=32, null=True, blank=True)
    lecturer = models.CharField(max_length=64, null=True, blank=True)
    weeks = models.CharField(max_length=64)
