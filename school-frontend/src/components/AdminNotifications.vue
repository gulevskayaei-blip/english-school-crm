<template>
  <div class="notifications-dropdown" v-click-outside="closeDropdown">
    <button @click="toggleDropdown" class="notifications-btn">
      🔔
      <span v-if="totalUnread > 0" class="badge">{{ totalUnread }}</span>
    </button>

    <div v-if="isOpen" class="dropdown-content">
      <!-- Заявки на запись -->
      <h3>📝 Заявки на запись</h3>
      <div v-if="pendingBookings.length === 0" class="empty">
        Нет новых заявок
      </div>
      <div v-for="booking in pendingBookings" :key="'b-'+booking.id" class="notification-item pending">
        <div class="notif-header">
          <strong>{{ booking.student_name }}</strong>
          <span class="notif-time">{{ formatTime(booking.created_at) }}</span>
        </div>
        <div class="notif-body">
          <div>👨‍🏫 {{ booking.teacher_name }}</div>
          <div>📅 {{ formatDateTime(booking.datetime_start) }} ({{ booking.duration }} мин)</div>
        </div>
        <div class="booking-actions">
          <button @click="approveBooking(booking.id)" class="approve-btn">✓ Подтвердить</button>
          <button @click="rejectBooking(booking.id)" class="reject-btn">✗ Отклонить</button>
        </div>
      </div>

      <!-- Уведомления об отменах -->
      <h3 style="margin-top: 15px;">❌ Уведомления об отменах</h3>
      <div v-if="notifications.length === 0" class="empty">
        Нет новых уведомлений
      </div>
      <div v-for="notif in notifications" :key="'n-'+notif.id" class="notification-item" :class="{ 'unread': !notif.read }">
        <div class="notif-header">
          <strong>{{ notif.student_name }}</strong>
          <span class="notif-time">{{ formatTime(notif.cancellation_time) }}</span>
        </div>
        <div class="notif-body">
          <div>❌ Отменил(а) занятие: {{ formatDateTime(notif.datetime_start) }}</div>
          <div>📝 Причина: {{ notif.cancellation_reason || 'Не указана' }}</div>
          <div v-if="notif.is_penalty_applied" class="penalty-warning">
            ⚠️ Занятие подлежит оплате (отмена менее чем за час)
          </div>
        </div>
        <button @click="markRead(notif.id)" class="mark-read-btn">✓ Отметить прочитанным</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

const isOpen = ref(false)
const notifications = ref([])
const pendingBookings = ref([])

const totalUnread = computed(() => {
  return pendingBookings.value.length + notifications.value.filter(n => !n.read).length
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const closeDropdown = () => {
  isOpen.value = false
}

const loadNotifications = async () => {
  try {
    const response = await api.get('cancellation-notifications/')
    notifications.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки уведомлений:', error)
  }
}

const loadPendingBookings = async () => {
  try {
    const response = await api.get('lessons/pending-bookings/')
    pendingBookings.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки заявок:', error)
  }
}

const approveBooking = async (id) => {
  try {
    await api.patch(`lessons/${id}/`, { status: 'scheduled' })
    pendingBookings.value = pendingBookings.value.filter(b => b.id !== id)
  } catch (error) {
    console.error('Ошибка подтверждения:', error)
  }
}

const rejectBooking = async (id) => {
  try {
    await api.patch(`lessons/${id}/`, { status: 'cancelled' })
    pendingBookings.value = pendingBookings.value.filter(b => b.id !== id)
  } catch (error) {
    console.error('Ошибка отклонения:', error)
  }
}

const markRead = async (id) => {
  try {
    await api.post(`cancellation-notifications/${id}/read/`)
    const notif = notifications.value.find(n => n.id === id)
    if (notif) notif.read = true
  } catch (error) {
    console.error('Ошибка отметки:', error)
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
  })
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

let interval
onMounted(() => {
  loadNotifications()
  loadPendingBookings()
  interval = setInterval(() => {
    loadNotifications()
    loadPendingBookings()
  }, 30000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>

<style scoped>
.notifications-dropdown {
  position: relative;
  display: inline-block;
}

.notifications-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  position: relative;
  padding: 5px 10px;
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background: red;
  color: white;
  border-radius: 50%;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: bold;
}

.dropdown-content {
  position: absolute;
  right: 0;
  top: 40px;
  width: 380px;
  max-height: 500px;
  overflow-y: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  z-index: 1000;
  padding: 10px;
}

.dropdown-content h3 {
  margin: 0 0 10px 0;
  padding-bottom: 5px;
  border-bottom: 1px solid #eee;
}

.notification-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
  margin-bottom: 5px;
  border-radius: 5px;
}

.notification-item.pending {
  background: #fff8e1;
  border-left: 3px solid #ff9800;
}

.notification-item.unread {
  background: #e3f2fd;
}

.notif-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.notif-time {
  font-size: 11px;
  color: #999;
}

.notif-body {
  font-size: 12px;
  margin-bottom: 8px;
}

.booking-actions {
  display: flex;
  gap: 5px;
}

.approve-btn {
  background: #4caf50;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
}

.reject-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
}

.penalty-warning {
  color: #ff9800;
  margin-top: 5px;
  font-weight: bold;
}

.mark-read-btn {
  background: #4caf50;
  color: white;
  border: none;
  padding: 3px 8px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 11px;
}

.empty {
  text-align: center;
  color: #999;
  padding: 20px;
}
</style>
