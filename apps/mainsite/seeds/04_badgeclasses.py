import json
from venv import logger
from django.conf import settings

from institution.models import Institution, Faculty
from badgeuser.models import BadgeUser
from issuer.models import Issuer, BadgeClass, BadgeClassExtension

from mainsite.seeds.util import institution_id_by_pba_id, read_seed_csv, seed_image_for

super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)

badge_class_extensions = {
    'extensions:LanguageExtension': {
        '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/LanguageExtension/context.json',
        'type': ['Extension', 'extensions:LanguageExtension'],
        'Language': 'nl_NL',
    },
    'extensions:ECTSExtension': {
        '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/ECTSExtension/context.json',
        'type': ['Extension', 'extensions:ECTSExtension'],
        'ECTS': 2.5,
    },
    'extensions:EQFExtension': {
        '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/EQFExtension/context.json',
        'type': ['Extension', 'extensions:EQFExtension'],
        'EQF': 7,
    },
    'extensions:LearningOutcomeExtension': {
        '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/LearningOutcomeExtension/context.json',
        'type': ['Extension', 'extensions:LearningOutcomeExtension'],
        'LearningOutcome': 'Will appreciate the benefits of learning a foreign language.',
    },
    'extensions:EducationProgramIdentifierExtension': {
        '@context': f'{settings.EXTENSIONS_ROOT_URL}/extensions/EducationProgramIdentifierExtension/context.json',
        'type': ['Extension', 'extensions:EducationProgramIdentifierExtension'],
        'EducationProgramIdentifier': [56823],
    },
}

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

    badgeclass, _ = BadgeClass.objects.get_or_create(
        name=course['Name'],
        issuer=issuer,
        defaults={
            'description': course['Description'],
            'image': image,
            'criteria_text': course['Criteria'],
            'created_by': super_user,
            'updated_by': super_user,
        },
    )

    for key, value in badge_class_extensions.items():
        BadgeClassExtension.objects.get_or_create(badgeclass=badgeclass, name=key, original_json=json.dumps(value))
