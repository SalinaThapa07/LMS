from django.db import models
from django.contrib.auth.models import AbstractUser
import random

class Teacher(AbstractUser): 
    department = models.CharField(max_length=100) 
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    teacher_id = models.CharField(max_length=3, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.teacher_id:
            while True:
                random_id = f"{random.randint(100, 999)}"
                if not Teacher.objects.filter(teacher_id=random_id).exists():
                    self.teacher_id = random_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Dept(models.Model):
    DEPT_CHOICES = [
        ('BIM', 'Bachelor in Information Management'),
        ('BCA', 'Bachelor of Computer Application'),
        ('CSIT', 'Computer Science and IT'),
    ]
    name = models.CharField(max_length=10, choices=DEPT_CHOICES, unique=True)

    def __str__(self):
        return self.name


class DepartmentCourse(models.Model):
    dept = models.ForeignKey(Dept, on_delete=models.CASCADE, related_name='courses')
    semester = models.PositiveIntegerField()
    course = models.CharField(max_length=100)
    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='department_courses')

    class Meta:
        unique_together = ('dept', 'semester', 'course')

    def __str__(self):
        teacher_name = f"{self.teacher.first_name} {self.teacher.last_name}" if self.teacher else "Unassigned"
        return f"{self.dept.name} - Semester {self.semester} - {self.course} ({teacher_name})"



class Schedule(models.Model):
    course = models.CharField(max_length=100)  # Store course name as plain text
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,  # Deletes schedules when teacher is deleted
        null=True,
        blank=True,
        related_name='schedules'
    )
    dept = models.ForeignKey(Dept, on_delete=models.CASCADE, null=True, blank=True, related_name='schedules')
    day = models.CharField(max_length=20)
    date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)

    def __str__(self):
        return f'{self.course} - {self.day}'







from django.utils import timezone

# models.py
class Meeting(models.Model):
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    venue = models.CharField(max_length=100)

    def __str__(self):
        return f"Meeting at {self.venue} on {self.date} at {self.time}"

from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.timezone import now
from .forms import TeacherSignupForm, TeacherProfileForm
from .models import Teacher, Dept, DepartmentCourse, Schedule, Meeting
from .forms import MeetingForm


def contact(request):
    return render(request, 'contact.html')


def department_page(request):
    return render(request, 'department.html')


@login_required
def department_detail(request, dept_name):
    query = request.GET.get('q', '')
    try:
        department = Dept.objects.get(name=dept_name.upper())
    except Dept.DoesNotExist:
        return HttpResponse("Department not found", status=404)

    dept_courses = DepartmentCourse.objects.filter(dept=department)
    course_semester_map = {dc.course: dc.semester for dc in dept_courses}

    schedules = Schedule.objects.filter(dept=department).select_related('teacher')

    if query:
        schedules = schedules.filter(
            Q(teacher__username__icontains=query) |
            Q(teacher__first_name__icontains=query) |
            Q(teacher__last_name__icontains=query)
        )

    department_data = {}
    for schedule in schedules:
        teacher = schedule.teacher
        course = schedule.course
        semester = course_semester_map.get(course, "N/A")

        if teacher.username not in department_data:
            department_data[teacher.username] = {
                'teacher': teacher.username,
                'courses': [],
            }

        department_data[teacher.username]['courses'].append({
            
            'name': course,
            'semester': semester,
        })

    department_data = [
        {
            'teacher': teacher,
            'courses': data['courses'],
        }
        for teacher, data in department_data.items()
    ]

    return render(request, f'{dept_name.lower()}_department.html', {
        'department_data': department_data,
        'dept_name': dept_name.upper(),
        'query': query
    })


@login_required
def schedule(request):
    query = request.GET.get('q', '')
    schedules = Schedule.objects.select_related('teacher', 'dept').filter(
        Q(teacher__is_superuser=False) | Q(teacher__isnull=True)
    )

    if query:
        schedules = schedules.filter(
            Q(teacher__first_name__icontains=query) |
            Q(teacher__last_name__icontains=query) |
            Q(course__icontains=query) |
            Q(dept__name__icontains=query)
        )

    return render(request, 'schedule.html', {
        'schedules': schedules,
        'query': query,
    })


