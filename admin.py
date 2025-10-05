from django.contrib import admin
from .models import Teacher, Dept, DepartmentCourse, Schedule, Meeting 


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'department', 'teacher_id')
    search_fields = ('username', 'first_name', 'last_name', 'department', 'teacher_id')


@admin.register(Dept)
class DeptAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(DepartmentCourse)
class DepartmentCourseAdmin(admin.ModelAdmin):
    list_display = ('dept', 'semester', 'course', 'teacher')
    list_filter = ('dept', 'semester')
    search_fields = ('course', 'teacher__first_name', 'teacher__last_name')
    ordering = ('dept', 'semester', 'course')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'teacher', 'dept', 'day', 'start_time', 'end_time', 'room', 'date')
    list_filter = ('dept', 'teacher', 'day', 'room', 'date')
    search_fields = ('course', 'teacher__username', 'teacher__first_name', 'teacher__last_name', 'dept__name')
    date_hierarchy = 'date'


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'venue', 'created_by')
    list_filter = ('date',)
    search_fields = ('venue', 'created_by__username',)
    date_hierarchy = 'date'
    ordering = ('-date', 'time')

from .models import LeaveRequest 


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'date', 'status', 'created_at')
    list_filter = ('status', 'date', 'teacher')
    search_fields = ('teacher__username', 'teacher__first_name', 'teacher__last_name')
    ordering = ('-date',)
