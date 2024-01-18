from django_rq import job
from django.core.mail import EmailMessage

from gtfseditor import settings
from user.models import User


@job('default', timeout=300)
def send_confirmation_email(username, verification_url):
    user = User.objects.get(username=username)
    subject, to = 'Verificación de Email', user.email
    text_content = f'Haz clic para verificar tu correo electrónico: {verification_url}'
    msg = EmailMessage(subject, text_content, settings.EMAIL_HOST_USER, [to])
    msg.send()

