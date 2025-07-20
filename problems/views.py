from django.shortcuts import render
from registration.models import User
from .models import Problem
from .models import Submission
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseForbidden
from django.db.models import Count, Avg, Sum, F
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .forms import *
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required


# Create your views here.
@login_required(login_url='login')
@never_cache
def render_homepage(request, id):
    user = get_object_or_404(User, id=id)

    if request.method == 'POST' and request.FILES.get('profile_photo'):
        user.profile_photo = request.FILES['profile_photo']
        user.save()

    solved_count = Submission.objects.filter(user=user, is_correct=True).values('problem').distinct().count()
    total = Submission.objects.filter(user=user).count()
    correct = Submission.objects.filter(user=user, is_correct=True).count()
    accuracy = round((correct / total) * 100, 2) if total > 0 else 0

    language_stats = Submission.objects.filter(user=user).values('language').annotate(count=Count('id'))
    difficulty_stats = Submission.objects.filter(user=user, is_correct=True).values('problem__difficulty').annotate(count=Count('id'))

    # Rename key for template compatibility
    difficulty_stats = [
        {'difficulty': stat['problem__difficulty'], 'count': stat['count']}
        for stat in difficulty_stats
    ]

    return render(request, "profile.html", {
        'user': user,
        'solved_count': solved_count,
        'accuracy': accuracy,
        'language_stats': language_stats,
        'difficulty_stats': difficulty_stats
    })

@login_required(login_url='login')
@never_cache
def render_problemspage(request, id):
    user = get_object_or_404(User, id=id)
    problems = Problem.objects.all()
    return render(request, "problems.html", {
        'user': user,
        'problems': problems
    })

@login_required
def delete_profile(request, id):
    # Get the user to delete
    user_to_delete = get_object_or_404(User, id=id)
    
    # Security check - only allow users to delete their own profile
    if request.user != user_to_delete:
        raise Http404("You can only delete your own profile")
    
    if request.method == 'POST':
        # Log the user out before deletion
        from django.contrib.auth import logout
        logout(request)
        request.session.flush()
        
        # Delete the user
        user_to_delete.delete()
        
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('signup')# Redirect to homepage
    
    # If GET request, redirect back to profile
    return redirect('user-details', id=id)

@login_required
def add_problem(request, id):
    user = request.user  # Always the logged-in user
    if not (user.is_superuser or (user.is_community_user and user.is_approved)):
        return HttpResponseForbidden("You are not allowed to add problems.")

    if request.method == 'POST':
        form = ProblemForm(request.POST)
        if form.is_valid():
            problem = form.save(commit=False)
            # You might want to associate the problem with the current user
            problem.created_by = request.user
            problem.save()
            messages.success(request, 'Problem added successfully!')
            return redirect('problems-page',  id=id)  # Redirect to problems list page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProblemForm()
    
    return render(request, 'add_problems.html', {'form': form})

@login_required(login_url='login')
@never_cache
def problems_list(request):
    problems = Problem.objects.all().order_by('-id')  # Show newest first
    
    # Filter by difficulty if requested
    difficulty = request.GET.get('difficulty')
    if difficulty and difficulty in ['Easy', 'Medium', 'Hard']:
        problems = problems.filter(difficulty=difficulty)
    
    # You can add more filtering logic here
    context = {
        'problems': problems,
        'user': request.user,
    }
    return render(request, 'problems.html', context)


@login_required
def approve_users(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Admins only.")

    pending_users = User.objects.filter(is_community_user=True, is_approved=False)
    approved_users = User.objects.filter(is_community_user=True, is_approved=True)

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        action = request.POST.get("action")

        try:
            user = User.objects.get(id=user_id)
            if action == "approve":
                user.is_approved = True
                user.save()
            elif action == "reject":
                user.is_community_user = False
                user.is_approved = False
                user.save()
            elif action == "remove":
                user.is_community_user = False
                user.is_approved = False
                user.save()
        except User.DoesNotExist:
            pass

        return redirect("approve-users")

    return render(request, "approve_users.html", {
        "pending_users": pending_users,
        "approved_users": approved_users
    })