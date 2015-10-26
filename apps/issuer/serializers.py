from itertools import chain
import os
import uuid
from django.conf import settings
from django.core.urlresolvers import reverse

from django.db.models import Q

from rest_framework import serializers
from badgeuser.models import BadgeUser

from mainsite.serializers import WritableJSONField
from mainsite.utils import installed_apps_list
from badgeuser.serializers import UserProfileField
from composition.format import V1InstanceSerializer

from .models import Issuer, BadgeClass, BadgeInstance
import utils


class AbstractComponentSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    # created_by = serializers.HyperlinkedRelatedField(view_name='user_detail', lookup_field='username', read_only=True)

    def to_representation(self, instance):
        representation = super(AbstractComponentSerializer, self).to_representation(instance)
        representation['created_by'] = (settings.HTTP_ORIGIN+reverse('user_detail', kwargs={'user_id': instance.created_by_id})) if instance.created_by_id is not None else None
        return representation


class IssuerSerializer(AbstractComponentSerializer):
    json = WritableJSONField(max_length=16384, read_only=True, required=False)
    name = serializers.CharField(max_length=1024)
    slug = serializers.CharField(max_length=255, allow_blank=True, required=False)
    image = serializers.ImageField(allow_empty_file=False, use_url=True, required=False)
    email = serializers.EmailField(max_length=255, required=True, write_only=True)
    description = serializers.CharField(max_length=1024, required=True, write_only=True)
    url = serializers.URLField(max_length=1024, required=True, write_only=True)
    # HyperlinkedRelatedField refuses to not hit the database, so this is done manually in to_representation
    # owner = serializers.HyperlinkedRelatedField(view_name='user_detail', lookup_field='username', read_only=True)
    # editors = serializers.HyperlinkedRelatedField(many=True, view_name='user_detail', lookup_field='username', read_only=True, source='cached_editors')
    # staff = serializers.HyperlinkedRelatedField(many=True, view_name='user_detail', lookup_field='username', read_only=True, source='cached_staff')

    def validate(self, data):
        # TODO: ensure email is a confirmed email in owner/creator's account
        # ^^^ that validation requires the request.user, which might be in self.context
        return data

    def validate_image(self, image):
        # TODO: Make sure it's a PNG (square if possible), and remove any baked-in badge assertion that exists.
        # Doing: add a random string to filename
        img_name, img_ext = os.path.splitext(image.name)

        image.name = 'issuer_logo_' + str(uuid.uuid4()) + img_ext
        return image

    def create(self, validated_data, **kwargs):
        validated_data['json'] = {
            '@context': utils.CURRENT_OBI_CONTEXT_IRI,
            'type': 'Issuer',
            'name': validated_data.get('name'),
            'url': validated_data.pop('url'),
            'email': validated_data.pop('email'),
            'description': validated_data.pop('description')
        }

        new_issuer = Issuer(**validated_data)

        # Use AutoSlugField's pre_save to provide slug if empty, else auto-unique
        new_issuer.slug = \
            Issuer._meta.get_field('slug').pre_save(new_issuer, add=True)

        full_url = new_issuer.get_full_url()
        new_issuer.json['id'] = full_url
        if validated_data.get('image') is not None:
            new_issuer.json['image'] = "%s/image" % (full_url,)

        new_issuer.save()
        return new_issuer

    def to_representation(self, obj):
        representation = super(IssuerSerializer, self).to_representation(obj)
        representation['description'] = obj.json.get('description', '')
        representation['owner'] = (settings.HTTP_ORIGIN+reverse('user_detail', kwargs={'user_id': obj.created_by_id})) if obj.created_by_id is not None else None
        representation['editors'] = [settings.HTTP_ORIGIN+reverse('user_detail', kwargs={'user_id': u.pk}) for u in obj.cached_editors()]
        representation['staff'] = [settings.HTTP_ORIGIN+reverse('user_detail', kwargs={'user_id': u.pk}) for u in obj.cached_staff()]
        if self.context.get('embed_badgeclasses', False):
            representation['badgeclasses'] = BadgeClassSerializer(obj.badgeclasses.all(), many=True, context=self.context).data

        return representation


