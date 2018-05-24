# -*- coding: utf-8 -*-
from allauth.socialaccount.forms import SignupForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from newsletter.forms import NewsletterForm


# has to be this order, because otherwise the form is lacking fields
class RegistrationForm(UserCreationForm, NewsletterForm):
    data_processing_part2 = u'''\
Dane są przetwarzane w zakresie niezbędnym do prowadzenia serwisu, a także w celach prowadzenia statystyk, \
ewaluacji i sprawozdawczości. W przypadku wyrażenia dodatkowej zgody adres e-mail zostanie wykorzystany \
także w celu przesyłania newslettera Wolnych Lektur.'''

    class Meta:
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        super(RegistrationForm, self).save(commit=commit)
        NewsletterForm.save(self)


class SocialSignupForm(SignupForm, NewsletterForm):
    data_processing_part2 = u'''\
Dane są przetwarzane w zakresie niezbędnym do prowadzenia serwisu, a także w celach prowadzenia statystyk, \
ewaluacji i sprawozdawczości. W przypadku wyrażenia dodatkowej zgody adres e-mail zostanie wykorzystany \
także w celu przesyłania newslettera Wolnych Lektur.'''

    def save(self, request):
        super(SocialSignupForm, self).save(request)
        NewsletterForm.save(self)
