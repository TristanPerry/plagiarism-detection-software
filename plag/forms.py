from django.contrib.auth.models import User
from django.templatetags.static import static
from django import forms

from plag.models import UserPreference


def text_to_tooltip(text):
    return '<img src="{0}" title="{1}" rel="tooltip" class="tooltip_img" />'.format(static('plag/icon/Help.png'),
                                                                                    text)


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', ]
        help_texts = {
            'first_name': text_to_tooltip(
                'Optional. If this is a company account, you can enter the company name here.'),
            'email': text_to_tooltip('Mandatory to manage your account. We will never spam you.'),
        }

    def clean(self):
        cleaned = super(UserInfoForm, self).clean()
        email = cleaned.get("email")

        if not email:
            raise forms.ValidationError('Email address is mandatory', code='invalid')


class UserCreationForm(forms.ModelForm):
    username = forms.CharField(label="Username", max_length=30,
                               widget=forms.TextInput(attrs={'class': 'order-username'}),
                               help_text=text_to_tooltip("Mandatory. 30 characters or fewer."))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password (confirm)", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', ]
        help_texts = {
            'first_name': text_to_tooltip(
                'Optional. If this is a company account, you can enter the company name here.'),
            'email': text_to_tooltip('Mandatory to manage your account. We will never spam you.'),
        }

    def clean(self):
        cleaned = super(UserCreationForm, self).clean()

    def clean_username(self):
        username = self.cleaned_data["username"]
        user = User.objects.filter(username=username)
        if user:
            raise forms.ValidationError('The chosen username already exists', code='invalid')
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('The entered passwords do not match', code='invalid')
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(label='Current Password', widget=forms.PasswordInput())
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput())
    new_password_confirm = forms.CharField(label='New Password (confirm)', widget=forms.PasswordInput())

    def __init__(self, user, data=None):
        self.user = user
        super(PasswordChangeForm, self).__init__(data=data)

    def clean(self):
        cleaned = super(PasswordChangeForm, self).clean()
        clean_current = cleaned.get("current_password")
        clean_new = cleaned.get("new_password")
        clean_confirm = cleaned.get("new_password_confirm")

        if not clean_current or not clean_new or not clean_confirm:
            raise forms.ValidationError('All password fields are mandatory to change your password', code='invalid')
        elif clean_new != clean_confirm:
            raise forms.ValidationError('Your new passwords do not match', code='invalid')
        elif not self.user.check_password(clean_current):
            raise forms.ValidationError('The entered current password is not correct', code='invalid')


class UserPreferencesForm(forms.ModelForm):
    results_per_page = forms.ChoiceField(choices=UserPreference.PER_PAGE_RESULTS, help_text=text_to_tooltip(
        'On sections with many results - such as Protected Resources and Scan History - choose how may results you see per page'))
    false_positive_prot = forms.BooleanField(label='False positive protection', help_text=text_to_tooltip(
        'Filter out results which we believe are not plagiarism, leading to you seeing better quality results'),
                                             required=False)
    email_frequency = forms.ChoiceField(choices=UserPreference.EMAIL_FREQ, help_text=text_to_tooltip(
        'We can email you to keep you updated on any plagiarism we find. Or you can disable this by choosing Never.'))

    class Meta:
        model = UserPreference
        fields = ['results_per_page', 'email_frequency', 'false_positive_prot']
