from django import forms
from .models import Student, School, Route, Bus, Driver, Notice, Allotment, Stoppage, Feedback
import re


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'roll_number', 'school', 'program', 'fee_amount',
                  'email', 'contact_number', 'route', 'gender', 'stoppage', 'photo']



# ✅ Multiple Seats Form
class MultipleSeatsForm(forms.Form):
    num_seats = forms.IntegerField(label="Number of Seats to Add", min_value=1)


# ✅ Bus Form
class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = ['number']


# ✅ Driver Form
class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'D_license_number', 'contact_number', 'reference_by']


# ✅ Notice Form (For Sending Notices to Students)
class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['type', 'bus', 'route', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['bus'].queryset = Bus.objects.all()
        self.fields['route'].queryset = Route.objects.all()

        # ❌ Default: Hide bus and route unless selected
        self.fields['bus'].required = False
        self.fields['route'].required = False

class AllotmentForm(forms.ModelForm):
    class Meta:
        model = Allotment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "route" in self.data:
            try:
                route_id = int(self.data.get("route"))
                self.fields["stoppages"].queryset = Stoppage.objects.filter(route_id=route_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields["stoppages"].queryset = self.instance.route.stoppages.all()
        else:
            self.fields["stoppages"].queryset = Stoppage.objects.none()


# add a new bus form

from django import forms
from .models import Bus

from django import forms
from .models import Bus

class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = '__all__'
        widgets = {
            'number': forms.TextInput(attrs={
                'required': True,
                'pattern': '^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,3}[0-9]{1,4}$',
                'title': 'Enter a valid bus number (e.g., MP07P0843, DL01AB1234)',
                'placeholder': 'e.g., MP07P0843',
            }),
            'identifier_number': forms.TextInput(attrs={
                'pattern': '[A-Z0-9]{1,10}',
                'placeholder': 'Unique Identifier',
                'title': 'Alphanumeric only (max 10 characters)',
            }),
            'pollution_issue_date': forms.DateInput(attrs={'type': 'date'}),
            'pollution_valid_upto': forms.DateInput(attrs={'type': 'date'}),
            'insurance_issue_date': forms.DateInput(attrs={'type': 'date'}),
            'insurance_valid_upto': forms.DateInput(attrs={'type': 'date'}),
            'tax_issue_date': forms.DateInput(attrs={'type': 'date'}),
            'tax_valid_upto': forms.DateInput(attrs={'type': 'date'}),
            'permit_issue_date': forms.DateInput(attrs={'type': 'date'}),
            'permit_valid_upto': forms.DateInput(attrs={'type': 'date'}),
        }



# add a new allotment model
class AllotmentForm(forms.ModelForm):
    class Meta:
        model = Allotment
        fields = ['bus', 'driver', 'route', 'stoppages']
        widgets = {
            'route': forms.Select(attrs={'id': 'route-select'}),
            'stoppages': forms.CheckboxSelectMultiple(attrs={'id': 'stoppage-checkboxes'})
        }
#add drivers
import re
from django import forms
from .models import Driver

from django.core.exceptions import ValidationError
import re
class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'address', 'D_license_number', 'contact_number', 'reference_by']

    def clean_D_license_number(self):
        license_no = self.cleaned_data.get('D_license_number', '')
        # Validate: only letters and numbers allowed
        if not re.match(r'^[A-Za-z0-9]+$', license_no):
            raise ValidationError("License number can only contain letters and numbers. No spaces or special characters allowed.")
        return license_no

    def clean_contact_number(self):
        contact = self.cleaned_data.get('contact_number', '')
        pattern = r'^[6-9]\d{9}$'  # Valid Indian mobile number format
        if not re.match(pattern, contact):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number starting with 6-9.")
        return contact

#add student
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'roll_number', 'crm_id', 'gender', 'school', 'program',
                  'fee_paid', 'fee_amount', 'email', 'contact_number',
                  'route', 'stoppage', 'assigned_bus', 'assigned_seat', 'photo']

        widgets = {
            'gender': forms.Select(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
            'school': forms.Select(),
            'route': forms.Select(),
            'assigned_bus': forms.Select(),
            'assigned_seat': forms.Select(),
        }


#add routes
class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['name', 'fare']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'styled-input',
                'placeholder': 'Enter Route Name'
            }),
        }
#add stoppage
class StoppageForm(forms.ModelForm):
    class Meta:
        model = Stoppage
        fields = ['name', 'route']


#for notices
class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['type', 'bus', 'route', 'message']

class FeedbackForm(forms.ModelForm):
    bus = forms.ModelChoiceField(
        queryset=Bus.objects.exclude(identifier_number__isnull=True).exclude(identifier_number=''),
        label="Select Bus Identifier",
        empty_label="Select your bus",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Feedback
        fields = ['bus', 'message']

    def __init__(self, *args, **kwargs):
        super(FeedbackForm, self).__init__(*args, **kwargs)
        self.fields['bus'].label_from_instance = lambda obj: obj.identifier_number