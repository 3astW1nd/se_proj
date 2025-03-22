from django.shortcuts import render

def home(request):
    return render(request, "index.html")  # Renders the HTML file

def login_view(request):
    return render(request, "login.html")

def logout_view(request):
    return render(request, "login.html")

def signup_view(request):
    return render(request, "signup.html")