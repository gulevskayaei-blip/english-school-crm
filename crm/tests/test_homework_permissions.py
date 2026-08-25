from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from crm.models import Profile, Teacher, Student, Course, Lesson, Homework, Branch

User = get_user_model()


class HomeworkPermissionsTest(TestCase):
    """Тесты прав доступа к домашним заданиям"""
    
    def setUp(self):
        # Создаем филиал
        self.branch = Branch.objects.create(name="Test Branch", address="Test Address")
        
        # Создаем администратора
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password123',
            role='admin'
        )
        
        # Создаем учителей
        self.teacher1_user = User.objects.create_user(
            username='teacher1',
            password='password123',
            role='teacher'
        )
        self.teacher1_profile = Profile.objects.create(
            user=self.teacher1_user,
            phone_number='1234567890'
        )
        self.teacher1 = Teacher.objects.create(
            profile=self.teacher1_profile,
            education='Test Education',
            experience='Test Experience',
            hourly_rate=100.00
        )
        
        self.teacher2_user = User.objects.create_user(
            username='teacher2',
            password='password123',
            role='teacher'
        )
        self.teacher2_profile = Profile.objects.create(
            user=self.teacher2_user,
            phone_number='1234567891'
        )
        self.teacher2 = Teacher.objects.create(
            profile=self.teacher2_profile,
            education='Test Education',
            experience='Test Experience',
            hourly_rate=100.00
        )
        
        # Создаем студентов
        self.student1_user = User.objects.create_user(
            username='student1',
            password='password123',
            role='student'
        )
        self.student1_profile = Profile.objects.create(
            user=self.student1_user,
            phone_number='1234567892'
        )
        self.student1 = Student.objects.create(
            profile=self.student1_profile,
            branch=self.branch,
            format='online'
        )
        
        self.student2_user = User.objects.create_user(
            username='student2',
            password='password123',
            role='student'
        )
        self.student2_profile = Profile.objects.create(
            user=self.student2_user,
            phone_number='1234567893'
        )
        self.student2 = Student.objects.create(
            profile=self.student2_profile,
            branch=self.branch,
            format='online'
        )
        
        # Создаем курсы: teacher1 обучает student1, teacher2 обучает student2
        self.course1 = Course.objects.create(
            name='Course 1',
            branch=self.branch,
            teacher=self.teacher1,
            lesson_price=100.00
        )
        self.course1.students.add(self.student1)
        
        self.course2 = Course.objects.create(
            name='Course 2',
            branch=self.branch,
            teacher=self.teacher2,
            lesson_price=100.00
        )
        self.course2.students.add(self.student2)
        
        # Создаем занятия
        from datetime import datetime, timedelta
        self.lesson1 = Lesson.objects.create(
            course=self.course1,
            teacher=self.teacher1,
            student=self.student1,
            branch=self.branch,
            datetime_start=datetime.now() + timedelta(days=1),
            datetime_end=datetime.now() + timedelta(days=1, hours=1),
            type='group',
            format='online'
        )
        
        self.lesson2 = Lesson.objects.create(
            course=self.course2,
            teacher=self.teacher2,
            student=self.student2,
            branch=self.branch,
            datetime_start=datetime.now() + timedelta(days=1),
            datetime_end=datetime.now() + timedelta(days=1, hours=1),
            type='group',
            format='online'
        )
        
        # Создаем ДЗ
        self.homework1 = Homework.objects.create(
            lesson=self.lesson1,
            teacher=self.teacher1,
            student=self.student1,
            title='Homework 1',
            description='Test homework 1'
        )
        
        self.homework2 = Homework.objects.create(
            lesson=self.lesson2,
            teacher=self.teacher2,
            student=self.student2,
            title='Homework 2',
            description='Test homework 2'
        )
        
        self.client = APIClient()
    
    def test_teacher_can_create_homework_for_own_student(self):
        """Учитель может создавать ДЗ для своего студента"""
        self.client.force_authenticate(user=self.teacher1_user)
        
        data = {
            'lesson': self.lesson1.id,
            'student': self.student1.id,
            'title': 'New Homework',
            'description': 'Test description'
        }
        
        response = self.client.post('/api/homeworks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Homework.objects.filter(student=self.student1, teacher=self.teacher1).count(), 2)
    
    def test_teacher_cannot_create_homework_for_other_student(self):
        """Учитель НЕ может создавать ДЗ для чужого студента"""
        self.client.force_authenticate(user=self.teacher1_user)
        
        data = {
            'lesson': self.lesson2.id,
            'student': self.student2.id,  # Чужой студент
            'title': 'New Homework',
            'description': 'Test description'
        }
        
        response = self.client.post('/api/homeworks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # ДЗ не должно быть создано
        self.assertEqual(Homework.objects.filter(student=self.student2, teacher=self.teacher1).count(), 0)
    
    def test_admin_can_create_homework_for_any_student(self):
        """Админ может создавать ДЗ для любого студента"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'lesson': self.lesson2.id,
            'student': self.student2.id,
            'title': 'Admin Homework',
            'description': 'Admin created homework'
        }
        
        response = self.client.post('/api/homeworks/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Homework.objects.filter(student=self.student2).count(), 2)
    
    def test_student_can_view_own_homework(self):
        """Студент может видеть свои ДЗ"""
        self.client.force_authenticate(user=self.student1_user)
        
        response = self.client.get('/api/homeworks/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Студент видит только свои ДЗ
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.homework1.id)
    
    def test_student_cannot_view_others_homework(self):
        """Студент НЕ может видеть чужие ДЗ"""
        self.client.force_authenticate(user=self.student1_user)
        
        # Пытаемся получить чужое ДЗ
        response = self.client.get(f'/api/homeworks/{self.homework2.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_teacher_can_view_own_homework(self):
        """Учитель может видеть свои ДЗ"""
        self.client.force_authenticate(user=self.teacher1_user)
        
        response = self.client.get('/api/homeworks/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Учитель видит только свои ДЗ
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.homework1.id)
    
    def test_teacher_cannot_view_others_homework(self):
        """Учитель НЕ может видеть чужие ДЗ"""
        self.client.force_authenticate(user=self.teacher1_user)
        
        # Пытаемся получить чужое ДЗ
        response = self.client.get(f'/api/homeworks/{self.homework2.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_admin_can_view_all_homework(self):
        """Админ может видеть все ДЗ"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/homeworks/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Админ видит все ДЗ
        self.assertEqual(len(response.data), 2)
