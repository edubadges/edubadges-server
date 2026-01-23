from institution.models import Institution, Faculty
from issuer.models import Issuer
from .util import add_terms_institution, institution_id_by_pba_id, seed_image_for, read_seed_csv


def get_institution_type(identifier: str) -> str:
    # Hardcoded mapping, because the PBA has no concept of institution type
    map = {'11BR': 'MBO', '41GM': 'WO', 'XXID': 'WO', '61PL': 'WO', '57GL': 'HBO', '21FD': 'HBO', '87TS': 'HBO'}
    return map.get(identifier, 'WO')


for row in read_seed_csv('institutions'):
    institution, _ = Institution.objects.get_or_create(
        identifier=institution_id_by_pba_id(row['InstitutionIdentifier']),
        defaults={
            'name_english': row['name'],
            'name_dutch': row['name'],
            'description_english': f'At {row["name"]}, we offer a wide range of courses and programs.',
            'description_dutch': f"Op {row['name']}, bieden we een breed scala aan cursussen en programma's aan.",
            'institution_type': get_institution_type(row['InstitutionIdentifier']),
            'image_english': seed_image_for('institution', f'logo-{row["shortcode"]}.png'),
            'image_dutch': seed_image_for('institution', f'logo-{row["shortcode"]}.png'),
            'grading_table': 'https://url.to.gradingtable/gradingtable.html',
            'direct_awarding_enabled': True,
            'micro_credentials_enabled': True,
            'ob3_ssi_agent_enabled': True,
            'brin': '000-7777-11111',
        },
    )
    add_terms_institution(institution)

for row in read_seed_csv('issuers_issuergroups'):
    fac = row['Issuergroup']
    if not fac or fac == '':
        continue

    institution_id = institution_id_by_pba_id(row['Issuergroupidentifier'].split('.')[0])

    ins = Institution.objects.get(identifier=institution_id)
    faculty = Faculty.objects.get_or_create(
        name_english=fac,
        name_dutch=fac,
        description_english=f'Description for {fac}',
        description_dutch=f'Beschrijving voor {fac}',
        faculty_type=ins.institution_type,
        institution=ins,
        image_english=ins.image_english,
        image_dutch=ins.image_dutch,
    )[0]
    faculty.save()

    issuer_name = f'{fac} Issuer'
    Issuer.objects.get_or_create(
        name_english=issuer_name,
        name_dutch=issuer_name,
        description_english=f'Description for {issuer_name}',
        description_dutch=f'Beschrijving voor {issuer_name}',
        faculty=faculty,
        old_json='{}',
        url_english='https://issuer.example.edu',
        email='issuer@example.edu',
        image_english=ins.image_english,
        image_dutch=ins.image_dutch,
    )

# TODO: Add update mechanism for institutions from pba.dev.... jsons
# OR port the institution data to be read from a CSV file. Choice depends on whether the json data is available or not.
