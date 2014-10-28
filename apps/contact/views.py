from django import http
from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView, CreateView
from contact.models import *
import json
from mainsite.views import ActiveTabMixin


class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return http.HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        return json.dumps({'is_valid': context['form'].is_valid(), 'errors': context['form'].errors})


class Contact(ActiveTabMixin, JSONResponseMixin, CreateView):
    template_name = 'contact/contact.html'
    model = Submission
    active_tab = 'contact'

    def form_invalid(self, form):
        return super(Contact, self).form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        try:
            output_message = "Name: %s\n\nEmail: %s\n\nPhone: %s\n\nComments: %s\n\n" % (self.object.name, self.object.email, self.object.phone, self.object.comments)
            from django.core.mail import send_mail
            send_mail(contact.subject, output_message, 'contactform@concentricsky.com', ['hello@concentricsky.com'], fail_silently=True)
        except:
            # ignoring email errors
            pass
        if self.request.is_ajax():
            return JSONResponseMixin.render_to_response(self, {'form': form})
        else:
            return http.HttpResponseRedirect(reverse('contact_thanks'))

    def render_to_response(self, context):
        if self.request.is_ajax():
            return JSONResponseMixin.render_to_response(self, context)
        else:
            return CreateView.render_to_response(self, context)


class ContactThanks(ActiveTabMixin, TemplateView):
    template_name = 'contact/thanks.html'
    active_tab = 'contact'