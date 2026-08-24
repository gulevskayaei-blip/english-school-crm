<template>
  <div class="teachers-list">
    <div class="header">
      <button @click="$router.push('/dashboard')" class="back-btn">← Назад</button>
      <h1>Преподаватели</h1>
      <button @click="loadTeachers" class="refresh-btn">🔄 Обновить</button>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка...</p>
    </div>

    <div v-else-if="teachers.length === 0" class="empty">
      <p>Нет данных о преподавателях</p>
    </div>

    <div v-else class="teachers-grid">
      <div v-for="teacher in teachers" :key="teacher.id" class="teacher-card">
        <div class="card-header">
          <h3>{{ teacher.name }}</h3>
          <span :class="['status', teacher.is_active ? 'active' : 'inactive']">
            {{ teacher.is_active ? 'Активен' : 'Неактивен' }}
          </span>
        </div>

        <div class="card-body">
          <div class="info-row">
            <span class="label">💰 Ставка:</span>
            <span class="value">{{ teacher.hourly_rate }} ₽/час</span>
          </div>

          <div class="info-row">
            <span class="label">📞 Телефон:</span>
            <span class="value">{{ teacher.phone || '—' }}</span>
          </div>

          <!-- БЛОК ЗАРПЛАТЫ -->
          <div class="salary-section">
            <div class="salary-title">📊 Зарплата за текущий месяц</div>
            
            <div class="salary-row actual">
              <span class="label">Фактическая:</span>
              <span class="value">{{ formatSalary(teacher.actual_salary) }} ₽</span>
              <span class="hours">({{ teacher.actual_hours || 0 }} ч)</span>
            </div>
            
            <div class="salary-row forecast">
              <span class="label">Прогнозируемая:</span>
              <span class="value">{{ formatSalary(teacher.forecast_salary) }} ₽</span>
              <span class="hours">({{ teacher.forecast_hours || 0 }} ч)</span>
            </div>
            
            <div class="salary-row difference" :class="getDifferenceClass(teacher.difference_salary)">
              <span class="label">Разница:</span>
              <span class="value">{{ formatSalary(teacher.difference_salary) }} ₽</span>
            </div>
          </div>
          <!-- КОНЕЦ БЛОКА ЗАРПЛАТЫ -->
        </div>

        <div class="card-footer">
          <button @click="viewDetails(teacher.id)" class="details-btn">
            Подробнее
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'TeachersList',
  data() {
    return {
      teachers: [],
      loading: true
    }
  },
  mounted() {
    this.loadTeachers()
  },
  methods: {
    async loadTeachers() {
      try {
        this.loading = true
        const response = await api.get('/teachers-list-with-salary/')
        this.teachers = response.data
        console.log('Загружены преподаватели:', this.teachers)
      } catch (error) {
        console.error('Ошибка загрузки:', error)
        alert('Ошибка загрузки списка преподавателей: ' + (error.response?.data?.message || error.message))
      } finally {
        this.loading = false
      }
    },
    formatSalary(salary) {
      if (!salary && salary !== 0) return '0'
      return Number(salary).toFixed(2)
    },
    getDifferenceClass(difference) {
      if (difference > 0) return 'positive'
      if (difference < 0) return 'negative'
      return 'zero'
    },
    viewDetails(id) {
  console.log('Переход к преподавателю с ID:', id);
  this.$router.push(`/teacher/${id}`);
}
  }
}
</script>

<style scoped>
.teachers-list {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header h1 {
  margin: 0;
  color: #2c3e50;
  flex: 1;
  text-align: center;
}

.back-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.back-btn:hover {
  background: #5a6268;
}

.refresh-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.refresh-btn:hover {
  background: #2980b9;
}

.loading {
  text-align: center;
  padding: 50px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty {
  text-align: center;
  padding: 50px;
  color: #7f8c8d;
  font-size: 18px;
}

.teachers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 25px;
}

.teacher-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.teacher-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
}

.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 1.3em;
}

.status {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
}

.status.active {
  background: #27ae60;
}

.status.inactive {
  background: #e74c3c;
}

.card-body {
  padding: 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.info-row:last-child {
  border-bottom: none;
}

.label {
  font-weight: 600;
  color: #7f8c8d;
}

.value {
  color: #2c3e50;
  font-weight: 500;
}

.salary-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-top: 15px;
  border-left: 4px solid #3498db;
}

.salary-title {
  font-weight: bold;
  margin-bottom: 12px;
  color: #2c3e50;
  text-align: center;
  font-size: 0.95em;
}

.salary-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 0.9em;
}

.salary-row.actual {
  color: #2c3e50;
}

.salary-row.forecast {
  color: #3498db;
}

.salary-row.difference.positive {
  color: #27ae60;
  font-weight: bold;
}

.salary-row.difference.negative {
  color: #e74c3c;
  font-weight: bold;
}

.salary-row.difference.zero {
  color: #95a5a6;
}

.hours {
  font-size: 0.85em;
  color: #95a5a6;
}

.card-footer {
  padding: 15px 20px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
}

.details-btn {
  width: 100%;
  background: #3498db;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.details-btn:hover {
  background: #2980b9;
}
</style>