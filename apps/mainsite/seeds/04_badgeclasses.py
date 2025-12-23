import json
from typing import Any
from venv import logger

from badgeuser.models import BadgeUser
from django.conf import settings
from institution.models import Faculty, Institution
from issuer.models import BadgeClass, BadgeClassExtension, Issuer
from mainsite.seeds.util import institution_id_by_pba_id, read_seed_csv, seed_image_for

super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)


def map_language(language: str) -> str:
    return {'nl': 'nl_NL', 'en': 'en_EN'}.get(language, 'en_EN')


def map_yes_no(value: str) -> bool:
    return value.lower() == 'yes'


def badge_class_extensions(
    learning_outcome: str,
    ects: float,
    studyload: int,
    time_investment: int,
    eqf: int,
    language: str,
    education_program_identifier: int,
) -> dict[str, dict[str, Any]]:
    # We must add one extension based on which attribute has a value
    if ects:
        load_extension = {
            'extensions:ECTSExtension': {
                '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/ECTSExtension/context.json',
                'type': ['Extension', 'extensions:ECTSExtension'],
                'ECTS': ects,
            }
        }
    elif studyload:
        load_extension = {
            'extensions:StudyLoadExtension': {
                '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/StudyLoadExtension/context.json',
                'type': ['Extension', 'extensions:StudyLoadExtension'],
                'StudyLoad': studyload,
            }
        }
    elif time_investment:
        load_extension = {
            'extensions:TimeInvestmentExtension': {
                '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/TimeInvestmentExtension/context.json',
                'type': ['Extension', 'extensions:TimeInvestmentExtension'],
                'TimeInvestment': time_investment,
            }
        }
    else:
        load_extension = {}

    extensions = {
        'extensions:LanguageExtension': {
            '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/LanguageExtension/context.json',
            'type': ['Extension', 'extensions:LanguageExtension'],
            'Language': language,
        },
        'extensions:EQFExtension': {
            '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/EQFExtension/context.json',
            'type': ['Extension', 'extensions:EQFExtension'],
            'EQF': eqf,
        },
        'extensions:LearningOutcomeExtension': {
            '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/LearningOutcomeExtension/context.json',
            'type': ['Extension', 'extensions:LearningOutcomeExtension'],
            'LearningOutcome': learning_outcome,
        },
        'extensions:EducationProgramIdentifierExtension': {
            '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/EducationProgramIdentifierExtension/context.json',
            'type': ['Extension', 'extensions:EducationProgramIdentifierExtension'],
            'EducationProgramIdentifier': [education_program_identifier],
        },
    }

    return {**extensions, **load_extension}


for course in read_seed_csv('courses'):
    institution_id = institution_id_by_pba_id(course['CourseID'].split('.')[0])
    if not institution_id:
        logger.debug(f'Invalid course ID: {course["CourseID"]} - skipped')
        continue

    institution = Institution.objects.get(identifier=institution_id)
    # Pick the first first faculty and then its first issuer
    faculty = Faculty.objects.filter(institution=institution).first()
    issuer = Issuer.objects.filter(faculty=faculty).first()

    if not issuer:
        logger.debug(f'No issuer found for institution {institution.name}')
        continue

    image = None
    try:
        image = seed_image_for('badges', course['Image'])
    except IsADirectoryError as e:
        logger.debug(f'Using fallback image. CSV has no image set for course {course["Name"]}')
        image = seed_image_for('badges', 'fallback.png')
    except Exception as e:
        logger.debug(f'Using fallback image. Seed image for {course["Name"]} cannot be found: {e}')
        image = seed_image_for('badges', 'fallback.png')

    # Entity IDs aren't allowed to contain periods as seen in
    # apps/public/public_api_urls.py regexes
    entity_id = course['CourseID'].replace('.', '-')

    badgeclass, _ = BadgeClass.objects.get_or_create(
        name=course['Name'],
        issuer=issuer,
        defaults={
            'entity_id': entity_id,
            'description': course['Description'],
            'image': image,
            'criteria_text': course['Criteria'],
            'created_by': super_user,
            'updated_by': super_user,
            'assessment_type': course['Type of Assesment'],  #  NOTE the typo is intentional
            'participation': course['Form of participation'],
            'assessment_supervised': map_yes_no(course['Supervised']),
            'assessment_id_verified': map_yes_no(course['Verified identity']),
            'quality_assurance_name': course['Quality Assurance Name'],
            'quality_assurance_description': course['Quality Assurance Description'],
            'quality_assurance_url': course['Quality Assurance URL'],
        },
    )

    extensions = badge_class_extensions(
        learning_outcome=course['LearningOutcome'],
        ects=course['ECTS'],
        studyload=course['Studyload'],
        time_investment=course['TimeInvestment'],
        eqf=course['EQF'],
        language=map_language(course['Language']),
        education_program_identifier=course['ProgrammeID'],
    )
    for key, value in extensions.items():
        BadgeClassExtension.objects.get_or_create(badgeclass=badgeclass, name=key, original_json=json.dumps(value))
