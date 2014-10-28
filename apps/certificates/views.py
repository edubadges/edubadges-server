from django.views.generic import *
from certificates.models import *
from mainsite.views import ActiveTabMixin


class CertificateCreate(ActiveTabMixin, CreateView):
    model = Certificate
    active_tab = 'certificates'
    

class CertificateDetail(ActiveTabMixin, DetailView):
    model = Certificate
    active_tab = 'certificates'



