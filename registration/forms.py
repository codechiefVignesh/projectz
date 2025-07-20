from django import forms
from .models import User
from django.core.exceptions import ValidationError


class SignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )

    class Meta:
        model = User
        fields = ['firstname', 'lastname', 'email', 'password']
        widgets = {
            'firstname': forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
            'lastname': forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists. Try logging in.")
        return email

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}))


class CommunityForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    is_community_user = forms.BooleanField(required=False, label="Apply as a community contributor?")
    class Meta:
        model = User
        fields = ['firstname', 'lastname', 'email', 'password', 'is_community_user']
        widgets = {
            'firstname': forms.TextInput(attrs={'placeholder': 'Enter your first name'}),
            'lastname': forms.TextInput(attrs={'placeholder': 'Enter your last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("The user is already a part of the Community!. Try logging in.")
        return email
