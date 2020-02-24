import graphene

import institution.schema
import issuer.schema

class Query(institution.schema.Query, issuer.schema.Query, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)
