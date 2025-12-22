import csv
import glob
import json
import os
from dataclasses import fields
from typing import Type, TypeVar, Union, get_args, get_origin

from badgeuser.models import Terms, TermsUrl
from django.core.files import File
from institution.models import Institution
from typing_extensions import Optional


def seed_image_for(type: str, name: str) -> File:
    base_path = 'apps/mainsite/seeds/images/'
    if type == 'institutions':
        raise ValueError('NOTE: path for institutions is inconsistent and must be singular: institution')

    path = os.path.join(base_path, type, name)
    return File(open(path, 'rb'), name)


def add_terms_institution(institution: Institution) -> None:
    formal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_FORMAL_BADGE)
    TermsUrl.objects.get_or_create(
        terms=formal_badge_terms,
        language=TermsUrl.LANGUAGE_ENGLISH,
        excerpt=False,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-agreement-en.md',
    )
    TermsUrl.objects.get_or_create(
        terms=formal_badge_terms,
        language=TermsUrl.LANGUAGE_DUTCH,
        excerpt=False,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-agreement-nl.md',
    )
    TermsUrl.objects.get_or_create(
        terms=formal_badge_terms,
        language=TermsUrl.LANGUAGE_ENGLISH,
        excerpt=True,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-en.md',
    )
    TermsUrl.objects.get_or_create(
        terms=formal_badge_terms,
        language=TermsUrl.LANGUAGE_DUTCH,
        excerpt=True,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-nl.md',
    )
    informal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_INFORMAL_BADGE)
    TermsUrl.objects.get_or_create(
        terms=informal_badge_terms,
        language=TermsUrl.LANGUAGE_ENGLISH,
        excerpt=False,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-agreement-en.md',
    )
    TermsUrl.objects.get_or_create(
        terms=informal_badge_terms,
        language=TermsUrl.LANGUAGE_DUTCH,
        excerpt=False,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-agreement-nl.md',
    )
    TermsUrl.objects.get_or_create(
        terms=informal_badge_terms,
        language=TermsUrl.LANGUAGE_ENGLISH,
        excerpt=True,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-excerpt-en.md',
    )
    TermsUrl.objects.get_or_create(
        terms=informal_badge_terms,
        language=TermsUrl.LANGUAGE_DUTCH,
        excerpt=True,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-excerpt-nl.md',
    )


def read_seed_csv(csv_name: str) -> list[dict[str, str]]:
    file_path = os.path.join('apps/mainsite/seeds/data', f'{csv_name}.csv')
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter=';', strict=True)
        return list(reader)


T = TypeVar('T')


def read_typed_seed_csv(csv_name: str, schema_class: Type[T]) -> list[T]:
    """
    Read a CSV file and return a list of typed objects based on the provided schema class.
    
    The schema class should be a dataclass with type annotations. This function will:
    1. Read the CSV file
    2. Convert string values to the appropriate types based on the dataclass annotations
    3. Return a list of instances of the schema class
    
    Type conversion rules:
    - int: Converts to integer, empty strings become 0
    - float: Converts to float, empty strings become 0.0
    - bool: Converts 'yes'/'no' (case insensitive) to True/False
    - str: Keeps as string (default)
    - Optional[T]: Converts to T or None if empty string
    
    Example:
        @dataclass
        class CourseSchema:
            name: str
            ects: float
            eqf: int
            supervised: bool
            
        courses = read_typed_seed_csv('courses', CourseSchema)
        # courses[0].ects will be a float, not a string
    """
    file_path = os.path.join('apps/mainsite/seeds/data', f'{csv_name}.csv')
    
    # Get type information from the dataclass fields
    field_types = {field.name: field.type for field in fields(schema_class)}
    
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter=';', strict=True)
        rows = []
        
        for row_dict in reader:
            converted_row = {}
            
            for field in fields(schema_class):
                field_name = field.name
                csv_value = row_dict.get(field_name, '')
                field_type = field_types.get(field_name, str)
                
                # Handle Optional types (Optional[T] is Union[T, None])
                origin = get_origin(field_type)
                if origin is Union:
                    # Get the non-None type from Union[T, None]
                    type_args = get_args(field_type)
                    # Filter out NoneType to get the actual type
                    actual_types = [t for t in type_args if t is not type(None)]
                    if csv_value == '':
                        converted_row[field_name] = None
                        continue
                    # Use the first non-None type for conversion
                    field_type = actual_types[0] if actual_types else str
                
                # Convert the value based on the field type
                try:
                    if field_type == int:
                        converted_row[field_name] = int(csv_value) if csv_value else 0
                    elif field_type == float:
                        converted_row[field_name] = float(csv_value) if csv_value else 0.0
                    elif field_type == bool:
                        converted_row[field_name] = csv_value.lower() == 'yes' if csv_value else False
                    else:
                        converted_row[field_name] = csv_value
                except (ValueError, AttributeError) as e:
                    # If conversion fails, keep the original string value
                    converted_row[field_name] = csv_value
            
            rows.append(schema_class(**converted_row))
        
        return rows


def read_seed_jsons(pattern: str) -> list[dict[str, str]]:
    files = glob.glob(f'apps/mainsite/seeds/data/{pattern}')

    # All files contain arrays at the .iam attribute, merge and return these
    merged = []
    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)
            merged.extend(data['iam'])

    return merged


def institution_by_identifier(identifier: str) -> Institution:
    return Institution.objects.get(identifier=identifier)


def institution_id_by_pba_id(identifier: str) -> Optional[str]:
    map = {
        '11BR': 'mbob.nl',
        '41GM': 'uvh.nl',
        'XXID': 'tun.nb',
        '87TS': 'hbot.nl',
    }
    # NOTE:  Following ids don't have a shortcode in the form of an URL yet in the PBA
    #     '61PL': 'eur.nl',
    #     '57GL': 'ahb.nl',
    #     '21FD': 'nhls.nl',
    return map.get(identifier)
