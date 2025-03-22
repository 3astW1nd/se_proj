from django.shortcuts import render

def home(request):
    return render(request, "index.html")  # Renders the login page

def login_view(request):
    return render(request, "login.html") # renders login page

def logout_view(request):
    return render(request, "login.html") # renders login page

def signup_view(request):
    return render(request, "signup.html") # renders signup page

def payroll_view(request):
    return render(request, 'payroll.html')

def dashboard_view(request):
    return render(request, "index.html")

def leave_view(request):
    return render(request, "leave.html")

def settings_view(request):
    return render(request, "settings.html")