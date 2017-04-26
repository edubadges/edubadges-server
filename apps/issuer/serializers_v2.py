import os
import uuid

from rest_framework import serializers

from badgeuser.models import BadgeUser
from badgeuser.serializers import BadgeUserIdentifierField
from badgeuser.serializers_v2 import BadgeUserProfileSerializerV2
from mainsite.base import DetailSerializerV2, EntityRelatedFieldV2
from mainsite.drf_fields import Base64FileField
from mainsite.serializers import StripTagsCharField
from mainsite.utils import verify_svg

from .models import Issuer, IssuerStaff


class IssuerStaffSerializerV2(DetailSerializerV2):
    user = EntityRelatedFieldV2(rel_source='id', read_only=True)
    role = serializers.CharField()


class IssuerSerializerV2(DetailSerializerV2):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(queryset=BadgeUser.objects.all(), source='created_by', rel_source='id')
    name = StripTagsCharField(max_length=1024)
    slug = StripTagsCharField(max_length=255, allow_blank=True, required=False)
    image = Base64FileField(allow_empty_file=False, use_url=True, required=False, allow_null=True)
    email = serializers.EmailField(max_length=255, required=True)
    description = StripTagsCharField(max_length=1024, required=True)
    url = serializers.URLField(max_length=1024, required=True)
    staff = IssuerStaffSerializerV2(source='issuerstaff_set', read_only=True, many=True)

    def validate(self, data):
        # TODO: ensure email is a confirmed email in owner/creator's account
        # ^^^ that validation requires the request.user, which might be in self.context
        return data

    def validate_image(self, image):
        # TODO: Make sure it's a PNG (square if possible), and remove any baked-in badge assertion that exists.
        # Doing: add a random string to filename

        if image is None:
            return image

        img_name, img_ext = os.path.splitext(image.name)

        try:
            from PIL import Image
            img = Image.open(image)
            img.verify()
        except Exception as e:
            if not verify_svg(image):
                raise serializers.ValidationError('Invalid image.')
        else:
            if img.format != "PNG":
                raise serializers.ValidationError('Invalid PNG')

        image.name = 'issuer_logo_' + str(uuid.uuid4()) + img_ext
        return image

    def create(self, validated_data, **kwargs):
        new_issuer = Issuer(**validated_data)

        # TODO: Is this needed anymore? [Wiggins Feb 2017]
        # Use AutoSlugField's pre_save to provide slug if empty, else auto-unique
        new_issuer.slug = Issuer._meta.get_field('slug').pre_save(new_issuer, add=True)

        new_issuer.save()

        staff = IssuerStaff(issuer=new_issuer, user=new_issuer.created_by, role=IssuerStaff.ROLE_OWNER)
        staff.save()
        return new_issuer

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')

        if 'image' in validated_data:
            instance.image = validated_data.get('image')

        instance.email = validated_data.get('email')
        instance.description = validated_data.get('description')
        instance.url = validated_data.get('url')

        instance.save()
        return instance