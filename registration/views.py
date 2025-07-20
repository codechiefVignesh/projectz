from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import SignupForm, LoginForm
from .models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
# Create your views here.
def render_homepage(request):
    return render(request, "home.html")

def render_signuppage(request):
    list(messages.get_messages(request))
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
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('problems-page', id=user.id)
            else:
                error = 'Invalid email or password'
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form, 'error': error})