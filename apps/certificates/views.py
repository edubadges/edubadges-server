from django.views.generic import *
from django.views.generic.edit import FormMixin
from certificates.models import *
# from mainsite.views import ActiveTabMixin


class CertificateCreate(FormMixin, CreateView):
    model = Certificate
    # active_tab = 'certificates'
    

class CertificateDetail(ActiveTabMixin, DetailView):
    model = Certificate
    active_tab = 'certificates'



