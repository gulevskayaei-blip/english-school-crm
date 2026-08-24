<template>
  <div class="notifications-dropdown" v-click-outside="closeDropdown">
    <button @click="toggleDropdown" class="notifications-btn">
      🔔
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
    </button>
    
    <div v-if="isOpen" class="dropdown-content">
      <div class="dropdown-header">
        <h3>📋 Мои уведомления</h3>
        <button v-if="unreadCount > 0" @click="markAllRead" class="mark-all-btn">✓ Все прочитаны</button>
      </div>
      <div v-if="notifications.length === 0" class="empty">
        Нет новых уведомлений
      </div>
      <div v-for="notif in notifications" :key="notif.id" class="notification-item">
        <div class="notif-header">
          <span class="notif-type">{{ getTypeIcon(notif.type) }} {{ getTypeName(notif.type) }}</span>
          <span class="notif-time">{{ formatTime(notif.created_at) }}</span>
        </div>
        <div class="notif-body">
          {{ notif.message }}
        </div>
        <button @click="markRead(notif.id)" class="mark-read-btn">✓ Отметить прочитанным</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

const isOpen = ref(false)
const notifications = ref([])
const unreadCount = ref(0)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const closeDropdown = () => {
  isOpen.value = false
}

const loadNotifications = async () => {
  try {
    const response = await api.get('student-notifications/')
    notifications.value = response.data
    unreadCount.value = notifications.value.length
  } catch (error) {
    console.error('Ошибка загрузки уведомлений:', error)
  }
}

const markRead = async (id) => {
  try {
    await api.post(`student-notifications/${id}/read/`)
    notifications.value = notifications.value.filter(n => n.id !== id)
    unreadCount.value = notifications.value.length
  } catch (error) {
    console.error('Ошибка отметки:', error)
  }
}

const markAllRead = async () => {
  try {
    for (const notif of notifications.value) {
      await api.post(`student-notifications/${notif.id}/read/`)
    }
    notifications.value = []
    unreadCount.value = 0
  } catch (error) {
    console.error('Ошибка отметки всех:', error)
  }
}

const getTypeIcon = (type) => {
  const icons = { debt: '⚠️', schedule: '📅', payment: '💰', custom: '✏️' }
  return icons[type] || '📋'
}

const getTypeName = (type) => {
  const names = { debt: 'Долг', schedule: 'Расписание', payment: 'Оплата', custom: 'Сообщение' }
  return names[type] || 'Уведомление'
}

const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
  })
}

let interval
onMounted(() => {
  loadNotifications()
  interval = setInterval(loadNotifications, 30000)
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
  width: 350px;
  max-height: 400px;
  overflow-y: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  z-index: 1000;
  padding: 10px;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 5px;
  border-bottom: 1px solid #eee;
}

.dropdown-header h3 {
  margin: 0;
  font-size: 16px;
}

.mark-all-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}

.notification-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
  margin-bottom: 5px;
  border-radius: 5px;
  background: #e3f2fd;
}

.notif-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.notif-type {
  font-size: 12px;
  font-weight: bold;
  color: #007bff;
}

.notif-time {
  font-size: 11px;
  color: #999;
}

.notif-body {
  font-size: 13px;
  margin-bottom: 8px;
  word-break: break-word;
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