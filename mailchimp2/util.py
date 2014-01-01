import mailchimp
from django.conf import settings

def get_mailchimp_api():
    """
    Uses the MAILCHIMP_API_KEY setting to create a connection to the
    mail chimp API.
    """

    return mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)
