from rest_framework import generics, permissions
from .models import Branch, Course, Teacher, BookingRequest
from .serializers import (
    BranchSerializer, CourseBookingSerializer,
    TeacherBookingSerializer, BookingRequestCreateSerializer,
)


class BranchListView(generics.ListAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.AllowAny]


class CourseBookingListView(generics.ListAPIView):
    serializer_class = CourseBookingSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Course.objects.filter(is_open_for_booking=True).select_related("teacher", "branch")
        branch = self.request.query_params.get("branch")
        if branch:
            qs = qs.filter(branch_id=branch)
        return [c for c in qs if c.has_free_slots]


class TeacherBookingListView(generics.ListAPIView):
    serializer_class = TeacherBookingSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Teacher.objects.all()


class BookingRequestCreateView(generics.CreateAPIView):
    queryset = BookingRequest.objects.all()
    serializer_class = BookingRequestCreateSerializer
    permission_classes = [permissions.AllowAny]
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from .models import Lesson, Course, Teacher, Branch
from .serializers import CourseBookingSerializer


class PublicScheduleView(APIView):
    """
    Публичное расписание занятий на неделю
    GET /api/booking/schedule/?branch=ID&teacher=ID&mode=group
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())  # Понедельник
        week_end = week_start + timedelta(days=6)  # Воскресенье

        mode = request.query_params.get('mode', 'group')
        branch_id = request.query_params.get('branch')
        teacher_id = request.query_params.get('teacher')

        lessons = Lesson.objects.filter(
            datetime_start__date__gte=week_start,
            datetime_start__date__lte=week_end,
            status='scheduled'
        ).select_related('course', 'teacher', 'branch', 'course__teacher')

        if branch_id:
            lessons = lessons.filter(branch_id=branch_id)
        if teacher_id:
            lessons = lessons.filter(teacher_id=teacher_id)
        if mode == 'group':
            lessons = lessons.filter(type='group')
        elif mode == 'individual':
            lessons = lessons.filter(type='individual')

        result = []
        for lesson in lessons:
            lesson_data = {
                "id": lesson.id,
                "date": lesson.datetime_start.date().isoformat(),
                "time_start": lesson.datetime_start.time().strftime('%H:%M'),
                "time_end": lesson.datetime_end.time().strftime('%H:%M'),
                "day_of_week": lesson.datetime_start.weekday(),  # 0=Пн, 6=Вс
                "teacher_name": str(lesson.teacher),
                "teacher_id": lesson.teacher_id,
                "branch_name": str(lesson.branch),
                "branch_id": lesson.branch_id,
                "format": lesson.format,
                "type": lesson.type,
            }
            if lesson.course:
                lesson_data["course_name"] = lesson.course.name
                lesson_data["course_id"] = lesson.course.id
                lesson_data["free_slots"] = lesson.course.free_slots
                lesson_data["has_free_slots"] = lesson.course.has_free_slots
                lesson_data["capacity"] = lesson.course.capacity
                lesson_data["price"] = str(lesson.course.lesson_price)
            if lesson.student:
                lesson_data["student_name"] = str(lesson.student)
            result.append(lesson_data)

        return Response(result)


class TeacherFreeSlotsView(APIView):
    """
    Свободные слоты преподавателя на неделю
    GET /api/booking/teacher-slots/?teacher=ID
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        teacher_id = request.query_params.get('teacher')
        if not teacher_id:
            return Response({"error": "Укажите ID преподавателя"}, status=400)

        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # Получаем слоты преподавателя
        from .models import TeacherSlot
        slots = TeacherSlot.objects.filter(
            teacher_id=teacher_id,
            datetime_start__date__gte=week_start,
            datetime_start__date__lte=week_end
        )

        # Получаем занятые слоты (занятия)
        busy_lessons = Lesson.objects.filter(
            teacher_id=teacher_id,
            datetime_start__date__gte=week_start,
            datetime_start__date__lte=week_end,
            status='scheduled'
        )

        free_slots = []
        for slot in slots:
            free_slots.append({
                "id": slot.id,
                "date": slot.datetime_start.date().isoformat(),
                "time_start": slot.datetime_start.time().strftime('%H:%M'),
                "time_end": slot.datetime_end.time().strftime('%H:%M'),
                "day_of_week": slot.datetime_start.weekday(),
                "is_free": True,
            })

        busy_slots = []
        for lesson in busy_lessons:
            busy_slots.append({
                "id": lesson.id,
                "date": lesson.datetime_start.date().isoformat(),
                "time_start": lesson.datetime_start.time().strftime('%H:%M'),
                "time_end": lesson.datetime_end.time().strftime('%H:%M'),
                "day_of_week": lesson.datetime_start.weekday(),
                "is_free": False,
                "student_name": str(lesson.student) if lesson.student else "Группа",
            })

        return Response({
            "teacher_id": int(teacher_id),
            "free_slots": free_slots,
            "busy_slots": busy_slots,
        })
