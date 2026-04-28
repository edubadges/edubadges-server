"""
Migration 0118: Safely re-add public field to BadgeInstance and BadgeInstanceCollection.

CONTEXT:
--------
This migration ensures that the 'public' field exists in the database for both
BadgeInstance and BadgeInstanceCollection models, regardless of whether it was
previously removed by an earlier migration (0118_remove_badgeinstance_public_and_more
that was later renamed to 0200_remove_badgeinstance_public_and_more).

Some environments had already run the original 0118 migration that removed the 'public'
field. When subsequent migrations (0118_badgeinstance_recipient_name and 0119_populate_recipient_name)
run, they use apps.get_model() which returns a model state that still expects the 'public'
field to exist, causing database errors if the column was already removed.

This migration conditionally re-adds the 'public' field to ensure consistency between
Django's model state and the actual database schema on all environments.

APPROACH:
---------
Similar to migration 0200, we use SeparateDatabaseAndState to handle state vs. schema
separately:
1. Database operations: Safely add the field only if it doesn't exist (ignoring errors)
2. State operations: Always add the field to Django's model state

This makes the migration idempotent and safe to run on all environments.

ALTERNATIVES:
---------
We considered the following

Manually re-adding the field to production databases on ewi environments

Dismissed, because in context of EWI, which runs on k8s, this is a non-trivial task.
It is deliberately and intentionally hard to manually poke around in production databases.

* Cleaning the  database in production
While technically easy, it will delete work that has been done to prepare these environments
for EWI pilot.

* Updating 0119_populate_recipient_name to use `from ... import BadgeInstance` instead of `apps.get_model()`
That, however, has a very real and likely chance to break in future again.

* Add some flags to apps.get_model() to have it load a model that does not have the public attribute.
It seems get_model() does not have this feature, and if it does, that's not documented so probably not supported.
"""

from collections.abc import Sequence
from contextlib import suppress
from typing import Any, Callable

from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.operations.base import Operation


def safe_add_field(app_label: str, model_name: str, field_name: str, field: models.Field) -> Callable[[Apps, BaseDatabaseSchemaEditor], None]:
    """Conditionally add a field to the database if it doesn't exist.

    This handles the case where the field may have already been removed
    by a previous migration (0118_remove_badgeinstance_public_and_more / 0200 in some envs).

    We use exception handling because:
    - The column may already exist in the database (most environments)
    - schema_editor.add_field() will raise an exception if the column already exists
    - We catch that exception and silently ignore it, making this a safe no-op
    """

    def add_if_not_exists(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
        model = apps.get_model(app_label, model_name)

        # Try to add the field, catch any database errors (column already exists, etc.)
        with suppress(Exception):
            schema_editor.add_field(model, field)  # pyright: ignore[reportUnknownMemberType, reportAny]

    return add_if_not_exists


class Migration(migrations.Migration):
    dependencies: Sequence[tuple[str, str]] = [
        ('issuer', '0117_rename_badgeinstance_recipient_identifier_badgeclass_revoked_issuer_badg_recipie_6a2cd8_idx_and_more'),
    ]

    operations: Sequence[Operation] = [
        migrations.SeparateDatabaseAndState(
            # Database operations: safe addition that handles already-existing columns
            database_operations=[
                migrations.RunPython(
                    safe_add_field('issuer', 'BadgeInstance', 'public', models.BooleanField(default=False)),
                    reverse_code=lambda apps, schema_editor: None,
                ),
                migrations.RunPython(
                    safe_add_field('issuer', 'BadgeInstanceCollection', 'public', models.BooleanField(default=False)),
                    reverse_code=lambda apps, schema_editor: None,
                ),
            ],
            # State operations: always update Django's model state
            # This is safe even if the field already exists - Django's state
            # tracking will simply see this as a no-op if the field is already present
            state_operations=[
                migrations.AddField(
                    model_name='badgeinstance',
                    name='public',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='badgeinstancecollection',
                    name='public',
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]
