from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# 1. Модель Пользователя (базовая для всех)
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('teacher', 'Преподаватель'),
        ('student', 'Студент'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# 2. Модель Филиала
class Branch(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название филиала")
    address = models.TextField(verbose_name="Адрес")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"


# 3. Модель Профиля (общие данные для преподавателей и студентов)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона")
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telegram Chat ID")
    
    def __str__(self):
        return f"Профиль {self.user.username}"
    
    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


# 4. Модель Преподавателя (расширенная)
class Teacher(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, verbose_name="Профиль")
    education = models.TextField(verbose_name="Образование")
    experience = models.TextField(verbose_name="Опыт работы")
    certificates = models.TextField(blank=True, null=True, verbose_name="Сертификаты")
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Базовая ставка в час")
    
    # Новые поля
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    hire_date = models.DateField(blank=True, null=True, verbose_name="Дата найма")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    bank_account = models.CharField(max_length=50, blank=True, null=True, verbose_name="Банковский счет")
    
    def __str__(self):
        return f"{self.profile.user.get_full_name() or self.profile.user.username}"
    
    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"


# 5. Модель Студента
class Student(models.Model):
    FORMAT_CHOICES = (
        ('offline', 'Офлайн'),
        ('online', 'Онлайн'),
    )
    
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, verbose_name="Профиль")
    parent_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="ФИО родителя")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Скидка (%)")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='offline', verbose_name="Формат обучения")
    
    def __str__(self):
        return f"{self.profile.user.get_full_name() or self.profile.user.username}"
    
    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"


# 6. Модель Группы/Курса
class Course(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название группы")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")
    students = models.ManyToManyField(Student, verbose_name="Студенты")
    lesson_duration = models.IntegerField(default=60, verbose_name="Длительность занятия (мин)")
    lesson_price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Стоимость занятия")
    
    # Новые поля для публичной записи
    capacity = models.PositiveIntegerField(default=8, verbose_name="Максимум студентов")
    is_open_for_booking = models.BooleanField(default=True, verbose_name="Открыта для записи")

    @property
    def free_slots(self):
        return max(self.capacity - self.students.count(), 0)

    @property
    def has_free_slots(self):
        return self.free_slots > 0
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"


# 7. Модель Логов занятий
class LessonLog(models.Model):
    ACTION_CHOICES = (
        ('create', 'Создание'),
        ('update', 'Изменение'),
        ('delete', 'Удаление'),
        ('status_change', 'Смена статуса'),
    )
    
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='logs', verbose_name="Занятие")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Действие")
    old_data = models.JSONField(blank=True, null=True, verbose_name="Старые данные")
    new_data = models.JSONField(blank=True, null=True, verbose_name="Новые данные")
    changed_fields = models.JSONField(blank=True, null=True, verbose_name="Измененные поля")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Лог занятия"
        verbose_name_plural = "Логи занятий"
    
    def __str__(self):
        return f'{self.get_action_display()} - {self.lesson} - {self.user}'


