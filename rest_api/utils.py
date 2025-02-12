from gtfseditor import settings
from datetime import datetime, timedelta

DAYS = ['monday',
        'tuesday',
        'wednesday',
        'thursday',
        'friday',
        'saturday',
        'sunday']


def log(*args, **kwargs):
    if settings.DEBUG:
        print(*args, **kwargs)


def normalize_time(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    hours %= 24
    return f'{hours:02}:{minutes:02}:{seconds:02}'


def create_foreign_key_hashmap(chunk, model, project_pk, csv_key, model_key):
    ids = set(map(lambda entry: entry[csv_key], filter(lambda entry: csv_key in entry, chunk)))
    mapping = dict()
    for row in model.objects.filter_by_project(project_pk).filter(**{model_key + '__in': ids}).values_list(model_key,
                                                                                                           'id'):
        mapping[row[0]] = row[1]
    mapping[None] = None
    return mapping
