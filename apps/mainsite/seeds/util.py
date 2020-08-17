from badgeuser.models import Terms, TermsUrl


def add_terms_institution(institution):
    formal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_FORMAL_BADGE)
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH,  excerpt=False,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-agreement-en.md")
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, excerpt=False,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-agreement-nl.md")
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=True,
                                   url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-en.md')
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, excerpt=True,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-nl.md")
    informal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_INFORMAL_BADGE)
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=False,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-agreement-en.md")
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, excerpt=False,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-agreement-nl.md")
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=True,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-excerpt-en.md")
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, excerpt=True,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-excerpt-nl.md")
