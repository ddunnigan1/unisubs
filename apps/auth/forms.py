# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import EMPTY_VALUES
from captcha.fields import CaptchaField
from django.template import loader
from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from models import CustomUser as User

class UserField(forms.Field):
    default_error_messages = {
        'invalid': _(u'Invalid user'),
    }

    def prepare_value(self, value):
        if isinstance(value, User):
            return value.username
        return value

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        if isinstance(value, User):
            return value
        try:
            return User.objects.get(username=value)
        except User.DoesNotExist:
            raise forms.ValidationError(self.error_messages['invalid'])

class CustomUserCreationForm(UserCreationForm):
    captcha = CaptchaField()
    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True


class ChooseUserForm(forms.Form):
    """
    Used in the login trap mechanism
    """

    username = forms.CharField(max_length=100)

    def clean_username(self):
        data = self.cleaned_data['username']

        try:
            data = User.objects.get(username=data)
        except User.DoesNotExist:
            raise forms.ValidationError("User doesn't exist.")

        return data

class SecureAuthenticationForm(AuthenticationForm):
    captcha = CaptchaField()

class EmailForm(forms.Form):
    email = forms.EmailField(label=_("E-mail"), max_length=100)
    url = forms.URLField(required=False, widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput())
    last_name = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput())
    avatar = forms.URLField(required=False, widget=forms.HiddenInput())

class CustomPasswordResetForm(forms.Form):
    """
    This custom version of the password reset form has two differences with
    the default one:
    * It sends an email to every user matching the address, even to the ones
    where has_usable_password is false so that oauth users can set a
    password and become a regular amara user
    * It adds data to context for the templates so that emails and views
    can describe better what will happen to the account if password is
    reset
    """
    error_messages = {
        'unknown': _("That e-mail address doesn't have an associated "
                     "user account. Are you sure you've registered?"),
        'unusable': _("The user account associated with this e-mail "
                      "address cannot reset the password."),
    }
    email = forms.EmailField(label=_("E-mail"), max_length=75)

    def clean_email(self):
        """
        Validates that an active user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        self.users_cache = User.objects.filter(email__iexact=email,
                                               is_active=True)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        return email

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        from django.core.mail import send_mail
        for user in self.users_cache:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
                'amara_user': user.has_valid_password(),
            }
            subject = loader.render_to_string(subject_template_name, c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            email = loader.render_to_string(email_template_name, c)
            send_mail(subject, email, from_email, [user.email])

class SecureCustomPasswordResetForm(CustomPasswordResetForm):
    captcha = CaptchaField()

class DeleteUserForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())

