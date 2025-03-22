from django.urls import path
from .views import home
from myapp import views

urlpatterns = [
    path('', home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
]


