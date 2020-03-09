import graphene

import institution.schema
import issuer.schema
import lti_edu.schema
from badgeuser import schema  # unused import is needed, without it staff cannot query users

class Query(institution.schema.Query,
            issuer.schema.Query,
            lti_edu.schema.Query,
            graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)
