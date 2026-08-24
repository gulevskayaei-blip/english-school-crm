<template>
  <div class="attendance-container">
    <h1>📚 Моя посещаемость</h1>

    <div class="stats-grid">
      <div class="stat-card total">
        <span class="stat-value">{{ statistics.total }}</span>
        <span class="stat-label">Всего занятий</span>
      </div>
      <div class="stat-card completed">
        <span class="stat-value">{{ statistics.completed }}</span>
        <span class="stat-label">Проведено</span>
      </div>
      <div class="stat-card paid">
        <span class="stat-value">{{ statistics.paid }}</span>
        <span class="stat-label">Оплачено</span>
      </div>
      <div class="stat-card missed">
        <span class="stat-value">{{ statistics.missed }}</span>
        <span class="stat-label">Пропущено</span>
      </div>
      <div class="stat-card cancelled">
        <span class="stat-value">{{ statistics.cancelled }}</span>
        <span class="stat-label">Отменено</span>
      </div>
      <div class="stat-card no-show">
        <span class="stat-value">{{ statistics.no_show || 0 }}</span>
        <span class="stat-label">Не явился</span>
      </div>
      <div class="stat-card debt">
        <span class="stat-value">{{ statistics.debt || 0 }}</span>
        <span class="stat-label">Долг</span>
      </div>
    </div>

    <div class="attendance-table">
      <div class="table-header">
        <div class="month-navigation">
          <button @click="prevMonth">◀</button>
          <h2>{{ monthName }} {{ year }}</h2>
          <button @click="nextMonth">▶</button>
        </div>
        <div class="legend">
          <span class="legend-item"><span class="color-dot paid-dot"></span> Оплачено</span>
          <span class="legend-item"><span class="color-dot completed-dot"></span> Проведено</span>
          <span class="legend-item"><span class="color-dot missed-dot"></span> Пропущено</span>
          <span class="legend-item"><span class="color-dot cancelled-dot"></span> Отменено</span>
          <span class="legend-item"><span class="color-dot no-show-dot"></span> Не явился</span>
          <span class="legend-item"><span class="color-dot debt-dot"></span> Долг</span>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Время</th>
            <th>Преподаватель</th>
            <th>Статус</th>
            <th>Сумма</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lesson in lessons" :key="lesson.id">
            <td>{{ lesson.date }}</td>
            <td>{{ lesson.time }}</td>
            <td>{{ lesson.teacher }}</td>
            <td>
              <span class="status-badge" :class="'status-' + lesson.status">
                {{ lesson.status_label }}
              </span>
            </td>
            <td>{{ lesson.price }} ₽</td>
          </tr>
          <tr v-if="!lessons.length">
            <td colspan="5" class="no-data">Нет занятий за этот месяц</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'

export default {
  name: 'AttendanceView',
  data() {
    return {
      lessons: [],
      statistics: {
        total: 0,
        completed: 0,
        missed: 0,
        cancelled: 0,
        paid: 0,
        debt: 0,
        no_show: 0,
        postponed: 0
      },
      year: new Date().getFullYear(),
      month: new Date().getMonth() + 1,
      loading: false
    }
  },
  computed: {
    monthName() {
      const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
      return months[this.month - 1]
    }
  },
  mounted() {
    this.fetchAttendance()
  },
  methods: {
    async fetchAttendance() {
      this.loading = true
      try {
        const response = await api.get('/attendance/', {
          params: { year: this.year, month: this.month }
        })
        this.lessons = response.data.lessons
        this.statistics = response.data.statistics
      } catch (error) {
        console.error('Ошибка загрузки посещаемости:', error)
      } finally {
        this.loading = false
      }
    },
    prevMonth() {
      if (this.month === 1) {
        this.month = 12
        this.year--
      } else {
        this.month--
      }
      this.fetchAttendance()
    },
    nextMonth() {
      if (this.month === 12) {
        this.month = 1
        this.year++
      } else {
        this.month++
      }
      this.fetchAttendance()
    }
  }
}
</script>

<style scoped>
.attendance-container { padding: 20px; max-width: 1200px; margin: 0 auto; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 30px; }
.stat-card { background: white; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.stat-value { display: block; font-size: 28px; font-weight: bold; }
.stat-label { font-size: 13px; color: #666; }
.stat-card.total .stat-value { color: #4A90D9; }
.stat-card.completed .stat-value { color: #2ECC71; }
.stat-card.paid .stat-value { color: #27AE60; }
.stat-card.missed .stat-value { color: #E74C3C; }
.stat-card.cancelled .stat-value { color: #95A5A6; }
.stat-card.debt .stat-value { color: #E67E22; }
.stat-card.no-show .stat-value { color: #8E44AD; }
.table-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 20px; }
.month-navigation { display: flex; align-items: center; gap: 15px; }
.month-navigation button { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 8px 16px; cursor: pointer; font-size: 18px; }
.legend { display: flex; gap: 15px; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 13px; }
.color-dot { width: 14px; height: 14px; border-radius: 50%; display: inline-block; }
.paid-dot { background: #27AE60; }
.completed-dot { background: #2ECC71; }
.missed-dot { background: #E74C3C; }
.cancelled-dot { background: #95A5A6; }
.no-show-dot { background: #8E44AD; }
.debt-dot { background: #E67E22; }
.attendance-table { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead { background: #f8f9fa; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
.status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.status-paid { background: #D5F5E3; color: #27AE60; }
.status-completed { background: #D5F5E3; color: #2ECC71; }
.status-missed { background: #FADBD8; color: #E74C3C; }
.status-cancelled { background: #EAECEE; color: #7F8C8D; }
.status-no_show { background: #E8DAEF; color: #8E44AD; }
.status-debt { background: #FDEBD0; color: #E67E22; }
.status-scheduled { background: #D6EAF8; color: #2E86C1; }
.status-postponed { background: #FCF3CF; color: #F39C12; }
.no-data { text-align: center; color: #999; padding: 40px; }
</style>