# 8. Модель Занятия (с поддержкой повторений и правилами отмены)
class Lesson(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Запланировано'),
        ('pending', 'Ожидает подтверждения'),
        ('completed', 'Проведено'),
        ('cancelled', 'Отменено'),
        ('postponed', 'Перенесено'),
        ('missed', 'Пропущено'),
        ('no_show', 'Не явился'),
        ('paid', 'Оплачено'),
        ('debt', 'Долг'),
    )
    TYPE_CHOICES = (
        ('group', 'Групповое'),
        ('individual', 'Индивидуальное'),
    )
    FORMAT_CHOICES = (
        ('offline', 'Офлайн'),
        ('online', 'Онлайн'),
    )
    RECURRING_TYPE_CHOICES = (
        ('weekly', 'Еженедельно'),
        ('biweekly', 'Раз в 2 недели'),
        ('monthly', 'Ежемесячно'),
    )
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Группа")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Студент (индив.)")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    datetime_start = models.DateTimeField(verbose_name="Начало занятия")
    datetime_end = models.DateTimeField(verbose_name="Конец занятия")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='scheduled', verbose_name="Статус")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Тип занятия")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Стоимость занятия")
    paid = models.BooleanField(default=False, verbose_name="Оплачено")
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, verbose_name="Формат")    
    topic = models.CharField(max_length=200, blank=True, null=True, verbose_name="Тема занятия")
    homework = models.TextField(blank=True, null=True, verbose_name="Текст ДЗ")
    homework_status = models.CharField(
        max_length=20,
        choices=(
            ("not_required", "Не требуется"),
            ("pending", "Ожидает сдачи"),
            ("submitted", "Сдано"),
            ("checked", "Проверено"),
            ("needs_revision", "Требует доработки"),
        ),
        default="not_required",
        verbose_name="Статус ДЗ"
    )
    homework_audio = models.FileField(upload_to="homework_audio/", blank=True, null=True, verbose_name="Аудио ДЗ")
    homework_file = models.FileField(upload_to="homework_files/", blank=True, null=True, verbose_name="Файл ДЗ (PDF/PNG/DOC)")
    homework_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий учителя к ДЗ")
    is_homework_completed = models.BooleanField(default=False, verbose_name="ДЗ выполнено")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    
    # Поля для повторяющихся занятий
    is_recurring = models.BooleanField(default=False, verbose_name="Регулярное занятие")
    recurring_type = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        choices=RECURRING_TYPE_CHOICES,
        verbose_name="Тип повтора"
    )
    recurring_end_date = models.DateField(blank=True, null=True, verbose_name="Дата окончания повторов")
    recurring_count = models.IntegerField(blank=True, null=True, verbose_name="Количество повторов")
    recurring_parent_id = models.IntegerField(blank=True, null=True, verbose_name="ID родительского занятия")
    
    # Поля для правил отмены
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name="Причина отмены")
    cancellation_time = models.DateTimeField(blank=True, null=True, verbose_name="Время отмены")
    is_penalty_applied = models.BooleanField(default=False, verbose_name="Штраф применен")
    sick_leave_provided = models.BooleanField(default=False, verbose_name="Справка предоставлена")
    
    # Поля для ставки и замены преподавателя
    custom_rate = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Индивидуальная ставка")
    substitute_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, blank=True, null=True, related_name='substitute_lessons', verbose_name="Преподаватель на замену")
    substitute_rate = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, verbose_name="Ставка замены")
    
    def __str__(self):
        return f"{self.course.name if self.course else 'Индивидуальное'} - {self.datetime_start}"
    
    # ==================== ВАЛИДАЦИЯ ====================
    
    def is_teacher_available(self):
        """Проверка, что преподаватель свободен в это время"""
        if not self.teacher:
            return True
        
        overlapping = Lesson.objects.filter(
            teacher=self.teacher,
            status__in=['scheduled', 'completed'],
            datetime_start__lt=self.datetime_end,
            datetime_end__gt=self.datetime_start
        ).exclude(id=self.id)
        
        return not overlapping.exists()
    
    def is_student_available(self):
        """Проверка, что студент свободен в это время"""
        if not self.student:
            return True
        
        overlapping = Lesson.objects.filter(
            student=self.student,
            status__in=['scheduled', 'completed'],
            datetime_start__lt=self.datetime_end,
            datetime_end__gt=self.datetime_start
        ).exclude(id=self.id)
        
        return not overlapping.exists()
    
    def clean(self):
        """Валидация перед сохранением"""
        if self.datetime_start >= self.datetime_end:
            raise ValidationError('Время начала должно быть меньше времени окончания')
        
        if not self.is_teacher_available():
            teacher_name = self.teacher.profile.user.username if self.teacher.profile else str(self.teacher)
            raise ValidationError(f'Преподаватель "{teacher_name}" уже занят в это время')
        
        if not self.is_student_available():
            student_name = self.student.profile.user.username if self.student.profile else str(self.student)
            raise ValidationError(f'Студент "{student_name}" уже занят в это время')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"


# 9. Модель Посещаемости
class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Присутствовал'),
        ('late', 'Опоздал'),
        ('sick', 'Отсутствует по болезни'),
        ('absent_no_reason', 'Отсутствует без предупреждения'),
    )
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name="Занятие")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present', verbose_name="Статус посещения")
    student_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий по студенту")
    
    def __str__(self):
        return f"{self.student} - {self.lesson} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"


# 10. Модель Платежа
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('transfer', 'Банковский перевод'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    date = models.DateField(auto_now_add=True, verbose_name="Дата")
    purpose = models.CharField(max_length=200, blank=True, null=True, verbose_name="Назначение")
    lessons_paid = models.IntegerField(default=1, verbose_name="Оплачено занятий")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name='Способ оплаты')
    receipt_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='Номер чека')
    
    def __str__(self):
        return f"{self.student} - {self.amount} руб."
    
    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"


