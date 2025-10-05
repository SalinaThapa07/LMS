from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.timezone import now
from .forms import TeacherSignupForm, TeacherProfileForm
from .models import Teacher, Dept, DepartmentCourse, Schedule, Meeting, LeaveRequest
from .forms import MeetingForm
from django.core.mail import send_mass_mail

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

    # Only use select_related on foreign key fields (teacher is okay)
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

        if not teacher:
            continue

        if teacher.username not in department_data:
            department_data[teacher.username] = {
                'teacher': teacher,
                'courses': [],
            }

        department_data[teacher.username]['courses'].append({
            'name': course.name if hasattr(course, 'name') else str(course),
            'semester': semester,
        })

    department_data = list(department_data.values())

    return render(request, f'{dept_name.lower()}_department.html', {
        'department_data': department_data,
        'dept_name': dept_name.upper(),
        'query': query
    })





'''@login_required
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
                'teacher': teacher,
                'courses': [],
            }

        department_data[teacher.username]['courses'].append({
            
            'name': course,
            'semester': semester,
        })

    department_data = [
        {
            'teacher':  data['teacher'],
            'courses': data['courses'],
        }
        for teacher, data in department_data.items()
    ]

    return render(request, f'{dept_name.lower()}_department.html', {
        'department_data': department_data,
        'dept_name': dept_name.upper(),
        'query': query
    })'''

# views.py

from .models import Schedule, LeaveRequest
from django.utils.timezone import now

@login_required
def schedule(request):
    query = request.GET.get('q', '')

    # Auto-delete leave requests after their date
    LeaveRequest.objects.filter(date__lt=now().date()).delete()

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

    # Get approved leave requests for today
    leave_today_teachers = LeaveRequest.objects.filter(
        date=now().date(),
        status='approved'
    ).values_list('teacher_id', flat=True)

    return render(request, 'schedule.html', {
        'schedules': schedules,
        'leave_today_teachers': leave_today_teachers,
        'query': query,
    })

'''from .models import LeaveRequest

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

    leave_dates = LeaveRequest.objects.values_list('teacher__id', 'date')

    leave_map = {
        f"{leave.teacher.id}_{leave.date}": True
        for leave in LeaveRequest.objects.filter(status='approved')
    }

    context = {
        'schedules': schedules,
        'leave_map': leave_map,  # ✅ PASS leave_map TO TEMPLATE
    }

    return render(request, 'schedule.html', context)'''


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
from django.utils.timezone import now

@login_required
def index(request):
    teacher = request.user

    # Prevent superuser from accessing the dashboard
    if teacher.is_superuser:
        messages.error(request, "Superusers are not allowed to log in.")
        return redirect('login')

    # Auto-delete past meetings
    Meeting.objects.filter(date__lt=now().date()).delete()

    # Get schedules and courses for the logged-in teacher
    schedules = Schedule.objects.filter(teacher=teacher)
    courses = schedules.values_list('course', flat=True).distinct()

    # Upcoming meetings in same department (via created_by -> department)
    upcoming_meetings = Meeting.objects.filter(
        created_by__department=teacher.department,
        date__gte=now().date()
    ).order_by('date', 'time')

    # Today's meeting
    today_meeting = upcoming_meetings.filter(date=now().date()).first()
    if today_meeting:
        messages.info(
            request,
            f"You have a department meeting today at {today_meeting.venue} at {today_meeting.time}."
        )

    context = {
        'teacher': teacher,
        'courses': courses,
        'schedules': schedules,
        'upcoming_meetings': upcoming_meetings,
        'today_meeting': today_meeting,
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
            meeting = Meeting.objects.create(
                created_by=teacher,
                date=date,
                time=time,
                venue=venue
            )

            # Get all teachers in the same department
            dept_teachers = Teacher.objects.filter(department=teacher.department, is_superuser=False)

            # Prepare subject and message
            subject = f"Department Meeting Scheduled on {date}"
            message = (
                f"Dear Lecturer,\n\n"
                f"A department meeting has been scheduled.\n\n"
                f"📅 Date: {date}\n"
                f"🕒 Time: {time}\n"
                f"📍 Venue: {venue}\n"
                f"👤 Scheduled by: {teacher.get_full_name() or teacher.username}\n\n"
                f"Please be punctual.\n\nRegards,\nAdmin"
            )

            from_email = None  # Uses DEFAULT_FROM_EMAIL
            recipient_list = [t.email for t in dept_teachers if t.email]

            # Send to all valid emails
            if recipient_list:
                send_mass_mail([
                    (subject, message, from_email, recipient_list)
                ], fail_silently=False)

            messages.success(request, 'Meeting created and email reminders sent.')
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






'''@login_required
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
    })'''
@login_required
def leave_request(request):
    teacher = request.user

    if request.method == 'POST':
        date = request.POST.get('date')
        reason = request.POST.get('reason')

        if date:
            LeaveRequest.objects.create(teacher=teacher, date=date, reason=reason)
            messages.success(request, "Leave request submitted successfully.")
        else:
            messages.error(request, "Please select a date.")

        return redirect('leave_request')

    leaves = LeaveRequest.objects.filter(teacher=teacher).order_by('-date')
    return render(request, 'leave_request.html', {'leaves': leaves})

from django.contrib.auth import logout

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('login')  # Or homepage


   
def logout_view(request):
    logout(request)
    return redirect('login')  # Make sure 'login' is the name of your login URL
