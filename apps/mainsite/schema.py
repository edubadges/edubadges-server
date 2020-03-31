import graphene
import institution.schema
import issuer.schema
import lti_edu.schema
import badgeuser.schema


class Query(institution.schema.Query,
            issuer.schema.Query,
            badgeuser.schema.Query,
            lti_edu.schema.Query,
            badgeuser.schema.Query,
            graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)
