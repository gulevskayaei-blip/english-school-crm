from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from crm.models import User
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError, PermissionDenied
from .models import (
    Branch, Profile, Teacher, Student, Course, Lesson, StudentProgress, 
    Attendance, Payment, Expense, 
    CancellationNotification, Notification, LessonLog, Homework
)
from .serializers import (
    UserSerializer, BranchSerializer, TeacherSerializer,
    StudentSerializer, CourseSerializer, LessonSerializer,
    PaymentSerializer, ExpenseSerializer, AttendanceSerializer, HomeworkSerializer
)
from .permissions import IsAdmin, IsTeacherOrAdmin, IsHomeworkOwner

# ==================== АВТОРИЗАЦИЯ ====================

@api_view(['POST'])
def login(request):
    """Авторизация пользователя"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user:
        token, created = Token.objects.get_or_create(user=user)
        
        # Роль хранится в самом пользователе (User.role)
        role = user.role if hasattr(user, 'role') else 'admin'
        
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'role': role
        })
    else:
        return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """Получение текущего пользователя с данными профиля"""
    role = request.user.role if hasattr(request.user, 'role') else 'admin'

    data = {
        'id': request.user.id,
        'username': request.user.username,
        'role': role
    }

    # Добавляем teacher_id, если пользователь учитель
    if role == 'teacher' and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'teacher'):
        data['teacher_id'] = request.user.profile.teacher.id

    # Если пользователь студент, добавляем профиль и прогресс
    if role == 'student':
        try:
            student = Student.objects.get(profile__user=request.user)
            # Создаем запись прогресса, если её нет
            progress, created = StudentProgress.objects.get_or_create(student=student)
            serializer = StudentSerializer(student)
            data['profile'] = serializer.data
        except Student.DoesNotExist:
            pass

    return Response(data)


# ==================== ОТЧЕТЫ ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_finance_report(request):
    """Финансовый отчет с учетом зарплат преподавателей"""
    period = request.GET.get('period', 'month')
    
    today = timezone.now().date()
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
    elif period == 'month':
        start_date = today.replace(day=1)
    else:
        start_date = today.replace(month=1, day=1)
    
    payments = Payment.objects.filter(date__gte=start_date)
    total_income = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_income = float(total_income)
    
    expenses = Expense.objects.filter(date__gte=start_date)
    total_expenses_regular = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses_regular = float(total_expenses_regular)
    
    completed_lessons = Lesson.objects.filter(
        datetime_start__date__gte=start_date,
        status='completed'
    )
    
    total_teacher_salaries = 0.0
    
    for lesson in completed_lessons:
        if lesson.custom_rate:
            rate = float(lesson.custom_rate)
        elif lesson.teacher:
            rate = float(lesson.teacher.hourly_rate)
        else:
            rate = 0.0
        
        if lesson.datetime_end and lesson.datetime_start:
            duration = (lesson.datetime_end - lesson.datetime_start).total_seconds() / 3600.0
        else:
            duration = 1.0
        
        total_teacher_salaries += rate * duration
    
    total_expenses = total_expenses_regular + total_teacher_salaries
    profit = total_income - total_expenses
    profit_margin = (profit / total_income * 100) if total_income > 0 else 0
    
    return Response({
        'total_income': round(total_income, 2),
        'total_expenses': round(total_expenses, 2),
        'total_expenses_regular': round(total_expenses_regular, 2),
        'total_teacher_salaries': round(total_teacher_salaries, 2),
        'profit': round(profit, 2),
        'profit_margin': round(profit_margin, 2),
        'period': period
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payments_report(request):
    """Отчет по платежам"""
    period = request.GET.get('period', 'month')
    
    today = timezone.now().date()
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
    elif period == 'month':
        start_date = today.replace(day=1)
    else:
        start_date = today.replace(month=1, day=1)
    
    payments = Payment.objects.filter(date__gte=start_date)
    
    result = []
    for payment in payments:
        student_name = 'Неизвестно'
        if payment.student and payment.student.profile:
            student_name = payment.student.profile.user.username
        elif payment.student:
            student_name = str(payment.student)
        
        result.append({
            'id': payment.id,
            'date': payment.date,
            'student_id': payment.student.id if payment.student else None,
            'student_name': student_name,
            'amount': float(payment.amount),
            'payment_method': payment.payment_method,
            'purpose': payment.purpose or '',
            'lessons_paid': payment.lessons_paid
        })
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_debtors_report(request):
    """Отчет по должникам"""
    students = Student.objects.all()
    
    debtors = []
    for student in students:
        payments_total = Payment.objects.filter(student=student).aggregate(total=Sum('amount'))['total'] or 0
        payments_total = float(payments_total)
        
        completed_lessons = Lesson.objects.filter(
            student=student,
            status='completed'
        )
        
        lessons_cost = 0.0
        for lesson in completed_lessons:
            if lesson.course:
                price = float(lesson.course.lesson_price)
            else:
                price = 0.0
            lessons_cost += price
        
        debt = lessons_cost - payments_total
        
        if debt > 0:
            last_payment = Payment.objects.filter(student=student).order_by('-date').first()
            student_name = 'Неизвестно'
            if student.profile:
                student_name = student.profile.user.username
            
            debtors.append({
                'student_id': student.id,
                'student_name': student_name,
                'debt': round(debt, 2),
                'last_payment_date': last_payment.date if last_payment else None,
                'last_payment_amount': float(last_payment.amount) if last_payment else 0
            })
    
    return Response(debtors)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teacher_salaries_report(request):
    """Отчет по зарплатам преподавателей"""
    period = request.GET.get('period', 'month')
    
    today = timezone.now().date()
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
    elif period == 'month':
        start_date = today.replace(day=1)
    else:
        start_date = today.replace(month=1, day=1)
    
    lessons = Lesson.objects.filter(
        datetime_start__date__gte=start_date,
        status='completed'
    )
    
    teacher_salaries = {}
    for lesson in lessons:
        if not lesson.teacher:
            continue
        
        teacher_id = lesson.teacher.id
        teacher_name = 'Неизвестно'
        if lesson.teacher.profile:
            teacher_name = lesson.teacher.profile.user.username
        
        if lesson.custom_rate:
            rate = float(lesson.custom_rate)
        else:
            rate = float(lesson.teacher.hourly_rate)
        
        if lesson.datetime_end and lesson.datetime_start:
            duration = (lesson.datetime_end - lesson.datetime_start).total_seconds() / 3600.0
        else:
            duration = 1.0
        
        salary = rate * duration
        
        if teacher_id not in teacher_salaries:
            teacher_salaries[teacher_id] = {
                'teacher_id': teacher_id,
                'teacher_name': teacher_name,
                'hours': 0,
                'hourly_rate': rate,
                'amount': 0
            }
        
        teacher_salaries[teacher_id]['hours'] += duration
        teacher_salaries[teacher_id]['amount'] += salary
    
    total_hours = sum(t['hours'] for t in teacher_salaries.values())
    total_salary = sum(t['amount'] for t in teacher_salaries.values())
    
    return Response({
        'total_hours': round(total_hours, 2),
        'total_salary': round(total_salary, 2),
        'teachers': list(teacher_salaries.values())
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teachers_list_with_salary(request):
    """Список преподавателей с зарплатой за текущий месяц"""
    teachers = Teacher.objects.filter(is_active=True)
    
    today = timezone.now().date()
    start_date = today.replace(day=1)
    
    result = []
    for teacher in teachers:
        actual_lessons = Lesson.objects.filter(
            teacher=teacher,
            status='completed',
            datetime_start__date__gte=start_date
        )
        
        actual_hours = 0.0
        actual_salary = 0.0
        
        for lesson in actual_lessons:
            if lesson.custom_rate:
                rate = float(lesson.custom_rate)
            else:
                rate = float(teacher.hourly_rate)
            
            if lesson.datetime_end and lesson.datetime_start:
                duration = (lesson.datetime_end - lesson.datetime_start).total_seconds() / 3600.0
            else:
                duration = 1.0
            
            actual_hours += duration
            actual_salary += rate * duration
        
        forecast_lessons = Lesson.objects.filter(
            teacher=teacher,
            status='scheduled',
            datetime_start__date__gte=start_date
        )
        
        forecast_hours = 0.0
        forecast_salary = 0.0
        
        for lesson in forecast_lessons:
            if lesson.custom_rate:
                rate = float(lesson.custom_rate)
            else:
                rate = float(teacher.hourly_rate)
            
            if lesson.datetime_end and lesson.datetime_start:
                duration = (lesson.datetime_end - lesson.datetime_start).total_seconds() / 3600.0
            else:
                duration = 1.0
            
            forecast_hours += duration
            forecast_salary += rate * duration
        
        teacher_name = 'Неизвестно'
        if teacher.profile:
            teacher_name = teacher.profile.user.username
        
        result.append({
            'id': teacher.id,
            'name': teacher_name,
            'hourly_rate': float(teacher.hourly_rate),
            'actual_hours': round(actual_hours, 2),
            'actual_salary': round(actual_salary, 2),
            'forecast_hours': round(forecast_hours, 2),
            'forecast_salary': round(forecast_salary, 2),
            'difference_salary': round(forecast_salary - actual_salary, 2),
            'is_active': teacher.is_active,
            'phone': teacher.phone or '',
            'email': teacher.email or '',
            'hire_date': teacher.hire_date,
            'bank_account': teacher.bank_account or ''
        })
    
    return Response(result)


@api_view(['GET', 'PUT'])
@permission_classes([IsAdmin])
def teacher_detail(request, pk):
    """Детальная информация о преподавателе и редактирование"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'GET':
        teacher_name = 'Неизвестно'
        if teacher.profile:
            teacher_name = teacher.profile.user.username
        
        data = {
            'id': teacher.id,
            'name': teacher_name,
            'hourly_rate': float(teacher.hourly_rate),
            'phone': teacher.phone or '',
            'email': teacher.email or '',
            'hire_date': teacher.hire_date,
            'is_active': teacher.is_active,
            'bank_account': teacher.bank_account or ''
        }
        return Response(data)
    
    elif request.method == 'PUT':
        if 'hourly_rate' in request.data:
            teacher.hourly_rate = request.data['hourly_rate']
        if 'phone' in request.data:
            teacher.phone = request.data['phone']
        if 'email' in request.data:
            teacher.email = request.data['email']
        if 'hire_date' in request.data:
            teacher.hire_date = request.data['hire_date']
        if 'is_active' in request.data:
            teacher.is_active = request.data['is_active']
        if 'bank_account' in request.data:
            teacher.bank_account = request.data['bank_account']
        
        teacher.save()
        
        return Response({'message': 'Данные сохранены'})


