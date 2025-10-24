from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.mail import EmailMessage
import os, qrcode
from django.views.decorators.csrf import csrf_exempt # type: ignore
from .models import Bus, Seat, Student, Driver, Route, School, Program, Stoppage, Allotment, Notice, Feedback
from .forms import StudentForm, DriverForm, MultipleSeatsForm
from .forms import BusForm
from .forms import AllotmentForm
from .forms import RouteForm
from .forms import StoppageForm
from .forms import NoticeForm
from .forms import FeedbackForm
from django.db.models import Q
from django.db.models import Count

# bus_app/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # user ko session me login kar dega
            return redirect('/')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('/login/')


# ✅ Home Page


def home(request):
    return render(request, 'home.html')


# ✅ Student Form View



# ✅ Bus Seating Chart
def bus_seating_chart(request, bus_number):
    bus = get_object_or_404(Bus, number=bus_number)
    seats = Seat.objects.filter(bus=bus).order_by('seat_number')

    # ✅ Seat Layout (Left: 2, Gap: 1, Right: 3)
    total_columns = 6  # 2 Left + 1 Gap + 3 Right
    seating_chart = []
    row = []
    seat_index = 0

    for seat in seats:
        if seat_index % total_columns == 2:  # Middle me gap add karo
            row.append({'is_gap': True})

        row.append(seat)
        seat_index += 1

        if len(row) == total_columns:  # Row complete ho gyi
            seating_chart.append(row)
            row = []
            seat_index = 0  # Next row ke liye seat count reset

    if row:  # Last row incomplete ho to bhi add kar do
        seating_chart.append(row)

    return render(request, 'bus_seating_chart.html', {'bus': bus, 'seating_chart': seating_chart})


def generate_qr(request):
    # ✅ Hardcoded full URL
    form_url = "https://kanhaiyasoni.pythonanywhere.com/about/"

    qr = qrcode.make(form_url)

    qr_path = os.path.join(settings.MEDIA_ROOT, "qr_code.png")
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    qr.save(qr_path)

    with open(qr_path, "rb") as image_file:
        return HttpResponse(image_file.read(), content_type="image/png")


# ✅ Allot Bus to Student
def allot_bus(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    # ✅ Sirf usi route ke buses fetch karo jo student ka route hai
    allotments = Allotment.objects.filter(route=student.route).select_related('bus', 'route')

    bus_details = []
    for allotment in allotments:
        bus = allotment.bus
        route = allotment.route  # ✅ Directly fetching route

        bus_details.append({
            'bus': bus,
            'route': route.name if route else "No Route",  # ✅ Fix: Route naam show hoga
            'total_seats': bus.total_seats(),
            'vacant_seats': bus.vacant_seats(),
            'occupied_seats': bus.occupied_seats()
        })

    return render(request, 'allot_bus.html', {'student': student, 'bus_details': bus_details})


# ✅ Assign Seat to Student
def assign_seat(request, student_id, bus_id, seat_number):
    student = get_object_or_404(Student, id=student_id)
    bus = get_object_or_404(Bus, id=bus_id)
    seat = get_object_or_404(Seat, bus=bus, seat_number=seat_number)


    if request.method == 'POST':
        seat.student = student
        seat.save()

        student.assigned_bus = bus
        student.assigned_seat = seat
        student.save()

        send_seat_allotment_email(student)

        return redirect('/buses/')

    return render(request, 'assign_seat.html', {'student': student, 'bus': bus, 'seat': seat})


# ✅ Send Seat Allotment Email
def send_seat_allotment_email(student):
    subject = f"Bus Seat Allotment Confirmation for {student.name}"

    route = student.assigned_bus.get_route()
    message = f"""
   <p>Dear <strong>{student.name}</strong>,</p>

<p>We are pleased to inform you that your **seat has been successfully assigned** in the college transport system.</p>

<p><strong>🚌 Bus Details:</strong></p>
<ul>
    <li><strong>🚌Bus Number:</strong> {student.assigned_bus.identifier_number}</li>
    <li><strong>📍 Route:</strong> {route.name if route else "Not Assigned"}</li>
    <li><strong>💺 Assigned Seat:</strong> {student.assigned_seat.seat_number}</li>
    <li><strong>🚍vehicle Number:</strong> {student.assigned_bus.number}</li>
</ul>

<p>For any queries regarding your bus assignment, please contact the **Transport Management Office**.</p>

<p>We wish you a comfortable and safe journey!</p>

<p>Best Regards,</p>
<p><strong>🚍 Transport Management Team</strong><br>
<strong>[I.T.M UNIVERSITY]</strong></p>
"""

    recipient_email = student.email
    try:
        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])
        email.content_subtype = "html"
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")


