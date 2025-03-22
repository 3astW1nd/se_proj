from django.urls import path
from .views import home
from myapp import views

urlpatterns = [
    path('', home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('payroll/', views.payroll_view, name='payroll'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('leave/', views.leave_view, name='leave'),
    path('settings/', views.settings_view, name='settings'),
]


