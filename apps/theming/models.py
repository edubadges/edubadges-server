from django.contrib.sites.models import Site
from django.db import models

from institution.models import Institution

"""
 Theming supplies themes for different sub domains
 A them contains a privacy policy , term and condition , welcome message 
 Css is skipped for now but could in the futere be added
"""

class Theme(models.Model):
    """
    Contains the theming data per subdomain
    """
    welcome_message = models.CharField('welcomeMessage',max_length=512)
    service_name = models.CharField('serviceName',max_length=512)
    show_powered_by_badgr = models.BooleanField('showPoweredByBadgr',  default=False)
    show_api_docs_link = models.BooleanField('showApiDocsLink', default=False)
    terms_of_service_link = models.CharField('termsOfServiceLink', max_length=512)
    privacy_policy_link = models.CharField('privacyPolicyLink', max_length=512)
    logo_small = models.FileField('logoImg.small',upload_to='themes')
    logo_desktop = models.FileField('logoImg.desktop',upload_to='themes')
    site = models.OneToOneField(Site,null=True, related_name='theme')
    institution = models.ForeignKey(Institution, related_name='theme')
    changed_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.service_name

    def __unicode__(self):
        return self.service_name