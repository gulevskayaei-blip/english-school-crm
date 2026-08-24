<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto;">
    <div class="header-with-notifications">
      <div>
        <h1>Добро пожаловать, {{ profile.username }}!</h1>
        <p><strong>Роль:</strong> {{ profile.role }}</p>
        <p><strong>ID пользователя:</strong> {{ profile.id }}</p>
      </div>
      <!-- Уведомления для админа и учителя -->
      <AdminNotifications v-if="profile.role === 'admin' || profile.role === 'teacher'" />
    </div>

    <hr />

    <!-- РђР”РњРРќ -->
    <div v-if="profile.role === 'admin'">
      <h2>Панель администратора</h2>
      <button @click="$router.push('/schedule')">📅 Расписание</button>
      <button @click="createStudent">👨‍🎓 Создать студента</button>
      <button @click="goToReports">📊 Отчеты</button>
      <button @click="$router.push('/students')">👨‍🎓 Список студентов</button>
      <button @click="$router.push('/teachers')">👨‍🏫 Преподаватели</button>
      <button @click="logout" style="background: red;">🚪 Выйти</button>
    </div>

    <!-- ПРЕПОДАВАТЕЛЬ -->
    <div v-else-if="profile.role === 'teacher'">
      <h2>Панель преподавателя</h2>
      
      <!-- БЛОК ЗАРПЛАТЫ ДЛЯ ПРЕПОДАВАТЕЛЯ -->
      <div v-if="teacherSalary && teacherSalary.forecast_salary !== undefined" class="teacher-salary-block">
        <h3>💰 Моя зарплата за текущий месяц</h3>
        <div class="salary-grid">
          <div class="salary-item actual">
            <span class="salary-label">Фактическая:</span>
            <span class="salary-value">{{ formatMoney(teacherSalary.actual_salary) }}</span>
            <span class="salary-hours">({{ teacherSalary.actual_hours || 0 }} ч)</span>
          </div>
          <div class="salary-item forecast">
            <span class="salary-label">Прогнозируемая:</span>
            <span class="salary-value">{{ formatMoney(teacherSalary.forecast_salary) }}</span>
            <span class="salary-hours">({{ teacherSalary.forecast_hours || 0 }} ч)</span>
          </div>
          <div class="salary-item difference" :class="{ positive: teacherSalary.difference_salary > 0, negative: teacherSalary.difference_salary < 0 }">
            <span class="salary-label">Разница:</span>
            <span class="salary-value">{{ formatMoney(teacherSalary.difference_salary) }}</span>
          </div>
        </div>
      </div>
      <div v-else-if="!teacherSalary" class="loading-salary">
        <p>⏳ Загрузка данных о зарплате...</p>
      </div>
      <div v-else class="loading-salary">
        <p>📊 Данные о зарплате временно недоступны</p>
        <p class="small-text">(Ставка: {{ teacherSalary.hourly_rate || 'не указана' }} ₽/час)</p>
      </div>
      <!-- КОНЕЦ БЛОКА ЗАРПЛАТЫ -->
      
      <h3>📅 Мои занятия сегодня</h3>
      <ul v-if="myLessonsToday.length">
        <li v-for="lesson in myLessonsToday" :key="lesson.id">
          <strong>{{ formatDateTime(lesson.datetime_start) }}</strong> — {{ lesson.course?.name || 'Без курса' }}
          <br />
          Студент: {{ lesson.student?.profile?.user?.username || lesson.student_name || 'Групповое' }}
        </li>
      </ul>
      <p v-else>Сегодня занятий нет.</p>
      <button @click="$router.push('/schedule')">📅 Мое расписание</button>
      <button @click="logout" style="background: red; margin-left: 10px;">🚪 Выйти</button>
    </div>

    <!-- СТУДЕНТ -->
    <div v-else-if="profile.role === 'student'" class="student-dashboard-new">
      <!-- Приветствие и аватар -->
      <div class="welcome-section">
        <div class="welcome-text">
          <h1>Добрый день, {{ profile.username }}! 👋</h1>
          <p>Твой прогресс в изучении английского языка</p>
        </div>
        <div class="avatar-section">
          <img v-if="profile.profile?.avatar" :src="profile.profile.avatar" alt="Avatar" class="user-avatar">
          <div v-else class="user-avatar-placeholder">{{ profile.username.charAt(0).toUpperCase() }}</div>
        </div>
      </div>

      <!-- Карточка прогресса -->
      <div class="progress-card">
        <div class="progress-header">
          <h2>Твой прогресс</h2>
          <span class="level-badge">{{ studentProgress?.current_level || 'A1' }}</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: (studentProgress?.overall_progress || 0) + '%' }"></div>
        </div>
        <p>{{ studentProgress?.overall_progress || 0 }}% курса пройдено</p>
        <div class="streak-info">
          🔥 Серия занятий: {{ studentProgress?.streak_days || 0 }} дней подряд
        </div>
      </div>

      <!-- Карточка следующего урока -->
      <div class="next-lesson-card" v-if="nextLesson">
        <h2>Следующий урок</h2>
        <div class="lesson-details">
          <p class="lesson-topic">{{ nextLesson.topic || nextLesson.course_name || 'Индивидуальное занятие' }}</p>
          <p class="lesson-date-time">{{ formatDateTime(nextLesson.datetime_start) }}</p>
          <p class="lesson-teacher">Преподаватель: {{ nextLesson.teacher_name || 'Не назначен' }}</p>
        </div>
