import json
from dataclasses import dataclass
from typing import Any
from venv import logger

from badgeuser.models import BadgeUser
from django.conf import settings
from institution.models import Faculty, Institution
from issuer.models import BadgeClass, BadgeClassExtension, Issuer
from mainsite.seeds.util import institution_id_by_pba_id, read_seed_csv, seed_image_for

super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)


@dataclass
class CourseRow:
    """
    Typed representation of a course CSV row.
    
    This dataclass enforces proper types for numeric and boolean fields,
    ensuring type safety when processing course data.
    """
    
    # String fields
    CourseID: str
    Name: str
    Description: str
    LearningOutcome: str
    Criteria: str
    Language: str
    Image: str
    Type_of_Assesment: str  # Typo is intentional - matches CSV
    Form_of_participation: str
    Quality_Assurance_Name: str
    Quality_Assurance_Description: str
    Quality_Assurance_URL: str
    
    # Numeric fields - properly typed
    ECTS: float
    Studyload: int
    TimeInvestment: int
    EQF: int
    ProgrammeID: int
    
    # Boolean fields
    Supervised: bool
    Verified_identity: bool


def parse_course_row(row: dict[str, str]) -> CourseRow:
    """
    Parse a CSV row dictionary into a typed CourseRow object.
    
    This function handles type conversion from CSV strings to appropriate Python types:
    - Empty numeric strings are converted to 0
    - 'yes'/'no' strings are converted to boolean True/False
    - All other strings are kept as-is
    
    Args:
        row: Dictionary from CSV DictReader with string values
        
    Returns:
        CourseRow: Typed dataclass instance with proper numeric and boolean types
    """
    return CourseRow(
        CourseID=row['CourseID'],
        Name=row['Name'],
        Description=row['Description'],
        LearningOutcome=row['LearningOutcome'],
        Criteria=row['Criteria'],
        Language=row['Language'],
        Image=row['Image'],
        Type_of_Assesment=row['Type of Assesment'],
        Form_of_participation=row['Form of participation'],
        Quality_Assurance_Name=row['Quality Assurance Name'],
        Quality_Assurance_Description=row['Quality Assurance Description'],
        Quality_Assurance_URL=row['Quality Assurance URL'],
        # Type conversions for numeric fields
        ECTS=float(row['ECTS']) if row['ECTS'] else 0.0,
        Studyload=int(row['Studyload']) if row['Studyload'] else 0,
        TimeInvestment=int(row['TimeInvestment']) if row['TimeInvestment'] else 0,
        EQF=int(row['EQF']) if row['EQF'] else 0,
        ProgrammeID=int(row['ProgrammeID']) if row['ProgrammeID'] else 0,
        # Type conversions for boolean fields
        Supervised=row['Supervised'].lower() == 'yes' if row['Supervised'] else False,
        Verified_identity=row['Verified identity'].lower() == 'yes' if row['Verified identity'] else False,
    )


def map_language(language: str) -> str:
    return {'nl': 'nl_NL', 'en': 'en_EN'}.get(language, 'en_EN')


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


for row in read_seed_csv('courses'):
    # Parse the CSV row into a typed CourseRow object
    # This enforces type conversion for numeric and boolean fields
    course = parse_course_row(row)
    
    institution_id = institution_id_by_pba_id(course.CourseID.split('.')[0])
    if not institution_id:
        logger.debug(f'Invalid course ID: {course.CourseID} - skipped')
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
        image = seed_image_for('badges', course.Image)
    except IsADirectoryError as e:
        logger.debug(f'Using fallback image. CSV has no image set for course {course.Name}')
        image = seed_image_for('badges', 'fallback.png')
    except Exception as e:
        logger.debug(f'Using fallback image. Seed image for {course.Name} cannot be found: {e}')
        image = seed_image_for('badges', 'fallback.png')

    badgeclass, _ = BadgeClass.objects.get_or_create(
        name=course.Name,
        issuer=issuer,
        defaults={
            'description': course.Description,
            'image': image,
            'criteria_text': course.Criteria,
            'created_by': super_user,
            'updated_by': super_user,
            'assessment_type': course.Type_of_Assesment,  # NOTE the typo is intentional
            'participation': course.Form_of_participation,
            'assessment_supervised': course.Supervised,  # Already a boolean
            'assessment_id_verified': course.Verified_identity,  # Already a boolean
            'quality_assurance_name': course.Quality_Assurance_Name,
            'quality_assurance_description': course.Quality_Assurance_Description,
            'quality_assurance_url': course.Quality_Assurance_URL,
        },
    )

    extensions = badge_class_extensions(
        learning_outcome=course.LearningOutcome,
        ects=course.ECTS,  # Now properly typed as float
        studyload=course.Studyload,  # Now properly typed as int
        time_investment=course.TimeInvestment,  # Now properly typed as int
        eqf=course.EQF,  # Now properly typed as int
        language=map_language(course.Language),
        education_program_identifier=course.ProgrammeID,  # Now properly typed as int
    )
    for key, value in extensions.items():
        BadgeClassExtension.objects.get_or_create(badgeclass=badgeclass, name=key, original_json=json.dumps(value))
