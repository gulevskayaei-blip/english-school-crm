<template>
  <div class="students-container">
    <div class="header">
      <h1>👨‍🎓 Список студентов</h1>
      <button @click="goBack" class="back-btn">← Назад</button>
    </div>

    <!-- Фильтры -->
    <div class="filters">
      <div class="filter-group">
        <label>📋 Филиал:</label>
        <select v-model="filters.branch">
          <option :value="null">Все филиалы</option>
          <option v-for="branch in branches" :key="branch.id" :value="branch.id">
            {{ branch.name }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label>🔍 Поиск:</label>
        <input type="text" v-model="filters.search" placeholder="Имя, телефон, email...">
      </div>
      <button @click="loadStudents" class="refresh-btn">🔄 Обновить</button>
      <button @click="createStudent" class="create-btn">➕ Создать студента</button>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>

    <!-- Список студентов -->
    <div v-else class="students-grid">
      <div v-for="student in filteredStudents" :key="student.id" class="student-card" @click="openStudentCard(student)">
        <div class="student-avatar">
          {{ student.profile?.user?.first_name?.charAt(0) || student.username?.charAt(0) || '👤' }}
        </div>
        <div class="student-info">
          <h3>{{ student.profile?.user?.first_name || student.username }} {{ student.profile?.user?.last_name || '' }}</h3>
          <p class="student-username">@{{ student.profile?.user?.username || student.username }}</p>
          <p class="student-phone">{{ student.profile?.phone_number || 'Нет телефона' }}</p>
          <p class="student-branch">{{ student.branch_name || student.branch?.name || 'Филиал не указан' }}</p>
        </div>
        <div class="student-debt" :class="{ 'has-debt': getStudentDebt(student.id) > 0 }">
          {{ formatMoney(getStudentDebt(student.id)) }}
        </div>
      </div>

      <div v-if="filteredStudents.length === 0" class="empty">
        Нет студентов
      </div>
    </div>

    <!-- Модальное окно карточки студента -->
    <div v-if="selectedStudent" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ selectedStudent.profile?.user?.first_name || selectedStudent.username }} {{ selectedStudent.profile?.user?.last_name || '' }}</h2>
          <button @click="closeModal" class="close-btn">✖</button>
        </div>
        
        <!-- Вкладки -->
        <div class="tabs">
          <button :class="{ active: activeTab === 'info' }" @click="activeTab = 'info'">📋 Информация</button>
          <button :class="{ active: activeTab === 'finance' }" @click="activeTab = 'finance'">💰 Финансы</button>
          <button :class="{ active: activeTab === 'lessons' }" @click="activeTab = 'lessons'">📚 Занятия</button>
        </div>

        <!-- Вкладка Информация -->
        <div v-if="activeTab === 'info' && !isEditing" class="tab-content">
          <div class="info-row">
            <span class="label">Логин:</span>
            <span>{{ selectedStudent.profile?.user?.username || selectedStudent.username }}</span>
          </div>
          <div class="info-row">
            <span class="label">Email:</span>
            <span>{{ selectedStudent.profile?.user?.email || 'Не указан' }}</span>
          </div>
          <div class="info-row">
            <span class="label">Телефон:</span>
            <span>{{ selectedStudent.profile?.phone_number || 'Не указан' }}</span>
          </div>
          <div class="info-row">
            <span class="label">Филиал:</span>
            <span>{{ selectedStudent.branch_name || selectedStudent.branch?.name }}</span>
          </div>
          <div class="info-row">
            <span class="label">Формат:</span>
            <span>{{ selectedStudent.format === 'online' ? 'Онлайн' : 'Офлайн' }}</span>
          </div>
          <div class="info-row">
            <span class="label">Скидка:</span>
            <span>{{ selectedStudent.discount || 0 }}%</span>
          </div>
          <div class="info-row">
            <span class="label">Родитель:</span>
            <span>{{ selectedStudent.parent_name || 'Не указан' }}</span>
          </div>
          
          <!-- Кнопки действий -->
          <div class="action-buttons">
            <button @click="startEditStudent" class="edit-student-btn">✏️ Редактировать</button>
            <button @click="openNotificationModal" class="notify-student-btn">📧 Отправить уведомление</button>
          </div>
        </div>

        <!-- Режим редактирования -->
        <div v-if="isEditing" class="tab-content">
          <h3>✏️ Редактирование студента</h3>
          <div class="edit-form">
            <div class="form-group">
              <label>Имя:</label>
              <input v-model="editForm.first_name" type="text" class="edit-input">
            </div>
            <div class="form-group">
              <label>Фамилия:</label>
              <input v-model="editForm.last_name" type="text" class="edit-input">
            </div>
            <div class="form-group">
              <label>Email:</label>
              <input v-model="editForm.email" type="email" class="edit-input">
            </div>
            <div class="form-group">
              <label>Телефон:</label>
              <input v-model="editForm.phone_number" type="tel" class="edit-input">
            </div>
            <div class="form-group">
              <label>Филиал:</label>
              <select v-model="editForm.branch_id" class="edit-input">
                <option v-for="branch in branches" :key="branch.id" :value="branch.id">
                  {{ branch.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Формат обучения:</label>
              <select v-model="editForm.format" class="edit-input">
                <option value="offline">Офлайн</option>
                <option value="online">Онлайн</option>
              </select>
            </div>
            <div class="form-group">
              <label>Скидка (%):</label>
              <input v-model.number="editForm.discount" type="number" min="0" max="100" class="edit-input">
            </div>
            <div class="form-group">
              <label>ФИО родителя:</label>
              <input v-model="editForm.parent_name" type="text" class="edit-input">
            </div>
            <div class="edit-buttons">
              <button @click="saveStudentEdit" class="save-btn">💾 Сохранить</button>
              <button @click="cancelEdit" class="cancel-btn">❌ Отмена</button>
            </div>
          </div>
        </div>

        <!-- Вкладка Финансы -->
        <div v-if="activeTab === 'finance'" class="tab-content">
          <div class="finance-filter">
            <label>Период:</label>
            <select v-model="financePeriod">
              <option value="all">За все время</option>
              <option value="month">Последний месяц</option>
              <option value="3months">Последние 3 месяца</option>
              <option value="year">Последний год</option>
            </select>
            <button @click="calculateStudentFinance" class="calc-btn">📊 Рассчитать</button>
          </div>

          <div class="finance-cards">
            <div class="finance-card income">
              <h4>💰 Оплачено</h4>
              <p class="amount">{{ formatMoney(studentFinance.paid) }}</p>
            </div>
            <div class="finance-card expenses">
              <h4>📉 Долг</h4>
              <p class="amount" :class="{ 'has-debt': studentFinance.debt > 0 }">{{ formatMoney(studentFinance.debt) }}</p>
            </div>
            <div class="finance-card lessons-cost">
              <h4>📚 Стоимость занятий</h4>
              <p class="amount">{{ formatMoney(studentFinance.lessonsCost) }}</p>
            </div>
          </div>

          <div class="payments-list" v-if="studentPayments.length > 0">
            <h4>История платежей</h4>
            <table class="data-table">
              <thead>
                <tr><th>Дата</th><th>Сумма</th><th>Способ</th><th>Назначение</th></tr>
              </thead>
              <tbody>
                <tr v-for="payment in studentPayments" :key="payment.id">
                  <td>{{ payment.date }}</td>
                  <td class="amount-cell">{{ formatMoney(payment.amount) }}</td>
                  <td>{{ getPaymentMethodIcon(payment.payment_method) }}</td>
                  <td>{{ payment.purpose || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="empty">Нет платежей</div>
        </div>

        <!-- Вкладка Занятия -->
        <div v-if="activeTab === 'lessons'" class="tab-content">
          <div class="lessons-list">
            <div v-for="lesson in studentLessons" :key="lesson.id" class="lesson-item" :class="{ cancelled: lesson.status === 'cancelled' }">
              <div class="lesson-date">{{ formatDateTime(lesson.datetime_start) }}</div>
              <div class="lesson-info">
                <strong>{{ lesson.course?.name || 'Индивидуальное' }}</strong>
                <br />
                Преподаватель: {{ lesson.teacher?.profile?.user?.username || lesson.teacher_name }}
              </div>
              <div class="lesson-status">
                <span :class="lesson.status === 'cancelled' ? 'badge-cancelled' : 'badge-scheduled'">
                  {{ lesson.status === 'cancelled' ? 'Отменено' : 'Запланировано' }}
                </span>
              </div>
            </div>
            <div v-if="studentLessons.length === 0" class="empty">Нет занятий</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно отправки уведомления -->
    <div v-if="showNotificationModal" class="notification-modal-overlay" @click="closeNotificationModal">
      <div class="notification-modal-content" @click.stop>
        <h3>📧 Отправить уведомление</h3>
        <div class="form-group">
          <label>Студент:</label>
          <input type="text" :value="selectedStudent?.profile?.user?.first_name || selectedStudent?.username" disabled class="disabled-input">
        </div>
        <div class="form-group">
          <label>Тип уведомления:</label>
          <select v-model="notificationType">
            <option value="debt">⚠️ Напоминание о долге</option>
            <option value="schedule">📅 Напоминание о занятии</option>
            <option value="payment">💰 Подтверждение оплаты</option>
            <option value="custom">✏️ Свое сообщение</option>
          </select>
        </div>
        <div class="form-group">
          <label>Сообщение:</label>
          <textarea v-model="notificationMessage" rows="5" class="message-input" placeholder="Введите сообщение..."></textarea>
        </div>
        <div class="notification-buttons">
          <button @click="sendNotification" class="send-btn">📨 Отправить</button>
          <button @click="closeNotificationModal" class="cancel-btn">Отмена</button>
        </div>
        <div v-if="notificationSent" class="success-message">
          ✅ Уведомление отправлено!
        </div>
        <div v-if="notificationError" class="error-message">
          ❌ {{ notificationError }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const loading = ref(false)
const students = ref([])
const branches = ref([])
const debtorsData = ref([])
const selectedStudent = ref(null)
const activeTab = ref('info')
const financePeriod = ref('all')
const studentPayments = ref([])
const studentLessons = ref([])
const studentFinance = ref({ paid: 0, debt: 0, lessonsCost: 0 })

// Редактирование студента
const isEditing = ref(false)
const editForm = ref({
  id: null,
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  branch_id: null,
  format: 'offline',
  discount: 0,
  parent_name: ''
})

// Уведомления
const showNotificationModal = ref(false)
const notificationType = ref('custom')
const notificationMessage = ref('')
const notificationSent = ref(false)
const notificationError = ref('')

const filters = ref({
  branch: null,
  search: ''
})

const goBack = () => {
  router.push('/dashboard')
}

const createStudent = () => {
  router.push('/create-student')
}

const formatMoney = (amount) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(amount || 0)
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
  })
}

const getPaymentMethodIcon = (method) => {
  const icons = { cash: '💵 Наличные', card: '💳 Карта', transfer: '🏦 Перевод' }
  return icons[method] || method
}

const getStudentDebt = (studentId) => {
  const debtor = debtorsData.value.find(d => d.student_id === studentId)
  return debtor ? debtor.debt : 0
}

const filteredStudents = computed(() => {
  let result = students.value
  
  if (filters.value.branch) {
    result = result.filter(s => s.branch === filters.value.branch || s.branch?.id === filters.value.branch)
  }
  
  if (filters.value.search) {
    const searchLower = filters.value.search.toLowerCase()
    result = result.filter(s => 
      (s.profile?.user?.username || '').toLowerCase().includes(searchLower) ||
      (s.profile?.user?.first_name || '').toLowerCase().includes(searchLower) ||
      (s.profile?.user?.last_name || '').toLowerCase().includes(searchLower) ||
      (s.profile?.phone_number || '').includes(searchLower)
    )
  }
  
  return result
})

const loadBranches = async () => {
  try {
    const response = await api.get('branches/')
    branches.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки филиалов:', error)
  }
}

const loadStudents = async () => {
  loading.value = true
  try {
    const [studentsRes, debtorsRes] = await Promise.all([
      api.get('students/'),
      api.get('reports/debtors/')
    ])
    students.value = studentsRes.data
    debtorsData.value = debtorsRes.data
  } catch (error) {
    console.error('Ошибка загрузки студентов:', error)
  } finally {
    loading.value = false
  }
}

const openStudentCard = async (student) => {
  selectedStudent.value = student
  activeTab.value = 'info'
  isEditing.value = false
  await loadStudentPayments(student.id)
  await loadStudentLessons(student.id)
  await calculateStudentFinance()
}

const loadStudentPayments = async (studentId) => {
  try {
    const response = await api.get(`reports/payments/?student=${studentId}`)
    studentPayments.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки платежей:', error)
  }
}

const loadStudentLessons = async (studentId) => {
  try {
    const response = await api.get(`lessons/?student=${studentId}`)
    studentLessons.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки занятий:', error)
  }
}

const calculateStudentFinance = async () => {
  try {
    let startDate = null
    const now = new Date()
    
    switch (financePeriod.value) {
      case 'month':
        startDate = new Date(now.setMonth(now.getMonth() - 1))
        break
      case '3months':
        startDate = new Date(now.setMonth(now.getMonth() - 3))
        break
      case 'year':
        startDate = new Date(now.setFullYear(now.getFullYear() - 1))
        break
      default:
        startDate = null
    }
    
    let payments = [...studentPayments.value]
    let lessons = [...studentLessons.value]
    
    if (startDate) {
      payments = payments.filter(p => new Date(p.date) >= startDate)
      lessons = lessons.filter(l => new Date(l.datetime_start) >= startDate)
    }
    
    const paid = payments.reduce((sum, p) => sum + p.amount, 0)
    const lessonsCost = lessons.filter(l => l.status === 'completed').length * 1500
    const debt = lessonsCost - paid
    
    studentFinance.value = { paid, debt: debt > 0 ? debt : 0, lessonsCost }
  } catch (error) {
    console.error('Ошибка расчета:', error)
  }
}

const closeModal = () => {
  selectedStudent.value = null
  isEditing.value = false
}

// Редактирование студента
const startEditStudent = () => {
  if (!selectedStudent.value) return
  
  editForm.value = {
    id: selectedStudent.value.id,
    first_name: selectedStudent.value.profile?.user?.first_name || '',
    last_name: selectedStudent.value.profile?.user?.last_name || '',
    email: selectedStudent.value.profile?.user?.email || '',
    phone_number: selectedStudent.value.profile?.phone_number || '',
    branch_id: selectedStudent.value.branch?.id || selectedStudent.value.branch,
    format: selectedStudent.value.format || 'offline',
    discount: selectedStudent.value.discount || 0,
    parent_name: selectedStudent.value.parent_name || ''
  }
  isEditing.value = true
}

const saveStudentEdit = async () => {
  try {
    // Обновляем пользователя
    const userId = selectedStudent.value.profile?.user?.id
    if (userId) {
      await api.put(`users/${userId}/`, {
        first_name: editForm.value.first_name,
        last_name: editForm.value.last_name,
        email: editForm.value.email
      })
    }
    
    // Обновляем профиль
    const profileId = selectedStudent.value.profile?.id
    if (profileId) {
      await api.put(`profiles/${profileId}/`, {
        phone_number: editForm.value.phone_number
      })
    }
    
    // Обновляем студента
    await api.put(`students/${selectedStudent.value.id}/`, {
      branch: editForm.value.branch_id,
      format: editForm.value.format,
      discount: editForm.value.discount,
      parent_name: editForm.value.parent_name
    })
    
    alert('Данные студента обновлены!')
    isEditing.value = false
    await loadStudents()
    await openStudentCard(selectedStudent.value)
  } catch (error) {
    console.error('Ошибка обновления:', error)
    alert('Ошибка при обновлении: ' + (error.response?.data?.detail || error.message))
  }
}

const cancelEdit = () => {
  isEditing.value = false
}

// Уведомления
const openNotificationModal = () => {
  notificationType.value = 'custom'
  notificationMessage.value = ''
  notificationSent.value = false
  notificationError.value = ''
  showNotificationModal.value = true
  updateNotificationMessage()
}

const updateNotificationMessage = () => {
  const studentName = selectedStudent.value?.profile?.user?.first_name || selectedStudent.value?.username || 'Студент'
  const debt = getStudentDebt(selectedStudent.value?.id)
  
  switch (notificationType.value) {
    case 'debt':
      notificationMessage.value = `Уважаемый(ая) ${studentName}! Напоминаем, что у вас есть задолженность в размере ${formatMoney(debt)}. Пожалуйста, произведите оплату.`
      break
    case 'schedule':
      notificationMessage.value = `Уважаемый(ая) ${studentName}! Напоминаем о предстоящем занятии. Расписание доступно в личном кабинете.`
      break
    case 'payment':
      notificationMessage.value = `Уважаемый(ая) ${studentName}! Ваш платеж успешно зачислен. Спасибо!`
      break
    default:
      notificationMessage.value = ''
  }
}

const sendNotification = async () => {
  if (!notificationMessage.value.trim()) {
    notificationError.value = 'Введите сообщение'
    return
  }
  
  notificationSent.value = false
  notificationError.value = ''
  
  try {
    await api.post('notifications/send/', {
      student_id: selectedStudent.value.id,
      message: notificationMessage.value,
      type: notificationType.value
    })
    
    notificationSent.value = true
    setTimeout(() => {
      closeNotificationModal()
    }, 2000)
  } catch (error) {
    notificationError.value = error.response?.data?.detail || 'Ошибка отправки'
  }
}

const closeNotificationModal = () => {
  showNotificationModal.value = false
  notificationSent.value = false
  notificationError.value = ''
}

// Следим за изменением типа уведомления
watch(notificationType, () => {
  updateNotificationMessage()
})

onMounted(() => {
  loadBranches()
  loadStudents()
})
</script>

<style scoped>
.students-container {
  padding: 20px;
  max-width: 1200px;
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

.filter-group select, .filter-group input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  min-width: 140px;
}

.refresh-btn, .create-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.create-btn {
  background: #28a745;
}

.students-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.student-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.2s;
}

.student-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.student-avatar {
  width: 60px;
  height: 60px;
  background: #007bff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: bold;
}

.student-info {
  flex: 1;
}

.student-info h3 {
  margin: 0 0 5px 0;
  font-size: 18px;
}

.student-username {
  font-size: 12px;
  color: #666;
  margin: 0;
}

.student-phone, .student-branch {
  font-size: 12px;
  color: #888;
  margin: 2px 0;
}

.student-debt {
  font-weight: bold;
  font-size: 16px;
  color: #4caf50;
}

.student-debt.has-debt {
  color: #ff5722;
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
  border-radius: 12px;
  width: 650px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  padding: 20px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.tabs button {
  padding: 8px 16px;
  background: #f8f9fa;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.tabs button.active {
  background: #007bff;
  color: white;
}

.tab-content {
  max-height: 500px;
  overflow-y: auto;
}

.info-row {
  display: flex;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.info-row .label {
  width: 120px;
  font-weight: bold;
  color: #666;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.edit-student-btn {
  background: #ffc107;
  color: #333;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
}

.notify-student-btn {
  background: #17a2b8;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
}

.edit-form {
  padding: 10px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  font-size: 13px;
}

.edit-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.edit-buttons {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.save-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.finance-filter {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
}

.finance-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.finance-card {
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  color: white;
}

.finance-card.income {
  background: linear-gradient(135deg, #28a745, #20c997);
}

.finance-card.expenses {
  background: linear-gradient(135deg, #dc3545, #fd7e14);
}

.finance-card.lessons-cost {
  background: linear-gradient(135deg, #007bff, #6610f2);
}

.finance-card .amount {
  font-size: 24px;
  font-weight: bold;
  margin: 10px 0 0;
}

.finance-card .amount.has-debt {
  color: #ffeb3b;
}

.calc-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th, .data-table td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.amount-cell {
  font-weight: bold;
  color: #28a745;
}

.lesson-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 8px;
}

.lesson-item.cancelled {
  background: #fff3e0;
  opacity: 0.8;
}

.badge-cancelled {
  background: #ff9800;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.badge-scheduled {
  background: #4caf50;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.loading, .empty {
  text-align: center;
  padding: 40px;
  color: #999;
}

/* Модальное окно уведомлений */
.notification-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}

.notification-modal-content {
  background: white;
  padding: 25px;
  border-radius: 12px;
  width: 500px;
  max-width: 90%;
}

.disabled-input {
  width: 100%;
  padding: 8px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  color: #666;
}

.message-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: vertical;
  font-family: inherit;
}

.notification-buttons {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.send-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.success-message {
  margin-top: 15px;
  padding: 10px;
  background: #d4edda;
  color: #155724;
  border-radius: 4px;
  text-align: center;
}

.error-message {
  margin-top: 15px;
  padding: 10px;
  background: #f8d7da;
  color: #721c24;
  border-radius: 4px;
  text-align: center;
}
</style>