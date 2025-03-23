
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Employee, Leave, Salary
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import redirect
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

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
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    try:
        employee = Employee.objects.get(id=user_id)
        
        # Fetch all salary records for the current employee
        payslips = Salary.objects.filter(employee_id=user_id).order_by('-generated_on')
        
        # Add month and year attributes to each payslip for display
        for payslip in payslips:
            payslip.month = payslip.generated_on.strftime('%B')  # Full month name
            payslip.year = payslip.generated_on.year
            payslip.status = "Processed"  # Default status
            payslip.net_salary = payslip.net_pay+800  # Match the template's expected attribute
        
        # Get the selected payslip if ID is provided
        selected_payslip_id = request.GET.get('id')
        selected_payslip = None
        
        if selected_payslip_id:
            try:
                selected_payslip = Salary.objects.get(id=selected_payslip_id, employee_id=user_id)
                selected_payslip.month = selected_payslip.generated_on.strftime('%B')
                selected_payslip.year = selected_payslip.generated_on.year
                selected_payslip.status = "Processed"
                selected_payslip.net_salary = selected_payslip.net_pay+800
                
                # Add common deductions and allowances for display
                selected_payslip.housing_allowance = Decimal('500.00')
                selected_payslip.transport_allowance = Decimal('300.00')
                selected_payslip.allowances = selected_payslip.housing_allowance + selected_payslip.transport_allowance
                selected_payslip.deductions = selected_payslip.tax
                selected_payslip.month = selected_payslip.generated_on.strftime('%B')
                selected_payslip.year = selected_payslip.generated_on.year
                selected_payslip.total_earnings = selected_payslip.basic_salary + 800
                
            except Salary.DoesNotExist:
                pass
        
        return render(request, 'payroll.html', {
            'user': {
                'get_full_name': f"{employee.first_name} {employee.last_name}",
                'employee': employee,
            },
            'payslips': payslips,
            'selected_payslip': selected_payslip,
        })
        
    except Employee.DoesNotExist:
        return redirect("login")


def download_payslip(request, payslip_id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    
    try:
        employee = Employee.objects.get(id=user_id)
        payslip = Salary.objects.get(id=payslip_id, employee_id=user_id)
        
        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()
        
        # Create the PDF object, using the buffer as its "file"
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add company header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(1 * inch, 10 * inch, "False 9 2 5")
        p.setFont("Helvetica", 12)
        p.drawString(1 * inch, 9.7 * inch, "Siraiki Adda")
        p.drawString(1 * inch, 9.4 * inch, "Email: hr@false925.com")
        
        # Add title
        p.setFont("Helvetica-Bold", 14)
        month_name = payslip.generated_on.strftime('%B')
        year = payslip.generated_on.year
        p.drawString(1 * inch, 8.7 * inch, f"Salary Slip - {month_name} {year}")
        
        # Add employee information
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, 8.0 * inch, "Employee Information")
        p.setFont("Helvetica", 12)
        p.drawString(1 * inch, 7.7 * inch, f"Name: {employee.first_name} {employee.last_name}")
        p.drawString(1 * inch, 7.4 * inch, f"Employee ID: {employee.id}")
        p.drawString(1 * inch, 7.1 * inch, f"Pay Period: {month_name} {year}")
        
        # Add earnings section
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, 6.4 * inch, "Earnings")
        p.line(1 * inch, 6.3 * inch, 7 * inch, 6.3 * inch)
        p.setFont("Helvetica", 12)
        p.drawString(1 * inch, 6.0 * inch, "Basic Salary")
        p.drawString(6 * inch, 6.0 * inch, f"${payslip.basic_salary}")
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, 5.6 * inch, "Total Earnings")
        p.drawString(6 * inch, 5.6 * inch, f"${payslip.basic_salary}")
        
        # Add deductions section
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, 4.9 * inch, "Deductions")
        p.line(1 * inch, 4.8 * inch, 7 * inch, 4.8 * inch)
        p.setFont("Helvetica", 12)
        p.drawString(1 * inch, 4.5 * inch, "Income Tax")
        p.drawString(6 * inch, 4.5 * inch, f"${payslip.tax}")
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, 4.1 * inch, "Total Deductions")
        p.drawString(6 * inch, 4.1 * inch, f"${payslip.tax}")
        
        # Add net pay
        p.setFont("Helvetica-Bold", 14)
        p.drawString(1 * inch, 3.4 * inch, "Net Pay")
        p.drawString(6 * inch, 3.4 * inch, f"${payslip.net_pay+800}")
        
        # Add payslip details
        p.setFont("Helvetica", 10)
        p.drawString(1 * inch, 2.7 * inch, f"Payslip ID: {payslip.id}")
        p.drawString(1 * inch, 2.4 * inch, f"Generated on: {payslip.generated_on}")
        
        # Add footer
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(1 * inch, 1.5 * inch, "This is a computer-generated document and does not require a signature.")
        p.drawString(1 * inch, 1.2 * inch, "For any queries regarding your salary, please contact the HR department.")
        
        # Close the PDF object cleanly, and we're done
        p.showPage()
        p.save()
        
        # Get the value of the BytesIO buffer and write it to the response
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payslip_{month_name}_{year}.pdf"'
        
        return response
        
    except (Employee.DoesNotExist, Salary.DoesNotExist):
        return redirect("payroll")

    

def salary_view(request):
    return render(request, 'salary.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

def salary_view(request):
    return render(request, 'salary.html')

@csrf_exempt  # For testing only, use proper CSRF protection in production
def submit_salary(request):
    if request.method != "POST":
        return redirect("salary")
    
    # Get form data
    employee_id = request.POST.get("employee_id")
    basic_salary = request.POST.get("salary")
    tax_percentage = request.POST.get("tax")
    date = request.POST.get("date") or timezone.now().strftime('%Y-%m-%d')
    
    # Validate data
    if not all([employee_id, basic_salary, tax_percentage]):
        messages.error(request, "All fields are required")
        return redirect("salary")
        
    try:
        # Convert to proper data types
        employee_id = int(employee_id)
        basic_salary = Decimal(basic_salary)
        tax_percentage = Decimal(tax_percentage)
        
        # Calculate tax amount
        tax_amount = (basic_salary * tax_percentage) / Decimal('100.0')
        
        # Calculate net pay
        net_pay = basic_salary - tax_amount
        
        # Insert directly into database using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO salary 
                (employee_id, basic_salary, tax, net_pay, generated_on) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                [employee_id, basic_salary, tax_amount, net_pay, date]
            )
        
        messages.success(request, f"Salary of ${basic_salary} processed successfully for employee ID {employee_id}")
        return redirect("salary")
        
    except (ValueError, TypeError):
        messages.error(request, "Invalid numeric values provided")
        return redirect("salary")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect("salary")

def leave_view(request):
    user_id = request.session.get("user_id")
    try:
        employee = Employee.objects.get(id=user_id)
        if employee.check_role() == "Manager": 
            return manager_leaves_view(request)
        elif employee.check_role() == "HR":
            return render(request, "hr_leave.html")
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
