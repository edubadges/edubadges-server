import logging

from graphene_django.views import GraphQLView

logger = logging.getLogger("Badgr.Debug")


class IntrospectionDisabledException(Exception):  # noqa: N818
    pass


class DisableIntrospectionMiddleware:
    def resolve(self, next, root, info, **kwargs):  # noqa: A002
        if info.field_name.lower() in ["__schema", "__introspection"]:
            raise IntrospectionDisabledException
        return next(root, info, **kwargs)


class ExtendedGraphQLView(GraphQLView):
    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):  # noqa: FBT002, PLR0913, PLR0917
        res = super().execute_graphql_request(
            request, data, query, variables, operation_name, show_graphiql=show_graphiql
        )
        if res.errors:
            logger.exception(str(res.errors))  # noqa: LOG004
        return res
