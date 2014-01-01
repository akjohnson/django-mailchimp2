from setuptools import setup, find_packages

version = __import__('mailchimp2').__version__

setup(
    name = 'django-mailchimp2',
    version = version,
    description = 'Mail Chimp integration with Django, using Mailchimp API 2.0',
    author = 'Audra Johnson et al.',
    url = 'http://github.com/akjohnson/django-mailchimp2',
    packages = find_packages(),
    zip_safe=False,
    package_data={
        'mailchimp': [
            'templates/mailchimp2/*.html',
            'locale/*/LC_MESSAGES/*',
        ],
    },
)
