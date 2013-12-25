#-*- coding: utf-8 -*-

import datetime
import jellyfish
import icalendar
import itertools
import pytz
import requests
from unidecode import unidecode


def get_potential_duplicates(strings):
    dups = set()
    for string_a, string_b in itertools.combinations(strings, 2):
        jaro_distance =  jellyfish.jaro_distance(
                unidecode(string_a or ''), unidecode(string_b or ''))
        if 0.9 < jaro_distance < 1:
            dups.add(string_a)
            dups.add(string_b)
    return dups

def get_disciplines(level, program, year, term):
    def clean_parentheses(s):
        """Clean junk in parentheses."""
        try:
            parenthesis_pos = s.index(u'(')
            return s[:parenthesis_pos].strip()
        except ValueError:
            return s

    USIC_API_URL = 'http://api.usic.at/api/v1/courses/subjects'
    response = requests.get(USIC_API_URL, params={
        'level': level.replace(u'ґ', u'г'),
        'program': program,
        'year': year,
        'term': term,
        'type': u'норм',
        })
    response_json = response.json()
    if not response_json:
        return []
    disciplines = []
    for raw_discipline, credits in response_json.items():
        if credits != '0':
            disciplines.append(clean_parentheses(raw_discipline))
    return disciplines

def lessons_to_events(lessons, lesson_times):
    events = []
    for lesson in lessons:
        lesson_start_time, lesson_end_time = lesson_times[lesson.lesson_number].split('-')
        lesson_start_hour, lesson_start_minute = map(int,
                lesson_start_time.split(':'))
        lesson_end_hour, lesson_end_minute = map(int,
                lesson_end_time.split(':'))
        tz = pytz.timezone('Europe/Kiev')
        dtstart = datetime.datetime.combine(lesson.date, datetime.time(
            lesson_start_hour,
            lesson_start_minute,
            tzinfo=tz))
        dtend = datetime.datetime.combine(lesson.date, datetime.time(
            lesson_end_hour,
            lesson_end_minute,
            tzinfo=tz))
        event = icalendar.Event()
        summary_parts = [lesson.discipline]
        if lesson.group:
            summary_parts.append(u'Група %s' % lesson.group)
        else:
            summary_parts.append(u'Лекція')
        if lesson.lecturer:
            summary_parts.append(lesson.lecturer)
        event.add('summary', u' — '.join(summary_parts))
        description_parts = []
        if description_parts:
            event.add('description', u'\n'.join(description_parts))
        if lesson.room:
            event.add('location', lesson.room)
        event.add('dtstart', dtstart)
        event.add('dtend', dtend)
        events.append(event)
    return events

def academic_terms_to_events(academic_terms):
    events = []
    for academic_term in academic_terms:
        for week_number in range(1, academic_term.number_of_weeks + 1):
            week_start_date = academic_term[week_number][0]
            week_end_date = academic_term[week_number][7]
            event = icalendar.Event()
            if week_number == academic_term.tcp_week:
                summary = u'%d тиждень - ТСР' % week_number
            else:
                summary = u'%d тиждень' % week_number
            event.add('summary', summary)
            event.add('description', u'%s' % academic_term)
            event.add('dtstart', week_start_date)
            event.add('dtend', week_end_date)
            events.append(event)
    return events

def table_diff_lines(left_rows, right_rows, full_diff):
    if full_diff:
        rows = set(map(tuple, left_rows)) | set(map(tuple, right_rows))
    else:
        rows = set(map(tuple, left_rows)) ^ set(map(tuple, right_rows))
    if not rows:
        return [], []
    widths = [max([len(row[i]) for row in rows]) for i in range(len(iter(rows).next()))]
    left_justified = [[cell.ljust(width) for cell, width in zip(row, widths)] for row in left_rows]
    right_justified = [[cell.ljust(width) for cell, width in zip(row, widths)] for row in right_rows]
    return [u'│'.join(row) for row in left_justified], [u'│'.join(row) for row in right_justified]
