import graphene

import institution.schema
import issuer.schema
from badgeuser import schema  # unused import is needed, without it staff cannot query users

class Query(institution.schema.Query,
            issuer.schema.Query,
            graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)
