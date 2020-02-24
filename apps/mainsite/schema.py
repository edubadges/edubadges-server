import graphene

import institution.schema

class Query(institution.schema.Query, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)
