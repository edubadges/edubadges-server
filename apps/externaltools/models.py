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
