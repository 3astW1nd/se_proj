
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .models import Employee, Leave
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, fields, IntegerField
from django.http import JsonResponse
from django.db.models.functions import ExtractDay



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
        if employee.check_role() == "Manager": 
            return manager_leaves_view(request)
        elif employee.check_role() == "HR":
            leave_summary = Leave.objects.annotate(
                days=ExpressionWrapper(
                   ExtractDay(F("end_date") - F("start_date")) + 1, output_field=IntegerField()
                )
            ).values("employee__department").annotate(
                annual_leave=Sum("days", filter=Q(leave_type="Annual")),
                sick_leave=Sum("days", filter=Q(leave_type="Sick")),
                personal_leave=Sum("days", filter=Q(leave_type="Personal")),
                other_leave=Sum("days", filter=Q(leave_type="Other")),
                total_days=Sum("days"),
                employee_count=Count("employee", distinct=True)
            ).order_by("employee__department")
            # Calculate average leave per employee
            for entry in leave_summary:
                entry["avg_per_employee"] = round(entry["total_days"] / entry["employee_count"], 2) if entry["employee_count"] > 0 else 0

            # Get overall totals
            totals = {
                "annual_leave": sum(entry["annual_leave"] or 0 for entry in leave_summary),
                "sick_leave": sum(entry["sick_leave"] or 0 for entry in leave_summary),
                "personal_leave": sum(entry["personal_leave"] or 0 for entry in leave_summary),
                "other_leave": sum(entry["other_leave"] or 0 for entry in leave_summary),
                "total_days": sum(entry["total_days"] or 0 for entry in leave_summary),
                "avg_per_employee": round(sum(entry["total_days"] for entry in leave_summary) / sum(entry["employee_count"] for entry in leave_summary), 2) if leave_summary else 0,
            }

            return render(request, "hr_leave.html", {
                "leave_summary": leave_summary,
                "totals": totals,
            })
        else:
            leave_requests = Leave.objects.filter(employee=employee).order_by('-requested_on')
            return render(request, "leave.html", {
                "employee": employee,
                "leave_requests": leave_requests
            })
         
    except Employee.DoesNotExist:
        return render(request, "login.html", {"error_message": "User does not exist"})
    

def settings_view(request):
    return render(request, "settings.html")

# ---------------- Leaves View ----------------
from django.shortcuts import redirect
from django.utils import timezone
from datetime import datetime

