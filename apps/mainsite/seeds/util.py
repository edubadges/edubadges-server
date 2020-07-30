from badgeuser.models import Terms, TermsUrl

def add_terms_instiution(institution):
    formal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, version=1, terms_type=Terms.TYPE_FORMAL_BADGE)
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH, url="https://github.com/edubadges/privacy/blob/master/university-example.org/formal-edubadges-agreement-en.md")
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, url="https://github.com/edubadges/privacy/blob/master/university-example.org/formal-edubadges-agreement-nl.md")
    informal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, version=1, terms_type=Terms.TYPE_INFORMAL_BADGE)
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH, url="https://github.com/edubadges/privacy/blob/master/university-example.org/informal-edubadges-agreement-en.md")
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, url="https://github.com/edubadges/privacy/blob/master/university-example.org/informal-edubadges-agreement-nl.md")