<div class="lesson-actions">
          <button class="primary-btn" @click="goToLesson(nextLesson)">К следующему уроку</button>
          <button v-if="canCancelLesson(nextLesson.datetime_start)" 
                  class="cancel-btn" 
                  title="⚠️ Занятие можно отменить только за 2 часа до начала. При отмене менее чем за 2 часа занятие будет оплачено."
                  @click="cancelLesson(nextLesson)">
            ❌ Отменить занятие
          </button>
          <div v-else class="cant-cancel-info" title="Занятие можно отменить только за 2 часа до начала. При отмене менее чем за 2 часа занятие будет оплачено.">
            ⏰ Отмена невозможна (менее 2 часов до начала) - занятие будет оплачено
          </div>
        </div>
      </div>

      <!-- Кнопка записи на урок -->
      <div class="booking-section" v-if="profile.role === 'student'">
        <button class="primary-btn booking-btn" @click="openBookingModal">
          📅 Записаться на урок
        </button>
      </div>

      <!-- Модальное окно записи -->
      <div v-if="showBookingModal" class="modal-overlay" @click.self="closeBookingModal">
        <div class="modal-content booking-modal">
          <h2>Запись на урок</h2>
          
          <!-- Шаг 1: Выбор преподавателя -->
          <div v-if="bookingStep === 1" class="booking-step">
            <label>Выберите преподавателя:</label>
            <select v-model="selectedTeacherId" class="form-select">
              <option value="">-- Выберите --</option>
              <option v-for="teacher in teachersList" :key="teacher.id" :value="teacher.id">
                {{ teacher.name }}
              </option>
            </select>
            <button class="primary-btn" @click="loadSlotsForTeacher" :disabled="!selectedTeacherId">Далее</button>
          </div>

          <!-- Шаг 2: Выбор даты и времени -->
          <div v-if="bookingStep === 2" class="booking-step">
            <label>Выберите дату:</label>
            <input type="date" v-model="selectedDate" class="form-input" @change="loadAvailableSlots">
            
            <div v-if="loadingSlots" class="loading">Загрузка слотов...</div>
            
            <div v-else-if="availableSlots.length === 0 && selectedDate" class="no-slots">
              Нет свободных слотов на эту дату
            </div>
            
            <div v-else class="slots-grid">
              <div v-for="slot in availableSlots" :key="slot.start"
                   class="slot-item"
                   :class="{ selected: selectedSlot?.start === slot.start }"
                   @click="selectSlot(slot)">
                {{ formatTime(slot.start) }} - {{ formatTime(slot.end) }}
              </div>
            </div>
            
            <div class="modal-actions">
              <button class="secondary-btn" @click="bookingStep = 1">Назад</button>
              <button class="primary-btn" @click="confirmBooking" :disabled="!selectedSlot">Подтвердить</button>
            </div>
          </div>

          <!-- Шаг 3: Подтверждение -->
          <div v-if="bookingStep === 3" class="booking-step confirmation">
            <p>✅ Заявка отправлена!</p>
            <p>Ваша заявка на {{ formatDateTime(selectedSlot?.start) }} ожидает подтверждения администратора.</p>
            <button class="primary-btn" @click="closeBookingModal">Закрыть</button>
          </div>

          <button class="close-modal-btn" @click="closeBookingModal">&times;</button>
        </div>
      </div>

      <!-- Карточка домашнего задания -->
      <div class="homework-card">
        <h2>📝 Домашнее задание</h2>
        <div v-if="currentHomework">
          <div class="homework-status" :class="currentHomework.homework_status">
            {{ getHomeworkStatusLabel(currentHomework.homework_status) }}
          </div>
          <p class="homework-text">{{ currentHomework.homework || 'Нет задания' }}</p>
          <div v-if="currentHomework.homework_audio" class="audio-player">
            <audio controls :src="currentHomework.homework_audio"></audio>
          </div>
          <div v-if="currentHomework.homework_file" class="homework-file">
            <a :href="currentHomework.homework_file" target="_blank" class="file-link">
              📎 Скачать файл ДЗ
            </a>
          </div>
          <button class="secondary-btn" @click="submitHomework(currentHomework)">Сдать ДЗ</button>
        </div>
        <div v-else class="no-homework">
          <p>🎉 Пока нет домашнего задания. Отличная работа!</p>
        </div>
      </div>

      <!-- Список всех занятий -->
      <div class="lessons-list-card">
        <h2>📚 Мои занятия</h2>
        <div v-if="allLessons.length === 0" class="empty-lessons">
          <p>У вас пока нет занятий</p>
        </div>
        <div v-else class="lessons-grid">
          <div v-for="lesson in allLessons" :key="lesson.id" 
               class="lesson-item"
               :class="{ 
                 'lesson-completed': lesson.status === 'completed',
                 'lesson-cancelled': lesson.status === 'cancelled',
                 'lesson-upcoming': lesson.status === 'scheduled'
               }">
            <div class="lesson-item-header">
              <span class="lesson-date-badge">{{ formatDateTime(lesson.datetime_start) }}</span>
              <span class="lesson-status-badge" :class="lesson.status">
                {{ lesson.status === 'completed' ? '✅ Проведено' : lesson.status === 'cancelled' ? '❌ Отменено' : lesson.status === 'pending' ? '⏳ Ожидает подтверждения' : '📅 Запланировано' }}
              </span>
            </div>
            <div class="lesson-item-body">
              <p class="lesson-item-topic">{{ lesson.topic || lesson.course_name || 'Индивидуальное занятие' }}</p>
              <p class="lesson-item-teacher">👨‍🏫 {{ lesson.teacher_name || 'Преподаватель' }}</p>
            </div>
            <div class="lesson-item-footer">
              <span class="payment-status" :class="lesson.payment_status === 'paid' ? 'paid' : 'unpaid'">
                {{ lesson.payment_status === 'paid' ? '💳 Оплачено' : '⚠️ Не оплачено' }}
              </span>
              <button v-if="lesson.status === 'scheduled' && canCancelLesson(lesson.datetime_start)"
                      class="cancel-btn-small"
                      @click="cancelLesson(lesson)">
                ❌ Отменить
              </button>
              <span v-else-if="lesson.status === 'scheduled' && !canCancelLesson(lesson.datetime_start)" class="no-cancel-hint">
                ⏰ Отмена менее чем за 2ч
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Таблица посещаемости -->
      <div class="attendance-card">
        <h2>📊 Посещаемость</h2>
        <div v-if="allLessons.length === 0" class="empty-attendance">
          <p>Нет данных о занятиях</p>
        </div>
        <div v-else class="attendance-table-container">
          <table class="attendance-table">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Тема</th>
                <th>Статус</th>
                <th>Оплата</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="lesson in sortedLessons" :key="lesson.id" 
                  :class="getAttendanceRowClass(lesson)">
                <td>{{ formatDateTime(lesson.datetime_start) }}</td>
                <td>{{ lesson.topic || lesson.course_name || 'Занятие' }}</td>
                <td>
                  <span class="status-badge" :class="lesson.status">
                    {{ getStatusLabel(lesson.status) }}
                  </span>
                </td>
                <td>
                  <span class="payment-badge" :class="getPaymentClass(lesson)">
                    {{ getPaymentLabel(lesson) }}
                  </span>
                </td>
                <td>
                  <button v-if="lesson.status === 'scheduled' && canCancelLesson(lesson.datetime_start)"
                          class="cancel-btn-small"
                          @click="cancelLesson(lesson)">
                    ❌ Отменить
                  </button>
                  <span v-else-if="lesson.status === 'scheduled'" class="no-cancel-hint">⏰ Менее 2ч</span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Навигация -->
      <div class="nav-buttons">
        <button class="nav-btn" @click="$router.push('/schedule')">📅 Полное расписание</button>
        <button class="nav-btn" @click="$router.push('/payments')">💳 История платежей</button>
        <button class="nav-btn logout" @click="logout">🚪 Выйти</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';
