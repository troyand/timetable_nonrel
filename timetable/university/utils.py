import jellyfish
import itertools
import requests
from unidecode import unidecode


def get_potential_duplicates(strings):
    dups = set()
    for string_a, string_b in itertools.combinations(strings, 2):
        jaro_distance =  jellyfish.jaro_distance(
                unidecode(string_a), unidecode(string_b))
        if 0.9 < jaro_distance < 1:
            print jaro_distance, string_a, string_b
            dups.add(string_a)
            dups.add(string_b)
    return dups

def get_disciplines(level, program, year, term):
    USIC_API_URL = 'http://api.usic.at/api/v1/courses/subjects'
    response = requests.get(USIC_API_URL, params={
        'level': level,
        'program': program,
        'year': year,
        'term': term,
        })
    if not response.json():
        return []
    result = [i for i in response.json().keys()]
    return result
