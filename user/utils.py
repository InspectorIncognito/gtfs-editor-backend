import re
from django.contrib.auth.password_validation import get_default_password_validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_user_password(password):
    """
    Validate whether the password meets all validator requirements.

    If the password is valid, return ``None``.
    If the password is invalid, raise ValidationError with all error messages.
    """
    errors = []
    password_validators = get_default_password_validators()
    for validator in password_validators:
        try:
            validator.validate(password)
        except ValidationError as error:
            errors.append(error)
    if not any(char.isupper() for char in password):
        errors.append(_("la contraseña debe contener al menos una mayúscula."))
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append(_('La contraseña debe contener al menos 1 caracter especial (!@#$%^&*(),.?":{}|<>).'))
    if errors:
        raise ValidationError(errors)
