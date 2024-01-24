from django_rq import job
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

from gtfseditor import settings
from user.models import User


@job('default', timeout=300)
def send_confirmation_email(username, verification_url):
    user = User.objects.get(username=username)
    subject, to = 'Verificación de Email', user.email
    text_content = ''
    html_content = render_to_string('confirmation_email.html',
                                    context={'name': user.name,
                                             'username': user.username,
                                             'form_url': verification_url})
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

