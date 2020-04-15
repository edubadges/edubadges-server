from graphene_django.views import GraphQLView


class ExtendedGraphQLView(GraphQLView):

    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):
        res = super().execute_graphql_request(request, data, query, variables, operation_name, show_graphiql=show_graphiql)
        # results = list(filter(lambda res: res is not None, res.data.values()))
        if res.errors:
            res.invalid = True
        return res
