import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from badgeuser.models import Terms, TermsUrl


def upload_initial_images_to_s3():
    """
    Upload initial PNG images to S3 storage if S3 is enabled.
    This replaces the file copying done in entrypoint-k8s.sh
    """
    if not getattr(settings, 'USE_S3', False):
        print("S3 storage not enabled, skipping image upload")
        return

    # Define source directory and files to upload
    source_dir = os.path.join(settings.BASE_DIR, 'uploads')

    files_to_upload = [
        ('badges/eduid.png', 'uploads/badges/eduid.png'),
        ('badges/edubadge_student.png', 'uploads/badges/edubadge_student.png'),
        ('issuers/surf.png', 'uploads/issuers/surf.png'),
        ('institution/surf.png', 'uploads/institution/surf.png'),
    ]

    uploaded_count = 0
    for local_path, s3_path in files_to_upload:
        local_file_path = os.path.join(source_dir, local_path)

        if not os.path.exists(local_file_path):
            print(f"Warning: Local file not found: {local_file_path}")
            continue

        try:
            # Check if file already exists in S3
            if default_storage.exists(s3_path):
                print(f"File already exists in S3: {s3_path}")
                continue

            # Read local file and upload to S3
            with open(local_file_path, 'rb') as file:
                file_content = file.read()
                content_file = ContentFile(file_content)

                stored_path = default_storage.save(s3_path, content_file)
                print(f"Uploaded: {local_path} -> {stored_path}")
                uploaded_count += 1

        except Exception as e:
            print(f"Failed to upload {local_path}: {str(e)}")

    print(f"Successfully uploaded {uploaded_count} images to S3")


def add_terms_institution(institution):
    formal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_FORMAL_BADGE)
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH,  excerpt=False,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-agreement-en.md")
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, excerpt=False,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-agreement-nl.md")
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=True,
                                   url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-en.md')
    TermsUrl.objects.get_or_create(terms=formal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, excerpt=True,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-nl.md")
    informal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_INFORMAL_BADGE)
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=False,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-agreement-en.md")
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, excerpt=False,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-agreement-nl.md")
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=True,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-excerpt-en.md")
    TermsUrl.objects.get_or_create(terms=informal_badge_terms, language=TermsUrl.LANGUAGE_DUTCH, excerpt=True,
                                   url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-excerpt-nl.md")
