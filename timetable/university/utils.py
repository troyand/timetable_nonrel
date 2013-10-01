import jellyfish
import itertools
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
