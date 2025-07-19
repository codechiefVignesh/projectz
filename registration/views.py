from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import SignupForm, LoginForm
from .models import User

# Create your views here.
def render_homepage(request):
    return render(request, "home.html")

def render_signuppage(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return HttpResponse("Signup successful! <a href='/login/'>Login</a>")
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})
def render_loginpage(request):
    error = ''
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=form.cleaned_data['email'])
                if user.check_password(form.cleaned_data['password']):
                    return HttpResponse(f"Welcome, {user.firstname}!")
                else:
                    error = 'Invalid password'
            except User.DoesNotExist:
                error = 'User not found'
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'error': error})