# ✅ Select Seat for Student
def select_seat(request, student_id, bus_id):
    student = get_object_or_404(Student, id=student_id)
    bus = get_object_or_404(Bus, id=bus_id)

    # Sirf khali seats dikhao
    seats = Seat.objects.filter(bus=bus, student__isnull=True)

    if request.method == "POST":
        seat_id = request.POST.get("seat_id")
        seat = get_object_or_404(Seat, id=seat_id)

        # Assign seat to student
        seat.student = student
        seat.save()

        student.assigned_seat = seat
        student.assigned_bus = bus
        student.save()

        return redirect('admin:bus_app_student_changelist')

    return render(request, 'select_seat.html', {
        'student': student,
        'bus': bus,
        'seats': seats
    })


# ✅ Get Seat Details
def get_seat_details(request, seat_id):
    seat = get_object_or_404(Seat, id=seat_id)
    return render(request, 'seat_details_modal.html', {'seat': seat})

def driver_list(request):
    # Fetch all drivers
    drivers = Driver.objects.all()

    # Fetch distinct driver names, license numbers, and contact numbers
    driver_names = Driver.objects.values_list('name', flat=True).distinct()
    license_numbers = Driver.objects.values_list('D_license_number', flat=True).distinct()
    contact_numbers = Driver.objects.values_list('contact_number', flat=True).distinct()

    # Get the search query and filter parameters from the GET request
    search_query = request.GET.get('search', '')
    name_filter = request.GET.get('driver_name')
    license_filter = request.GET.get('license_number')
    contact_filter = request.GET.get('contact_number')

    # Apply universal search filter if search query exists
    if search_query:
        drivers = drivers.filter(
            Q(name__icontains=search_query) |
            Q(D_license_number__icontains=search_query) |
            Q(contact_number__icontains=search_query)
        )

    # Apply dropdown filters
    if name_filter:
        drivers = drivers.filter(name=name_filter)
    if license_filter:
        drivers = drivers.filter(D_license_number=license_filter)
    if contact_filter:
        drivers = drivers.filter(contact_number=contact_filter)

    # Prepare context for the template
    context = {
        'drivers': drivers,
        'driver_names': driver_names,
        'license_numbers': license_numbers,
        'contact_numbers': contact_numbers,
    }

    return render(request, 'driver_list.html', context)



def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('driver_list')  # Redirect to driver list after adding
    else:
        form = DriverForm()
    return render(request, 'add_driver.html', {'form': form})

def edit_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)

    if request.method == "POST":
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            form.save()
            return redirect('driver_list')  # Redirect to driver list page

    else:
        form = DriverForm(instance=driver)

    return render(request, 'edit_driver.html', {'form': form, 'driver': driver})



def get_stoppages(request):
    route_id = request.GET.get("route_id")
    stoppages = Stoppage.objects.filter(route_id=route_id).values("id", "name")
    return JsonResponse(list(stoppages), safe=False)



def student_form(request):
    form = StudentForm()  # or PublicStudentForm()
    return render(request, "student_form.html", {"form": form})



# ✅ Handle Form Submission
def submit_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("success")  # Redirect to success page
    else:
        form = StudentForm()
    return render(request, "student_form.html", {"form": form})

# ✅ Success Page
def success_page(request):
    return render(request, "success.html")

# ✅ AJAX for Programs
def get_schools(request):
    schools = School.objects.values_list('name', flat=True)
    return JsonResponse({'schools': list(schools)})

def get_programs(request):
    school_name = request.GET.get('school', '')
    programs = Program.objects.filter(school__name__iexact=school_name).values_list('name', flat=True)
    return JsonResponse({'programs': list(programs)})

def get_routes(request):
    routes = Route.objects.values_list('name', flat=True)
    return JsonResponse({'routes': list(routes)})

def get_stoppages(request):
    route_name = request.GET.get('route', '')
    stoppages = Stoppage.objects.filter(route__name__iexact=route_name).values_list('name', flat=True)
    return JsonResponse({'stoppages': list(stoppages)})

