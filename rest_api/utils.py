from gtfseditor import settings

def log(*args, **kwargs):
    if settings.DEBUG:
        print(*args, **kwargs)