class IssuerRoleActionSerializer(serializers.Serializer):
    """ A serializer used for validating user role change POSTS """
    action = serializers.ChoiceField(('add', 'modify', 'remove'), allow_blank=True)
    username = serializers.CharField(allow_blank=False)
    editor = serializers.BooleanField(default=False)


class IssuerStaffSerializer(serializers.Serializer):
    """ A read_only serializer for staff roles """
    user = UserProfileField()
    editor = serializers.BooleanField()


class BadgeClassSerializer(AbstractComponentSerializer):
    issuer = serializers.HyperlinkedRelatedField(view_name='issuer_json', read_only=True, lookup_field='slug')
    json = WritableJSONField(max_length=16384, read_only=True, required=False)
    name = serializers.CharField(max_length=255)
    image = serializers.ImageField(allow_empty_file=False, use_url=True)
    slug = serializers.CharField(max_length=255, allow_blank=True, required=False)
    criteria = serializers.CharField(allow_blank=True, required=False, write_only=True)

    def validate_image(self, image):
        # TODO: Make sure it's a PNG (square if possible), and remove any baked-in badge assertion that exists.
        # Doing: add a random string to filename
        img_name, img_ext = os.path.splitext(image.name)

        image.name = 'issuer_badgeclass_' + str(uuid.uuid4()) + img_ext
        return image

    def validate(self, data):

        if utils.is_probable_url(data.get('criteria')):
            data['criteria_url'] = data.pop('criteria')
        elif not isinstance(data.get('criteria'), (str, unicode)):
            raise serializers.ValidationError(
                "Provided criteria text could not be properly processed as URL or plain text."
            )
        else:
            data['criteria_text'] = data.pop('criteria')

        return data

    def create(self, validated_data, **kwargs):

        # TODO: except KeyError on pops for invalid keys? or just ensure they're there with validate()
        # "gets" data that must be in both model and model.json,
        # "pops" data that shouldn't be sent to model init
        validated_data['json'] = {
            '@context': utils.CURRENT_OBI_CONTEXT_IRI,
            'type': 'BadgeClass',
            'name': validated_data.get('name'),
            'description': validated_data.pop('description'),
            'issuer': validated_data.get('issuer').get_full_url()
        }

        try:
            criteria_url = validated_data.pop('criteria_url')
            validated_data['json']['criteria'] = criteria_url
        except KeyError:
            pass

        new_badgeclass = BadgeClass(**validated_data)

        # Use AutoSlugField's pre_save to provide slug if empty, else auto-unique
        new_badgeclass.slug = \
            BadgeClass._meta.get_field('slug').pre_save(new_badgeclass, add=True)

        full_url = new_badgeclass.get_full_url()
        new_badgeclass.json['id'] = full_url
        new_badgeclass.json['image'] = "%s/image" % (full_url,)
        if new_badgeclass.criteria_text:
            validated_data['json']['criteria'] = "%s/criteria" % (full_url,)

        new_badgeclass.save()
        return new_badgeclass


