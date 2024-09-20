from django.urls import path

from user.views import UserConfirmationEmailView, UserRegisterView, UserRecoverPasswordView, UserLoginView, \
    UserLogoutView

urlpatterns = [
    path(r'email-verification/', UserConfirmationEmailView.as_view(), name='user-confirmation-email'),
    path(r'email-register/', UserRegisterView.as_view(), name='user-register'),
    path(r'recover-password/', UserRecoverPasswordView.as_view(), name='recover-password'),
    path(r'login/', UserLoginView.as_view(), name='user-login'),
    path(r'logout/', UserLogoutView.as_view(), name='user-logout')
]
