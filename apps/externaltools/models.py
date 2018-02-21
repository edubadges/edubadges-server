# encoding: utf-8
from __future__ import unicode_literals

import cachemodel
import lti
from django.db import models
from lti import LaunchParams

from entity.models import BaseVersionedEntity
from issuer.models import BaseAuditedModel, BadgeInstance
from mainsite.utils import OriginSetting, get_tool_consumer_instance_guid


class ExternalTool(BaseAuditedModel, BaseVersionedEntity):
    name = models.CharField(max_length=254)
    description = models.CharField(max_length=254, blank=True, null=True)
    xml_config = models.TextField()
    config_url = models.URLField(blank=True, null=True)
    client_id = models.CharField(max_length=254, blank=True, null=True)
    client_secret = models.CharField(max_length=254, blank=True, null=True)

    def get_lti_config(self):
        return lti.ToolConfig.create_from_xml(self.xml_config)

    @cachemodel.cached_method(auto_publish=True)
    def cached_launchpoints(self):
        return self.externaltoollaunchpoint_set.all()

    def get_launchpoint(self, launchpoint_name):
        try:
            return next(lp for lp in self.cached_launchpoints() if lp.launchpoint == launchpoint_name)
        except StopIteration:
            raise ExternalToolLaunchpoint.DoesNotExist


class ExternalToolLaunchpoint(cachemodel.CacheModel):
    externaltool = models.ForeignKey('externaltools.ExternalTool')
    launchpoint = models.CharField(max_length=254)
    launch_url = models.URLField()
    label = models.CharField(max_length=254)
    icon_url = models.URLField(blank=True, null=True)

    def publish(self):
        super(ExternalToolLaunchpoint, self).publish()
        self.externaltool.publish()

    def delete(self, *args, **kwargs):
        super(ExternalToolLaunchpoint, self).delete(*args, **kwargs)
        self.externaltool.publish()

    @property
    def cached_externaltool(self):
        return ExternalTool.cached.get(pk=self.externaltool_id)

    def get_tool_consumer(self, extra_params=None):
        params = dict(
            lti_message_type="basic-lti-launch-request",
            lti_version="1.1",
            resource_link_id=self.pk,
        )
        if extra_params:
            params.update(extra_params)

        return lti.ToolConsumer(
            consumer_key=self.cached_externaltool.client_id,
            consumer_secret=self.cached_externaltool.client_secret,
            launch_url=self.launch_url,
            params=params
        )

    def lookup_obj_by_launchpoint(self, launch_data, user, context_id):
        roles = []
        obj = None
        if self.launchpoint in ['issuer_assertion_action', 'earner_assertion_action']:
            obj = BadgeInstance.cached.get_by_slug_or_entity_id(context_id)
            if obj:
                launch_data.update(
                    custom_badgr_assertion_recipient=obj.recipient_identifier,
                    custom_badgr_assertion_id=obj.entity_id,
                    custom_badgr_badgeclass_id=obj.cached_badgeclass.entity_id,
                    custom_badgr_badgeclass_name=obj.cached_badgeclass.name,
                    custom_badgr_issuer_id=obj.cached_issuer.entity_id,
                    custom_badgr_issuer_name=obj.cached_issuer.name,
                )
                if any(s.user.id == user.id for s in obj.cached_issuer.cached_issuerstaff()):
                    roles.append('issuer')

                if obj.recipient_identifier in user.all_recipient_identifiers:
                    roles.append('earner')

        launch_data['roles'] = roles
        return obj

    def generate_launch_data(self, user=None, context_id=None, **additional_launch_data):
        params = dict(
            tool_consumer_instance_guid=get_tool_consumer_instance_guid(),
            custom_badgr_api_url=OriginSetting.HTTP,
            custom_launchpoint=self.launchpoint
        )
        params.update(additional_launch_data)
        if user is not None:
            params.update(dict(
                custom_badgr_user_id=user.entity_id,
                lis_person_name_family=user.last_name,
                lis_person_name_given=user.first_name,
                lis_person_contact_email_primary=user.primary_email
            ))
        if context_id is not None:
            params['custom_context_id'] = context_id
            context_obj = self.lookup_obj_by_launchpoint(params, user, context_id)

        tool_consumer = self.get_tool_consumer(extra_params=params)
        launch_data = tool_consumer.generate_launch_data()
        return launch_data

