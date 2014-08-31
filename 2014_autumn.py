#-*- coding: utf-8 -*-

import logging
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable.settings')

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from timetable.university.models import *

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.INFO)

with transaction.commit_on_success():
    try:
        user = User.objects.get(username='webmaster')
        logging.info('User webmaster exists, using existing')
    except User.DoesNotExist:
        logging.info('User webmaster does not exist, creating')
        user = User.objects.create_user('webmaster', 'webmaster@usic.at', '')
    try:
        Major.objects.get(code='6.040302')
    except Major.DoesNotExist:
        logging.info('Creating major 6.040302')
        Major.objects.create(
            faculty=Faculty.objects.get(abbr=u'ФІ'),
            code='6.040302',
            name=u'Інформатика',
            kind=u'бакалавр'
        )
    # mark all the old academic terms as inactive
    for academic_term in AcademicTerm.objects.filter(is_active=True):
        logging.info('Marking %s as inactive', academic_term)
        academic_term.is_active = False
        academic_term.save()
    academic_term = AcademicTerm.objects.create(
            university=University.objects.get(abbr=u'НаУКМА'),
            year=2014,
            kind=u'триместр',
            season=u'осінній',
            number_of_weeks=15,
            tcp_week=8,
            start_date='2014-09-01',
            exams_start_date='2014-12-15',
            exams_end_date='2014-12-26',
            is_active=True,
            )
    logging.info('Created new active academic term %s', academic_term)

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
            logging.info('Creating timetable for %s %d', major, year)
            timetable = Timetable.objects.create(
                major=major,
                year=year,
                academic_term=academic_term,
            )
            timetable_version = TimetableVersion.objects.create(
                timetable=timetable,
                author=user,
                approver=user,
                approve_date=timezone.now(),
                parent=None,
                remark=u'Порожній розклад',
            )
    logging.info('Comitting...')
