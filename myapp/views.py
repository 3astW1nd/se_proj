from django.shortcuts import render, redirect
from myapp.models import Employee

def home(request):
    return render(request, "index.html")  # Renders the login page

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .models import Employee

# ---------------- Signup View ----------------
def signup_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")  # Unused in model, remove if unnecessary
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        department = request.POST.get("department")

        # Check if passwords match
        if password != confirm_password:
            return render(request, "signup.html", {"error_message": "Passwords do not match"})

        # Check if email already exists
        if Employee.objects.filter(email=email).exists():
            return render(request, "signup.html", {"error_message": "Email already registered"})

        # Create a new employee
        employee = Employee(
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department
        )
        employee.set_password(password)  # Securely hash the password before saving
        employee.save()

        # Redirect to login after signup
        return redirect("login")

    return render(request, "signup.html")

# ---------------- Login View ----------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            employee = Employee.objects.get(email=email)
            if employee.check_password(password):  # Securely check password
                request.session["user_id"] = employee.id  # Store user session
                return redirect("dashboard")
            else:
                return render(request, "login.html", {"error_message": "Invalid credentials"})

        except Employee.DoesNotExist:
            return render(request, "login.html", {"error_message": "User does not exist"})

    return render(request, "login.html")

# ---------------- Logout View ----------------
def logout_view(request):
    request.session.flush()  # Clear session
    return redirect("login")

# ---------------- Dashboard View ----------------
def dashboard_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    employee = Employee.objects.get(id=user_id)
    return render(request, "index.html", {"employee": employee})


def payroll_view(request):
    return render(request, 'payroll.html')


def leave_view(request):
    user_id = request.session.get("user_id")
    try:
        employee = Employee.objects.get(id=user_id)
        if employee.check_role() == "Admin": 
            return render(request, "admin_leave.html")
        elif employee.check_role() == "HR":
            return render(request, "hr_leave.html")
        else:
            return render(request, "leave.html")
         
    except Employee.DoesNotExist:
        return render(request, "login.html", {"error_message": "User does not exist"})
    

def settings_view(request):
    return render(request, "settings.html")