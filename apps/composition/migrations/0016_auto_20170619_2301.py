# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0015_auto_20170420_0649'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='collection',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='collection',
            name='instances',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='shared_with',
        ),
        migrations.AlterUniqueTogether(
            name='collectionpermission',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='collectionpermission',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='collectionpermission',
            name='user',
        ),
        migrations.RemoveField(
            model_name='collectionshare',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstance',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstance',
            name='issuer_badgeclass',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstance',
            name='recipient_user',
        ),
        migrations.AlterUniqueTogether(
            name='localbadgeinstancecollection',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='localbadgeinstancecollection',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstancecollection',
            name='instance',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstancecollection',
            name='issuer_instance',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstanceshare',
            name='instance',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstanceshare',
            name='issuer_instance',
        ),
        migrations.DeleteModel(
            name='Collection',
        ),
        migrations.DeleteModel(
            name='CollectionPermission',
        ),
        migrations.DeleteModel(
            name='CollectionShare',
        ),
        migrations.DeleteModel(
            name='LocalBadgeInstance',
        ),
        migrations.DeleteModel(
            name='LocalBadgeInstanceCollection',
        ),
        migrations.DeleteModel(
            name='LocalBadgeInstanceShare',
        ),
    ]
