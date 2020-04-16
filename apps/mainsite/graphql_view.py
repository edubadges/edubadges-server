import logging

from graphene_django.views import GraphQLView

logger = logging.getLogger('Badgr.Debug')


class ExtendedGraphQLView(GraphQLView):

    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):
        res = super().execute_graphql_request(request, data, query, variables, operation_name,
                                              show_graphiql=show_graphiql)
        vals = res.data.values() if res.data else []
        results = list(filter(lambda res: res is not None, vals))
        if not results or res.errors:
            if res.errors:
                logger.exception(str(res.errors))
            res.invalid = True
        return res
