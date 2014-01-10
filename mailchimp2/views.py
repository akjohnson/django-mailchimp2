from __future__ import unicode_literals

import logging

log = logging.getLogger(__name__)

from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.shortcuts import render_to_response, redirect
from django.contrib import messages

from django.views.generic.base import ContextMixin
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from ipware.ip import get_real_ip
import mailchimp

from .util import get_mailchimp_api
from .forms import SubscribeForm

class IndexView(TemplateView):
    """Shows a list of the mailing lists."""
    
    template_name = "mailchimp2/index.html"
    
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        
        # will throw a 500 error on failure
        mail_api = get_mailchimp_api()
        lists = mail_api.lists.list()
        
        context["lists"] = lists['data']
        
        return context

class ListBasedMixin(ContextMixin):
    """This encapsulates common behavior for views based on a particular list."""
    
    def get_list_id(self):
        
        self.list_id = self.kwargs['list_id']
    
    def setup_mail(self):
        
        self.list_id = self.get_list_id()
        
        # keep this around in case we want to do queries on it later
        self.mail_api = get_mailchimp_api()
        lists = self.mail_api.lists.list({'list_id':self.list_id})
        self.list_info = lists['data'][0]
        
    def merge_vars(self):
        """Call after setup_mail-- returns a list of merge variables for
        signing up."""
        
        if not 'mail_api' in self.__dict__:
            self.setup_mail()
        
        return self.mail_api.lists.merge_vars(
            {'list_id':self.list_id})['data'][0]['merge_vars']
            
    def get_context_data(self, **kwargs):
        context = super(ListBasedMixin, self).get_context_data(**kwargs)
        
        # set up the list information if something has not already called it
        if 'list_info' not in self.__dict__:
            self.setup_mail()
        
        context["list"] = self.list_info
        
        return context

class SubscribeFormView(FormView, ListBasedMixin):
    """Handles subscribing to the list."""
    
    template_name = "mailchimp2/subscribe.html"
    form_class = SubscribeForm

    def get_form_kwargs(self):
        """The SubscribeForm class relies on merge vars from mail chimp to
        assemble itself."""
    
        kwargs = super(SubscribeFormView, self).get_form_kwargs()
        kwargs['merge_vars'] = self.merge_vars()
        kwargs['mail_api'] = self.mail_api
        kwargs['list_id'] = self.list_id
        kwargs['subscriber_IP'] = get_real_ip(self.request)
        return kwargs        
    
    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        logging.debug("FORM INVALID")
        return self.render_to_response(self.get_context_data(form=form))    
    
    def form_valid(self, form):
        logging.debug("FORM VALID")
        
        self.merge_vars = form.get_updated_merge_vars()
        
        return self.render_to_response(self.get_context_data(success=True, merge_vars=self.merge_vars))