class BadgeInstanceSerializer(AbstractComponentSerializer):
    json = WritableJSONField(max_length=16384, read_only=True, required=False)
    # HyperlinkedRelatedField refuses to not hit the database, so this is done manually in to_representation
    #issuer = serializers.HyperlinkedRelatedField(view_name='issuer_json', read_only=True,  lookup_field='slug')
    #badgeclass = serializers.HyperlinkedRelatedField(view_name='badgeclass_json', read_only=True, lookup_field='slug')
    slug = serializers.CharField(max_length=255, read_only=True)
    image = serializers.ImageField(read_only=True)  # use_url=True, might be necessary
    recipient_identifier = serializers.EmailField(max_length=1024)
    evidence = serializers.URLField(write_only=True, required=False, allow_blank=True, max_length=1024)

    revoked = serializers.BooleanField(read_only=True)
    revocation_reason = serializers.CharField(read_only=True)

    create_notification = serializers.BooleanField(write_only=True, required=False)

    def to_representation(self, instance):
        if self.context.get('extended_json'):
            self.fields['json'] = V1InstanceSerializer(source='extended_json')

        representation = super(BadgeInstanceSerializer, self).to_representation(instance)
        if self.context.get('include_issuer', False):
            representation['issuer'] = IssuerSerializer(instance.cached_badgeclass.cached_issuer).data
        else:
            representation['issuer'] = settings.HTTP_ORIGIN+reverse('issuer_json', kwargs={'slug': instance.cached_issuer.slug})
        if self.context.get('include_badge_class', False):
            representation['badge_class'] = BadgeClassSerializer(instance.cached_badgeclass, context=self.context).data
        else:
            representation['badge_class'] = settings.HTTP_ORIGIN+reverse('badgeclass_json', kwargs={'slug': instance.cached_badgeclass.slug})


        # TODO: only bother doing this if badgebook is in INSTALLED_APPS
        from badgebook.models import BadgeObjectiveAward
        from badgebook.serializers import BadgeObjectiveAwardSerializer
        try:
            award = BadgeObjectiveAward.cached.get(badge_instance_id=instance.id)
        except BadgeObjectiveAward.DoesNotExist:
            representation['award'] = None
        else:
            representation['award'] = BadgeObjectiveAwardSerializer(award).data

        return representation

    def create(self, validated_data, **kwargs):
        # Assemble Badge Object
        validated_data['json'] = {
            # 'id': TO BE ADDED IN SAVE
            '@context': utils.CURRENT_OBI_CONTEXT_IRI,
            'type': 'Assertion',
            'recipient': {
                'type': 'email',
                'hashed': True
                # 'email': TO BE ADDED IN SAVE
            },
            'badge': validated_data.get('badgeclass').get_full_url(),
            'verify': {
                'type': 'hosted'
                # 'url': TO BE ADDED IN SAVE
            }
        }
        try:
            create_notification = validated_data.pop('create_notification')
        except KeyError:
            create_notification = False

        try:
            evidence = validated_data.pop('evidence')
        except KeyError:
            pass
        else:
            validated_data['json']['evidence'] = evidence

        new_assertion = BadgeInstance(**validated_data)
        new_assertion.slug = new_assertion.get_new_slug()

        # Augment json with id
        full_url = new_assertion.get_full_url()  # this sets the slug
        new_assertion.json['id'] = full_url
        new_assertion.json['uid'] = new_assertion.slug
        new_assertion.json['verify']['url'] = full_url
        new_assertion.json['image'] = full_url + '/image'

        # Use AutoSlugField's pre_save to provide slug if empty, else auto-unique
        new_assertion.slug = \
            BadgeInstance._meta.get_field('slug').pre_save(new_assertion, add=True)

        new_assertion.save()

        if create_notification is True:
            new_assertion.notify_earner()

        return new_assertion


class IssuerPortalSerializer(serializers.Serializer):
    """
    A serializer used to pass initial data to a view template so that the React.js
    front end can render.
    It should detect which of the core Badgr applications are installed and return
    appropriate contextual information.
    """

    def to_representation(self, user):
        view_data = {}

        user_issuers = Issuer.objects.filter(
            Q(owner__id=user.id) |
            Q(staff__id=user.id)
        ).distinct().select_related('badgeclasses')
        user_issuer_badgeclasses = chain.from_iterable(i.badgeclasses.all() for i in user_issuers)

        issuer_data = IssuerSerializer(
            user_issuers,
            many=True,
            context=self.context
        )
        badgeclass_data = BadgeClassSerializer(
            user_issuer_badgeclasses,
            many=True,
            context=self.context
        )

        view_data['issuer_issuers'] = issuer_data.data
        view_data['issuer_badgeclasses'] = badgeclass_data.data
        view_data['installed_apps'] = installed_apps_list()

        return view_data
