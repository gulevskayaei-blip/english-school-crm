<template>
  <div class="booking-wizard">
    <!-- Заголовок -->
    <div class="header">
      <h1>Запись на занятия</h1>
      <p>Выберите удобное время и формат обучения</p>
      <button class="test-btn" @click="$router.push('/level-test')">📝 Определить свой уровень</button>
    </div>

    <!-- Шаг 1: Выбор формата -->
    <div class="step-cards">
      <div 
        class="card" 
        :class="{ active: mode === 'group' }"
        @click="selectMode('group')"
      >
        <div class="card-icon">🏫</div>
        <h3>В группу</h3>
        <p>Занятия в мини-группах до 8 человек</p>
      </div>
      <div 
        class="card" 
        :class="{ active: mode === 'individual' }"
        @click="selectMode('individual')"
      >
        <div class="card-icon">👤</div>
        <h3>Индивидуально</h3>
        <p>Персональные занятия с преподавателем</p>
      </div>
    </div>

    <!-- Шаг 2: Сетка расписания -->
    <div v-if="mode">
      <!-- Фильтры -->
      <div class="filters" v-if="mode === 'group'">
        <select v-model="selectedBranch" @change="loadSchedule">
          <option value="">Все филиалы</option>
          <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
        </select>
      </div>

      <!-- Сетка на неделю -->
      <div class="schedule-grid" v-if="schedule.length || loading">
        <h2>Расписание на неделю</h2>
        <div class="week-navigation">
          <button @click="prevWeek">←</button>
          <span>{{ weekStart }} — {{ weekEnd }}</span>
          <button @click="nextWeek">→</button>
        </div>

        <div class="grid">
          <div class="grid-header">
            <div class="time-col">Время</div>
            <div v-for="day in weekDays" :key="day.date" class="day-col" :class="{ today: day.isToday }">
              <div class="day-name">{{ day.name }}</div>
              <div class="day-date">{{ day.date }}</div>
            </div>
          </div>

          <div class="grid-body">
            <div v-for="hour in hours" :key="hour" class="grid-row">
              <div class="time-cell">{{ hour }}:00</div>
              <div v-for="day in weekDays" :key="day.date" class="cell">
                <div 
                  v-for="lesson in getLessonsForCell(day.date, hour)" 
                  :key="lesson.id"
                  class="lesson-card"
                  :class="{ 
                    'has-slots': lesson.has_free_slots && mode === 'group',
                    'no-slots': !lesson.has_free_slots && mode === 'group',
                    'individual': mode === 'individual',
                    'clickable': isClickable(lesson)
                  }"
                  @click="selectLesson(lesson)"
                >
                  <div class="lesson-time">{{ lesson.time_start }} — {{ lesson.time_end }}</div>
                  <div class="lesson-course">{{ lesson.course_name || lesson.teacher_name }}</div>
                  <div class="lesson-teacher">{{ lesson.teacher_name }}</div>
                  <div class="lesson-slots" v-if="mode === 'group'">
                    <span class="slots-badge" :class="{ free: lesson.has_free_slots, full: !lesson.has_free_slots }">
                      {{ lesson.has_free_slots ? `Свободно ${lesson.free_slots} мест` : 'Нет мест' }}
                    </span>
                  </div>
                  <div class="lesson-price">{{ lesson.price }} ₽</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Загрузка -->
      <div v-if="loading" class="loading">Загрузка расписания...</div>
    </div>

    <!-- Шаг 3: Модальное окно записи -->
    <div v-if="selectedLesson" class="modal-overlay" @click.self="selectedLesson = null">
      <div class="modal">
        <h2>Записаться на занятие</h2>
        <div class="lesson-info">
          <p><strong>{{ selectedLesson.course_name || 'Индивидуальное занятие' }}</strong></p>
          <p>📅 {{ selectedLesson.date }} | 🕐 {{ selectedLesson.time_start }} — {{ selectedLesson.time_end }}</p>
          <p>👨‍🏫 {{ selectedLesson.teacher_name }}</p>
          <p v-if="selectedLesson.price">💰 {{ selectedLesson.price }} ₽</p>
        </div>

        <form @submit.prevent="submitBooking">
          <input v-model="form.full_name" placeholder="Ваше ФИО *" required />
          <input v-model="form.phone" placeholder="Телефон *" required />
          <input v-model="form.email" placeholder="Email" type="email" />
          <textarea v-model="form.comment" placeholder="Комментарий"></textarea>
          
          <button type="submit" :disabled="sending">
            {{ sending ? 'Отправка...' : 'Записаться' }}
          </button>
          
          <div v-if="success" class="success">✅ Заявка отправлена!</div>
          <div v-if="error" class="error">❌ {{ error }}</div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'PublicSchedule',
  data() {
    return {
      mode: null,
      selectedBranch: null,
      schedule: [],
      branches: [],
      loading: false,
      selectedLesson: null,
      form: {
        full_name: '',
        phone: '',
        email: '',
        comment: '',
      },
      sending: false,
      success: false,
      error: null,
      weekOffset: 0,
      hours: Array.from({ length: 13 }, (_, i) => i + 8),
    }
  },
  computed: {
    weekDays() {
      const today = new Date()
      const monday = new Date(today)
      monday.setDate(today.getDate() - today.getDay() + 1 + this.weekOffset * 7)
      
      const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
      return days.map((name, i) => {
        const date = new Date(monday)
        date.setDate(monday.getDate() + i)
        const todayDate = new Date()
        return {
          name,
          date: date.toISOString().split('T')[0],
          isToday: date.toDateString() === todayDate.toDateString(),
        }
      })
    },
    weekStart() {
      return this.weekDays[0].date
    },
    weekEnd() {
      return this.weekDays[6].date
    },
  },
  mounted() {
    this.loadBranches()
  },
  methods: {
    async loadBranches() {
      try {
        const res = await api.get('/booking/branches/')
        this.branches = res.data
      } catch (e) {
        console.error(e)
      }
    },
    async loadSchedule() {
      this.loading = true
      try {
        const params = { mode: this.mode }
        if (this.selectedBranch) params.branch = this.selectedBranch
        const res = await api.get('/booking/schedule/', { params })
        this.schedule = res.data
      } catch (e) {
        console.error(e)
      } finally {
        this.loading = false
      }
    },
    selectMode(mode) {
      this.mode = mode
      this.schedule = []
      this.loadSchedule()
    },
    prevWeek() {
      this.weekOffset--
      this.loadSchedule()
    },
    nextWeek() {
      this.weekOffset++
      this.loadSchedule()
    },
    getLessonsForCell(date, hour) {
      return this.schedule.filter(lesson => {
        return lesson.date === date && 
               parseInt(lesson.time_start.split(':')[0]) === hour
      })
    },
    isClickable(lesson) {
      if (this.mode === 'group') return lesson.has_free_slots
      return true
    },
    selectLesson(lesson) {
      if (!this.isClickable(lesson)) return
      this.selectedLesson = lesson
      this.form = {
        full_name: '',
        phone: '',
        email: '',
        comment: '',
        mode: this.mode,
        branch: lesson.branch_id,
        course: lesson.course_id || null,
        teacher: lesson.teacher_id || null,
      }
      this.success = false
      this.error = null
    },
    async submitBooking() {
      this.sending = true
      this.error = null
      try {
        await api.post('/booking/request/', this.form)
        this.success = true
        setTimeout(() => {
          this.selectedLesson = null
        }, 2000)
      } catch (e) {
        this.error = e.response?.data ? Object.values(e.response.data).flat().join(', ') : 'Ошибка'
      } finally {
        this.sending = false
      }
    },
  },
}
</script>

