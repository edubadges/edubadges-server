import graphene
import issuer.schema
import institution.schema
import lti_edu.schema
import badgeuser.schema


class Query(institution.schema.Query,
            badgeuser.schema.Query,
            issuer.schema.Query,
            lti_edu.schema.Query,
            graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
