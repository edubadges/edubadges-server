# encoding: utf-8
from __future__ import unicode_literals

import cachemodel
import lti
from django.db import models

from entity.models import BaseVersionedEntity
from issuer.models import BaseAuditedModel


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

    def get_tool_consumer(self):
        return lti.ToolConsumer(
            consumer_key=self.cached_externaltool.client_id,
            consumer_secret=self.cached_externaltool.client_secret,
            launch_url=self.launch_url,
            params=dict(
                lti_message_type="basic-lti-launch-request",
                lti_version="1.1",
                resource_link_id=self.pk,
            )
        )

    def generate_launch_data(self):
        tool_consumer = self.get_tool_consumer()
        return tool_consumer.generate_launch_data()
