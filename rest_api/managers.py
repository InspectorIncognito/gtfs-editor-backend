from django.db import models


class FilterManager(models.Manager):
    def __init__(self, project_filter='project_id'):
        super().__init__()
        self.project_filter = project_filter

    def get_project_filter(self):
        return self.project_filter

    def filter_by_project(self, project_id):
        return self.get_queryset().filter(**{self.project_filter: project_id})


class InternalIDFilterManager(FilterManager):
    def __init__(self, id_filter, project_filter='project_id'):
        super().__init__(project_filter)
        self.id_filter = id_filter

    def select_by_internal_id(self, project_id, internal_id):
        return self.filter_by_project(project_id).filter(**{self.id_filter: internal_id})

    def multiselect_by_internal_ids(self, project_id, internal_ids):
        internal_ids = list(internal_ids)
        return self.filter_by_project(project_id).filter(**{self.id_filter + '__in': internal_ids})

    def get_internal_id_name(self):
        return self.id_filter
