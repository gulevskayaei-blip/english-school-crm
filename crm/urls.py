from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_booking as vb
from .views import (
    BranchViewSet, TeacherViewSet, StudentViewSet, CourseViewSet,
    LessonViewSet, PaymentViewSet, ExpenseViewSet, AttendanceViewSet, HomeworkViewSet,
    login, get_current_user,
    get_finance_report, get_payments_report, get_debtors_report,
    get_teacher_salaries_report, get_teachers_list_with_salary, teacher_detail,
    my_lessons, my_payments, get_expense_categories,
    get_available_slots, book_lesson, get_teachers_for_booking, get_pending_bookings, get_cancellation_notifications, mark_cancellation_notification_read, get_student_notifications, mark_notification_read, cancel_lesson
)

router = DefaultRouter()
router.register(r'branches', BranchViewSet)
router.register(r'teachers', TeacherViewSet)
router.register(r'students', StudentViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'expenses', ExpenseViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'homeworks', HomeworkViewSet, basename='homework')

urlpatterns = [
    path("lessons/available-slots/", get_available_slots, name="available_slots"),
    path("lessons/book/", book_lesson, name="book_lesson"),
    path("teachers/for-booking/", get_teachers_for_booking, name="teachers_for_booking"),
    path("lessons/pending-bookings/", get_pending_bookings, name="pending_bookings"),
    path("cancellation-notifications/", get_cancellation_notifications, name="cancellation_notifications"),
    path("cancellation-notifications/<int:pk>/read/", mark_cancellation_notification_read, name="mark_cancellation_notification_read"),
    path("student-notifications/", get_student_notifications, name="student_notifications"),
    path("student-notifications/<int:pk>/read/", mark_notification_read, name="mark_notification_read"),
    path("lessons/<int:pk>/cancel/", cancel_lesson, name="cancel_lesson"),
    # Auth
    path('auth/login/', login, name='login'),
    path('users/me/', get_current_user, name='current_user'),
    
    # Reports
    path('reports/finance/', get_finance_report, name='finance_report'),
    path('reports/payments/', get_payments_report, name='payments_report'),
    path('reports/debtors/', get_debtors_report, name='debtors_report'),
    path('reports/teacher-salaries/', get_teacher_salaries_report, name='teacher_salaries'),
    path('teachers-list-with-salary/', get_teachers_list_with_salary, name='teachers_with_salary'),
    path('teacher-detail/<int:pk>/', teacher_detail, name='teacher_detail'),
    
    # Expenses
    path('expenses-categories/', get_expense_categories, name='expense_categories'),
    
    # My data
    path('my-lessons/', my_lessons, name='my_lessons'),
    path('my-payments/', my_payments, name='my_payments'),
    # Router
    # Public booking API
    path('booking/branches/', vb.BranchListView.as_view()),
    path('booking/courses/',  vb.CourseBookingListView.as_view()),
    path('booking/teachers/', vb.TeacherBookingListView.as_view()),
    path('booking/request/',  vb.BookingRequestCreateView.as_view()),
    path('booking/schedule/', vb.PublicScheduleView.as_view()),
    path('booking/teacher-slots/', vb.TeacherFreeSlotsView.as_view()),

    # Router
    path('', include(router.urls)),
]