import AdminNotifications from '@/components/AdminNotifications.vue';
import StudentNotifications from '@/components/StudentNotifications.vue';

const router = useRouter();
const profile = ref({});
const myLessonsToday = ref([]);
const myUpcomingLessons = ref([]);
const allLessons = ref([]);
const studentPayments = ref([]);
const studentDebt = ref(0);
const totalPaid = ref(0);
const teacherSalary = ref(null);
const studentProgress = ref(null);
const nextLesson = ref(null);
// Переменные для записи на урок
const showBookingModal = ref(false);
const bookingStep = ref(1);
const teachersList = ref([]);
const selectedTeacherId = ref("");
const selectedDate = ref("");
const availableSlots = ref([]);
const selectedSlot = ref(null);
const loadingSlots = ref(false);
const currentHomework = ref(null);

onMounted(async () => {
  await loadProfile();
  await loadMyLessons();
  if (profile.value.role === 'student') {
    await loadStudentPayments();
    await loadStudentDebt();
  }
  if (profile.value.role === 'teacher') {
    await loadTeacherSalary();
  }
});

async function loadProfile() {
  try {
    const res = await api.get('users/me/');
    profile.value = res.data;
  } catch (error) {
    console.error('Ошибка загрузки профиля', error);
    router.push('/login');
  }
}


