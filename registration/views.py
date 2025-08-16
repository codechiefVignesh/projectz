from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from .forms import SignupForm, LoginForm, CommunityForm
from .models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
# Create your views here.
def render_homepage(request):
    return render(request, "home.html")

@never_cache
@csrf_protect
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


@never_cache
@csrf_protect
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
        form = LoginForm()
    else:
        form = LoginForm()

    response = render(request, 'login.html', {'form': form, 'error': error})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
@csrf_protect
def render_communitypage(request):
    list(messages.get_messages(request))
    if request.method == 'POST':
        form = CommunityForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            if user.is_community_user:
                user.is_approved = False  # Needs admin approval
            user.save()
            return HttpResponse("Community Signup successful! <a href='/login/'>Login</a>")
    else:
        form = SignupForm()
    return render(request, 'community.html', {'form': form})