# ==================== VIEWSETS ====================

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        role = user.role if hasattr(user, 'role') else 'admin'

        if role == 'admin':
            return Attendance.objects.all()
        elif role == 'teacher':
            teacher = Teacher.objects.get(profile__user=user)
            return Attendance.objects.filter(lesson__teacher=teacher)
        else:
            student = Student.objects.get(profile__user=user)
            return Attendance.objects.filter(student=student)


    def perform_create(self, serializer):
        user = self.request.user
        role = user.role if hasattr(user, 'role') else 'admin'
        if role == 'teacher':
            teacher = Teacher.objects.get(profile__user=user)
            lesson = serializer.validated_data.get('lesson')
            if lesson.teacher != teacher:
                raise PermissionDenied("Вы можете отмечать посещаемость только своих занятий.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        role = user.role if hasattr(user, 'role') else 'admin'
        if role == 'teacher':
            teacher = Teacher.objects.get(profile__user=user)
            if self.get_object().lesson.teacher != teacher:
                raise PermissionDenied("Вы можете изменять посещаемость только своих занятий.")
        serializer.save()

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        role = user.role if hasattr(user, 'role') else 'admin'
        
        if role == 'admin':
            return Lesson.objects.all()
        elif role == 'teacher':
            teacher = Teacher.objects.get(profile__user=user)
            return Lesson.objects.filter(teacher=teacher)
        else:
            student = Student.objects.get(profile__user=user)
            return Lesson.objects.filter(student=student)
    
    def perform_create(self, serializer):
        """Создание занятия с валидацией и логированием"""
        try:
            lesson = serializer.save()
            # Логируем создание
            LessonLog.objects.create(
                lesson=lesson,
                user=self.request.user,
                action='create',
                new_data=serializer.data
            )
        except ValidationError as e:
            raise DRFValidationError({'detail': str(e)})
    
    def perform_update(self, serializer):
        """Обновление занятия с валидацией и логированием"""
        try:
            old_lesson = self.get_object()
            old_data = LessonSerializer(old_lesson).data
            lesson = serializer.save()
            new_data = LessonSerializer(lesson).data
            
            # Определяем измененные поля
            changed_fields = {}
            for key in old_data:
                if key in new_data and old_data[key] != new_data[key]:
                    changed_fields[key] = {'old': old_data[key], 'new': new_data[key]}
            
            # Логируем обновление
            LessonLog.objects.create(
                lesson=lesson,
                user=self.request.user,
                action='update',
                old_data=old_data,
                new_data=new_data,
                changed_fields=changed_fields if changed_fields else None
            )

            # Создаём уведомление для студента при подтверждении заявки
            old_status = old_data.get('status')
            new_status = new_data.get('status')
            if old_status == 'pending' and new_status == 'scheduled' and lesson.student:
                from django.utils import timezone
                lesson_time = lesson.datetime_start.strftime('%d.%m.%Y %H:%M') if lesson.datetime_start else ''
                Notification.objects.create(
                    student=lesson.student,
                    message=f'Ваша заявка на занятие подтверждена! Занятие назначено на {lesson_time}.',
                    type='schedule',
                    sent_by=self.request.user
                )
        except ValidationError as e:
            raise DRFValidationError({'detail': str(e)})
    
    def perform_destroy(self, instance):
        """Удаление занятия с логированием"""
        # Логируем удаление
        LessonLog.objects.create(
            lesson=instance,
            user=self.request.user,
            action='delete',
            old_data=LessonSerializer(instance).data
        )
        instance.delete()
    
    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        """Отметить занятие как проведенное"""
        lesson = self.get_object()
        old_status = lesson.status
        lesson.status = 'completed'
        
        try:
            lesson.save()
            
            # Логируем смену статуса
            LessonLog.objects.create(
                lesson=lesson,
                user=request.user,
                action='status_change',
                changed_fields={'status': {'old': old_status, 'new': 'completed'}}
            )
            
            return Response({'status': 'completed', 'message': 'Занятие отмечено как проведенное'})
        except ValidationError as e:
            raise DRFValidationError({'detail': str(e)})


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_expense_categories(request):
    """Список категорий расходов"""
    default_categories = ['Аренда', 'Зарплата', 'Коммунальные услуги', 'Канцелярия', 
                          'Учебные материалы', 'Реклама', 'Налоги', 'Обслуживание', 'Другое']
    return Response(default_categories)


# ==================== МОИ ЗАНЯТИЯ И ПЛАТЕЖИ ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teachers_for_booking(request):
    """Список преподавателей для записи (доступен всем авторизованным)"""
    try:
        teachers = Teacher.objects.select_related('profile__user').all()
        result = []
        for t in teachers:
            user = t.profile.user if hasattr(t, 'profile') and t.profile else None
            name = user.get_full_name() or user.username if user else f'Преподаватель {t.id}'
            result.append({
                'id': t.id,
                'name': name,
                'username': user.username if user else None
            })
        return JsonResponse(result, safe=False)
    except Exception:
        return JsonResponse([], safe=False)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_bookings(request):
    """Список заявок на запись (статус pending) для админа"""
    try:
        user = request.user
        if not user or not user.is_authenticated:
            return JsonResponse([], safe=False)
        role = getattr(user, 'role', 'student')
        if role != 'admin':
            return JsonResponse([], safe=False)

        lessons = Lesson.objects.filter(status='pending').select_related(
            'student__profile__user', 'teacher__profile__user'
        ).order_by('-datetime_start')

        result = []
        for lesson in lessons:
            student_user = lesson.student.profile.user if lesson.student and lesson.student.profile else None
            teacher_user = lesson.teacher.profile.user if lesson.teacher and lesson.teacher.profile else None
            duration_minutes = int((lesson.datetime_end - lesson.datetime_start).total_seconds() / 60) if lesson.datetime_end and lesson.datetime_start else 60
            result.append({
                'id': lesson.id,
                'student_name': student_user.get_full_name() or student_user.username if student_user else 'Неизвестно',
                'teacher_name': teacher_user.get_full_name() or teacher_user.username if teacher_user else 'Неизвестно',
                'datetime_start': lesson.datetime_start.isoformat() if lesson.datetime_start else None,
                'duration': duration_minutes,
                'created_at': lesson.datetime_start.isoformat() if lesson.datetime_start else None,
            })
        return JsonResponse(result, safe=False)
    except Exception:
        return JsonResponse([], safe=False)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cancellation_notifications(request):
    """Уведомления об отменах занятий"""
    try:
        from crm.models import CancellationNotification
        notifs = CancellationNotification.objects.select_related(
            'lesson__student__profile__user', 'user'
        ).filter(user=request.user).order_by('-created_at')[:20]
        result = []
        for n in notifs:
            lesson = n.lesson
            student_user = None
            if lesson and lesson.student and lesson.student.profile:
                student_user = lesson.student.profile.user
            result.append({
                'id': n.id,
                'student_name': student_user.get_full_name() or student_user.username if student_user else 'Неизвестно',
                'datetime_start': lesson.datetime_start.isoformat() if lesson and lesson.datetime_start else None,
                'cancellation_time': n.created_at.isoformat() if n.created_at else None,
                'cancellation_reason': lesson.cancellation_reason if lesson and lesson.cancellation_reason else '',
                'is_penalty_applied': lesson.is_penalty_applied if lesson and hasattr(lesson, 'is_penalty_applied') else False,
                'read': n.is_read,
            })
        return Response(result)
    except Exception:
        return Response([])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_lessons(request):
    """Занятия текущего пользователя"""
    user = request.user
    role = user.role if hasattr(user, 'role') else 'admin'
    
    if role == 'student':
        student = Student.objects.get(profile__user=user)
        lessons = Lesson.objects.filter(student=student)
    elif role == 'teacher':
        teacher = Teacher.objects.get(profile__user=user)
        lessons = Lesson.objects.filter(teacher=teacher)
    else:
        lessons = Lesson.objects.all()
    
    serializer = LessonSerializer(lessons, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_payments(request):
    """Платежи текущего студента"""
    user = request.user
    role = user.role if hasattr(user, 'role') else 'admin'
    
    if role != 'student':
        return Response([], status=status.HTTP_200_OK)
    
    student = Student.objects.get(profile__user=user)
    payments = Payment.objects.filter(student=student)
    
    result = []
    for payment in payments:
        result.append({
            'id': payment.id,
            'date': payment.date,
            'amount': float(payment.amount),
            'payment_method': payment.payment_method,
            'purpose': payment.purpose or '',
            'lessons_paid': payment.lessons_paid
        })
    
    return Response(result)
   
# ==================== ПОСЕЩАЕМОСТЬ ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance(request):
    """Получение посещаемости ученика по месяцам"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    user = request.user
    
    if user.role != 'student':
        return Response({'error': 'Только для студентов'}, status=403)
    
    try:
        student = Student.objects.get(profile__user=user)
    except Student.DoesNotExist:
        return Response({'error': 'Студент не найден'}, status=404)
    
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    lessons = Lesson.objects.filter(
        student=student,
        datetime_start__year=year,
        datetime_start__month=month
    ).order_by('datetime_start')
    
    status_labels = dict(Lesson.STATUS_CHOICES)
    
    data = {
        'year': year,
        'month': month,
        'lessons': [],
        'statistics': {
            'total': 0,
            'completed': 0,
            'paid': 0,
            'missed': 0,
            'cancelled': 0,
            'debt': 0,
            'no_show': 0,
            'postponed': 0,
        }
    }
    
    for lesson in lessons:
        status = lesson.status or 'scheduled'
        
        data['lessons'].append({
            'id': lesson.id,
            'date': lesson.datetime_start.strftime('%Y-%m-%d'),
            'time': lesson.datetime_start.strftime('%H:%M'),
            'course': lesson.course.name if lesson.course else '',
            'teacher': lesson.teacher.profile.user.username if lesson.teacher else '',
            'status': status,
            'status_label': status_labels.get(status, status),
            'price': float(lesson.price) if lesson.price else 0,
            'paid': lesson.paid,
        })
        
        data['statistics']['total'] += 1
        if status == 'completed':
            data['statistics']['completed'] += 1
        elif status == 'paid':
            data['statistics']['paid'] += 1
        elif status == 'missed':
            data['statistics']['missed'] += 1
        elif status == 'cancelled':
            data['statistics']['cancelled'] += 1
        elif status == 'debt':
            data['statistics']['debt'] += 1
        elif status == 'no_show':
            data['statistics']['no_show'] += 1
        elif status == 'postponed':
            data['statistics']['postponed'] += 1
    
    return Response(data)


# ==================== ЗАПИСЬ НА УРОКИ (СТУДЕНТ) ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_slots(request):
    """Получение свободных слотов для записи"""
    teacher_id = request.query_params.get('teacher_id')
    date_str = request.query_params.get('date')  # YYYY-MM-DD
    
    if not teacher_id or not date_str:
        return Response({'error': 'Необходимы teacher_id и date'}, status=400)
    
    try:
        from datetime import datetime, timedelta
        from django.utils import timezone
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        day_start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))
        
        # Получаем все уроки преподавателя в этот день
        existing_lessons = Lesson.objects.filter(
            teacher_id=teacher_id,
            datetime_start__range=(day_start, day_end),
            status__in=['scheduled', 'pending']
        ).order_by('datetime_start')
        
        # Генерируем слоты с 9:00 до 21:00 с шагом 60 минут
        slots = []
        current_time = timezone.make_aware(datetime.combine(target_date, datetime.strptime('09:00', '%H:%M').time()))
        end_time = timezone.make_aware(datetime.combine(target_date, datetime.strptime('21:00', '%H:%M').time()))
        
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=60)
            # Проверяем, не пересекается ли слот с существующими уроками
            is_busy = any(
                lesson.datetime_start < slot_end and 
                lesson.datetime_start + timedelta(minutes=getattr(lesson, 'duration', 60)) > current_time
                for lesson in existing_lessons
            )
            
            if not is_busy:
                slots.append({
                    'start': current_time.isoformat(),
                    'end': slot_end.isoformat(),
                    'available': True
                })
            
            current_time += timedelta(minutes=60)
        
        return Response(slots)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_lesson(request):
    """Запись студента на урок (создание заявки со статусом pending)"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    student_user = request.user
    
    try:
        student = Student.objects.get(profile__user=student_user)
    except Student.DoesNotExist:
        return Response({'error': 'Профиль студента не найден'}, status=404)
    
    teacher_id = request.data.get('teacher_id')
    datetime_start = request.data.get('datetime_start')
    duration = int(request.data.get('duration', 60))
    
    if not teacher_id or not datetime_start:
        return Response({'error': 'Необходимы teacher_id и datetime_start'}, status=400)
    
    try:
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return Response({'error': 'Преподаватель не найден'}, status=404)
    
    # Парсим дату с учётом часового пояса
    start_dt = datetime.fromisoformat(datetime_start.replace('Z', '+00:00'))
    if timezone.is_naive(start_dt):
        start_dt = timezone.make_aware(start_dt)
    end_dt = start_dt + timedelta(minutes=duration)
    
    # Проверяем доступность слота
    conflicting = Lesson.objects.filter(
        teacher=teacher,
        datetime_start__lt=end_dt,
        datetime_end__gt=start_dt,
        status__in=['scheduled', 'pending']
    ).exists()
    
    if conflicting:
        return Response({'error': 'Слот уже занят или ожидает подтверждения'}, status=409)
    
    # Получаем филиал преподавателя (или первый доступный)
    branch = teacher.branch if hasattr(teacher, 'branch') else Branch.objects.first()
    
    # Создаём урок со статусом pending
    lesson = Lesson.objects.create(
        student=student,
        teacher=teacher,
        datetime_start=start_dt,
        datetime_end=end_dt,
        status='pending',
        type='individual',
        format='online',
        branch=branch
    )
    
    serializer = LessonSerializer(lesson)
    return Response(serializer.data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_notifications(request):
    """Уведомления текущего студента"""
    user = request.user
    role = getattr(user, 'role', 'student')
    if role != 'student':
        return Response([])
    try:
        student = Student.objects.get(profile__user=user)
    except Student.DoesNotExist:
        return Response([])

    notifs = Notification.objects.filter(student=student, is_read=False)
    result = []
    for n in notifs:
        result.append({
            'id': n.id,
            'message': n.message,
            'type': n.type,
            'created_at': n.created_at.isoformat() if n.created_at else None,
        })
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """Отметить уведомление как прочитанное"""
    user = request.user
    role = getattr(user, 'role', 'student')
    if role != 'student':
        return Response({'error': 'Доступ запрещён'}, status=403)
    try:
        student = Student.objects.get(profile__user=user)
        notif = Notification.objects.get(pk=pk, student=student)
        notif.is_read = True
        notif.save()
        return Response({'status': 'ok'})
    except (Student.DoesNotExist, Notification.DoesNotExist):
        return Response({'error': 'Уведомление не найдено'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_lesson(request, pk):
    """Отмена занятия студентом (не менее чем за 2 часа до начала)"""
    from django.utils import timezone
    from datetime import timedelta

    user = request.user
    role = getattr(user, 'role', 'student')
    if role != 'student':
        return Response({'error': 'Доступ запрещён'}, status=403)

    try:
        student = Student.objects.get(profile__user=user)
    except Student.DoesNotExist:
        return Response({'error': 'Профиль студента не найден'}, status=404)

    try:
        lesson = Lesson.objects.get(pk=pk, student=student)
    except Lesson.DoesNotExist:
        return Response({'error': 'Занятие не найдено'}, status=404)

    if lesson.status == 'cancelled':
        return Response({'error': 'Занятие уже отменено'}, status=400)

    # Проверка: нельзя отменить менее чем за 2 часа до начала
    if lesson.datetime_start:
        now = timezone.now()
        if lesson.datetime_start - now < timedelta(hours=2):
            # Применяем штраф, но всё равно отменяем (или не даём отменить)
            lesson.status = 'cancelled'
            lesson.is_penalty_applied = True
            lesson.cancellation_reason = 'Отмена менее чем за 2 часа до начала (подлежит оплате)'
            lesson.save()
            # Уведомления админам и преподавателю
            admins = User.objects.filter(role='admin')
            for admin in admins:
                CancellationNotification.objects.get_or_create(lesson=lesson, user=admin)
            if lesson.teacher and lesson.teacher.profile:
                teacher_user = lesson.teacher.profile.user
                if teacher_user:
                    CancellationNotification.objects.get_or_create(lesson=lesson, user=teacher_user)
            return Response({
                'status': 'cancelled_with_penalty',
                'message': 'Занятие отменено менее чем за 2 часа до начала. Оно подлежит оплате.'
            })

    # Обычная отмена
    lesson.status = 'cancelled'
    lesson.is_penalty_applied = False
    lesson.cancellation_reason = 'Отменено студентом'
    lesson.save()

    # Уведомления админам и преподавателю
    admins = User.objects.filter(role='admin')
    for admin in admins:
        CancellationNotification.objects.get_or_create(lesson=lesson, user=admin)
    if lesson.teacher and lesson.teacher.profile:
        teacher_user = lesson.teacher.profile.user
        if teacher_user:
            CancellationNotification.objects.get_or_create(lesson=lesson, user=teacher_user)

    return Response({'status': 'cancelled', 'message': 'Занятие успешно отменено.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_cancellation_notification_read(request, pk):
    """Отметить уведомление об отмене как прочитанное"""
    from crm.models import CancellationNotification
    try:
        notif = CancellationNotification.objects.get(pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return Response({'status': 'ok'})
    except CancellationNotification.DoesNotExist:
        return Response({'error': 'Уведомление не найдено'}, status=404)


class HomeworkViewSet(viewsets.ModelViewSet):
    serializer_class = HomeworkSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Разные права для разных действий"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Создавать/редактировать/удалять могут только учителя и админы
            permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
        else:
            # Читать могут все авторизованные (фильтрация в get_queryset)
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        role = user.role if hasattr(user, 'role') else 'admin'
        if role == 'admin':
            return Homework.objects.all()
        elif role == 'teacher':
            teacher = Teacher.objects.get(profile__user=user)
            # Учитель видит только ДЗ, которые он создал для своих учеников
            return Homework.objects.filter(teacher=teacher)
        elif role == 'student':
            student = Student.objects.get(profile__user=user)
            # Студент видит только свои ДЗ
            return Homework.objects.filter(student=student)
        return Homework.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        role = user.role if hasattr(user, 'role') else 'admin'
        
        if role == 'teacher':
            teacher = Teacher.objects.get(profile__user=user)
            student = serializer.validated_data.get('student')
            # Проверка: учитель может создавать ДЗ только для своих учеников
            # Студент должен быть связан с этим учителем через Course
            courses_taught_by_teacher = Course.objects.filter(teacher=teacher)
            is_own_student = any(student in course.students.all() for course in courses_taught_by_teacher)
            if not is_own_student:
                raise DRFValidationError("Вы можете создавать домашние задания только для своих учеников.")
            homework = serializer.save(teacher=teacher)
        elif role == 'admin':
            # Админ может создавать ДЗ для любого студента
            homework = serializer.save()
        else:
            # Студенты не могут создавать ДЗ через этот endpoint
            raise PermissionDenied("Студенты не могут создавать домашние задания.")
        
        # Синхронизация с полями Lesson для отображения на фронтенде ученика
        lesson = homework.lesson
        lesson.homework = f"{homework.title}\n\n{homework.description or ''}".strip()
        if homework.file:
            lesson.homework_file = homework.file
        lesson.homework_status = 'assigned'
        lesson.save()

    def perform_update(self, serializer):
        user = self.request.user
        role = user.role if hasattr(user, 'role') else 'admin'
        homework = self.get_object()
        
        # Проверка прав на обновление
        if role == 'teacher':
            teacher = Teacher.objects.get(profile__user=user)
            if homework.teacher != teacher:
                raise PermissionDenied("Вы можете редактировать только свои домашние задания.")
        elif role == 'student':
            # Студенты не могут редактировать ДЗ через этот endpoint
            raise PermissionDenied("Студенты не могут редактировать домашние задания.")
        
        homework = serializer.save()
        # Синхронизация при редактировании
        lesson = homework.lesson
        lesson.homework = f"{homework.title}\n\n{homework.description or ''}".strip()
        if homework.file:
            lesson.homework_file = homework.file
        lesson.homework_status = 'assigned'
        lesson.save()