@csrf_exempt
def register_student(request):
    if request.method == "POST":
        try:
            name = request.POST.get("name").strip()
            roll_number = request.POST.get("roll_number", "").strip()
            crm_id = request.POST.get("crm_id", "").strip()
            school_name = request.POST.get("school")
            program_name = request.POST.get("program")
            fee_paid = request.POST.get("fee_paid") == "on"
            fee_amount = request.POST.get("fee_amount")
            email = request.POST.get("email").strip()
            contact_number = request.POST.get("contact_number").strip()
            route_name = request.POST.get("route")
            stoppage_name = request.POST.get("stoppage")
            gender = request.POST.get("gender")
            photo = request.FILES.get("photo")

            # ⚠️ Ensure at least one ID is given
            if roll_number == "" and crm_id == "":
                return JsonResponse({"success": False, "error": "Either Roll Number or CRM ID is required!"}, status=400)

            # ⚠️ Convert empty CRM ID to None
            if crm_id == "":
                crm_id = None

            # 🛑 Check if CRM ID already exists
            if crm_id and Student.objects.filter(crm_id=crm_id).exists():
                return JsonResponse({"success": False, "error": "CRM ID already exists!"}, status=400)

            # 🏫 Fetch Related Objects
            school = School.objects.filter(name__iexact=school_name).first()
            program = Program.objects.filter(name__iexact=program_name, school=school).first()
            route = Route.objects.filter(name__iexact=route_name).first()
            stoppage = Stoppage.objects.filter(name__iexact=stoppage_name, route=route).first()

            # 🎯 Save Student
            student = Student.objects.create(
                name=name,
                roll_number=roll_number,
                crm_id=crm_id,
                school=school,
                program=program,
                fee_paid=fee_paid,
                fee_amount=fee_amount,
                email=email,
                contact_number=contact_number,
                route=route,
                stoppage=stoppage,
                gender=gender,
                photo=photo
            )

            return JsonResponse({"success": True, "message": "Student Registered Successfully!"})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)



# bus list view

def bus_list(request):
    buses = Bus.objects.all()

    # Get unique options for dropdowns
    bus_numbers = Bus.objects.values_list('number', flat=True).distinct()
    identifiers = Bus.objects.values_list('identifier_number', flat=True).distinct()
    routes = Route.objects.values_list('name', flat=True).distinct()

    # Get filters from request
    number_filter = request.GET.get('bus_no')
    identifier_filter = request.GET.get('bus_id')
    route_filter = request.GET.get('route')
    search_query = request.GET.get('search')

    if number_filter:
        buses = buses.filter(number=number_filter)
    if identifier_filter:
        buses = buses.filter(identifier_number=identifier_filter)
    if route_filter:
        buses = buses.filter(allotments__route__name=route_filter)

    if search_query:
        buses = buses.filter(
            Q(number__icontains=search_query) |
            Q(identifier_number__icontains=search_query) |
            Q(allotments__route__name__icontains=search_query)
        ).distinct()

    # Prepare bus data with route name
    bus_data = []
    for bus in buses:
        allotment = bus.allotments.select_related('route').first()
        route_name = allotment.route.name if allotment and allotment.route else "N/A"

        bus_data.append({
            'number': bus.number,
            'identifier_number': bus.identifier_number,
            'route': route_name,
        })

    context = {
        'buses': bus_data,
        'bus_numbers': bus_numbers,
        'identifiers': identifiers,
        'routes': routes,
    }
    return render(request, 'bus_list.html', context)



# bus details view

def bus_detail(request, number):
    bus = get_object_or_404(Bus, number=number)
    return render(request, 'bus_detail.html', {'bus': bus})

# bus form view
def add_bus(request):
    if request.method == 'POST':
        form = BusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('bus_list')  # or your list view name
    else:
        form = BusForm()

    return render(request, 'add_bus.html', {'form': form})

#edit bus details:
def edit_bus(request, number):
    bus = get_object_or_404(Bus, number=number)

    if request.method == 'POST':
        form = BusForm(request.POST, instance=bus)
        if form.is_valid():
            form.save()
            return redirect('bus_list')  # redirect to bus list or bus detail page
    else:
        form = BusForm(instance=bus)

    return render(request, 'edit_bus.html', {'form': form,'bus': bus
    })