function calculateStudentProgress(lessons, courseTotalLessons) {
  if (!lessons || lessons.length === 0) {
    studentProgress.value = { overall_progress: 0, streak_days: 0, current_level: 'A1' };
    return;
  }

  const completed = lessons.filter(l => l.status === 'completed');
  
  // Используем course_total_lessons если задано, иначе считаем по всем занятиям
  const total = (courseTotalLessons && courseTotalLessons > 0) ? courseTotalLessons : lessons.length;
  const progress = Math.min(100, Math.round((completed.length / total) * 100));

  // Расчет серии занятий (streak)
  // Берем только прошедшие занятия (не scheduled), сортируем по дате (новые сначала)
  const pastLessons = lessons
    .filter(l => l.status !== 'scheduled')
    .sort((a, b) => new Date(b.datetime_start) - new Date(a.datetime_start));
  
  let streak = 0;
  for (const lesson of pastLessons) {
    if (lesson.status === 'completed') {
      streak++;
    } else if (lesson.status === 'cancelled') {
      // Отмененные пропускаем, они не прерывают серию
      continue;
    } else {
      // missed, no_show и другие статусы прерывают серию
      break;
    }
  }

  // Определение уровня по количеству занятий
  let level = 'A1';
  if (completed.length >= 50) level = 'C1';
  else if (completed.length >= 30) level = 'B2';
  else if (completed.length >= 15) level = 'B1';
  else if (completed.length >= 5) level = 'A2';

  studentProgress.value = {
    overall_progress: progress,
    streak_days: streak,
    current_level: level,
    completed_count: completed.length,
    total_count: total
  };
}

async function loadMyLessons() {
  try {
    const res = await api.get('my-lessons/', { headers: { 'Cache-Control': 'no-cache' } });
    const lessons = res.data;
    allLessons.value = lessons;

    // Рассчитываем прогресс для студента
    if (profile.value.role === 'student') {
      const courseTotal = profile.value.student?.progress?.course_total_lessons || 0;
      calculateStudentProgress(lessons, courseTotal);
    }

    const today = new Date().toISOString().slice(0, 10);

    if (profile.value.role === 'teacher') {
      myLessonsToday.value = lessons.filter(l => l.datetime_start?.startsWith(today));
    } else if (profile.value.role === 'student') {
      myUpcomingLessons.value = lessons.filter(l => l.datetime_start?.startsWith(today)).slice(0, 5);
    }
    // Определяем текущее домашнее задание для студента
    if (profile.value.role === 'student' && lessons.length > 0) {
      const now = new Date();
      // Ищем ближайшее будущее занятие с ДЗ или последнее прошедшее с невыполненным ДЗ
      const hasHomework = (l) => l.homework || l.homework_file || l.homework_audio;
      const futureWithHomework = lessons
        .filter(l => new Date(l.datetime_start) >= now && hasHomework(l))
        .sort((a, b) => new Date(a.datetime_start) - new Date(b.datetime_start));
      
      const pastUnfinished = lessons
        .filter(l => new Date(l.datetime_start) < now && hasHomework(l) && !l.is_homework_completed)
        .sort((a, b) => new Date(b.datetime_start) - new Date(a.datetime_start));
      
      currentHomework.value = futureWithHomework[0] || pastUnfinished[0] || null;
      
      // Определяем следующее занятие для карточки "К следующему уроку"
      const now2 = new Date();
      const futureLessons = lessons
        .filter(l => new Date(l.datetime_start) > now2 && l.status !== 'cancelled')
        .sort((a, b) => new Date(a.datetime_start) - new Date(b.datetime_start));
      nextLesson.value = futureLessons[0] || null;
    }
  } catch (error) {
    console.error('Ошибка загрузки занятий', error);
  }
}

