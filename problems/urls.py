from django.urls import path
from problems.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home/<int:id>/problems', render_problemspage, name = "problems-page"),
    path('home/<int:id>/', render_homepage, name = "user-details"),
    path('home/<int:id>/delete/', delete_profile, name="delete-profile"),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)