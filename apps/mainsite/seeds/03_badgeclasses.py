from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass


# Faculty
for ins in Institution.objects.exclude(name="surfnet.nl"):
    Faculty.objects.get_or_create(name="Law", institution=ins)
    Faculty.objects.get_or_create(name="Business", institution=ins)
    Faculty.objects.get_or_create(name="Humanities", institution=ins)
    Faculty.objects.get_or_create(name="Medicine", institution=ins)
    Faculty.objects.get_or_create(name="Science", institution=ins)
    Faculty.objects.get_or_create(name="Social and Behavioural Science", institution=ins)


# Issuer
issuers = {
    'Law': ['Notarial Law', 'Tax Law', 'Criminology'],
    'Business': ['Economics', 'Global Affairs', 'Public Administration'],
    'Humanities': ['History', 'International Relations', 'Linguistics'],
    'Medicine': ['Medicine', 'Biomedical Sciences'],
    'Science': ['Astronomy', 'Biology', 'Mathematics', 'Physics', 'Computer Science'],
    'Social and Behavioural Science': ['Psychology', 'Sociology', 'Political Science', 'Anthropology']
}

for fac in Faculty.objects.exclude(name="eduBadges"):
    [Issuer.objects.get_or_create(name=issuer, faculty=fac, old_json="{}") for issuer in issuers[fac.name]]


# BadgeClass
## Faculty: Social and Behavioural Science ## Issuer: Psychology
for iss in Issuer.objects.filter(name="Psychology"):
    [BadgeClass.objects.get_or_create(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
    ) for bc in ['Introduction to Psychology', 'Cognitive Psychology', 'Psychometrics', 'Group Dynamics']]

## Faculty: Social and Behavioural Science ## Issuer: Political Science
for iss in Issuer.objects.filter(name="Political Science"):
    [BadgeClass.objects.get_or_create(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
    ) for bc in ['Introduction to Political Science', 'Law and Politics', 'History of Political Thought', 'Research Methods']]

## Faculty: Medicine ## Issuer: Medicine
for iss in Issuer.objects.filter(name="Medicine"):
    [BadgeClass.objects.get_or_create(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
    ) for bc in ['Growth and Development', 'Circulation and Breathing', 'Regulation and Integration', 'Digestion and Defense']]
