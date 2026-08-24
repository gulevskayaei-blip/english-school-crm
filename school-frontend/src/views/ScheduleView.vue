<template>
  <div class="schedule-container">
    <div class="header">
      <h1>📅 Расписание занятий</h1>
      <button @click="goBack" class="back-btn">← Назад</button>
    </div>

    <!-- Фильтры -->
    <div class="filters">
      <div class="filter-group">
        <label>🏢 Филиал:</label>
        <select v-model="filters.branch_id">
          <option :value="null">Все филиалы</option>
          <option v-for="branch in branchesList" :key="branch.id" :value="branch.id">
            {{ branch.name }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label>👨‍🏫 Преподаватель:</label>
        <select v-model="filters.teacher_id">
          <option :value="null">Все преподаватели</option>
          <option v-for="teacher in teachersList" :key="teacher.id" :value="teacher.id">
            {{ getTeacherDisplayName(teacher) }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label>👥 Группа/Курс:</label>
        <select v-model="filters.course_id">
          <option :value="null">Все группы</option>
          <option v-for="course in coursesList" :key="course.id" :value="course.id">
            {{ course.name }}
          </option>
        </select>
      </div>

      <button @click="applyFilters" class="filter-btn">🔍 Применить</button>
      <button @click="resetFilters" class="reset-filter-btn">🔄 Сбросить</button>
    </div>

    <!-- Управление календарем -->
    <div class="calendar-controls">
      <button @click="prevWeek" class="nav-btn">◀ Предыдущая неделя</button>
      <h2>{{ weekRange }}</h2>
      <button @click="nextWeek" class="nav-btn">Следующая неделя ▶</button>
      <button @click="today" class="today-btn">📅 Сегодня</button>
      <button @click="updateAllStatuses" class="update-btn">🔄 Обновить статусы</button>
    </div>

    <!-- Кнопка добавления занятия -->
    <button v-if="profile.role !== 'student'" @click="openAddModal" class="add-btn">➕ Добавить занятие</button>

    <!-- Календарная сетка -->
    <div class="calendar-grid">
      <div class="calendar-header">
        <div class="time-column">Время</div>
        <div v-for="day in weekDays" :key="day.date" class="day-header" :class="{ today: isToday(day.date) }">
          <div class="day-name">{{ day.name }}</div>
          <div class="day-date">{{ formatDate(day.date) }}</div>
        </div>
      </div>

      <div v-for="hour in hours" :key="hour" class="calendar-row">
        <div class="time-column">{{ hour }}:00</div>
        <div v-for="day in weekDays" :key="day.date" class="calendar-cell" :class="{ 'has-lessons': getFilteredLessonsAt(day.date, hour).length > 0 }" @click="profile.role !== 'student' ? openAddModalAt(day.date, hour) : null">
          <div v-for="lesson in getFilteredLessonsAt(day.date, hour)" :key="lesson.id" class="lesson-cell" :class="[lesson.status, { 'other-teacher': !isOwnLesson(lesson) }]" @click.stop="openEditModal(lesson)">
            <div class="lesson-time">{{ getLessonTime(lesson) }}</div>
            <div class="lesson-teacher">{{ getTeacherName(lesson) }}</div>
            <div class="lesson-student">
              <span v-if="profile.role === 'student' && lesson.type === 'individual'">🔒 Занято</span>
              <span v-else-if="profile.role === 'student' && lesson.type === 'group'">{{ lesson.course?.name || 'Групповое' }}</span>
              <span v-else>{{ getStudentName(lesson) }}</span>
            </div>
            <div v-if="lesson.custom_rate" class="lesson-rate">💰 {{ lesson.custom_rate }} ₽/ч</div>
            <div class="lesson-actions">
              <button v-if="isOwnLesson(lesson)" @click.stop="deleteLesson(lesson.id)" class="delete-btn-small" title="Удалить">🗑️</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно добавления/редактирования занятия -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h2>{{ isEditing ? '✏️ Редактировать занятие' : '➕ Новое занятие' }}</h2>
        
        <div class="form-group">
          <label>🏢 Филиал *</label>
          <select v-model="formData.branch_id" :disabled="isReadOnly || profile.role === 'teacher'">
            <option :value="null">-- Выберите филиал --</option>
            <option v-for="branch in branchesList" :key="branch.id" :value="branch.id">
              {{ branch.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>👨‍🏫 Преподаватель *</label>
          <select v-model="formData.teacher_id" :disabled="isReadOnly || profile.role === 'teacher'">
            <option :value="null">-- Выберите преподавателя --</option>
            <option v-for="teacher in teachersList" :key="teacher.id" :value="teacher.id">
              {{ getTeacherDisplayName(teacher) }} ({{ teacher.hourly_rate }} ₽/ч)
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>👨‍🎓 Студент *</label>
          <select v-model="formData.student_id" :disabled="isReadOnly || profile.role === 'teacher'">
            <option :value="null">-- Выберите студента --</option>
            <option v-for="student in studentsList" :key="student.id" :value="student.id">
              {{ getStudentDisplayName(student) }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>👥 Группа/Курс</label>
          <select v-model="formData.course_id" :disabled="isReadOnly || profile.role === 'teacher'">
            <option :value="null">-- Без группы --</option>
            <option v-for="course in coursesList" :key="course.id" :value="course.id">
              {{ course.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>📅 Дата и время *</label>
          <input type="datetime-local" v-model="formData.datetime_start" :disabled="isReadOnly || profile.role === 'teacher'">
        </div>

        <div class="form-group">
          <label>⏰ Длительность (часов) *</label>
          <input type="number" v-model="formData.duration" :disabled="isReadOnly || profile.role === 'teacher'" step="0.5" min="0.5">
        </div>

        <div class="form-group">
          <label>💰 Индивидуальная ставка (₽/час)</label>
          <input type="number" v-model="formData.custom_rate" :disabled="isReadOnly || profile.role === 'teacher'" step="100" placeholder="Оставьте пустым для базовой ставки">
          <small class="hint">Если указана, будет использована вместо базовой ставки преподавателя</small>
        </div>

        <div class="form-group">
          <label>📋 Тип занятия *</label>
          <select v-model="formData.type" :disabled="isReadOnly || profile.role === 'teacher'">
            <option value="individual">👤 Индивидуальное</option>
            <option value="group">👥 Групповое</option>
          </select>
        </div>

        <div class="form-group">
          <label>📍 Формат</label>
          <select v-model="formData.format" :disabled="isReadOnly || profile.role === 'teacher'">
            <option value="offline">🏢 Офлайн</option>
            <option value="online">💻 Онлайн</option>
          </select>
        </div>

        <div class="form-group">
          <label>📊 Статус занятия</label>
          <select v-model="formData.status" :disabled="isReadOnly || profile.role === 'teacher'">
            <option value="scheduled">📅 Запланировано</option>
            <option value="completed">✅ Проведено</option>
            <option value="cancelled">❌ Отменено</option>
          </select>
        </div>

        <div class="form-group" v-if="profile.role !== 'student' && (formData.status === 'completed' || formData.status === 'scheduled')">
          <label>📝 Посещаемость ученика</label>
          <select v-model="attendance_status" :disabled="isReadOnly || profile.role === 'teacher'">
            <option value="">-- Не отмечено --</option>
            <option value="present">✅ Присутствовал</option>
            <option value="late">⏰ Опоздал</option>
            <option value="sick">🤒 Болезнь</option>
            <option value="absent_no_reason">❌ Отсутствует без причины</option>
          </select>
        </div>

        <!-- Домашнее задание -->
        <div class="form-group homework-section" v-if="profile.role === 'teacher' && isOwnLessonCurrent && formData.student_id">
          <h3>📚 Домашнее задание</h3>
          <div class="hw-field">
            <label>Название задания</label>
            <input v-model="hw_title" type="text" placeholder="Например: Упражнение 10, стр. 25" />
          </div>
          <div class="hw-field">
            <label>Описание</label>
            <textarea v-model="hw_description" rows="3" placeholder="Дополнительные инструкции..."></textarea>
          </div>
          <div class="hw-field">
            <label>📎 Файл (аудио, PDF, изображение)</label>
            <input type="file" @change="handleHwFileChange" accept=".mp3,.wav,.m4a,.pdf,.png,.jpg,.jpeg" />
            <small>Поддерживаются: MP3, WAV, M4A, PDF, PNG, JPG</small>
          </div>
          <div v-if="hw_file" class="hw-file-info">
            📄 Выбран файл: {{ hw_file.name }}
          </div>
        </div>


        <div class="form-group">
          <label>🔄 Повторять занятие</label>
          <select v-model="formData.recurring_type" :disabled="isReadOnly || profile.role === 'teacher'">
            <option :value="null">Нет</option>
            <option value="weekly">Каждую неделю</option>
            <option value="biweekly">Раз в 2 недели</option>
            <option value="monthly">Каждый месяц</option>
          </select>
        </div>

        <div v-if="formData.recurring_type" class="form-group">
          <label>📅 Дата окончания повторов</label>
          <input type="date" v-model="formData.recurring_end_date" :disabled="isReadOnly || profile.role === 'teacher'">
          <small class="hint">Оставьте пустым для 10 повторов</small>
        </div>

        <div class="form-actions">
          <button v-if="!isReadOnly" @click="saveLesson" class="save-btn">💾 Сохранить</button>
          <button @click="closeModal" class="cancel-btn">❌ Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'ScheduleView',
  data() {
    return {
      lessonsList: [],
      teachersList: [],
      studentsList: [],
      branchesList: [],
      coursesList: [],
      showModal: false,
      isEditing: false,
      editingId: null,
      loading: false,
      currentDate: new Date(),
      hours: [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
      filters: {
        branch_id: null,
        teacher_id: null,
        course_id: null
      },
      profile: {},
      formData: {
        branch_id: null,
        teacher_id: null,
        student_id: null,
        course_id: null,
        datetime_start: '',
        duration: 1,
        custom_rate: null,
        type: 'individual',
        format: 'offline',
        status: 'scheduled',
        recurring_type: null,
        recurring_end_date: '',
        attendance_id: null,
        attendance_status: '',
        isReadOnly: false,
        hw_title: '',
        hw_description: '',
        hw_file: null,
        hw_existing_id: null
      }
    }
  },
  computed: {
    isOwnLessonCurrent() {
      // Проверяем, является ли текущее открытое занятие занятием текущего учителя
      if (!this.formData.teacher_id || !this.profile.teacher_id) return false
      return this.formData.teacher_id === this.profile.teacher_id
    },
    weekDays() {
      const days = []
      const startOfWeek = new Date(this.currentDate)
      const day = startOfWeek.getDay()
      const diff = startOfWeek.getDate() - day + (day === 0 ? -6 : 1)
      startOfWeek.setDate(diff)
      
      for (let i = 0; i < 7; i++) {
        const date = new Date(startOfWeek)
        date.setDate(startOfWeek.getDate() + i)
        days.push({
          name: this.getDayName(date.getDay()),
          date: date
        })
      }
      return days
    },
    
    weekRange() {
      const start = this.weekDays[0].date
      const end = this.weekDays[6].date
      return `${this.formatDate(start)} - ${this.formatDate(end)}`
    }
  },
  async mounted() {
    await this.loadProfile()
    await this.loadBranches()
    await this.loadTeachers()
    await this.loadStudents()
    await this.loadCourses()
    await this.loadLessons()
    await this.updateAllStatuses()
  },
  methods: {
    goBack() {
      this.$router.push('/dashboard')
    },
    async loadProfile() {
      try {
        const res = await api.get('users/me/');
        this.profile = res.data;
      } catch (error) {
        console.error('Ошибка загрузки профиля', error);
      }
    },

    
    getDayName(dayIndex) {
      const days = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
      return days[dayIndex]
    },
    
    formatDate(date) {
      if (!date) return ''
      return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit'
      })
    },
    
    formatDateTime(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    isToday(date) {
      const today = new Date()
      return date.toDateString() === today.toDateString()
    },
    
    prevWeek() {
      this.currentDate.setDate(this.currentDate.getDate() - 7)
      this.currentDate = new Date(this.currentDate)
      this.loadLessons()
    },
    
    nextWeek() {
      this.currentDate.setDate(this.currentDate.getDate() + 7)
      this.currentDate = new Date(this.currentDate)
      this.loadLessons()
    },
    
    today() {
      this.currentDate = new Date()
      this.loadLessons()
    },
    
    applyFilters() {
      this.loadLessons()
    },
    
    resetFilters() {
      this.filters = {
        branch_id: null,
        teacher_id: null,
        course_id: null
      }
      this.loadLessons()
    },
    
    getTeacherDisplayName(teacher) {
      if (!teacher) return '—'
      if (teacher.profile?.user?.username) return teacher.profile.user.username
      if (teacher.profile?.user?.first_name) {
        const firstName = teacher.profile.user.first_name
        const lastName = teacher.profile.user.last_name
        return lastName ? `${firstName} ${lastName}` : firstName
      }
      if (teacher.name) return teacher.name
      return `Преподаватель #${teacher.id}`
    },
    
    getStudentDisplayName(student) {
      if (!student) return '—'
      if (student.profile?.user?.username) return student.profile.user.username
      if (student.name) return student.name
      return `Студент #${student.id}`
    },
    
    getTeacherName(lesson) {
      if (!lesson.teacher) return '—'
      if (lesson.teacher.profile?.user?.username) return lesson.teacher.profile.user.username
      if (lesson.teacher.name) return lesson.teacher.name
      return 'Преподаватель'
    },
    
    isOwnLesson(lesson) {
      if (this.profile.role !== 'teacher') return true
      const teacherId = typeof lesson.teacher === 'object' ? lesson.teacher?.id : lesson.teacher
      return teacherId === this.profile.teacher_id
    },

    getStudentName(lesson) {
      if (!lesson.student) return '—'
      if (lesson.student.profile?.user?.username) return lesson.student.profile.user.username
      if (lesson.student.name) return lesson.student.name
      return 'Студент'
    },
    
    getLessonTime(lesson) {
      if (!lesson.datetime_start) return ''
      const date = new Date(lesson.datetime_start)
      return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    },
    
    getLessonsAt(date, hour) {
      return this.lessonsList.filter(lesson => {
        const lessonDate = new Date(lesson.datetime_start)
        // Сравниваем только дату (год, месяц, день) без учета времени и часовых поясов
        const sameDate = lessonDate.getFullYear() === date.getFullYear() &&
                        lessonDate.getMonth() === date.getMonth() &&
                        lessonDate.getDate() === date.getDate()
        // Сравниваем час (в локальном времени браузера)
        const sameHour = lessonDate.getHours() === hour
        return sameDate && sameHour
      })
    },
    
    getFilteredLessonsAt(date, hour) {
      let lessons = this.getLessonsAt(date, hour)
      
      // Фильтр по филиалу
      if (this.filters.branch_id) {
        lessons = lessons.filter(lesson => lesson.branch?.id === this.filters.branch_id)
      }
      
      // Фильтр по преподавателю
      if (this.filters.teacher_id) {
        lessons = lessons.filter(lesson => lesson.teacher?.id === this.filters.teacher_id)
      }
      
      // Фильтр по группе/курсу
      if (this.filters.course_id) {
        lessons = lessons.filter(lesson => lesson.course?.id === this.filters.course_id)
      }
      
      return lessons
    },
    
    async updateAllStatuses() {
      const now = new Date()
      let updated = 0
      
      for (const lesson of this.lessonsList) {
        const lessonDate = new Date(lesson.datetime_start)
        if (lesson.status === 'scheduled' && lessonDate < now) {
          try {
            await api.patch(`/lessons/${lesson.id}/`, { status: 'completed' })
            updated++
          } catch (error) {
            console.error('Ошибка обновления:', error)
          }
        }
      }
      
      if (updated > 0) {
        console.log(`Обновлено ${updated} занятий на статус "completed"`)
        await this.loadLessons()
      }
    },
    
    openAddModal() {
      this.isEditing = false
      this.editingId = null
      this.formData = {
        branch_id: null,
        teacher_id: null,
        student_id: null,
        course_id: null,
        datetime_start: '',
        duration: 1,
        custom_rate: null,
        type: 'individual',
        format: 'offline',
        status: 'scheduled',
        recurring_type: null,
        recurring_end_date: ''
      }
      this.showModal = true
    },
    
    openAddModalAt(date, hour) {
      const datetime = new Date(date)
      datetime.setHours(hour, 0, 0)
      this.isEditing = false
      this.editingId = null
      this.formData = {
        branch_id: null,
        teacher_id: null,
        student_id: null,
        course_id: null,
        datetime_start: datetime.toISOString().slice(0, 16),
        duration: 1,
        custom_rate: null,
        type: 'individual',
        format: 'offline',
        status: 'scheduled',
        recurring_type: null,
        recurring_end_date: ''
      }
      this.showModal = true
    },
    async openEditModal(lesson) {
      this.isEditing = true
      this.editingId = lesson.id
      this.isReadOnly = !this.isOwnLesson(lesson)
      
      let duration = 1
      if (lesson.datetime_end && lesson.datetime_start) {
        const start = new Date(lesson.datetime_start)
        const end = new Date(lesson.datetime_end)
        duration = (end - start) / (1000 * 60 * 60)
      }
      
      this.formData = {
        branch_id: typeof lesson.branch === "object" ? lesson.branch?.id : lesson.branch,
        teacher_id: typeof lesson.teacher === "object" ? lesson.teacher?.id : lesson.teacher,
        student_id: typeof lesson.student === "object" ? lesson.student?.id : lesson.student,
        course_id: typeof lesson.course === "object" ? lesson.course?.id : lesson.course,
        datetime_start: lesson.datetime_start?.slice(0, 16) || '',
        duration: duration,
        custom_rate: lesson.custom_rate || null,
        type: lesson.type || 'individual',
        format: lesson.format || 'offline',
        status: lesson.status || 'scheduled',
        recurring_type: lesson.recurring_type || null,
        recurring_end_date: lesson.recurring_end_date || ''
      }
      this.showModal = true
      await this.loadHomeworkForLesson(lesson.id, lesson.student?.id)
    },
    
    async loadBranches() {
      try {
        const response = await api.get('/branches/')
        this.branchesList = response.data
        console.log('Филиалы загружены:', this.branchesList)
      } catch (error) {
        console.error('Ошибка загрузки филиалов:', error)
        this.branchesList = []
      }
    },
    
    async loadTeachers() {
      try {
        const response = await api.get('/teachers/')
        this.teachersList = response.data
        console.log('Преподаватели загружены:', this.teachersList)
      } catch (error) {
        console.error('Ошибка загрузки преподавателей:', error)
        this.teachersList = []
      }
    },
    
    async loadStudents() {
      try {
        const response = await api.get('/students/')
        this.studentsList = response.data
        console.log('Студенты загружены:', this.studentsList)
      } catch (error) {
        console.error('Ошибка загрузки студентов:', error)
        this.studentsList = []
      }
    },
    
    async loadCourses() {
      try {
        const response = await api.get('/courses/')
        this.coursesList = response.data
        console.log('Курсы загружены:', this.coursesList)
      } catch (error) {
        console.error('Ошибка загрузки курсов:', error)
        this.coursesList = []
      }
    },
    
    async loadLessons() {
      try {
        this.loading = true
        const response = await api.get('/lessons/')
        let lessons = response.data
        
        // Применяем фильтры на бэкенде (если нужно)
        if (this.filters.branch_id) {
          lessons = lessons.filter(l => l.branch?.id === this.filters.branch_id)
        }
        if (this.filters.teacher_id) {
          lessons = lessons.filter(l => l.teacher?.id === this.filters.teacher_id)
        }
        if (this.filters.course_id) {
          lessons = lessons.filter(l => l.course?.id === this.filters.course_id)
        }
        
        this.lessonsList = lessons
        console.log('Занятия загружены:', this.lessonsList.length)
      } catch (error) {
        console.error('Ошибка загрузки занятий:', error)
      } finally {
        this.loading = false
      }
    },
    
    async saveLesson() {
      if (!this.formData.branch_id) {
        alert('Выберите филиал')
        return
      }
      if (!this.formData.teacher_id) {
        alert('Выберите преподавателя')
        return
      }
      if (!this.formData.student_id) {
        alert('Выберите студента')
        return
      }
      if (!this.formData.datetime_start) {
        alert('Выберите дату и время')
        return
      }
      
      try {
        const startDate = new Date(this.formData.datetime_start)
        const endDate = new Date(startDate)
        endDate.setHours(startDate.getHours() + this.formData.duration)
        
        const lessonData = {
          branch: this.formData.branch_id,
          teacher: this.formData.teacher_id,
          student: this.formData.student_id,
          course: this.formData.course_id || null,
          datetime_start: startDate.toISOString(),
          datetime_end: endDate.toISOString(),
          type: this.formData.type,
          format: this.formData.format,
          status: this.formData.status,
          custom_rate: this.formData.custom_rate ? parseFloat(this.formData.custom_rate) : null,
          is_recurring: !!this.formData.recurring_type,
          recurring_type: this.formData.recurring_type,
          recurring_end_date: this.formData.recurring_end_date || null
        }
        
        let lessonIdForHw = this.editingId;
        if (this.isEditing) {
          await api.put(`/lessons/${this.editingId}/`, lessonData)
          alert('Занятие обновлено!')
        } else {
          const res = await api.post('/lessons/', lessonData)
          lessonIdForHw = res.data.id;
          alert('Занятие создано!')
        }

        // Сохраняем ДЗ, если учитель заполнил поля (ПЕРЕД closeModal!)
        if (this.profile.role === 'teacher' && this.isOwnLessonCurrent && this.formData.student_id) {
          await this.saveHomework(lessonIdForHw, this.formData.student_id)
        }

        this.closeModal()
        await this.loadLessons()
        await this.updateAllStatuses()
      } catch (error) {
        console.error('Ошибка сохранения:', error)
        alert('Ошибка при сохранении занятия: ' + (error.response?.data?.message || error.message))
      }
    },
    
    async deleteLesson(id) {
      if (confirm('Удалить это занятие?')) {
        try {
          await api.delete(`/lessons/${id}/`)
          alert('Занятие удалено!')
          await this.loadLessons()
        } catch (error) {
          console.error('Ошибка удаления:', error)
          alert('Ошибка при удалении')
        }
      }
    },
    
    async loadHomeworkForLesson(lessonId, studentId) {
      this.hw_title = ''
      this.hw_description = ''
      this.hw_file = null
      this.hw_existing_id = null
      if (!lessonId || !studentId) return
      try {
        const res = await api.get('/homeworks/', { params: { lesson: lessonId } })
        if (res.data && res.data.length > 0) {
          const hw = res.data[0]
          this.hw_existing_id = hw.id
          this.hw_title = hw.title
          this.hw_description = hw.description || ''
        }
      } catch (e) {
        console.error('Ошибка загрузки ДЗ:', e)
      }
    },

    handleHwFileChange(event) {
      this.hw_file = event.target.files[0] || null
    },

    async saveHomework(lessonId, studentId) {
      if (!this.hw_title && !this.hw_description && !this.hw_file) return
      try {
        const formData = new FormData()
        formData.append('lesson', lessonId)
        formData.append('student', studentId)
        formData.append('teacher', this.formData.teacher_id)
        formData.append('title', this.hw_title || 'Домашнее задание')
        formData.append('description', this.hw_description || '')
        if (this.hw_file) {
          formData.append('file', this.hw_file)
        }

        if (this.hw_existing_id) {
          await api.put(`/homeworks/${this.hw_existing_id}/`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
        } else {
          await api.post('/homeworks/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })
        }
      } catch (e) {
        console.error('Ошибка сохранения ДЗ:', e)
      }
    },

    closeModal() {
      this.showModal = false
      this.isEditing = false
      this.editingId = null
      this.isReadOnly = false
      this.hw_title = ''
      this.hw_description = ''
      this.hw_file = null
      this.hw_existing_id = null
    }
  }
}
</script>

<style scoped>
.schedule-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.back-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
}

/* Стили для фильтров */
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-group label {
  font-size: 12px;
  font-weight: bold;
  color: #333;
}

.filter-group select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 160px;
}

.filter-btn, .reset-filter-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.filter-btn {
  background: #007bff;
  color: white;
}

.reset-filter-btn {
  background: #6c757d;
  color: white;
}

.calendar-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.nav-btn, .today-btn, .update-btn {
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  cursor: pointer;
}

.nav-btn {
  background: #007bff;
}

.today-btn {
  background: #28a745;
}

.update-btn {
  background: #ffc107;
  color: #333;
}

.add-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  margin-bottom: 20px;
}

.calendar-grid {
  background: white;
  border-radius: 8px;
  overflow-x: auto;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.calendar-header {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
}

.day-header {
  text-align: center;
  padding: 12px;
  border-right: 1px solid #dee2e6;
}

.day-header.today {
  background: #fff3cd;
}

.day-name {
  font-weight: bold;
  font-size: 14px;
}

.day-date {
  font-size: 12px;
  color: #6c757d;
}

.calendar-row {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  border-bottom: 1px solid #dee2e6;
}

.time-column {
  padding: 10px;
  background: #f8f9fa;
  text-align: center;
  font-weight: bold;
  border-right: 1px solid #dee2e6;
}

.calendar-cell {
  min-height: 80px;
  padding: 5px;
  border-right: 1px solid #dee2e6;
  cursor: pointer;
  transition: background 0.2s;
}

.calendar-cell:hover {
  background: #f8f9fa;
}

.calendar-cell.has-lessons {
  background: #e3f2fd;
  padding: 0;
}

.lesson-cell {
  background: #2196f3;
  color: white;
  padding: 5px;
  border-radius: 4px;
  margin: 2px;
  cursor: pointer;
  transition: transform 0.2s;
}

.lesson-cell:hover {
  transform: scale(1.02);
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.lesson-cell.completed {
  background: #28a745;
}

.lesson-cell.cancelled {
  background: #dc3545;
  opacity: 0.7;
}

.lesson-time {
  font-size: 10px;
  font-weight: bold;
  margin-bottom: 2px;
}

.lesson-teacher, .lesson-student, .lesson-rate {
  font-size: 9px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lesson-rate {
  color: #ffd700;
}

.lesson-actions {
  display: flex;
  gap: 3px;
  margin-top: 3px;
  justify-content: flex-end;
}

.delete-btn-small {
  background: rgba(255,255,255,0.3);
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 9px;
  padding: 2px 4px;
}

.delete-btn-small:hover {
  background: rgba(255,255,255,0.5);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  width: 550px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h2 {
  margin: 0 0 20px 0;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.hint {
  font-size: 11px;
  color: #6c757d;
  margin-top: 3px;
  display: block;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.save-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  flex: 1;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  flex: 1;
}
.lesson-cell.other-teacher { background: #95a5a6; opacity: 0.6; border: 2px dashed #7f8c8d; }

.homework-section {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}
.homework-section h3 {
  margin-top: 0;
  color: #495057;
}
.hw-field {
  margin-bottom: 12px;
}
.hw-field label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: #495057;
}
.hw-field input[type="text"],
.hw-field textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
}
.hw-field small {
  color: #6c757d;
  font-size: 11px;
}
.hw-file-info {
  background: #e3f2fd;
  padding: 8px;
  border-radius: 4px;
  font-size: 13px;
  color: #1565c0;
}
</style>