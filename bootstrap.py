#-*- coding: utf-8 -*-

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable.settings')

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from timetable.university.models import *


with transaction.commit_on_success():
    user = User.objects.create_user('webmaster', 'webmaster@usic.at', '')
    academic_term = AcademicTerm.objects.create(
            university=University.objects.get(abbr=u'НаУКМА'),
            year=2013,
            kind=u'семестр',
            season=u'весняний',
            number_of_weeks=15,
            tcp_week=8,
            start_date='2014-01-13',
            exams_start_date='2014-04-28',
            exams_end_date='2014-05-09',
            is_active=True,
            )
    academic_term_short = AcademicTerm.objects.create(
            university=University.objects.get(abbr=u'НаУКМА'),
            year=2013,
            kind=u'семестр',
            season=u'весняний',
            number_of_weeks=14,
            tcp_week=None,
            start_date='2014-01-13',
            exams_start_date='2014-04-21',
            exams_end_date='2014-05-02',
            is_active=True,
            )


    for major in Major.objects.all():
        if major.kind == u'бакалавр':
            years = [1, 2, 3, 4]
        elif major.kind == u'спеціаліст':
            years = [1]
        elif major.kind == u'маґістр' and major.name == u'Правознавство':
            years = [1]
        else:
            years = [1, 2]
        for year in years:
            at = academic_term
            if major.name == u'Правознавство':
                if major.kind == u'бакалавр':
                    if year == 4:
                        at = academic_term_short
                else:
                    at = academic_term_short
            timetable = Timetable.objects.create(
                major=major,
                year=year,
                academic_term=at,
            )
            timetable_version = TimetableVersion.objects.create(
                timetable=timetable,
                author=user,
                approver=user,
                approve_date=timezone.now(),
                parent=None,
                remark=u'Порожній розклад',
            )
