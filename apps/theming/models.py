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
    showPoweredByBadgr = models.CharField('showPoweredByBadgr',max_length=512)
    showApiDocsLink = models.CharField('showApiDocsLink',max_length=512)
    termsOfServiceLink = models.CharField('termsOfServiceLink',max_length=512)
    privacyPolicyLink = models.CharField('privacyPolicyLink',max_length=512)
    logo_small = models.FileField('logoImg.small',upload_to='themes')
    logo_desktop = models.FileField('logoImg.desktop',upload_to='themes')
    subdomain = models.CharField('Sub domain', max_length=56, unique=True)
    institution = models.ForeignKey(Institution, related_name='theme')
    changed_on = models.DateTimeField(auto_now=True)