@login_required
def teacher_list(request):
    # Exclude superusers (e.g., root) from the teacher list
    teachers = Teacher.objects.filter(is_superuser=False)
    return render(request, 'teacher_list.html', {'teachers': teachers})


def signup(request):
    if request.method == 'POST':
        form = TeacherSignupForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.set_password(form.cleaned_data['password'])
            teacher.save()
            messages.success(request, "Signup successful! You can now log in.")
            return redirect('login')
        else:
            messages.error(request, "There was an error in the form. Please try again.")
    else:
        form = TeacherSignupForm()

    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')



from .models import Meeting
from django.utils import timezone

'''@login_required
def index(request):
    teacher = request.user
    schedules = Schedule.objects.filter(teacher=teacher)

    # Auto-delete past meetings
    Meeting.objects.filter(date__lt=timezone.now().date()).delete()

    # Get department-specific upcoming meetings
    upcoming_meetings = Meeting.objects.filter(
        department=teacher.department,
        date__gte=timezone.now().date()
    ).order_by('date', 'time')

    if upcoming_meetings.exists():
        messages.info(request, f"You have an upcoming department meeting at {upcoming_meetings[0].venue} on {upcoming_meetings[0].date}.")

    context = {
        'teacher': teacher,
        'courses': schedules.values_list('course', flat=True).distinct(),
        'schedules': schedules,
        'upcoming_meetings': upcoming_meetings,
    }

    return render(request, 'index.html', context)'''

@login_required
def index(request):
    teacher = request.user

    # Auto-delete old meetings
    Meeting.objects.filter(date__lt=now().date()).delete()

    # Meetings for the teacher's department
    upcoming_meetings = Meeting.objects.filter(
        created_by__department=teacher.department,
        date__gte=now().date()
    ).order_by('date', 'time')

    # Show reminder if a meeting is scheduled today
    today_meetings = upcoming_meetings.filter(date=now().date())
    if today_meetings.exists():
        next_meeting = today_meetings.first()
        messages.info(request, f"Reminder: Meeting today at {next_meeting.time} in {next_meeting.venue}")

    context = {
        'upcoming_meetings': upcoming_meetings
    }
    return render(request, 'index.html', context)




'''@login_required
def index(request):
    teacher = request.user
    schedules = Schedule.objects.filter(teacher=teacher)

    context = {
        'teacher': teacher,
        'courses': schedules.values_list('course', flat=True).distinct(),
        'schedules': schedules,
    }

    return render(request, 'index.html', context)'''


@login_required
def report(request):
    return render(request, 'report.html')


@login_required
def profile_view(request):
    teacher = request.user

    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = TeacherProfileForm(instance=teacher)

    return render(request, 'profile.html', {
        'form': form,
        'teacher': teacher,
    })




@login_required
def create_meeting(request):
    teacher = request.user

    # Auto-delete past meetings
    Meeting.objects.filter(date__lt=now().date()).delete()

    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        venue = request.POST.get('venue')

        if date and time and venue:
            Meeting.objects.create(
                created_by=teacher,
                date=date,
                time=time,
                venue=venue
            )
            messages.success(request, 'Meeting created successfully.')
            return redirect('create_meeting')
        else:
            messages.error(request, "Please fill in all fields.")

    # Filter meetings visible to the same department
    meetings = Meeting.objects.filter(
        created_by__department=teacher.department,
        date__gte=now().date()
    ).order_by('date', 'time')

    return render(request, 'home/meeting.html', {
        'meetings': meetings,
    })


# home/models.py

# models.py

from django.utils import timezone

class LeaveRequest(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'), 
        ('approved', 'Approved'), 
        ('rejected', 'Rejected')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.teacher.username} - {self.date} - {self.status}"

    @property
    def is_today(self):
        return self.date == timezone.now().date()
