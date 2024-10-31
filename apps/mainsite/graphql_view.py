import logging
from graphene_django.views import GraphQLView
from django.core.cache import cache

logger = logging.getLogger('Badgr.Debug')


class IntrospectionDisabledException(Exception):
    pass


class DisableIntrospectionMiddleware(object):
    def resolve(self, next, root, info, **kwargs):
        if info.field_name.lower() in ['__schema', '__introspection']:
            raise IntrospectionDisabledException
        return next(root, info, **kwargs)


class ExtendedGraphQLView(GraphQLView):
    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):
        key = hash(repr(query))
        cache_time = 3600  # time in seconds for cache to be valid, 1 hour
        # if cache key in table, return cached result
        res = cache.get(key)
        if not res:
            logger.debug("No cache hit!")
            res = super().execute_graphql_request(
                request, data, query, variables, operation_name, show_graphiql=show_graphiql
            )
            if res.errors:
                logger.exception(str(res.errors))
                res.invalid = True
            else:
                cache.set(key, res, cache_time)
        else:
            logger.debug("Cache hit!")
        return res