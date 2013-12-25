#-*- coding: utf-8 -*-

from django.core.management import setup_environ
from timetable import settings

setup_environ(settings)
from django.contrib.auth.models import User
from django.db import transaction
from timetable.university.models import *


with transaction.commit_on_success():
    user = User.objects.create_user('webmaster', 'webmaster@usic.at', '')
    academic_term = AcademicTerm.objects.create(
            university=University.objects.get(abbr=u'НаУКМА'),
            year=2013,
            kind=u'семестр',
            season=u'осінній',
            number_of_weeks=15,
            tcp_week=8,
            start_date='2013-09-02',
            exams_start_date='2013-12-16',
            exams_end_date='2012-12-29',
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
            timetable = Timetable.objects.create(
                major=major,
                year=year,
                academic_term=academic_term,
            )
            timetable_version = TimetableVersion.objects.create(
                timetable=timetable,
                author=user,
                parent=None,
                remark=u'Порожній розклад',
            )
