from django.urls import path
from registration.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', render_homepage, name = "home-page"),
    path('signup/', render_signuppage, name = "signup"),
    path('login/', render_loginpage, name = "login"),
]


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)