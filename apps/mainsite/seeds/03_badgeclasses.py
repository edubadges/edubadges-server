from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass

faculties = ["Law", "Business", "Humanities", "Medicine", "Science", "Social and Behavioural Science"]

# Faculty
for ins in Institution.objects.exclude(name="surfnet.nl"):
    for fac in faculties:
        Faculty.objects.get_or_create(name=fac, description=f"Description for {fac}", institution=ins)

# Issuer
issuers = [['Notarial Law', 'Tax Law', 'Criminology'],
           ['Economics', 'Global Affairs', 'Public Administration'],
           ['History', 'International Relations', 'Linguistics'],
           ['Medicine', 'Biomedical Sciences'],
           ['Astronomy', 'Biology', 'Mathematics', 'Physics', 'Computer Science'],
           ['Psychology', 'Sociology', 'Political Science', 'Anthropology']]

issuers = dict(zip(faculties, issuers))

for fac in Faculty.objects.exclude(name="eduBadges"):
    [Issuer.objects.get_or_create(name=issuer, description=f"Description for {issuer}", faculty=fac, old_json="{}",
                                  url=f"https://issuer", email="issuer@info.nl", image="uploads/issuers/surf.png") for
     issuer in issuers[fac.name]]

# BadgeClass
# Faculty: Social and Behavioural Science ## Issuer: Psychology
for iss in Issuer.objects.filter(name="Psychology"):
    [BadgeClass.objects.get_or_create(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
        image="uploads/badges/eduid.png",
    ) for bc in ['Introduction to Psychology', 'Cognitive Psychology', 'Psychometrics', 'Group Dynamics']]

# Faculty: Social and Behavioural Science ## Issuer: Political Science
for iss in Issuer.objects.filter(name="Political Science"):
    [BadgeClass.objects.get_or_create(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
        image="uploads/badges/eduid.png",
    ) for bc in
        ['Introduction to Political Science', 'Law and Politics', 'History of Political Thought', 'Research Methods']]

# Faculty: Medicine ## Issuer: Medicine
for iss in Issuer.objects.filter(name="Medicine"):
    [BadgeClass.objects.get_or_create(
        name=bc,
        issuer=iss,
        description="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        old_json="{}",
        image="uploads/badges/eduid.png",
    ) for bc in
        ['Growth and Development', 'Circulation and Breathing', 'Regulation and Integration', 'Digestion and Defense']]

# TODO StudentsEnrolled - different statusses, BadgeInstances,