# allotment list
def allotment_list(request):
    allotments = Allotment.objects.select_related('bus', 'driver', 'route').all()

    bus_no = request.GET.get('bus_no')
    driver_id = request.GET.get('driver')
    route_id = request.GET.get('route')
    search_query = request.GET.get('search')

    if bus_no:
        allotments = allotments.filter(bus__number=bus_no)
    if driver_id:
        allotments = allotments.filter(driver__id=driver_id)
    if route_id:
        allotments = allotments.filter(route__id=route_id)

    if search_query:
        allotments = allotments.filter(
            Q(bus__number__icontains=search_query) |
            Q(driver__name__icontains=search_query) |
            Q(route__name__icontains=search_query)
        ).distinct()

    context = {
        'allotments': allotments,
        'bus_numbers': Bus.objects.values_list('number', flat=True).distinct(),
        'drivers': Driver.objects.all(),
        'routes': Route.objects.all(),
    }
    return render(request, 'allotment_list.html', context)


#add allotment

def add_allotment(request):
    if request.method == 'POST':
        form = AllotmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('allotment_list')  # redirect after saving
    else:
        form = AllotmentForm()
    return render(request, 'add_allotment.html', {'form': form})

def get_stoppages_by_route(request):      #for filtering the stopages bases on routes
    route_id = request.GET.get('route_id')
    stoppages = Stoppage.objects.filter(route_id=route_id).values('id', 'name')
    return JsonResponse(list(stoppages), safe=False)

#driver_list


#driver details
def driver_detail(request, license_number):
    driver = get_object_or_404(Driver, D_license_number=license_number)
    return render(request, 'driver_detail.html', {'driver': driver})

#edit driver

#add drivers
def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('driver_list')  # After saving, go back to driver list
    else:
        form = DriverForm()

    return render(request, 'add_driver.html', {'form': form})

#delete driver
def delete_driver(request, license_number):
    driver = get_object_or_404(Driver, D_license_number=license_number)
    driver.delete()
    messages.success(request, "Driver deleted successfully.")
    return redirect('driver_list')


#student list

def student_list(request):
    students = Student.objects.all()

    student_names = Student.objects.values_list('name', flat=True).distinct()
    roll_numbers = Student.objects.values_list('roll_number', flat=True).distinct()
    school_names = School.objects.values_list('name', flat=True).distinct()

    # Universal search bar functionality
    search_query = request.GET.get('search')
    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(crm_id__icontains=search_query) |
            Q(school__name__icontains=search_query) |
            Q(program__icontains=search_query)
        )

    # Existing filters
    if request.GET.get('student_name'):
        students = students.filter(name=request.GET.get('student_name'))
    if request.GET.get('roll_number'):
        students = students.filter(roll_number=request.GET.get('roll_number'))
    if request.GET.get('school_name'):
        students = students.filter(school__name=request.GET.get('school_name'))

    return render(request, 'student_list.html', {
        'students': students,
        'student_names': student_names,
        'roll_numbers': roll_numbers,
        'school_names': school_names,
    })


#add student
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)  # Handling file uploads for student photo
        if form.is_valid():
            form.save()
            return redirect('student_list')  # Redirecting back to the student list
    else:
        form = StudentForm()

    return render(request, 'add_student.html', {'form': form})


def student_detail(request, id):
    # Get the student object, or return a 404 error if not found
    student = get_object_or_404(Student, pk=id)

    # Render the template and pass the student object
    return render(request, 'student_detail.html', {'student': student})

#route_list
def route_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        routes = Route.objects.filter(name__icontains=search_query)
    else:
        routes = Route.objects.all()
    return render(request, 'route_list.html', {'routes': routes})

