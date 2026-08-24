<template>
  <div class="teacher-detail">
    <div class="header">
      <button @click="$router.push('/teachers')" class="back-btn">← Назад</button>
      <h1>Карточка преподавателя</h1>
      <button @click="toggleEdit" class="edit-btn">
        {{ isEditing ? 'Отмена' : '✏️ Редактировать' }}
      </button>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>

    <div v-else-if="teacher" class="teacher-card">
      <!-- Режим просмотра -->
      <div v-if="!isEditing" class="view-mode">
        <div class="avatar">👨‍🏫</div>
        <h2>{{ teacher.name }}</h2>
        
        <div class="info-grid">
          <div class="info-item">
            <span class="label">💰 Ставка в час:</span>
            <span class="value">{{ teacher.hourly_rate }} ₽</span>
          </div>
          <div class="info-item">
            <span class="label">📞 Телефон:</span>
            <span class="value">{{ teacher.phone || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">📧 Email:</span>
            <span class="value">{{ teacher.email || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">📅 Дата найма:</span>
            <span class="value">{{ teacher.hire_date || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">🏦 Банковский счет:</span>
            <span class="value">{{ teacher.bank_account || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">📊 Статус:</span>
            <span :class="['status', teacher.is_active ? 'active' : 'inactive']">
              {{ teacher.is_active ? 'Активен' : 'Неактивен' }}
            </span>
          </div>
        </div>

        <!-- Блок зарплаты -->
        <div class="salary-section">
          <h3>💰 Зарплата за текущий месяц</h3>
          <div class="salary-grid">
            <div class="salary-item actual">
              <span>Фактическая:</span>
              <strong>{{ formatMoney(teacher.actual_salary) }}</strong>
              <small>({{ teacher.actual_hours || 0 }} ч)</small>
            </div>
            <div class="salary-item forecast">
              <span>Прогнозируемая:</span>
              <strong>{{ formatMoney(teacher.forecast_salary) }}</strong>
              <small>({{ teacher.forecast_hours || 0 }} ч)</small>
            </div>
            <div class="salary-item difference" :class="{ positive: teacher.difference_salary > 0, negative: teacher.difference_salary < 0 }">
              <span>Разница:</span>
              <strong>{{ formatMoney(teacher.difference_salary) }}</strong>
            </div>
          </div>
        </div>
      </div>

      <!-- Режим редактирования -->
      <div v-else class="edit-mode">
        <h2>Редактирование: {{ teacher.name }}</h2>
        
        <div class="edit-form">
          <div class="form-group">
            <label>💰 Ставка в час (₽):</label>
            <input type="number" v-model.number="editForm.hourly_rate" class="form-input">
          </div>
          
          <div class="form-group">
            <label>📞 Телефон:</label>
            <input type="text" v-model="editForm.phone" class="form-input">
          </div>
          
          <div class="form-group">
            <label>📧 Email:</label>
            <input type="email" v-model="editForm.email" class="form-input">
          </div>
          
          <div class="form-group">
            <label>📅 Дата найма:</label>
            <input type="date" v-model="editForm.hire_date" class="form-input">
          </div>
          
          <div class="form-group">
            <label>🏦 Банковский счет:</label>
            <input type="text" v-model="editForm.bank_account" class="form-input">
          </div>
          
          <div class="form-group">
            <label>📊 Статус:</label>
            <select v-model="editForm.is_active" class="form-input">
              <option :value="true">Активен</option>
              <option :value="false">Неактивен</option>
            </select>
          </div>
          
          <div class="form-actions">
            <button @click="saveTeacher" class="save-btn">💾 Сохранить</button>
            <button @click="toggleEdit" class="cancel-btn">❌ Отмена</button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error">
      <p>Преподаватель не найден</p>
      <button @click="$router.push('/teachers')">Вернуться к списку</button>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'TeacherDetail',
  data() {
    return {
      teacher: null,
      loading: true,
      isEditing: false,
      editForm: {}
    }
  },
  async mounted() {
    await this.loadTeacher()
  },
  methods: {
    async loadTeacher() {
      try {
        const id = this.$route.params.id
        console.log('Загрузка преподавателя ID:', id)
        
        // Сначала получаем список с зарплатой
        const response = await api.get('/teachers-list-with-salary/')
        const teacherWithSalary = response.data.find(t => t.id == id)
        
        if (teacherWithSalary) {
          this.teacher = teacherWithSalary
          this.editForm = { ...teacherWithSalary }
        } else {
          // Если не нашли, пробуем получить через teacher-detail
          const detailResponse = await api.get(`/teacher-detail/${id}/`)
          this.teacher = detailResponse.data
          this.editForm = { ...detailResponse.data }
        }
        
        console.log('Загружен преподаватель:', this.teacher)
      } catch (error) {
        console.error('Ошибка загрузки:', error)
        alert('Ошибка загрузки данных преподавателя')
      } finally {
        this.loading = false
      }
    },
    
    toggleEdit() {
      if (this.isEditing) {
        // Отмена - восстанавливаем исходные данные
        this.editForm = { ...this.teacher }
      }
      this.isEditing = !this.isEditing
    },
    
    async saveTeacher() {
      try {
        const id = this.$route.params.id
        const response = await api.put(`/teacher-detail/${id}/`, this.editForm)
        
        if (response.status === 200) {
          this.teacher = { ...this.editForm, ...response.data }
          this.isEditing = false
          alert('✅ Данные преподавателя сохранены!')
        }
      } catch (error) {
        console.error('Ошибка сохранения:', error)
        alert('Ошибка при сохранении: ' + (error.response?.data?.message || error.message))
      }
    },
    
    formatMoney(amount) {
      if (!amount && amount !== 0) return '0 ₽'
      return new Intl.NumberFormat('ru-RU', { 
        style: 'currency', 
        currency: 'RUB', 
        minimumFractionDigits: 0 
      }).format(amount)
    }
  }
}
</script>

<style scoped>
.teacher-detail {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.back-btn, .edit-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.back-btn {
  background: #6c757d;
  color: white;
}

.edit-btn {
  background: #3498db;
  color: white;
}

.loading {
  text-align: center;
  padding: 50px;
  font-size: 18px;
  color: #7f8c8d;
}

.teacher-card {
  background: white;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.avatar {
  text-align: center;
  font-size: 80px;
  margin-bottom: 10px;
}

.teacher-card h2 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.label {
  font-weight: 600;
  color: #7f8c8d;
}

.value {
  color: #2c3e50;
}

.status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.status.active {
  background: #27ae60;
  color: white;
}

.status.inactive {
  background: #e74c3c;
  color: white;
}

.salary-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  border-radius: 12px;
  margin-top: 20px;
}

.salary-section h3 {
  margin: 0 0 15px 0;
  text-align: center;
}

.salary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.salary-item {
  background: rgba(255,255,255,0.2);
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.salary-item span {
  display: block;
  font-size: 12px;
  margin-bottom: 5px;
}

.salary-item strong {
  display: block;
  font-size: 18px;
}

.salary-item small {
  display: block;
  font-size: 10px;
  margin-top: 3px;
}

.salary-item.difference.positive strong {
  color: #a5d6a7;
}

.salary-item.difference.negative strong {
  color: #ef9a9a;
}

.edit-mode h2 {
  text-align: center;
  margin-bottom: 25px;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: 600;
  color: #2c3e50;
}

.form-input {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.save-btn {
  background: #27ae60;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  flex: 1;
}

.cancel-btn {
  background: #95a5a6;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  flex: 1;
}

.error {
  text-align: center;
  padding: 50px;
  background: #f8f9fa;
  border-radius: 12px;
}

.error button {
  margin-top: 15px;
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>