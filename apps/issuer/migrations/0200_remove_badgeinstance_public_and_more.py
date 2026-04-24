"""
Migration 0200: Remove public field from BadgeInstance and BadgeInstanceCollection

CONTEXT / LESSONS LEARNED:
-------------------------
This migration file is the result of a Django migration conflict that was not properly
resolved. This documentation explains what happened, what the proper solution would have
been, and why we ended up with this workaround.

WHAT HAPPENED:
- The feature/ewi branch introduced migration 0118_remove_badgeinstance_public_and_more.py
  to remove the 'public' field from BadgeInstance and BadgeInstanceCollection models.
- The develop branch, in parallel, introduced migrations 0118_badgeinstance_recipient_name.py
  and 0119_populate_recipient_name.py (adding recipient_name field and populating it).
- When develop was merged into feature/ewi (commit 1bc4fb10), Django detected a conflict:
  both branches had migration 0118 with different operations. This is a migration numbering
  conflict, not a code merge conflict.

WHAT SHOULD HAVE BEEN DONE:
The correct approach would have been to run:

    python manage.py makemigrations --merge

This would have created an empty merge migration (e.g., 0120_merge.py) that depends on both
conflicting migrations (0118_remove_badgeinstance_public_and_more and 0119_populate_recipient_name),
resolving the branch in the migration graph without renumbering anything.

The proper migration chain would have been:
  0117_... -> 0118_remove_badgeinstance_public_and_more -> 0119_populate_recipient_name
                                                                   -> 0120_merge

WHAT WAS DONE INSTEAD:
Due to BKs lack of understanding of Django's migration conflict resolution at the time,
the conflicting migration 0118_remove_badgeinstance_public_and_more.py was manually
renamed to 0200_remove_badgeinstance_public_and_more.py and given a dependency on 0119.
This resolved the graph conflict but created a new problem:

- Environments that had previously run the original 0118_remove_badgeinstance_public_and_more
  (before the merge) had already removed the 'public' fields from their database.
- On those environments, migration 0200 would attempt to remove the same fields again,
  causing a failure because the columns no longer exist.

WHY THIS WORKAROUND:
Rather than attempting to untangle the migration history (which would require careful
coordination across all environments and risk breaking those with partial migration
states), we chose to make this migration idempotent by:
1. Using SeparateDatabaseAndState to handle state vs. schema separately
2. Making database operations conditional: only attempt to remove fields if they exist
3. Keeping state operations unchanged (Django's state tracking needs to see the removal)

This approach ensures the migration succeeds on ALL environments regardless of whether
they previously ran the original 0118 migration or not.

FUTURE GUIDANCE:
- When you see "Conflicting migrations detected" DO NOT manually rename migrations.
- Run `python manage.py makemigrations --merge` and let Django create a merge migration.
- If you must manually resolve, NEVER reuse or rename migration numbers that may have
  already run on production environments.
"""

from django.db import migrations


def safe_remove_field(app_label, model_name, field_name):
    """
    Conditionally remove a field only if it exists in the model.

    This handles the case where the field may have already been removed
    by a previous migration (0118_remove_badgeinstance_public_and_more in some envs).
    """
    def remove_if_exists(apps, schema_editor):
        model = apps.get_model(app_label, model_name)
        # Check if field exists in the model's meta (state check)
        field_names = [f.name for f in model._meta.get_fields()]
        if field_name in field_names:
            # Field exists in Django's state, attempt to remove from database
            field = model._meta.get_field(field_name)
            schema_editor.remove_field(model, field)
    return remove_if_exists


class Migration(migrations.Migration):
    dependencies = [
        ('issuer', '0119_populate_recipient_name'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # Database operations: only remove if the column exists in the database
            database_operations=[
                migrations.RunPython(
                    safe_remove_field('issuer', 'BadgeInstance', 'public'),
                    reverse=lambda apps, schema_editor: None,
                    description='Remove public field from BadgeInstance if it exists'
                ),
                migrations.RunPython(
                    safe_remove_field('issuer', 'BadgeInstanceCollection', 'public'),
                    reverse=lambda apps, schema_editor: None,
                    description='Remove public field from BadgeInstanceCollection if it exists'
                ),
            ],
            # State operations: always update Django's model state
            # This is safe even if the field was already removed - Django's state
            # tracking will simply see this as a no-op if the field is already gone
            state_operations=[
                migrations.RemoveField(
                    model_name='badgeinstance',
                    name='public',
                ),
                migrations.RemoveField(
                    model_name='badgeinstancecollection',
                    name='public',
                ),
            ],
        ),
    ]