#add route
def add_route(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('route_list')
    else:
        form = RouteForm()

    return render(request, 'add_route.html', {'form': form})


#edit route

def edit_route(request, route_id):
    route = get_object_or_404(Route, id=route_id)
    if request.method == "POST":
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            return redirect("route_list")
    else:
        form = RouteForm(instance=route)
    return render(request, "edit_route.html", {"form": form})

#stoppage_list
def stoppage_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        stoppages = Stoppage.objects.filter(name__icontains=search_query)
    else:
        stoppages = Stoppage.objects.all()

    return render(request, 'stoppage_list.html', {'stoppages': stoppages})
#add stoppage
def add_stoppage(request):
    if request.method == 'POST':
        form = StoppageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('stoppage_list')
    else:
        form = StoppageForm()

    return render(request, 'add_stoppage.html', {'form': form})

#edit_stoppage
def edit_stoppage(request, pk):
    stoppage = get_object_or_404(Stoppage, pk=pk)

    if request.method == 'POST':
        form = StoppageForm(request.POST, instance=stoppage)
        if form.is_valid():
            form.save()
            return redirect('stoppage_list')  # or wherever you want to redirect
    else:
        form = StoppageForm(instance=stoppage)

    return render(request, 'edit_stoppage.html', {'form': form, 'stoppage': stoppage})

#delete_stoppages
from django.shortcuts import get_object_or_404, redirect
from .models import Stoppage

def delete_stoppage(request, pk):
    stoppage = get_object_or_404(Stoppage, pk=pk)
    stoppage.delete()
    return redirect('stoppage_list')  # Replace with your actual redirect target





#for notices
def notice_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        notices = Notice.objects.filter(message__icontains=search_query)
    else:
        notices = Notice.objects.all().order_by('-created_at')  # latest first

    return render(request, 'notice_list.html', {'notices': notices})

def add_notice(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save()
            notice.send_notice()  # Send emails after saving
            return redirect('notice_list')
    else:
        form = NoticeForm()

    return render(request, 'add_notice.html', {'form': form})


def about(request):
    team = [
        {'name': 'Prakhar Bajpai', 'image': 'prakhar3.jpg'},
        {'name': 'Kanhaiya Soni', 'image': 'kanhaiya.png'},
        {'name': 'Prakhar Gupta', 'image': 'gupta ji.png'},
        {'name': 'Khushi samadhiya', 'image': 'khushi.png'},
        {'name': 'Shreya sharma', 'image': 'shreya.png'},
        {'name': 'Himanshi saxena', 'image': 'himanshi.png'},
        {'name': 'Astha gangle', 'image': 'astha.png'},
    ]
    return render(request, 'about.html', {'team': team})


def choice (request):
    return render(request, 'choice.html')


# ✅ Feedback Form
from .forms import FeedbackForm

def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'thankyou.html')  # optional: make a nice thank-you page
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})


def thank_you_page(request):
    return render(request, 'thankyou.html')


def feedback_list(request):
    feedbacks = Feedback.objects.all().order_by('-submitted_at')
    return render(request, 'feedback_list.html', {'feedbacks': feedbacks})

def reports_view(request):
    # 🔢 Total stats
    total_buses = Bus.objects.count()
    total_routes = Route.objects.count()
    total_students = Student.objects.count()
    total_schools = School.objects.count()
    total_drivers = Driver.objects.count()

    # 👨‍👩‍👧‍👦 Gender Distribution
    gender_counts = Student.objects.values('gender').annotate(count=Count('id'))
    gender_summary = {'Male': 0, 'Female': 0, 'Other': 0}
    for item in gender_counts:
        gender_summary[item['gender']] = item['count']

    # 🚌 Buses per Route (via Allotments)
    buses_per_route = Route.objects.annotate(bus_count=Count('allotment'))

    # 👨‍🎓 Students per Bus
    students_per_bus = Bus.objects.annotate(student_count=Count('students'))

    # 👨‍🎓 Students per Route
    students_per_route = Route.objects.annotate(student_count=Count('students'))

    # 🏫 Top Schools by student count
    top_schools = School.objects.annotate(student_count=Count('students')).order_by('-student_count')[:3]

    # 🧑‍💻 Top Programs by student count
    top_programs = Student.objects.values('program').annotate(count=Count('id')).order_by('-count')[:3]

    # 🧑‍✈️ All driver-bus-route assignments
    driver_assignments = Allotment.objects.select_related('driver', 'bus', 'route')

    context = {
        'total_buses': total_buses,
        'total_routes': total_routes,
        'total_students': total_students,
        'total_schools': total_schools,
        'total_drivers': total_drivers,
        'gender_summary': gender_summary,
        'buses_per_route': buses_per_route,
        'students_per_bus': students_per_bus,
        'students_per_route': students_per_route,
        'top_schools': top_schools,
        'top_programs': top_programs,
        'driver_assignments': driver_assignments,
    }

    return render(request, 'reports.html', context)


