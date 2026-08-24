from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Настройка отображения пользователей
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('role',)}),
    )

# Настройка отображения профилей
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

# Настройка отображения преподавателей
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('profile', 'hourly_rate')
    search_fields = ('profile__user__first_name', 'profile__user__last_name')

# Настройка отображения студентов
class StudentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'branch', 'format', 'discount')
    list_filter = ('branch', 'format')
    search_fields = ('profile__user__first_name', 'profile__user__last_name')

# Настройка отображения групп
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'teacher', 'lesson_price')
    list_filter = ('branch', 'teacher')
    filter_horizontal = ('students',)

# Настройка отображения занятий
class LessonAdmin(admin.ModelAdmin):
    list_display = ('datetime_start', 'teacher', 'course', 'student', 'status', 'type')
    list_filter = ('status', 'type', 'format', 'branch', 'teacher')
    date_hierarchy = 'datetime_start'

# Настройка отображения посещаемости
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'student', 'status')
    list_filter = ('status',)

# Настройка отображения платежей
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'date', 'purpose')
    list_filter = ('date',)
    date_hierarchy = 'date'

# Настройка отображения расходов
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'date')
    list_filter = ('category', 'date')
    date_hierarchy = 'date'

# Настройка отображения свободных слотов
class TeacherSlotAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'datetime_start', 'datetime_end')
    list_filter = ('teacher',)

# Регистрируем все модели в админке
admin.site.register(User, CustomUserAdmin)
admin.site.register(Branch)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(TeacherSlot, TeacherSlotAdmin)
# ===== Админка для заявок с сайта =====
from .models import BookingRequest

@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "mode", "course", "teacher", "status", "created_at")
    list_filter = ("status", "mode", "branch")
    search_fields = ("full_name", "phone", "email")
