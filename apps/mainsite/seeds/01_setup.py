import json

from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.sites.models import Site

from badgeuser.models import Terms, BadgeUser, TermsUrl
from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass, BadgeClassExtension
from mainsite.models import BadgrApp
# BadgrApp
from mainsite.seeds.constants import EDU_BADGES_FACULTY_NAME, SURF_INSTITUTION_NAME
from .util import add_terms_institution


setattr(settings, 'SUPPRESS_EMAILS', 1)

main_badgr_app, _ = BadgrApp.objects.get_or_create(
    is_active=1,
    cors=settings.UI_URL,
    email_confirmation_redirect="{}/login/".format(settings.UI_URL),
    forgot_password_redirect="{}/change-password/".format(settings.UI_URL),
    signup_redirect="{}/signup/".format(settings.UI_URL),
    ui_login_redirect="{}/auth/login/".format(settings.UI_URL),
    ui_signup_success_redirect="{}/signup/success/".format(settings.UI_URL),
    ui_connect_success_redirect="{}/profile/".format(settings.UI_URL),
    public_pages_redirect="{}/public/".format(settings.UI_URL),
    oauth_authorization_redirect="{}/oauth/".format(settings.UI_URL),
    use_auth_code_exchange=0
)

# Site
site, _ = Site.objects.get_or_create(domain=settings.DOMAIN, name=settings.DOMAIN)

# SocialApp
edu_id_secret = settings.EDU_ID_SECRET
edu_id_app, _ = SocialApp.objects.get_or_create(
    provider="edu_id",
    name="edu_id",
    client_id=settings.EDU_ID_CLIENT,
    secret=edu_id_secret
)

surf_conext_secret = settings.SURF_CONEXT_SECRET
surf_conext_app, _ = SocialApp.objects.get_or_create(
    provider="surf_conext",
    name="surf_conext",
    client_id=settings.SURF_CONEXT_CLIENT,
    secret=surf_conext_secret
)

edu_id_app.sites.add(site)
surf_conext_app.sites.add(site)



# Superuser
superuser, _ = BadgeUser.objects.get_or_create(
    is_superuser=1,
    username=settings.SUPERUSER_NAME,
    email=settings.SUPERUSER_EMAIL,
    is_staff=1
)
superuser.set_password(settings.SUPERUSER_PWD)
superuser.save()

# SURF / eduBadges static
surf_net_institution, _ = Institution.objects.get_or_create(name_english=SURF_INSTITUTION_NAME,
                                                            name_dutch=SURF_INSTITUTION_NAME,
                                                            identifier=SURF_INSTITUTION_NAME,
                                                            description_english=SURF_INSTITUTION_NAME,
                                                            description_dutch=SURF_INSTITUTION_NAME,
                                                            image_english="uploads/issuers/surf.png",
                                                            image_dutch="uploads/issuers/surf.png",
                                                            )
# Terms general
terms_service_agreement_student, _ = Terms.objects.get_or_create(institution=None, terms_type=Terms.TYPE_SERVICE_AGREEMENT_STUDENT)
TermsUrl.objects.get_or_create(terms=terms_service_agreement_student, language=TermsUrl.LANGUAGE_ENGLISH, url="https://raw.githubusercontent.com/edubadges/privacy/master/service-agreement-student-en.md")
TermsUrl.objects.get_or_create(terms=terms_service_agreement_student, language=TermsUrl.LANGUAGE_DUTCH, url="https://raw.githubusercontent.com/edubadges/privacy/master/service-agreement-student-nl.md")
terms_service_agreement_employee, _ = Terms.objects.get_or_create(institution=None, terms_type=Terms.TYPE_SERVICE_AGREEMENT_EMPLOYEE)
TermsUrl.objects.get_or_create(terms=terms_service_agreement_employee, language=TermsUrl.LANGUAGE_ENGLISH, url="https://raw.githubusercontent.com/edubadges/privacy/master/service-agreement-employee-en.md")
TermsUrl.objects.get_or_create(terms=terms_service_agreement_employee, language=TermsUrl.LANGUAGE_DUTCH, url="https://raw.githubusercontent.com/edubadges/privacy/master/service-agreement-employee-nl.md")
terms_of_service, _ = Terms.objects.get_or_create(institution=None, terms_type=Terms.TYPE_TERMS_OF_SERVICE)
TermsUrl.objects.get_or_create(terms=terms_of_service, language=TermsUrl.LANGUAGE_ENGLISH, url="https://raw.githubusercontent.com/edubadges/privacy/master/edubadges-termsofservice-en.md")
TermsUrl.objects.get_or_create(terms=terms_of_service, language=TermsUrl.LANGUAGE_DUTCH, url="https://raw.githubusercontent.com/edubadges/privacy/master/edubadges-termsofservice-nl.md")




add_terms_institution(surf_net_institution)
# surf_net_institution.remove_cached_data(['cached_terms'])
edu_badges_faculty, _ = Faculty.objects.get_or_create(name_english=EDU_BADGES_FACULTY_NAME,
                                                      institution=surf_net_institution,
                                                      description_english=EDU_BADGES_FACULTY_NAME,
                                                      description_dutch=EDU_BADGES_FACULTY_NAME,
                                                      )

surf_issuer, _ = Issuer.objects.get_or_create(name_english="Team edubadges",
                                              name_dutch="Team edubadges",
                                              image_english="uploads/issuers/surf.png",
                                              faculty=edu_badges_faculty,
                                              description_english="Team edubadges",
                                              description_dutch="Team edubadges",
                                              email="info@surf.nl",
                                              url_english="https://www.surf.nl/edubadges",
                                              source="local", original_json="{}", badgrapp=main_badgr_app)

badge_class_extensions = {
    "extensions:LanguageExtension": {
        "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/LanguageExtension/context.json",
        "type": ["Extension", "extensions:LanguageExtension"],
        "Language": "en_EN"
    },
    "extensions:LearningOutcomeExtension": {
        "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/LearningOutcomeExtension/context.json",
        "type": ["Extension", "extensions:LearningOutcomeExtension"],
        "LearningOutcome": "You successfully created an eduID. "
                           "You successfully linked your institution to your eduID. "
                           "You are now ready to collect badges and use your backpack."
    }
}
badge_class, _ = BadgeClass.objects.get_or_create(
    name=settings.EDUID_BADGE_CLASS_NAME, issuer=surf_issuer,
    description="Welcome to edubadges. Let your lifelong learning begin! You are now ready to collect all your "
                "badges in your backpack where you can store and manage them safely. "
                "Share them anytime you like and with whomever you like. "
                "Badges are visual representations of your knowledge, skills and competences.",
    source="local",
    criteria_url="https://www.surf.nl/edubadges",
    old_json="{}",
    formal=True,
    image="uploads/badges/edubadge_student.png",
)
for key, value in badge_class_extensions.items():
    BadgeClassExtension.objects.get_or_create(
        name=key,
        original_json=json.dumps(value),
        badgeclass_id=badge_class.id
    )
