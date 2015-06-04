from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

import cachemodel
from jsonfield import JSONField

from .utils import find_recipient_user, baked_image_from_abi


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class AbstractStoredComponent(cachemodel.CacheModel):
    json = JSONField()
    errors = JSONField()
    url = models.URLField(max_length=1024, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk and not self.url:
            self.url = self.get_url()

        super(AbstractStoredComponent, self).save(*args, **kwargs)

    def get_url(self):
        return self.json.get('id')


class StoredIssuer(AbstractStoredComponent):
    @classmethod
    def from_analyzed_instance(cls, abi, **kwargs):
        if not abi.is_valid():
            raise ValidationError(
                "Cannot save badgeclass from an invalid badge instance."
            )

        try:
            existing_issuer = cls.objects.get(url=abi.issuer_url)
        except cls.DoesNotExist:
            pass
        except AttributeError:
            return None  # for 0.5 badges, where no Issuer exists.
        else:
            return existing_issuer

        if abi.issuer.version is None:
            issuer_errors = [(
                'error.version_detection',
                'Could not determine Open Badges version of Issuer',
                abi.issuer.version_errors
            )]
        else:
            issuer_errors = []

        # TODO: replace with native method on AnalyzedBadgeInstance
        issuer_json = abi.data.get('badge', {}).get('issuer').copy()
        issuer_json['@context'] = 'https://w3id.org/openbadges/v1'

        new_issuer = cls(
            json=issuer_json,
            errors=issuer_errors,
            url=abi.issuer_url
        )
        new_issuer.save()

        return new_issuer


class StoredBadgeClass(AbstractStoredComponent):
    issuer = models.ForeignKey(StoredIssuer, null=False)

    @classmethod
    def from_analyzed_instance(cls, abi, **kwargs):
        if not abi.is_valid():
            raise ValidationError(
                "Cannot save badgeclass from an invalid badge instance."
            )

        try:
            existing_badgeclass = cls.objects.get(url=abi.badge_url)
        except cls.DoesNotExist:
            pass
        except AttributeError:
            return None  # for 0.5 badges, where no BadgeClass exists.
        else:
            return existing_badgeclass

        if abi.badge.version is None:
            badgeclass_errors = [(
                'error.version_detection',
                'Could not determine Open Badges version of BadgeClass',
                abi.badge.version_errors
            )]
        else:
            badgeclass_errors = []

        # TODO: replace with native method on AnalyzedBadgeInstance
        badgeclass_json = abi.data.get('badge').copy()
        badgeclass_json['@context'] = 'https://w3id.org/openbadges/v1'

        new_badgeclass = cls(
            json=badgeclass_json,
            errors=badgeclass_errors,
            url=abi.badge_url
        )
        new_badgeclass.issuer = StoredIssuer.from_analyzed_instance(abi, **kwargs)
        new_badgeclass.save()

        return new_badgeclass


class StoredBadgeInstance(AbstractStoredComponent):
    recipient_user = models.ForeignKey(AUTH_USER_MODEL, null=True)
    recipient_id = models.CharField(max_length=1024, blank=False)
    badgeclass = models.ForeignKey(StoredBadgeClass, null=True)
    issuer = models.ForeignKey(StoredIssuer, null=True)
    image = models.ImageField(upload_to='uploads/badges', null=True)

    @classmethod
    def from_analyzed_instance(cls, abi, **kwargs):
        if not abi.is_valid():
            raise ValidationError("Cannot save an invalid badge instance.")

        try:
            existing_instance = cls.objects.get(url=abi.instance_url)
        except cls.DoesNotExist:
            pass
        else:
            if existing_instance.recipient_user is None and \
                    kwargs.get('recipient_user') is not None:
                existing_instance.recipient_user = kwargs.get('recipient_user')
                existing_instance.save()

            return existing_instance

        recipient_user = kwargs.get(
            'recipient_user', find_recipient_user(abi.recipient_id)
        )

        new_instance = cls(
            recipient_user=recipient_user,
            recipient_id=abi.recipient_id,
            json=abi.data,
            errors=abi.all_errors()
        )
        new_instance.badgeclass = StoredBadgeClass.from_analyzed_instance(
            abi, **kwargs
        )
        if kwargs.get('image') is not None:
            new_instance.image = kwargs.get('image')
        else:
            new_instance.image = baked_image_from_abi(abi)

        new_instance.json['image'] = new_instance.image_url()

        # StoredBadgeClass is responsible for detecting issuer
        if new_instance.badgeclass is not None:
            new_instance.issuer = new_instance.badgeclass.issuer

        new_instance.save()

        eurl = new_instance.image_url()
        if eurl != new_instance.json['image']:
            new_instance.json['image'] = eurl
            new_instance.save(update_fields=['json'])

        return new_instance

    def image_url(self):
        if getattr(settings, 'MEDIA_URL').startswith('http'):
            return getattr(settings, 'MEDIA_URL') \
                + self.image.name
        else:
            return getattr(settings, 'HTTP_ORIGIN') \
                + getattr(settings, 'MEDIA_URL') \
                + self.image.name

    @property
    def owner(self):
        return self.recipient_user

# class StoredEndorsement(AbstractStoredComponent):
#     recipient_id = models.CharField(max_length=1024, blank=False)
#     # TODO: needs generic foreign key to one of (SBI, SBC, SI)