async function loadTeacherSalary() {
  try {
    const response = await api.get('/teachers-list-with-salary/');
    const teachers = response.data;
    console.log('Все преподаватели из API:', teachers);
    console.log('Текущий пользователь:', profile.value);
    
    // Пробуем найти преподавателя разными способами
    let currentTeacher = null;
    
    // 1. По id пользователя (если совпадает)
    currentTeacher = teachers.find(t => t.id === profile.value.id);
    
    // 2. По имени (username)
    if (!currentTeacher) {
      currentTeacher = teachers.find(t => t.name === profile.value.username);
    }
    
    // 3. По email (если есть)
    if (!currentTeacher && profile.value.email) {
      currentTeacher = teachers.find(t => t.email === profile.value.email);
    }
    
    // 4. Если учитель один в системе - берем первого (для теста)
    if (!currentTeacher && teachers.length === 1) {
      currentTeacher = teachers[0];
    }
    
    // 5. Если все равно не нашли, создаем fallback данные для отображения
    if (currentTeacher) {
      teacherSalary.value = currentTeacher;
      console.log('Найдена зарплата преподавателя:', teacherSalary.value);
    } else {
      console.warn('Преподаватель не найден, используем fallback данные');
      teacherSalary.value = {
        actual_salary: 0,
        actual_hours: 0,
        forecast_salary: 0,
        forecast_hours: 0,
        difference_salary: 0,
        name: profile.value.username,
        hourly_rate: 0,
        is_active: true
      };
    }
  } catch (error) {
    console.error('Ошибка загрузки зарплаты:', error);
    teacherSalary.value = {
      actual_salary: 0,
      actual_hours: 0,
      forecast_salary: 0,
      forecast_hours: 0,
      difference_salary: 0,
      name: profile.value.username,
      hourly_rate: 0,
      is_active: true
    };
  }
}

async function loadStudentPayments() {
  try {
    const response = await api.get('my-payments/');
    studentPayments.value = response.data;
    totalPaid.value = studentPayments.value.reduce((sum, p) => sum + p.amount, 0);
  } catch (error) {
    console.error('Ошибка загрузки платежей:', error);
  }
}

function getStudentId() {
  if (profile.value.role === 'student' && profile.value.profile) {
    return profile.value.profile.id || null;
  }
  return null;
}

async function loadStudentDebt() {
  try {
    const response = await api.get('reports/debtors/');
    const studentId = getStudentId();
    if (studentId) {
      const debtor = response.data.find(d => d.id === studentId);
      studentDebt.value = debtor?.debt || 0;
    }
  } catch (error) {
    console.error('Ошибка загрузки долга:', error);
  }
}

function formatMoney(amount) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(amount || 0);
}

