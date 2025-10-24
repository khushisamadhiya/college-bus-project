from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from .forms import AllotmentForm
from .models import Bus, Student, Seat, Driver, School, Route, Allotment, Notice, Program, Stoppage, Feedback
import openpyxl
from io import BytesIO

admin.site.register(Feedback)

def export_to_excel(modeladmin, request, queryset):
    model = queryset.model
    meta = model._meta
    field_names = [field.name for field in meta.fields]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = meta.verbose_name_plural.title()
    ws.append(field_names)

    for obj in queryset:
        row = []
        for field in field_names:
            value = getattr(obj, field)
            row.append(str(value) if value is not None else "")
        ws.append(row)

    # ✅ Save workbook to in-memory buffer
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"{meta.model_name}_backup.xlsx"
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response



# ✅ Register Models
admin.site.register(Program)
admin.site.register(Stoppage)

# ✅ School Admin
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name",)
    def save_model(self, request, obj, form, change):
        obj.name = obj.name.strip().upper()
        super().save_model(request, obj, form, change)

# ✅ Route Admin
@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_stoppages', 'fare')
    search_fields = ('name',)
    def get_stoppages(self, obj):
        return ", ".join(stoppage.name for stoppage in obj.stoppages.all())

# ✅ Driver Admin
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'bus_assigned')
    actions = [export_to_excel]

    def bus_assigned(self, obj):
        allotment = Allotment.objects.filter(driver=obj).first()
        return allotment.bus.number if allotment else "No Bus Assigned"
    bus_assigned.short_description = "Assigned Bus"

admin.site.register(Driver, DriverAdmin)

# ✅ Bus Admin
class BusAdmin(admin.ModelAdmin):
    list_display = ('number', 'identifier_number', 'get_route', 'pollution_paid', 'insurance_paid', 'tax_paid', 'permit', 'seating_chart_button')
    list_filter = ('pollution_paid', 'insurance_paid', 'tax_paid', 'permit')
    search_fields = ('number', 'identifier_number')
    actions = [export_to_excel]

    def get_route(self, obj):
        allotment = Allotment.objects.filter(bus=obj).first()
        return allotment.route.name if allotment and allotment.route else "No Route"
    get_route.short_description = "Route"
    get_route.admin_order_field = "route"

    def seating_chart_button(self, obj):
        url = reverse('bus_seating_chart', kwargs={'bus_number': obj.number})
        return format_html('<a class="button" href="{}" target="_blank">View Seating Chart</a>', url)
    seating_chart_button.short_description = "Seating Chart"

admin.site.register(Bus, BusAdmin)

# ✅ Student Form
class StudentForm(forms.ModelForm):
    program = forms.ChoiceField(label="Select Program", required=False)
    stoppage = forms.ChoiceField(label="Select Stoppage", required=False)

    class Meta:
        model = Student
        fields = ['name', 'roll_number', 'crm_id', 'school', 'program', 'fee_paid', 'fee_amount',
                  'email', 'contact_number', 'route', 'gender', 'assigned_bus', 'assigned_seat', 'stoppage', 'photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.school:
            self.fields['program'].choices = [(program.name, program.name) for program in self.instance.school.programs.all()]
        else:
            self.fields['program'].choices = []
        if self.instance and self.instance.route and self.instance.route.stoppages.exists():
            self.fields['stoppage'].choices = [(stop.id, stop.name) for stop in self.instance.route.stoppages.all()]
        else:
            self.fields['stoppage'].choices = []

# ✅ Student Admin
class StudentAdmin(admin.ModelAdmin):
    form = StudentForm
    list_display = ('photo_preview', 'name', 'roll_number', 'crm_id', 'school', 'program', 'fee_paid',
                    'fee_amount', 'email', 'contact_number', 'gender', 'route', 'stoppage', 'allot_bus_link')
    list_filter = ('route', 'school', 'program', 'fee_paid', 'gender')
    search_fields = ('roll_number', 'crm_id')
    actions = [export_to_excel]

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;"/>', obj.photo.url)
        return "No Photo"
    photo_preview.short_description = "Photo"

    def allot_bus_link(self, obj):
        url = reverse('allot_bus', args=[obj.id])
        return format_html('<a href="{}" class="button">Allot Bus</a>', url)
    allot_bus_link.short_description = "Allot Bus"

admin.site.register(Student, StudentAdmin)

# ✅ Seat Admin
class SeatAdminForm(forms.ModelForm):
    seat_count = forms.IntegerField(required=False, help_text="Enter number of seats to create")
    class Meta:
        model = Seat
        fields = ["seat_number", "bus", "student", "seat_count"]
    def save(self, commit=True):
        seat_count = self.cleaned_data.get("seat_count", 1)
        bus = self.cleaned_data.get("bus")
        if seat_count and bus:
            for i in range(1, seat_count + 1):
                Seat.objects.create(seat_number=i, bus=bus)
        return self.instance
    def save_m2m(self):
        pass

class SeatAdmin(admin.ModelAdmin):
    form = SeatAdminForm
    list_display = ("seat_number", "bus", "get_route", "student")
    fields = ["seat_number", "bus", "student", "seat_count"]

    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get("seat_count"):
            return
        super().save_model(request, obj, form, change)

    def get_route(self, obj):
        return obj.get_route()
    get_route.short_description = 'Route'

admin.site.register(Seat, SeatAdmin)

# ✅ Allotment Admin
class AllotmentAdmin(admin.ModelAdmin):
    form = AllotmentForm
    list_display = ("bus", "driver", "route", "assigned_date")
    search_fields = ("bus__number", "driver__name", "route__name")
    filter_horizontal = ("stoppages",)
    actions = [export_to_excel]

    class Media:
        js = ("admin/js/allotment.js",)

admin.site.register(Allotment, AllotmentAdmin)

# ✅ Notice Admin
@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('type', 'bus', 'route', 'created_at')
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if hasattr(obj, 'send_notice'):
            obj.send_notice()
