from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext as _
from django_rq import job

from gtfseditor import settings
from user.models import User


@job('default', timeout=300)
def send_confirmation_email(username, verification_url, language_code):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValueError(_("User does not exist."))

    with translation.override(language_code):
        subject = _("Email Verification")
        recipient_email = user.email
        username = user.email.split('@')[0]

        html_content = render_to_string(
            'confirmation_email.html',
            context={
                'username': username,
                'link_url': verification_url
            }
        )
        msg = EmailMultiAlternatives(
            subject,
            '',
            settings.EMAIL_SENDER_USER,
            [recipient_email]
        )
        msg.attach_alternative(html_content, "text/html")
        try:
            msg.send()
        except Exception as e:
            raise RuntimeError('Failed to send email:', e)


@job('default', timeout=300)
def send_pw_recovery_email(username, recovery_url):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise ValueError(_("User does not exist."))
    subject = _("Password Recovery")
    recipient_email = user.email

    username_display = user.email.split('@')[0]
    html_content = render_to_string(
        'recover_password.html',
        context={
            'username': username_display,
            'link_url': recovery_url
        }
    )

    msg = EmailMultiAlternatives(
        subject,
        '',
        settings.EMAIL_SENDER_USER,
        [recipient_email]
    )

    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
    except Exception as e:
        raise RuntimeError('Failed to send email:', e)