# 11. Модель Расхода
class Expense(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('transfer', 'Банковский перевод'),
    ]
    
    category = models.CharField(max_length=100, verbose_name='Категория')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    date = models.DateField(auto_now_add=True, verbose_name='Дата')
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash', verbose_name='Способ оплаты')
    receipt_image = models.FileField(upload_to='receipts/', blank=True, null=True, verbose_name='Чек')
    
    def __str__(self):
        return f"{self.category} - {self.amount} руб."
    
    class Meta:
        verbose_name = "Расход"
        verbose_name_plural = "Расходы"


# 12. Модель Свободных слотов преподавателя
class TeacherSlot(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name="Преподаватель")
    datetime_start = models.DateTimeField(verbose_name="Начало слота")
    datetime_end = models.DateTimeField(verbose_name="Конец слота")
    
    def __str__(self):
        return f"{self.teacher} - {self.datetime_start}"
    
    class Meta:
        verbose_name = "Свободный слот преподавателя"
        verbose_name_plural = "Свободные слоты преподавателей"


# 13. Модель Уведомлений об отменах
class CancellationNotification(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, verbose_name="Занятие")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь (админ/учитель)")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        unique_together = ('lesson', 'user')
        verbose_name = "Уведомление об отмене"
        verbose_name_plural = "Уведомления об отменах"
    
    def __str__(self):
        return f"Отмена {self.lesson} для {self.user}"


# 14. Модель Уведомлений студентам
class Notification(models.Model):
    TYPE_CHOICES = (
        ('debt', 'О долге'),
        ('schedule', 'О расписании'),
        ('payment', 'Об оплате'),
        ('custom', 'Свое'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент", related_name='notifications')
    message = models.TextField(verbose_name="Сообщение")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='custom', verbose_name="Тип")
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Отправитель", related_name='sent_notifications')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Уведомление для {self.student}"


# ===== Заявка на запись с сайта =====
class BookingRequest(models.Model):
    MODE_CHOICES = (
        ("group", "В группу"),
        ("individual", "Индивидуально к преподавателю"),
    )
    STATUS_CHOICES = (
        ("new", "Новая"),
        ("confirmed", "Подтверждена"),
        ("rejected", "Отклонена"),
    )

    full_name = models.CharField(max_length=120, verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    mode = models.CharField(max_length=12, choices=MODE_CHOICES, verbose_name="Тип записи")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, verbose_name="Филиал")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Группа")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Преподаватель")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий клиента")

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="new", verbose_name="Статус")
    manager_comment = models.TextField(blank=True, null=True, verbose_name="Комментарий менеджера")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заявка на запись"
        verbose_name_plural = "Заявки на запись"

    def __str__(self):
        return f"{self.full_name} — {self.get_mode_display()} ({self.get_status_display()})"

# 9. Модель Прогресса и Стриков Студента
class StudentProgress(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="progress", verbose_name="Студент")
    current_level = models.CharField(max_length=5, blank=True, null=True, verbose_name="Текущий уровень (A1-C2)")
    current_module = models.CharField(max_length=100, blank=True, null=True, verbose_name="Текущий модуль/тема")
    overall_progress = models.FloatField(default=0.0, verbose_name="Общий прогресс (%)")
    streak_days = models.IntegerField(default=0, verbose_name="Дней занятий подряд")
    last_activity_date = models.DateField(blank=True, null=True, verbose_name="Дата последней активности")
    course_total_lessons = models.IntegerField(default=0, blank=True, null=True, verbose_name="Всего занятий в курсе")

    def __str__(self):
        return f"Прогресс: {self.student}"

    class Meta:
        verbose_name = "Прогресс студента"
        verbose_name_plural = "Прогресс студентов"

# Модель Домашнего задания
class Homework(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='homeworks', verbose_name="Занятие")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='created_homeworks', verbose_name="Преподаватель")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='homeworks', verbose_name="Студент")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    file = models.FileField(upload_to='homework_files/', blank=True, null=True, verbose_name="Файл (аудио/PDF/PNG)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"{self.title} - {self.student}"

    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"
        ordering = ['-created_at']
