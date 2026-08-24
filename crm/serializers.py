from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    teacher_id = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'role', 'teacher_id')
    
    def get_teacher_id(self, obj):
        if hasattr(obj, 'profile') and hasattr(obj.profile, 'teacher'):
            return obj.profile.teacher.id
        return None

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = '__all__'

class TeacherSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = Teacher
        fields = '__all__'

class StudentProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProgress
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    progress = StudentProgressSerializer(read_only=True)

    profile = ProfileSerializer(read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Student
        fields = ('id', 'profile', 'parent_name', 'date_of_birth', 'discount', 'branch', 'format', 'branch_name', 'progress')

class CourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.profile.user.get_full_name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'

class LessonSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.profile.user.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    student_name = serializers.CharField(source='student.profile.user.get_full_name', read_only=True)
    substitute_teacher_name = serializers.CharField(source='substitute_teacher.profile.user.get_full_name', read_only=True, default=None)
    
    class Meta:
        model = Lesson
        fields = ['id', 'course', 'student', 'teacher', 'branch', 'datetime_start', 'datetime_end', 
                  'status', 'type', 'format', 'topic', 'homework', 'homework_status', 'homework_audio', 'homework_file', 'homework_comment', 'is_homework_completed', 'comment', 'is_recurring', 
                  'recurring_type', 'recurring_end_date', 'recurring_count', 'recurring_parent_id',
                  'teacher_name', 'course_name', 'student_name',
                  'cancellation_reason', 'cancellation_time', 'is_penalty_applied', 'sick_leave_provided',
                  'custom_rate', 'substitute_teacher', 'substitute_rate', 'substitute_teacher_name']
        read_only_fields = ['id']

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.profile.user.get_full_name', read_only=True)
    lesson_info = serializers.CharField(source='lesson.__str__', read_only=True)
    
    class Meta:
        model = Attendance
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.profile.user.get_full_name', read_only=True)
    payment_method_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = '__all__'
    
    def get_payment_method_display(self, obj):
        methods = {'cash': '💵 Наличные', 'card': '💳 Карта', 'transfer': '🏦 Перевод'}
        return methods.get(obj.payment_method, obj.payment_method)

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
# ===== Сериализаторы для публичной записи =====
class CourseBookingSerializer(serializers.ModelSerializer):
    free_slots = serializers.IntegerField(read_only=True)
    teacher_name = serializers.CharField(source="teacher.__str__", read_only=True)

    class Meta:
        model = Course
        fields = ["id", "name", "branch", "teacher_name",
                  "lesson_price", "lesson_duration", "free_slots"]


class TeacherBookingSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = Teacher
        fields = ["id", "full_name"]


class BookingRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingRequest
        fields = ["id", "full_name", "phone", "email",
                  "mode", "branch", "course", "teacher", "comment"]

    def validate(self, data):
        if data.get("mode") == "group":
            course = data.get("course")
            if not course:
                raise serializers.ValidationError({"course": "Выберите группу"})
            if not course.has_free_slots:
                raise serializers.ValidationError({"course": "В этой группе нет свободных мест"})
        elif data.get("mode") == "individual":
            if not data.get("teacher"):
                raise serializers.ValidationError({"teacher": "Выберите преподавателя"})
        return data

class HomeworkSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    lesson_info = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Homework
        fields = '__all__'

    def get_teacher_name(self, obj):
        return obj.teacher.profile.user.username if obj.teacher else ''

    def get_student_name(self, obj):
        return obj.student.profile.user.username if obj.student else ''

    def get_lesson_info(self, obj):
        return str(obj.lesson) if obj.lesson else ''

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