<style scoped>
.booking-wizard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', sans-serif;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 32px;
  color: #2c3e50;
  margin-bottom: 10px;
}

.step-cards {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 40px;
}

.card {
  flex: 1;
  max-width: 300px;
  padding: 30px;
  border: 2px solid #e0e0e0;
  border-radius: 15px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.card:hover {
  border-color: #42b983;
  transform: translateY(-2px);
  box-shadow: 0 5px 20px rgba(0,0,0,0.1);
}

.card.active {
  border-color: #42b983;
  background: #f0fff4;
}

.card-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.card h3 {
  margin: 0 0 10px;
  color: #2c3e50;
}

.card p {
  color: #666;
  margin: 0;
}

.filters {
  margin-bottom: 20px;
}

.filters select {
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  min-width: 250px;
}

.schedule-grid {
  background: white;
  border-radius: 15px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: hidden;
}

.schedule-grid h2 {
  padding: 20px;
  margin: 0;
  background: #42b983;
  color: white;
}

.week-navigation {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 15px;
  background: #f8f9fa;
}

.week-navigation button {
  padding: 5px 15px;
  border: none;
  background: #42b983;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}

.grid {
  overflow-x: auto;
}

.grid-header {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  background: #f8f9fa;
  border-bottom: 2px solid #dee2e6;
}

.time-col, .day-col {
  padding: 10px;
  text-align: center;
  font-weight: bold;
  border-right: 1px solid #dee2e6;
}

.today {
  background: #fff3cd;
}

.grid-body {
  max-height: 600px;
  overflow-y: auto;
}

.grid-row {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  min-height: 80px;
  border-bottom: 1px solid #eee;
}

.time-cell {
  padding: 5px;
  text-align: center;
  font-size: 12px;
  color: #999;
  border-right: 1px solid #eee;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.cell {
  padding: 3px;
  border-right: 1px solid #eee;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.lesson-card {
  padding: 5px;
  border-radius: 5px;
  font-size: 11px;
  cursor: default;
  border-left: 3px solid #ccc;
}

.lesson-card.has-slots {
  background: #d4edda;
  border-left-color: #28a745;
  cursor: pointer;
}

.lesson-card.no-slots {
  background: #f8d7da;
  border-left-color: #dc3545;
  opacity: 0.7;
}

.lesson-card.individual {
  background: #d1ecf1;
  border-left-color: #17a2b8;
  cursor: pointer;
}

.lesson-card.clickable:hover {
  transform: scale(1.02);
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.lesson-time {
  font-weight: bold;
  margin-bottom: 2px;
}

.lesson-course {
  color: #2c3e50;
}

.lesson-teacher {
  color: #666;
  font-size: 10px;
}

.slots-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: bold;
}

.slots-badge.free {
  background: #28a745;
  color: white;
}

.slots-badge.full {
  background: #dc3545;
  color: white;
}

.lesson-price {
  color: #28a745;
  font-weight: bold;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #999;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 15px;
  padding: 30px;
  max-width: 450px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}

.modal h2 {
  margin: 0 0 20px;
  color: #2c3e50;
}

.lesson-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.lesson-info p {
  margin: 5px 0;
}

form input, form textarea {
  width: 100%;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}

form button {
  width: 100%;
  padding: 12px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}

form button:disabled {
  background: #ccc;
}

.success {
  margin-top: 10px;
  padding: 10px;
  background: #d4edda;
  color: #155724;
  border-radius: 8px;
  text-align: center;
}

.error {
  margin-top: 10px;
  padding: 10px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 8px;
  text-align: center;
}

.test-btn {
  display: block;
  margin: 15px auto 0;
  padding: 10px 25px;
  background: #ff9800;
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.test-btn:hover {
  background: #f57c00;
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255,152,0,0.4);
}
</style>