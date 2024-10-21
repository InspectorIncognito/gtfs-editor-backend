from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext as _
from django_rq import job

from gtfseditor import settings
from user.models import User


@job('default', timeout=300)
def send_confirmation_email(username, verification_url, language_code):
    user = User.objects.get(username=username)

    with translation.override(language_code):
        subject, to = _("Email Verification"), user.email
        text_content = ''
        username = user.email.split('@')[0]
        html_content = render_to_string('confirmation_email.html',
                                        context={'username': username,
                                                 'link_url': verification_url})
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@job('default', timeout=300)
def send_pw_recovery_email(username, recovery_url):
    user = User.objects.get(username=username)
    subject, to = _("Password Recovery"), user.email
    text_content = ''
    username = user.email.split('@')[0]
    html_content = render_to_string('recover_password.html',
                                    context={'username': username,
                                             'link_url': recovery_url})
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
