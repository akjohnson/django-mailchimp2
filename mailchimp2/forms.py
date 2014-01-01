from __future__ import unicode_literals

import logging
import datetime
import sys

log = logging.getLogger(__name__)

from django import forms

from localflavor.us.forms import USZipCodeField
import mailchimp

class SubscribeForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.mail_api = kwargs.pop('mail_api')
        self.list_id = kwargs.pop('list_id')
        self.subscriber_IP = kwargs.pop('subscriber_IP', None)
                
        # automatically fetch merge vars or fetch them from the API
        self.merge_vars = kwargs.pop('merge_vars', None)
        
        # todo: make sure merge_vars sorted on order
        if not self.merge_vars:
            self.merge_vars = self.mail_api.lists.merge_vars(
                {'list_id':self.list_id})['data'][0]['merge_vars']
        
        super(SubscribeForm, self).__init__(*args, **kwargs)
        
        for merge_var in self.merge_vars:
            logging.debug("Adding merge var to form: %s" % str(merge_var))
            
            if merge_var['field_type'] == 'email':
                self.add_emailfield(merge_var)
            if merge_var['field_type'] == 'text':
                self.add_textfield(merge_var)
            if merge_var['field_type'] == 'zip':
                self.add_zipfield(merge_var)
            if merge_var['field_type'] == 'number':
                logging.debug("Need to add number field")
            if merge_var['field_type'] == 'phone':
                logging.debug("Need to add in phone field.")
            if merge_var['field_type'] == 'address':
                logging.debug("Need to add address field")
            if merge_var['field_type'] in ('date', 'birthday'):
                logging.debug("Need to add date/birthday field")
            if merge_var['field_type'] == 'address':
                logging.debug("Need to add in address field")
            if merge_var['field_type'] == 'website':
                logging.debug("Need to add in URL field")
    
    def is_valid(self):
        """This submits the form to the service. The reason this is done here
        is because the service might send back errors that must be fixed
        in the form when we try to submit."""
        
        is_valid = super(SubscribeForm, self).is_valid()
    
        # Don't proceed further if this form isn't valid already
        if not is_valid:
            logging.debug("Form invalid before submission")
            return False
    
        logging.debug("CHECKING IF FORM IS VALID for list %s" % self.list_id)
        
        updated_merge_vars = self.get_updated_merge_vars()
        
        email = self.cleaned_data['EMAIL']
        
        # TODO: user add_error in django 1.7
        
        try:
            self.mail_api.lists.subscribe(self.list_id, {"email": email},
                merge_vars=updated_merge_vars)
        except mailchimp.ListAlreadySubscribedError:
            self._errors[forms.forms.NON_FIELD_ERRORS] = "This email is already subscribed!"
            is_valid = False
        except mailchimp.ValidationError, e:
            self._errors[forms.forms.NON_FIELD_ERRORS] = e
            is_valid = False
        except:
            self._errors[forms.forms.NON_FIELD_ERRORS] = "Unknown error! %s" % sys.exc_info()[0]
            is_valid = False
        
        if not is_valid:
            logging.debug("Form invalid after submission")
    
        return is_valid

    def get_default_args(self, merge_var):
        """
        Many merge var values are similar across fields; this creates
        some default Field arguments based on the merge variables.
        """
 
        defaults = {                           
            'required': merge_var['req'],
            'help_text': merge_var['helptext'],
            'label': merge_var['name'],
        }
        
        # if this is put in and empty and it's required it will give an
        # error on first load
        if merge_var['default']:
            defaults['initial'] = merge_var['default']
        
        # Use the hidden input widget if we're not showing this variable
        # but it has initial content
        if merge_var['show'] == False and defaults['initial']:
            defaults['widget'] = forms.HiddenInput()
         
        return defaults
    
    def get_updated_merge_vars(self):
        """
        Goes though the form's cleaned data and creates the dict
        for subscribing using the API.        

        Only call this after clean() has been called so cleaned_data
        exists."""
        
        updated_merge_vars = dict()
        
        if self.subscriber_IP:
            updated_merge_vars['subscriber_IP'] = self.subscriber_IP
            
        # add in the time this call is being made
        updated_merge_vars['optin_time'] = datetime.datetime.utcnow().strftime(
            '%Y-%m-%d %H:%M:%S')
        
        for merge_var in self.merge_vars:
            tag = merge_var['tag']
            # only include tags that we have as fields
            if tag in self.cleaned_data:
                updated_merge_vars[tag] = self.cleaned_data[tag]
    
        return updated_merge_vars
 
    def add_emailfield(self, merge_var):
        """Adds in an email field based on a merge var."""

        self.fields[merge_var['tag']] = forms.EmailField(
            **self.get_default_args(merge_var))
    
    def add_textfield(self, merge_var):
        """Adds in a text field based on a merge var."""
        
        self.fields[merge_var['tag']] = forms.CharField(
            **self.get_default_args(merge_var))
        
    def add_zipfield(self, merge_var):
        """Adds in a US ZIP field based on a merge var. Relies on the localflavors app."""
        
        default_args = self.get_default_args(merge_var)
        
        if not default_args['help_text']:
            default_args['help_text'] = "Enter in your US zip code."
            
        self.fields[merge_var['tag']] = USZipCodeField(**default_args)