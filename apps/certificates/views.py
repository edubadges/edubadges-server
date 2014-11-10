from django.views.generic import *
from certificates.models import *
from mainsite.views import ActiveTabMixin
from badgeanalysis.utils import analyze_image_upload
import json

class CertificateCreate( ActiveTabMixin, CreateView):
    model = Certificate
    active_tab = 'certificates'
    

class CertificateDetail(ActiveTabMixin, DetailView):
    model = Certificate
    active_tab = 'certificates'
    # analysis = json.dumps(analyze_image_upload(object.image))




