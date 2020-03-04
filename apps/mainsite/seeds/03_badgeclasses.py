from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass


# Faculty
for ins in Institution.objects.all():
    law = Faculty(name="Law", institution=ins).save()
    business = Faculty(name="Business", institution=ins).save()
    humanities = Faculty(name="Humanities", institution=ins).save()
    medicine = Faculty(name="Medicine", institution=ins).save()
    science = Faculty(name="Science", institution=ins).save()
    social = Faculty(name="Social and Behavioural Science", institution=ins).save()


# Issuer
issuers = {
    'Law': ['Notarial Law', 'Tax Law', 'Criminology'],
    'Business': ['Economics', 'Global Affairs', 'Public Administration'],
    'Humanities': ['History', 'International Relations', 'Linguistics'],
    'Medicine': ['Medicine', 'Biomedical Sciences'],
    'Science': ['Astronomy', 'Biology', 'Mathematics', 'Physics', 'Computer Science'],
    'Social and Behavioural Science': ['Psychology', 'Sociology', 'Political Science', 'Anthropology']
}

for fac in Faculty.objects.all():
    [Issuer(name=issuer, faculty=fac, old_json="{}").save() for issuer in issuers[fac.name]]


# BadgeClass
## Faculty: Social and Behavioural Science ## Issuer: Psychology
for iss in Issuer.objects.filter(name="Psychology"):
    [BadgeClass(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
    ).save() for bc in ['Introduction to Psychology', 'Cognitive Psychology', 'Psychometrics', 'Group Dynamics']]

## Faculty: Social and Behavioural Science ## Issuer: Political Science
for iss in Issuer.objects.filter(name="Political Science"):
    [BadgeClass(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
    ).save() for bc in ['Introduction to Political Science', 'Law and Politics', 'History of Political Thought', 'Research Methods']]

## Faculty: Medicine ## Issuer: Medicine
for iss in Issuer.objects.filter(name="Medicine"):
    [BadgeClass(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
    ).save() for bc in ['Growth and Development', 'Circulation and Breathing', 'Regulation and Integration', 'Digestion and Defense']]
