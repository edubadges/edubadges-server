from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from badgeuser.models import BadgeUser, TermsAgreement
from institution.models import Faculty, FacultyStaff, Institution
from issuer.models import BadgeClass, BadgeClassStaff, Issuer, IssuerStaff


def accept_terms(user):
    if user.is_teacher:
        terms = user.institution.cached_terms()
        for term in terms:
            terms_agreement, _ = TermsAgreement.objects.get_or_create(user=user, terms=term)
            terms_agreement.agreed_version = term.version
            terms_agreement.agreed = True
            terms_agreement.save()


all_perms = {
    'may_create': True,
    'may_read': True,
    'may_update': True,
    'may_delete': True,
    'may_award': True,
    'may_sign': True,
    'may_administrate_users': True,
}

award_perms = {
    'may_create': False,
    'may_read': False,
    'may_update': False,
    'may_delete': False,
    'may_award': True,
    'may_sign': True,
    'may_administrate_users': False,
}


def create_facultystaff(username, email, first_name, last_name, institution_name, faculty_name, uid, perms=all_perms):
    user, _ = BadgeUser.objects.get_or_create(
        username=username,
        email=email,
        last_name=last_name,
        first_name=first_name,
        is_teacher=True,
        invited=True,
        is_superuser=False,
    )

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(identifier=institution_name)
    faculty = Faculty.objects.get(name_english=faculty_name, institution=institution)
    user.institution = institution
    accept_terms(user)
    user.save()

    # We cannot faculty.create_staff_membership() here, because this doesn't consider
    # existing memberships. So we have to do it manually.
    FacultyStaff.objects.get_or_create(user=user, faculty=faculty, **perms)


def create_issuerstaff(
    username, email, first_name, last_name, institution_name, faculty_name, issuer_name, uid, perms=all_perms
):
    user, _ = BadgeUser.objects.get_or_create(
        username=username, email=email, last_name=last_name, first_name=first_name, is_teacher=True, invited=True
    )

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(identifier=institution_name)
    user.institution = institution
    faculty = Faculty.objects.get(name_english=faculty_name, institution=institution)
    issuer = Issuer.objects.get(name_english=issuer_name, faculty=faculty)
    accept_terms(user)
    user.save()

    # We cannot issuer.create_staff_membership() here, because this doesn't consider
    # existing memberships. So we have to do it manually.
    IssuerStaff.objects.get_or_create(user=user, issuer=issuer, **perms)


def create_badgeclassstaff(
    username,
    email,
    first_name,
    last_name,
    institution_name,
    faculty_name,
    issuer_name,
    badgeclass_name,
    uid,
    perms=all_perms,
):
    user, _ = BadgeUser.objects.get_or_create(
        username=username, email=email, last_name=last_name, first_name=first_name, is_teacher=True, invited=True
    )

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(identifier=institution_name)
    user.institution = institution

    faculty = Faculty.objects.get(name_english=faculty_name, institution=institution)
    issuer = Issuer.objects.get(name_english=issuer_name, faculty=faculty)
    badgeclass = BadgeClass.objects.get(name=badgeclass_name, issuer=issuer)
    accept_terms(user)
    user.save()

    # We cannot badgeclass.create_staff_membership() here, because this doesn't consider
    # existing memberships. So we have to do it manually.
    BadgeClassStaff.objects.get_or_create(user=user, badgeclass=badgeclass, **perms)


issuer_group_staff = [
    # staff2
    {
        'username': 'anthony',
        'email': 'Anthony_West@university-example.org',
        'first_name': 'Anthony',
        'last_name': 'West',
        'institution_name': 'university-example.org',
        'faculty_name': 'Medicine',
        'uid': '94d8812c425944e5b707ffd12bdf44f0ed71b809',
    },
    # staff3
    {
        'username': 'oburton',
        'email': 'Osc@r__Burton@university-example.org',
        'first_name': 'Oscar',
        'last_name': 'Burton',
        'institution_name': 'university-example.org',
        'faculty_name': 'Medicine',
        'uid': '802d1a5325b08dca8ce30fe7e92a69187abb8ead',
        'perms': award_perms,
    },
    # t eacher 7
    {
        'username': 'teacher7',
        'email': 'teacher7@harvard-example.edu',
        'first_name': 'Teacher7',
        'last_name': 'East',
        'institution_name': 'harvard-example.edu',
        'faculty_name': 'Medicine',
        'uid': 'c39bc64457075f9953c4608c2bd57f28bed6d2aa',
    },
    # teacher 8
    {
        'username': 'teacher8',
        'email': 'teacher8@yale-uni-example.edu',
        'first_name': 'Teacher8',
        'last_name': 'West',
        'institution_name': 'yale-uni-example.edu',
        'faculty_name': 'Medicine',
        'uid': '20c67628b85c421edfb2ca95c92654455cd69aa5',
    },
]

issuer_staff = [
    # professor 5
    {
        'username': 'jrockefeller',
        'email': 'John.D.Rockefeller@university-example.org',
        'first_name': 'John Davison',
        'last_name': 'Rockefeller',
        'institution_name': 'university-example.org',
        'faculty_name': 'Medicine',
        'issuer_name': 'Medicine',
        'uid': '981c9a944fe8ed05a0c33d40dc4da134ed6c0d93',
    },
    # teacher 2
    {
        'username': 'pkrugman',
        'email': 'P.R.Krugman@harvard-example.edu',
        'first_name': 'Paul',
        'last_name': 'Krugman',
        'institution_name': 'harvard-example.edu',
        'faculty_name': 'Medicine',
        'issuer_name': 'Medicine',
        'uid': 'a400fdc5edda4ab3c99400506610c1bb062bedb8',
        'perms': award_perms,
    },
    # teacher 11
    {
        'username': 'teacher11',
        'email': 'teacher11@harvard-example.edu',
        'first_name': 'Teacher11',
        'last_name': 'North',
        'institution_name': 'harvard-example.edu',
        'faculty_name': 'Medicine',
        'issuer_name': 'Medicine',
        'uid': 'c3df59f7a8d884c5db8852aa5b60a813eb6a4183',
    },
    # teacher 12
    {
        'username': 'teacher12',
        'email': 'teacher12@yale-uni-example.edu',
        'first_name': 'Teacher12',
        'last_name': 'South',
        'institution_name': 'yale-uni-example.edu',
        'faculty_name': 'Medicine',
        'issuer_name': 'Medicine',
        'uid': '00b953fcc7849c084761b3a9163a475c9c700d88',
    },
]

badgeclass_staff = [
    # professor 2
    {
        'username': 'p2u1',
        'email': 'S.Wynn@harvard-example.edu',
        'first_name': 'Steve',
        'last_name': 'Wynn',
        'institution_name': 'harvard-example.edu',
        'faculty_name': 'Medicine',
        'issuer_name': 'Medicine',
        'badgeclass_name': 'Growth and Development',
        'uid': '19e584047361617f97a8b0cfa6a17555d68753c1',
    },
    # professor 3
    {
        'username': 'p1u2',
        'email': 'isaacnewton@university-example.org',
        'first_name': 'Isaac',
        'last_name': 'Newton',
        'institution_name': 'university-example.org',
        'faculty_name': 'Medicine',
        'issuer_name': 'Medicine',
        'badgeclass_name': 'Growth and Development',
        'uid': '838b97344478a4086f07cf66b29d93730580a023',
        'perms': award_perms,
    },
]

[create_facultystaff(**a) for a in issuer_group_staff]
[create_issuerstaff(**a) for a in issuer_staff]
[create_badgeclassstaff(**a) for a in badgeclass_staff]