def request_leave_view(request):
    """View for employees to request leave"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    try:
        employee = Employee.objects.get(id=user_id)
        
        if request.method == "POST":
            # Get form data
            leave_type = request.POST.get("leave_type")
            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")
            reason = request.POST.get("reason")
            
            # Validate form data
            if not all([leave_type, start_date, end_date, reason]):
                return render(request, "leave.html", {
                    "employee": employee,
                    "error_message": "All fields are required",
                    "form_data": request.POST
                })
            
            # Calculate number of days
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            days = (end - start).days + 1  
            
            # Validate date range
            if days < 1:
                return render(request, "leave.html", {
                    "employee": employee,
                    "error_message": "End date must be after start date",
                    "form_data": request.POST
                })
            
            # Save leave request
            leave = Leave(
                employee=employee,
                leave_type=leave_type,
                start_date=start_date,
                end_date=end_date,
                status="Pending",
                requested_on=timezone.now()
            )
            leave.save()
            
            # ✅ Redirect to prevent resubmission on refresh
            return redirect("request_leave_success")  # Replace with actual success page or same form page
            
        # GET request - Display form
        leave_requests = Leave.objects.filter(employee=employee).order_by('-requested_on')
        return render(request, "leave.html", {
            "employee": employee,
            "leave_requests": leave_requests
        })
        
    except Employee.DoesNotExist:
        return redirect("login")


def request_leave_success(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    employee = Employee.objects.get(id=user_id)
    leave_requests = Leave.objects.filter(employee=employee).order_by('-requested_on')

    return render(request, "leave.html", {
        "employee": employee,
        "success_message": "Leave request submitted successfully!",
        "leave_requests": leave_requests
    })


def manager_leaves_view(request):
    """View for administrators to see all pending leave requests"""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    try:
        # Check if user is admin or HR
        employee = Employee.objects.get(id=user_id)
        if employee.check_role() not in ["Manager"]:
            messages.error(request, "You don't have permission to access this page")
            return redirect("dashboard")
        
        # Get filter parameters
        department = request.GET.get('department', '')
        leave_type = request.GET.get('leave_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        # Base query - get all pending leave requests
        pending_requests = Leave.objects.select_related('employee')
        
        # Apply filters if provided
        if department:
            pending_requests = pending_requests.filter(employee__department=department)
        
        if leave_type:
            pending_requests = pending_requests.filter(leave_type=leave_type)
        
        if date_from:
            pending_requests = pending_requests.filter(start_date__gte=date_from)
        
        if date_to:
            pending_requests = pending_requests.filter(end_date__lte=date_to)
        
        for leave in pending_requests:
            # If days field doesn't already exist
            if not hasattr(leave, 'days') or leave.days is None:
                start = leave.start_date
                end = leave.end_date
                leave.days = (end - start).days + 1  # Include both start and end days

        # Get unique departments and leave types for filter dropdowns
        departments = Employee.objects.values_list('department', flat=True).distinct()
        leave_types = Leave.objects.values_list('leave_type', flat=True).distinct()
        
        # Get counts for dashboard stats
        pending_count = Leave.objects.filter(status="Pending").count()
        approved_count = Leave.objects.filter(status="Approved").count()
        rejected_count = Leave.objects.filter(status="Rejected").count()
        
        # Get employees currently on leave (approved leaves that include today's date)
        from django.utils import timezone
        today = timezone.now().date()
        on_leave_count = Leave.objects.filter(
            status="Approved",
            start_date__lte=today,
            end_date__gte=today
        ).count()
        
        context = {
            'employee': employee,
            'pending_requests': pending_requests,
            'departments': departments,
            'leave_types': leave_types,
            'filters': {
                'department': department,
                'leave_type': leave_type,
                'date_from': date_from,
                'date_to': date_to,
            },
            'stats': {
                'pending_count': pending_count,
                'approved_count': approved_count,
                'rejected_count': rejected_count,
                'on_leave_count': on_leave_count,
            }
        }
        
        return render(request, "manager_leave.html", context)
        
    except Employee.DoesNotExist:
        return redirect("login")
    


def leave_action_view(request, leave_id, action):
    """View for approving or rejecting leave requests"""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)
    
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    try:
        # Check if user is a Manager
        employee = Employee.objects.get(id=user_id)
        if employee.check_role() != "Manager":
            return JsonResponse({"error": "You don't have permission to perform this action"}, status=403)

        # Get the leave request
        leave_request = get_object_or_404(Leave, id=leave_id)

        # Check if leave is already processed
        if leave_request.status != "Pending":
            return JsonResponse({"message": f"This leave request has already been {leave_request.status.lower()}."}, status=400)

        # Process the action
        if action == "approve":
            leave_request.status = "Approved"
            success_message = "Leave request approved successfully."
        elif action == "reject":
            leave_request.status = "Rejected"
            success_message = "Leave request rejected successfully."
        else:
            return JsonResponse({"error": "Invalid action"}, status=400)

        
        # Update approval details
        leave_request.manager = employee
        leave_request.approved_on = timezone.now()
        leave_request.save()

        return JsonResponse({"success": True, "message": success_message})

    except Employee.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    except Leave.DoesNotExist:
        return JsonResponse({"error": "Leave request not found"}, status=404)


from django.db.models import Sum, Count
from django.shortcuts import render
from .models import Leave, Employee

def leave_summary_view(request):
    """View to display leave summary by department."""
    
    # Get all leave requests, grouped by department
    


def get_leave_report(request):
    department = request.GET.get("department", "all")
    leave_type = request.GET.get("leave_type", "all")

    # Calculate leave duration in days
    leave_duration = ExpressionWrapper(
        ExtractDay(F("end_date") - F("start_date")) + 1,
        output_field=IntegerField()
    )

    # Apply filters
    filters = Q()
    if department != "all":
        filters &= Q(employee__department=department)
    if leave_type != "all":
        filters &= Q(leave_type__iexact=leave_type)

    # Fetch filtered leave data
    report_data = (
        Leave.objects.filter(filters)
        .values("employee__department")
        .annotate(
            annual_leave=Sum(leave_duration, filter=Q(leave_type="Annual")),
            sick_leave=Sum(leave_duration, filter=Q(leave_type="Sick")),
            personal_leave=Sum(leave_duration, filter=Q(leave_type="Personal")),
            other_leave=Sum(leave_duration, filter=Q(leave_type="Other")),
            total_days=Sum(leave_duration),
            employee_count=Count("employee", distinct=True),
        )
    )

    result = []
    total_annual_leave = 0
    total_sick_leave = 0
    total_personal_leave = 0
    total_other_leave = 0
    total_days = 0
    total_employees = 0

    for item in report_data:
        annual_leave = item["annual_leave"] or 0
        sick_leave = item["sick_leave"] or 0
        personal_leave = item["personal_leave"] or 0
        other_leave = item["other_leave"] or 0
        total_leave_days = item["total_days"] or 0
        employee_count = item["employee_count"] or 0

        result.append({
            "department": item["employee__department"],
            "annual_leave": annual_leave,
            "sick_leave": sick_leave,
            "personal_leave": personal_leave,
            "other_leave": other_leave,
            "total_days": total_leave_days,
            "avg_per_employee": round(total_leave_days / employee_count, 2) if employee_count else 0,
        })

        # Accumulate totals
        total_annual_leave += annual_leave
        total_sick_leave += sick_leave
        total_personal_leave += personal_leave
        total_other_leave += other_leave
        total_days += total_leave_days
        total_employees += employee_count

    # Create a totals dictionary
    totals = {
        "annual_leave": total_annual_leave,
        "sick_leave": total_sick_leave,
        "personal_leave": total_personal_leave,
        "other_leave": total_other_leave,
        "total_days": total_days,
        "avg_per_employee": round(total_days / total_employees, 2) if total_employees else 0,
    }

    return JsonResponse({"report": result, "totals": totals}, safe=False)
