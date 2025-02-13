import json
from typing import List
from django.conf import settings
from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass, BadgeClassExtension
from mainsite.seeds.constants import EDU_BADGES_FACULTY_NAME, SURF_INSTITUTION_NAME, \
    BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY, BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_PSYCHOMETRICS, \
    BADGE_CLASS_GROUP_DYNAMICS

faculties = ["Law", "Business", "Humanities", "Medicine", "Science", "Social and Behavioural Science"]

# Faculty
for ins in Institution.objects.exclude(identifier=SURF_INSTITUTION_NAME):
    for fac in faculties:
        Faculty.objects.get_or_create(
            name_english=fac,
            description_english=f"Description for {fac}",
            description_dutch=f"Beschrijving voor {fac}",
            institution=ins
        )

# Issuer
issuers = [['Notarial Law', 'Tax Law', 'Criminology'],
           ['Economics', 'Global Affairs', 'Public Administration'],
           ['History', 'International Relations', 'Linguistics'],
           ['Medicine', 'Biomedical Sciences'],
           ['Astronomy', 'Biology', 'Mathematics', 'Physics', 'Computer Science'],
           ['Psychology', 'Sociology', 'Political Science', 'Anthropology']]

issuers = dict(zip(faculties, issuers))

for fac in Faculty.objects.exclude(name_english=EDU_BADGES_FACULTY_NAME):
    [Issuer.objects.get_or_create(name_english=issuer,
                                  description_english=f"Description for {issuer}",
                                  description_dutch=f"Beschrijving voor {issuer}",
                                  faculty=fac, old_json="{}",
                                  url_english=f"https://issuer", email="issuer@info.nl", image_english="uploads/issuers/surf.png") for
     issuer in issuers[fac.name]]

badge_class_extensions = {
    "extensions:LanguageExtension": {
        "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/LanguageExtension/context.json",
        "type": ["Extension", "extensions:LanguageExtension"],
        "Language": "nl_NL"
    },
    "extensions:ECTSExtension": {
        "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/ECTSExtension/context.json",
        "type": ["Extension", "extensions:ECTSExtension"],
        "ECTS": 2.5
    },
    "extensions:EQFExtension": {
        "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/EQFExtension/context.json",
        "type": ["Extension", "extensions:EQFExtension"],
        "EQF": 7
    },
    "extensions:LearningOutcomeExtension": {
        "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/LearningOutcomeExtension/context.json",
        "type": ["Extension", "extensions:LearningOutcomeExtension"],
        "LearningOutcome": "Will appreciate the benefits of learning a foreign language."
    },
    "extensions:EducationProgramIdentifierExtension": {
        "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/EducationProgramIdentifierExtension/context.json",
        "type": ["Extension", "extensions:EducationProgramIdentifierExtension"],
        "EducationProgramIdentifier": [56823]
    }
}

# add some markdown to the description, make it multiline.
badge_class_description = '''
# Introduction to Lorem Ipsum
Lorem ipsum dolor **sit amet**, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Subtitle
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.

* Excepteur sint occaecat cupidatat non proident
* Sunt in culpa qui officia deserunt mollit anim id est laborum

### Subsubtitle

1. Lorem ipsum dolor sit amet
2. Consectetur adipiscing elit
3. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua
'''

def create_badge_class(name, issuer):
    badge_class, _ = BadgeClass.objects.get_or_create(
        name=name,
        issuer=issuer,
        description=badge_class_description,
        formal=True,
        criteria_text="In order to earn this badge, you must complete the course and show proficiency in things.",
        old_json="{}",
        image="uploads/badges/eduid.png",
    )
    for key, value in badge_class_extensions.items():
        BadgeClassExtension.objects.get_or_create(
            name=key,
            original_json=json.dumps(value),
            badgeclass_id=badge_class.id
        )
    return badge_class


# BadgeClass
# Faculty: Social and Behavioural Science ## Issuer: Psychology
for iss in Issuer.objects.filter(name_english="Psychology"):
    [create_badge_class(bc, iss) for bc in
     [BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY, BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_PSYCHOMETRICS,
      BADGE_CLASS_GROUP_DYNAMICS]]

# Faculty: Social and Behavioural Science ## Issuer: Political Science
for iss in Issuer.objects.filter(name_english="Political Science"):
    [create_badge_class(bc, iss) for bc in
     ['Introduction to Political Science', 'Law and Politics', 'History of Political Thought', 'Research Methods']]

# Faculty: Medicine ## Issuer: Medicine
for iss in Issuer.objects.filter(name_english="Medicine"):
    [create_badge_class(bc, iss) for bc in
     ['Growth and Development', 'Circulation and Breathing', 'Regulation and Integration', 'Digestion and Defense']]

# Faculty Medicine ## Alignments
for bc in BadgeClass.objects.filter(issuer__name_english="Medicine"):
    bc.alignment_items = [
            { "target_name": "EQF", "target_url": "https://ec.europa.eu/ploteus/content/descriptors-page", "target_description": "European Qualifications Framework", "target_framework": "EQF", "target_code": "7" },
            { "target_name": "ECTS", "target_url": "https://ec.europa.eu/education/resources-and-tools/european-credit-transfer-and-accumulation-system-ects_en", "target_description": "European Credit Transfer and Accumulation System", "target_framework": "ECTS", "target_code": "2.5" },
    ]
    bc.save()

# Add quality assurance to half of the badges
for bc in BadgeClass.objects.all()[::2]:
    bc.quality_assurance_description = "Quality assurance framework FAKE1.0"
    bc.quality_assurance_name = "FAKE1.0"
    bc.quality_assurance_url = "https://example.com/qaf/FAKE1.0"
    bc.save()

# Add assessment_type to half of the badges
iterator = 0
assessment_types: List[str] = ["testing", "application of a skill", "portfolio", "recognition of prior learning"]
n_types = len(assessment_types)
for bc in BadgeClass.objects.all()[::2]:
    bc.assessment_type = assessment_types[iterator % n_types]
    bc.save()
    iterator += 1

iterator = 0

# For half of the badges with assessment_type "testing", set assessment_supervised to True
for bc in BadgeClass.objects.filter(assessment_type="testing")[::2]:
    bc.assessment_supervised = True
    bc.save()

# for half of that are supervised, set identity_checked to True
for bc in BadgeClass.objects.exclude(assessment_supervised=False)[::2]:
    bc.identity_checked = True
    bc.save()