function formatDateTime(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getPaymentMethodIcon(method) {
  const icons = { cash: '💵 Наличные', card: '💳 Карта', transfer: '🏦 Перевод' };
  return icons[method] || method;
}

function canCancelLesson(datetimeStart) {
  if (!datetimeStart) return false
  const lessonTime = new Date(datetimeStart)
  const now = new Date()
  const hoursDiff = (lessonTime - now) / (1000 * 60 * 60)
  return hoursDiff > 2 && lessonTime > now
}

async function cancelLesson(lesson) {
  try {
    const response = await api.post(`lessons/${lesson.id}/cancel/`)
    const data = response.data
    if (data.status === 'cancelled_with_penalty') {
      alert('⚠️ ' + data.message)
    } else {
      alert('✅ Занятие отменено! Уведомление отправлено администратору и преподавателю.')
    }
    await loadMyLessons()
    await loadStudentDebt()
  } catch (error) {
    console.error('Ошибка отмены занятия:', error)
    alert('Ошибка при отмене занятия: ' + (error.response?.data?.error || error.message))
  }
}

function createStudent() {
  router.push('/create-student');
}

function goToReports() {
  router.push('/reports');
}

function logout() {
  localStorage.removeItem('auth_token');
  router.push('/login');
}

// === Новые методы для кабинета студента ===
function getHomeworkStatusLabel(status) {
  const labels = {
    'not_required': 'Не требуется',
    'pending': 'Ожидает сдачи',
    'submitted': 'Сдано, ожидает проверки',
    'checked': 'Проверено',
    'needs_revision': 'Требует доработки'
  };
  return labels[status] || 'Неизвестно';
}

function goToLesson(lesson) {
  // Переход к уроку (можно добавить роутинг на страницу урока)
  alert('Переход к уроку: ' + (lesson.topic || lesson.course_name));
}

function submitHomework(lesson) {
  // Логика сдачи ДЗ (загрузка файла и т.д.)
  alert('Сдача ДЗ для урока: ' + (lesson.topic || lesson.course_name));
}









// === Функции для таблицы посещаемости ===
const sortedLessons = computed(() => {
  return [...allLessons.value].sort((a, b) => 
    new Date(b.datetime_start) - new Date(a.datetime_start)
  );
});

function getStatusLabel(status) {
  const labels = {
    'completed': '✅ Проведено',
    'cancelled': '⏰ Отменено',
    'scheduled': '📅 Запланировано',
    'missed': '❌ Пропущено',
    'no_show': '❌ Не явился'
  };
  return labels[status] || status;
}

function getPaymentLabel(lesson) {
  if (lesson.payment_status === 'paid') return '💳 Оплачено';
  if (lesson.status === 'cancelled') return '—';
  if (lesson.status === 'scheduled') return '⏳ Ожидает';
  return '⚠️ Долг';
}

function getAttendanceRowClass(lesson) {
  if (lesson.status === 'completed' && lesson.payment_status === 'paid') return 'row-success';
  if (lesson.status === 'missed' || lesson.status === 'no_show') return 'row-danger';
  if (lesson.status === 'cancelled') return 'row-neutral';
  if (lesson.payment_status !== 'paid' && lesson.status === 'completed') return 'row-warning';
  return '';
}

function getPaymentClass(lesson) {
  if (lesson.payment_status === 'paid') return 'payment-paid';
  if (lesson.status === 'cancelled') return 'payment-neutral';
  return 'payment-unpaid';
}


// ==================== МЕТОДЫ ЗАПИСИ НА УРОК ====================

async function openBookingModal() {
  showBookingModal.value = true;
  bookingStep.value = 1;
  selectedTeacherId.value = "";
  selectedDate.value = "";
  availableSlots.value = [];
  selectedSlot.value = null;
  
  // Загружаем список преподавателей
  try {
    const response = await api.get('teachers/for-booking/');
    teachersList.value = response.data.map(t => ({ id: t.id, name: t.profile?.user?.username || t.name || `Преподаватель ${t.id}` }));
  } catch (error) {
    console.error('Ошибка загрузки преподавателей:', error);
  }
}

function closeBookingModal() {
  showBookingModal.value = false;
}

async function loadSlotsForTeacher() {
  if (!selectedTeacherId.value) return;
  bookingStep.value = 2;
  // Устанавливаем дату на завтра по умолчанию
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  selectedDate.value = tomorrow.toISOString().split('T')[0];
  await loadAvailableSlots();
}

async function loadAvailableSlots() {
  if (!selectedTeacherId.value || !selectedDate.value) return;
  
  loadingSlots.value = true;
  availableSlots.value = [];
  selectedSlot.value = null;
  
  try {
    const response = await api.get(`lessons/available-slots/?teacher_id=${selectedTeacherId.value}&date=${selectedDate.value}`);
    availableSlots.value = response.data;
  } catch (error) {
    console.error('Ошибка загрузки слотов:', error);
  } finally {
    loadingSlots.value = false;
  }
}

function selectSlot(slot) {
  selectedSlot.value = slot;
}

async function confirmBooking() {
  if (!selectedSlot.value || !selectedTeacherId.value) return;
  
  try {
    await api.post('lessons/book/', {
      teacher_id: parseInt(selectedTeacherId.value),
      datetime_start: selectedSlot.value.start,
      duration: 60
    });
    bookingStep.value = 3;
    // Обновляем список уроков
    await loadMyLessons();
  } catch (error) {
    console.error('Ошибка записи:', error);
    alert(error.response?.data?.error || 'Ошибка при записи на урок');
  }
}

function formatTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

</script>

<style scoped>
.header-with-notifications {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

button {
  margin: 5px;
  padding: 8px 16px;
  cursor: pointer;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
}

button:hover {
  background-color: #45a049;
}

/* Студенческая панель */
.student-dashboard {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.student-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

/* Карточка долга */
.debt-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  border-radius: 12px;
  background: #f8f9fa;
  border-left: 5px solid #28a745;
}

.debt-card.has-debt {
  background: #fff3e0;
  border-left-color: #ff9800;
  animation: pulse 2s infinite;
}

.debt-card.no-debt {
  background: #e8f5e9;
  border-left-color: #4caf50;
}

@keyframes pulse {
  0% { background-color: #fff3e0; }
  50% { background-color: #ffe0b2; }
  100% { background-color: #fff3e0; }
}

.debt-icon {
  font-size: 48px;
}

.debt-info h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
}

.debt-amount {
  font-size: 24px;
  font-weight: bold;
}

.debt-value {
  color: #ff5722;
}

.paid-value {
  color: #4caf50;
}

.debt-hint {
  margin-top: 8px;
  font-size: 14px;
  color: #ff9800;
}

/* Правила отмены */
.rules-card {
  background: #e3f2fd;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  border-left: 4px solid #2196f3;
}

.rules-card h4 {
  margin: 0 0 10px 0;
  color: #1565c0;
}

.rules-card ul {
  margin: 0;
  padding-left: 20px;
}

.rules-card li {
  margin: 5px 0;
  font-size: 13px;
}

/* Карточки занятий */
.lesson-card {
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 10px;
  padding: 12px;
  transition: all 0.2s;
}

.lesson-card.cancelled {
  background: #fff3e0;
  opacity: 0.8;
}

.lesson-card.unpaid {
  border-left: 4px solid #ff9800;
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.lesson-date {
  font-weight: bold;
  color: #007bff;
}

.status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-badge.cancelled {
  background: #ff9800;
  color: white;
}

.status-badge.scheduled {
  background: #4caf50;
  color: white;
}

.lesson-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.lesson-payment {
  text-align: right;
}

.payment-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
}

.payment-badge.paid {
  background: #d4edda;
  color: #155724;
}

.payment-badge.unpaid {
  background: #fff3e0;
  color: #ff9800;
}

.penalty-info {
  font-size: 11px;
  color: #ff5722;
  margin-top: 5px;
  max-width: 250px;
}

.cancel-lesson-btn {
  margin-top: 8px;
  background: #ff9800;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}

.cancel-lesson-btn:hover {
  background: #f57c00;
}

.cant-cancel-info {
  margin-top: 8px;
  font-size: 11px;
  color: #f44336;
  background: #ffebee;
  padding: 4px 8px;
  border-radius: 4px;
}

.lessons-section h2,
.payments-section h2 {
  margin-bottom: 15px;
  font-size: 20px;
}

.lesson-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 10px;
}

.lesson-date {
  font-weight: bold;
  color: #007bff;
  min-width: 120px;
}

.schedule-btn {
  margin-top: 15px;
}

.payments-table {
  overflow-x: auto;
}

.payments-table table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.payments-table th,
.payments-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.payments-table th {
  background: #f8f9fa;
  font-weight: bold;
}

.amount-cell {
  font-weight: bold;
  color: #28a745;
}

.total-row {
  background: #f8f9fa;
  font-weight: bold;
}

.empty {
  text-align: center;
  padding: 20px;
  color: #999;
  background: #f8f9fa;
  border-radius: 8px;
}

/* Блок зарплаты для преподавателя */
.teacher-salary-block {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
}

.teacher-salary-block h3 {
  margin: 0 0 15px 0;
  text-align: center;
}

.salary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.salary-item {
  background: rgba(255,255,255,0.2);
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.salary-label {
  display: block;
  font-size: 12px;
  opacity: 0.9;
  margin-bottom: 5px;
}

.salary-value {
  display: block;
  font-size: 20px;
  font-weight: bold;
}

.salary-hours {
  display: block;
  font-size: 11px;
  opacity: 0.8;
  margin-top: 3px;
}

.salary-item.difference.positive .salary-value {
  color: #a5d6a7;
}

.salary-item.difference.negative .salary-value {
  color: #ef9a9a;
}

.loading-salary {
  background: #f0f0f0;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 20px;
  color: #666;
}

.small-text {
  font-size: 12px;
  margin-top: 5px;
  opacity: 0.7;
}

/* === Новый дизайн кабинета студента (Instagram mood) === */
.student-dashboard-new {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.welcome-text h1 {
  font-size: 24px;
  margin-bottom: 8px;
  color: #262626;
}

.welcome-text p {
  color: #8e8e8e;
  font-size: 14px;
}

.user-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #fff;
  box-shadow: 0 0 0 2px #e1306c;
}

.user-avatar-placeholder {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(45deg, #405de6, #5851db, #833ab4, #c13584, #e1306c, #fd1d1d);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: bold;
}

.progress-card {
  background: white;
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.level-badge {
  background: linear-gradient(45deg, #833ab4, #e1306c);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: bold;
  font-size: 14px;
}

.progress-bar-container {
  background: #efefef;
  border-radius: 10px;
  height: 12px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-bar {
  background: linear-gradient(90deg, #405de6, #e1306c);
  height: 100%;
  border-radius: 10px;
  transition: width 0.5s ease;
}

.streak-info {
  margin-top: 12px;
  font-weight: 600;
  color: #ff6b35;
}

.next-lesson-card, .homework-card {
  background: white;
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.lesson-details p {
  margin: 8px 0;
  color: #555;
}

.lesson-topic {
  font-weight: 600;
  font-size: 16px;
  color: #262626 !important;
}

.primary-btn, .secondary-btn {
  margin-top: 16px;
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.primary-btn {
  background: linear-gradient(45deg, #405de6, #e1306c);
  color: white;
  width: 100%;
}

.secondary-btn {
  background: #efefef;
  color: #262626;
  width: 100%;
}

.primary-btn:hover, .secondary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.homework-status {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 12px;
}

.homework-status.pending { background: #fff3cd; color: #856404; }
.homework-status.submitted { background: #d1ecf1; color: #0c5460; }
.homework-status.checked { background: #d4edda; color: #155724; }
.homework-status.needs_revision { background: #f8d7da; color: #721c24; }

.audio-player {
  margin-top: 16px;
}

.audio-player audio {
  width: 100%;
}


.homework-file {
  margin-top: 12px;
}

.file-link {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: background 0.2s;
}

.file-link:hover {
  background: #bae6fd;
}
/* === Кнопки навигации === */
.nav-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  padding: 20px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.nav-btn {
  flex: 1;
  min-width: 150px;
  padding: 14px 20px;
  border: none;
  border-radius: 12px;
  background: #f0f2f5;
  color: #262626;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-btn:hover {
  background: #e4e6eb;
  transform: translateY(-2px);
}

.nav-btn.logout {
  background: #ffebee;
  color: #c62828;
}

.nav-btn.logout:hover {
  background: #ffcdd2;
}
/* === Список занятий === */
.lessons-list-card {
  background: white;
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}

.lessons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.lesson-item {
  background: #fafafa;
  border-radius: 16px;
  padding: 16px;
  border: 1px solid #efefef;
  transition: all 0.3s ease;
}

.lesson-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.lesson-item.lesson-completed { border-left: 4px solid #4caf50; }
.lesson-item.lesson-cancelled { border-left: 4px solid #f44336; opacity: 0.7; }
.lesson-item.lesson-upcoming { border-left: 4px solid #2196f3; }

.lesson-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.lesson-date-badge {
  font-size: 12px;
  color: #8e8e8e;
  font-weight: 600;
}

.lesson-status-badge {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 600;
}

.lesson-status-badge.completed { background: #e8f5e9; color: #2e7d32; }
.lesson-status-badge.cancelled { background: #ffebee; color: #c62828; }
.lesson-status-badge.scheduled { background: #e3f2fd; color: #1565c0; }

.lesson-item-topic {
  font-weight: 600;
  margin: 8px 0;
  color: #262626;
}

.lesson-item-teacher {
  font-size: 13px;
  color: #8e8e8e;
}

.lesson-item-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #efefef;
}

.payment-status {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
}

.payment-status.paid { background: #e8f5e9; color: #2e7d32; }
.payment-status.unpaid { background: #fff3e0; color: #e65100; }

.empty-lessons {
  text-align: center;
  padding: 40px;
  color: #8e8e8e;
}

.no-homework {
  text-align: center;
  padding: 20px;
  color: #4caf50;
  font-weight: 600;
}
/* === Кнопка отмены и напоминание === */
.cancel-rule-reminder {
  background: #fff3e0;
  color: #e65100;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  margin: 16px 0;
  border-left: 4px solid #ff9800;
}

.lesson-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 12px;
  background: #ffebee;
  color: #c62828;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background: #ffcdd2;
  transform: translateY(-2px);
}

.cant-cancel-info {
  padding: 12px 16px;
  background: #f5f5f5;
  color: #9e9e9e;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}
/* === Таблица посещаемости === */
.attendance-card {
  background: white;
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  margin-bottom: 20px;
}

.attendance-table-container {
  overflow-x: auto;
  margin-top: 16px;
}

.attendance-table {
  width: 100%;
  border-collapse: collapse;
}

.attendance-table th, .attendance-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #efefef;
}

.attendance-table th {
  background: #fafafa;
  font-weight: 600;
  color: #8e8e8e;
  font-size: 13px;
}

.status-badge, .payment-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.completed { background: #e8f5e9; color: #2e7d32; }
.status-badge.cancelled { background: #f5f5f5; color: #9e9e9e; }
.status-badge.scheduled { background: #e3f2fd; color: #1565c0; }
.status-badge.missed, .status-badge.no_show { background: #ffebee; color: #c62828; }

.payment-badge.payment-paid { background: #e8f5e9; color: #2e7d32; }
.payment-badge.payment-unpaid { background: #fff3e0; color: #e65100; }
.payment-badge.payment-neutral { background: #f5f5f5; color: #9e9e9e; }

.row-success { background: #f1f8e9; }
.row-danger { background: #fce4ec; }
.row-warning { background: #fff8e1; }
.row-neutral { background: #fafafa; opacity: 0.7; }

.empty-attendance {
  text-align: center;
  padding: 40px;
  color: #8e8e8e;
}

/* ==================== СТИЛИ ЗАПИСИ НА УРОК ==================== */
.booking-section {
  margin: 20px 0;
  text-align: center;
}

.booking-btn {
  padding: 15px 30px;
  font-size: 1.1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.booking-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 30px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
}

.booking-modal h2 {
  margin-top: 0;
  color: #333;
}

.booking-step label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}

.form-select, .form-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  margin-bottom: 15px;
  box-sizing: border-box;
}

.form-select:focus, .form-input:focus {
  border-color: #667eea;
  outline: none;
}

.slots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
  margin: 15px 0;
}

.slot-item {
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.slot-item:hover {
  border-color: #667eea;
  background: #f5f7ff;
}

.slot-item.selected {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.modal-actions button {
  flex: 1;
}

.close-modal-btn {
  position: absolute;
  top: 15px;
  right: 20px;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
}

.close-modal-btn:hover {
  color: #333;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.no-slots {
  text-align: center;
  padding: 20px;
  color: #999;
}

.confirmation {
  text-align: center;
}

.confirmation p {
  margin: 15px 0;
  font-size: 1.1rem;
}


.cancel-btn-small {
  background: #dc3545;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-top: 5px;
}
.cancel-btn-small:hover {
  background: #c82333;
}
.no-cancel-hint {
  font-size: 11px;
  color: #999;
  margin-top: 5px;
}
</style>