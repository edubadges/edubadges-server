import logging

from graphene_django.views import GraphQLView

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
        res = super().execute_graphql_request(request, data, query, variables, operation_name,
                                              show_graphiql=show_graphiql)
        if res.errors:
            logger.exception(str(res.errors))
        return res
