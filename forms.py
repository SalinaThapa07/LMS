

from django import forms
from .models import Teacher
from django.contrib.auth.forms import UserCreationForm

class TeacherSignupForm(forms.ModelForm):
    DEPARTMENT_CHOICES=[
        ('BIM','BIM'),
        ('BCA','BCA'),
        ('CSIT','CSIT'),
    ]
    department=forms.ChoiceField(choices=DEPARTMENT_CHOICES,required=True)
    password = forms.CharField(widget=forms.PasswordInput, min_length=6)

    class Meta:
        model = Teacher
        fields = ['username', 'email', 'first_name', 'last_name', 'department', 'teacher_id', 'password']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None 
        
'''from django import forms
from django.core.exceptions import ValidationError
from .models import Teacher
import re

class TeacherSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Teacher
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'profile_picture']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            raise ValidationError("Username must contain only letters and numbers.")
        return username

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not re.match(r'^[a-zA-Z]+$', first_name):
            raise ValidationError("First name must contain only letters.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not re.match(r'^[a-zA-Z]+$', last_name):
            raise ValidationError("Last name must contain only letters.")
        return last_name'''


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['username', 'profile_picture']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This line removes the "Currently: <a href>" text for profile_picture
        self.fields['profile_picture'].widget.template_name = 'widgets/custom_clearable_file_input.html'
        
from .models import Meeting

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['time', 'date', 'venue']

