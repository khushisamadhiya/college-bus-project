from django.db import models
from django.core.mail import send_mail

# ✅ School Model (With Programs in JSONField)

class School(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Program Model (Linked to School)
class Program(models.Model):
    name = models.CharField(max_length=100)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="programs")

    def __str__(self):
        return f"{self.name} ({self.school.name})"

# Route Model
class Route(models.Model):
    name = models.CharField(max_length=100, unique=True)
    fare = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.name

# Stoppage Model (Linked to Route)
class Stoppage(models.Model):
    name = models.CharField(max_length=100)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="stoppages")

    def __str__(self):
        return f"{self.name} ({self.route.name})"

# ✅ Driver Model
class Driver(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    D_license_number = models.CharField(max_length=50, unique=True)
    contact_number = models.CharField(max_length=15, unique=True)
    reference_by = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# ✅ Bus Model
class Bus(models.Model):
    number = models.CharField(max_length=10, unique=True)  # Example: MP07VV467
    identifier_number = models.CharField(max_length=10, unique=True, null=True, blank=True)

    # ✅ Pollution Details
    pollution_paid = models.BooleanField(default=False)
    pollution_issue_date = models.DateField(null=True, blank=True)
    pollution_valid_upto = models.DateField(null=True, blank=True)

    # ✅ Insurance Details
    insurance_paid = models.BooleanField(default=False)
    insurance_issue_date = models.DateField(null=True, blank=True)
    insurance_valid_upto = models.DateField(null=True, blank=True)

    # ✅ Tax Details
    tax_paid = models.BooleanField(default=False)
    tax_issue_date = models.DateField(null=True, blank=True)
    tax_valid_upto = models.DateField(null=True, blank=True)
    permit = models.BooleanField(default=False)
    permit_issue_date = models.DateField(null=True, blank=True)
    permit_valid_upto = models.DateField(null=True, blank=True)

    # ✅ Route Assigned (Remove this field, as we are fetching from Allotment)
    # route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True)

    def get_route(self):
        allotment = Allotment.objects.filter(bus=self).first()
        return allotment.route if allotment else None

    def total_seats(self):
        return self.seats.count()

    def occupied_seats(self):
        return self.seats.filter(student__isnull=False).count()

    def vacant_seats(self):
        return self.total_seats() - self.occupied_seats()

    def __str__(self):
        return f"{self.number} ({self.get_route().name if self.get_route() else 'No Route'})"

# ✅ Seat Model
class Seat(models.Model):
    seat_number = models.PositiveIntegerField(null=True, blank=True)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
    student = models.ForeignKey('Student', null=True, blank=True, on_delete=models.SET_NULL, related_name='seats')

    class Meta:
        unique_together = ('bus', 'seat_number')

    def get_route(self):
        allotment = Allotment.objects.filter(bus=self.bus).first()
        return allotment.route if allotment else "No Route"

    def __str__(self):
        return f"Seat {self.seat_number} - {self.bus.number} ({self.get_route()})"


# ✅ Student Model (With Proper Foreign Keys)
class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, null=True, blank=True, unique=True)
    crm_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default="Male")

    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    program = models.CharField(max_length=100, blank=True, null=True)  # Directly storing program name

    fee_paid = models.BooleanField(default=False)
    fee_amount = models.CharField(max_length=10, blank=True, null=True)

    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=15, default="0000000000")

    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    stoppage = models.CharField(max_length=100, blank=True, null=True)  # Directly storing stoppage name

    assigned_bus = models.ForeignKey(Bus, null=True, blank=True, on_delete=models.SET_NULL, related_name="students")
    assigned_seat = models.ForeignKey(Seat, null=True, blank=True, on_delete=models.SET_NULL, related_name='students')

    photo = models.ImageField(upload_to="student_photos/", null=True, blank=True)

    def __str__(self):
        return self.name


    def save(self, *args, **kwargs):
        if not self.roll_number and not self.crm_id:
            raise ValueError("Either Roll Number or CRM ID must be provided.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

# ✅ Allotment Model (Driver & Bus Relationship)
class Allotment(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name="allotments")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="allotments")
    assigned_date = models.DateField(auto_now_add=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True, blank=True)
    stoppages = models.ManyToManyField(Stoppage)

    def __str__(self):
        return f"Bus {self.bus.number} -> Driver {self.driver.name} - {self.route.name}"

# ✅ Notice Model (With Email Sending Functionality)
class Notice(models.Model):
    TYPE_CHOICES = (
        ('Bus', 'Bus'),
        ('Route', 'Route'),
        ('All', 'All'),
    )

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='All')
    bus = models.ForeignKey(Bus, on_delete=models.SET_NULL, null=True, blank=True, related_name="notices")
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name="notices")

    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notice for {self.get_type_display()}"

    def send_notice(self):
        """
        🚀 Send notice email to related students
        """
        students = []

        if self.type == "Bus" and self.bus:
            students = Student.objects.filter(assigned_bus=self.bus)

        elif self.type == "Route" and self.route:
            students = Student.objects.filter(route=self.route)

        elif self.type == "All":
            students = Student.objects.all()

        email_list = [student.email for student in students if student.email]

        if email_list:
            send_mail(
                subject="🚍 Important Transport Notice 🚍",
                message=self.message,
                from_email="universityitm698@gmail.com",
                recipient_list=email_list,
                fail_silently=True,
            )

class Feedback(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback - Bus {self.bus.identifier_number if self.bus else 'Unknown'}"

