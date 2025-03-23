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
    path('request-leave/', views.request_leave_view, name='request_leave'),
    path("request-leave/success/", views.request_leave_success, name="request_leave_success"),
    path('manager/leaves/', views.manager_leaves_view, name='manager_leaves_view'),
    path('manager/leave/<int:leave_id>/<str:action>/', views.leave_action_view, name='leave_action'),
   
]


