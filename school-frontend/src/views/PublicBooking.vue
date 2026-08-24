<template>
  <div class="public-booking">
    <h1>Запись в English School</h1>
    <p>Оставьте заявку, и мы свяжемся с вами!</p>

    <form @submit.prevent="submitBooking" class="booking-form">
      <!-- ФИО -->
      <div class="form-group">
        <label>ФИО *</label>
        <input v-model="form.full_name" required placeholder="Иванов Иван Иванович" />
      </div>

      <!-- Телефон -->
      <div class="form-group">
        <label>Телефон *</label>
        <input v-model="form.phone" required placeholder="+7 (999) 123-45-67" />
      </div>

      <!-- Email -->
      <div class="form-group">
        <label>Email</label>
        <input v-model="form.email" type="email" placeholder="email@example.com" />
      </div>

      <!-- Тип записи -->
      <div class="form-group">
        <label>Тип записи *</label>
        <select v-model="form.mode" required @change="onModeChange">
          <option value="">Выберите тип</option>
          <option value="group">В группу</option>
          <option value="individual">Индивидуально к преподавателю</option>
        </select>
      </div>

      <!-- Филиал -->
      <div class="form-group">
        <label>Филиал *</label>
        <select v-model="form.branch" required @change="onBranchChange">
          <option value="">Выберите филиал</option>
          <option v-for="b in branches" :key="b.id" :value="b.id">
            {{ b.name }} ({{ b.address }})
          </option>
        </select>
      </div>

      <!-- Группа (если выбран group) -->
      <div class="form-group" v-if="form.mode === 'group'">
        <label>Группа *</label>
        <select v-model="form.course" required :disabled="!form.branch">
          <option value="">Выберите группу</option>
          <option v-for="c in courses" :key="c.id" :value="c.id">
            {{ c.name }} — {{ c.teacher_name }} ({{ c.free_slots }} мест)
          </option>
        </select>
        <small v-if="!form.branch">Сначала выберите филиал</small>
        <small v-if="form.branch && courses.length === 0 && form.mode === 'group'">
          Нет доступных групп в этом филиале
        </small>
      </div>

      <!-- Преподаватель (если выбран individual) -->
      <div class="form-group" v-if="form.mode === 'individual'">
        <label>Преподаватель *</label>
        <select v-model="form.teacher" required>
          <option value="">Выберите преподавателя</option>
          <option v-for="t in teachers" :key="t.id" :value="t.id">
            {{ t.full_name }}
          </option>
        </select>
      </div>

      <!-- Комментарий -->
      <div class="form-group">
        <label>Комментарий</label>
        <textarea v-model="form.comment" placeholder="Дополнительная информация..."></textarea>
      </div>

      <!-- Кнопка -->
      <button type="submit" :disabled="loading" class="submit-btn">
        {{ loading ? 'Отправка...' : 'Отправить заявку' }}
      </button>

      <!-- Сообщения -->
      <div v-if="success" class="success-msg">✅ Заявка отправлена! Мы скоро свяжемся с вами.</div>
      <div v-if="error" class="error-msg">❌ {{ error }}</div>
    </form>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'PublicBooking',
  data() {
    return {
      form: {
        full_name: '',
        phone: '',
        email: '',
        mode: '',
        branch: null,
        course: null,
        teacher: null,
        comment: '',
      },
      branches: [],
      courses: [],
      teachers: [],
      loading: false,
      success: false,
      error: null,
    }
  },
  mounted() {
    this.loadBranches()
    this.loadTeachers()
  },
  methods: {
    async loadBranches() {
      try {
        const res = await api.get('/booking/branches/')
        this.branches = res.data
      } catch (e) {
        console.error('Ошибка загрузки филиалов', e)
      }
    },
    async loadTeachers() {
      try {
        const res = await api.get('/booking/teachers/')
        this.teachers = res.data
      } catch (e) {
        console.error('Ошибка загрузки преподавателей', e)
      }
    },
    async loadCourses(branchId) {
      try {
        const res = await api.get(`/booking/courses/?branch=${branchId}`)
        this.courses = res.data
      } catch (e) {
        console.error('Ошибка загрузки курсов', e)
      }
    },
    onModeChange() {
      this.form.course = null
      this.form.teacher = null
    },
    onBranchChange() {
      this.form.course = null
      if (this.form.branch && this.form.mode === 'group') {
        this.loadCourses(this.form.branch)
      }
    },
    async submitBooking() {
      this.loading = true
      this.error = null
      this.success = false

      try {
        await api.post('/booking/request/', this.form)
        this.success = true
        this.form = {
          full_name: '',
          phone: '',
          email: '',
          mode: '',
          branch: null,
          course: null,
          teacher: null,
          comment: '',
        }
      } catch (e) {
        const data = e.response?.data
        if (data) {
          this.error = Object.values(data).flat().join(', ')
        } else {
          this.error = 'Ошибка отправки. Попробуйте позже.'
        }
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.public-booking {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  color: #2c3e50;
}

.booking-form {
  margin-top: 30px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input, select, textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
}

textarea {
  min-height: 80px;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 18px;
  cursor: pointer;
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.success-msg {
  margin-top: 15px;
  padding: 10px;
  background: #d4edda;
  color: #155724;
  border-radius: 5px;
}

.error-msg {
  margin-top: 15px;
  padding: 10px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 5px;
}
</style>
