import os

from django.conf import settings
from django.db import models
from django.utils.functional import lazy
from institution.models import Institution
from mainsite.models import BadgrApp

"""
 Theming supplies themes for different sub domains
 A them contains a privacy policy , term and condition , welcome message 
 Css is skipped for now but could in the future be added
"""

"""
get templates in directory
"""


def get_current_templates():
    templates = []
    for template in os.listdir(os.path.join(settings.TOP_DIR, 'apps', 'mainsite', 'templates', 'terms_of_service')):
        templates.append((os.path.join('terms_of_service', template), os.path.join('terms_of_service', template)))

    return tuple(templates)


class Theme(models.Model):
    """
    Contains the theming data per subdomain
    """

    welcome_message = models.CharField('welcomeMessage', max_length=512)
    service_name = models.CharField('serviceName', max_length=512)
    show_powered_by_badgr = models.BooleanField('showPoweredByBadgr', default=False)
    show_api_docs_link = models.BooleanField('showApiDocsLink', default=False)
    terms_of_service_link = models.CharField('termsOfServiceLink', max_length=512)
    privacy_policy_link = models.CharField('privacyPolicyLink', max_length=512)
    logo_small = models.FileField('logoImg.small', upload_to='themes')
    logo_desktop = models.FileField('logoImg.desktop', upload_to='themes')
    badgr_app = models.OneToOneField(BadgrApp, on_delete=models.SET_NULL, null=True, related_name='theme')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='theme')
    changed_on = models.DateTimeField(auto_now=True)
    terms_and_conditions_template = models.CharField('Terms and conditions template',
                                                     null=True,
                                                     blank=True,
                                                     max_length=512
                                                     )
    terms_and_conditions_template_en = models.CharField('Terms and conditions template english',
                                                        null=True,
                                                        blank=True,
                                                        max_length=512
                                                        )

    def __str__(self):
        return self.service_name

    def __init__(self, *args, **kwargs):
        super(Theme, self).__init__(*args, **kwargs)
        self._meta.get_field('terms_and_conditions_template')._choices = lazy(get_current_templates, list)()

    def __unicode__(self):
        return self.service_name
