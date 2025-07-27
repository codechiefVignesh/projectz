from django.urls import path
from problems.views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/<int:id>/problems', render_problemspage, name = "problems-page"),
    path('home/<int:id>/', render_homepage, name = "user-details"),
    path('home/<int:id>/delete/', delete_profile, name="delete-profile"),
    path('home/<int:id>/add-problem/', add_problem, name='add_problem'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path("approve-users/", approve_users, name="approve-users"),
    path('home/<int:id>/problems/<int:problem_id>/solve/', solve_problem, name='solve_problem'),
    path('home/<int:id>/problems/<int:problem_id>/run/', run_code, name='run_code'),
    path('home/<int:id>/problems/<int:problem_id>/submit/', submit_code, name='submit_code'),
    path('home/<int:user_id>/problems/<int:problem_id>/solutions/', solution_history, name='solution-history'),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)