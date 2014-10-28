from django.views.generic import TemplateView
from django.db import models
import itertools
from djangosphinx.models import SphinxQuerySet

_all_sphinx_indexes_cache = None

def live_indexes():
    global _all_sphinx_indexes_cache
    if _all_sphinx_indexes_cache is None:
        indexes = []
        model_classes = itertools.chain(*(models.get_models(app) for app in models.get_apps()))
        for model in model_classes:
            if getattr(model._meta, 'proxy', False) or getattr(model._meta, 'abstract', False):
                continue
            index = getattr(model, '__sphinx_indexes__', None)
            if index is not None:
                indexes.extend(index)
        _all_sphinx_indexes_cache = ' '.join(indexes)
    return _all_sphinx_indexes_cache


class SearchResults(TemplateView):
    template_name = 'search.html'

    def get_context_object_name(self, request, *args, **kwargs):
        return "Search"

    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        filter_query = request.GET.get('filter', None)
        limit = 20

        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        qs = SphinxQuerySet(index=live_indexes()).query(query)
        
        context = self.get_context_data(params=kwargs)

        try:
            offset = limit * (page - 1)
            results = list(qs[offset:offset+limit])
            count = qs.count()
        except:
            count = -1
            results = []
            offset = 0

        context['page'] = page
        context['count'] = count
        context['num_pages'] = max(1, count / limit)
        context['object_list'] = results
        context['query'] = query
        context['filter'] = filter_query
        if context['num_pages'] > 1:
            context['is_paginated'] = True
        if page > 1:
            context['previous_page_number'] = page-1
        if page < context['num_pages']:
            context['next_page_number'] = page+1
        return self.render_to_response(context)

