<template>
  <div class="reports-container">
    <div class="header">
      <h1>📊 Отчеты</h1>
      <button @click="goBack" class="back-btn">← Назад</button>
    </div>

    <!-- Фильтры -->
    <div class="filters">
      <div class="filter-group">
        <label>📅 Период:</label>
        <select v-model="filters.period">
          <option value="week">Неделя</option>
          <option value="month">Месяц</option>
          <option value="year">Год</option>
        </select>
      </div>
      
      <div class="filter-group">
        <label>📋 Филиал:</label>
        <select v-model="filters.branch">
          <option :value="null">Все филиалы</option>
          <option v-for="branch in branches" :key="branch.id" :value="branch.id">
            {{ branch.name }}
          </option>
        </select>
      </div>
      
      <button @click="loadAllReports" class="refresh-btn">🔄 Обновить</button>
      
      <!-- Кнопка перехода к преподавателям -->
      <button @click="$router.push('/teachers')" class="teachers-btn">
        👨‍🏫 Зарплаты преподавателей
      </button>
    </div>

    <!-- Вкладки -->
    <div class="tabs">
      <button :class="{ active: activeTab === 'finance' }" @click="activeTab = 'finance'">💰 Финансы</button>
      <button :class="{ active: activeTab === 'payments' }" @click="activeTab = 'payments'">💳 Платежи</button>
      <button :class="{ active: activeTab === 'addPayment' }" @click="activeTab = 'addPayment'">➕ Добавить платеж</button>
      <button :class="{ active: activeTab === 'debtors' }" @click="activeTab = 'debtors'">⚠️ Должники</button>
      <button :class="{ active: activeTab === 'salaries' }" @click="activeTab = 'salaries'">👨‍🏫 Зарплаты</button>
      <button :class="{ active: activeTab === 'expenses' }" @click="activeTab = 'expenses'">💸 Расходы</button>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>

    <!-- Финансовый отчет с кликабельными карточками -->
    <div v-if="activeTab === 'finance' && !loading" class="finance-cards">
      <div class="card income" @click="showIncomeDetails">
        <h3>💰 Доходы</h3>
        <p class="amount">{{ formatMoney(financeData.total_income) }}</p>
        <p class="click-hint">▼ Нажмите для деталей</p>
      </div>
      <div class="card expenses" @click="showExpensesDetails">
        <h3>📉 Расходы</h3>
        <p class="amount">{{ formatMoney(financeData.total_expenses) }}</p>
        <p class="click-hint">▼ Нажмите для деталей</p>
      </div>
      <div class="card profit" @click="showProfitDetails">
        <h3>📈 Прибыль</h3>
        <p class="amount">{{ formatMoney(financeData.profit) }}</p>
        <p class="click-hint">▼ Нажмите для деталей</p>
      </div>
    </div>

    <!-- Модальное окно деталей -->
    <div v-if="showDetailsModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h2>{{ modalTitle }}</h2>
        <div class="modal-details">
          <div class="detail-row" v-for="(item, index) in modalDetails" :key="index">
            <span class="detail-label">{{ item.label }}</span>
            <span class="detail-value" :class="item.class">{{ item.value }}</span>
          </div>
        </div>
        <button @click="closeModal" class="modal-close-btn">Закрыть</button>
      </div>
    </div>

    <!-- Добавление платежа -->
    <div v-if="activeTab === 'addPayment' && !loading">
      <div class="add-payment-form">
        <h3>💳 Добавить платеж от студента</h3>
        
        <div class="form-group">
          <label>👨‍🎓 Студент *</label>
          <select v-model="newPayment.student_id">
            <option :value="null">-- Выберите студента --</option>
            <option v-for="student in studentsList" :key="student.id" :value="student.id">
              {{ student.profile?.user?.first_name || student.user?.first_name || student.username || 'Студент ' + student.id }}
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label>💰 Сумма *</label>
          <input type="number" v-model="newPayment.amount" placeholder="Например: 5000">
        </div>
        
        <div class="form-group">
          <label>💳 Способ оплаты *</label>
          <select v-model="newPayment.payment_method">
            <option value="cash">💵 Наличные</option>
            <option value="card">💳 Карта</option>
            <option value="transfer">🏦 Банковский перевод</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>📝 Назначение</label>
          <input type="text" v-model="newPayment.purpose" placeholder="Например: Апрель 2026">
        </div>
        
        <div class="form-group">
          <label>📚 Количество оплаченных занятий</label>
          <input type="number" v-model.number="newPayment.lessons_paid" placeholder="Например: 4">
        </div>
        
        <div class="form-group">
          <label>📅 Дата платежа (оставьте пустым для сегодня)</label>
          <input type="date" v-model="newPayment.date">
        </div>
        
        <div class="form-buttons">
          <button @click="addPayment" :disabled="addingPayment" class="submit-btn">
            {{ addingPayment ? 'Добавление...' : '✅ Добавить платеж' }}
          </button>
          <button @click="resetPaymentForm" class="reset-btn">🔄 Очистить</button>
        </div>
        
        <div v-if="paymentSuccess" class="success-message">
          🎉 Платеж успешно добавлен!
        </div>
        <div v-if="paymentError" class="error-message">
          ❌ {{ paymentError }}
        </div>
      </div>
    </div>

    <!-- Платежи (список с редактированием) -->
    <div v-if="activeTab === 'payments' && !loading">
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr><th>Дата</th><th>Студент</th><th>Сумма</th><th>Назначение</th><th>Способ</th><th>Действия</th></tr>
          </thead>
          <tbody>
            <tr v-for="payment in paymentsData" :key="payment.id">
              <td v-if="editingPaymentId !== payment.id">
                {{ payment.date }}
              </td>
              <td v-else>
                <input type="date" v-model="editPaymentForm.date" class="edit-input">
              </td>
              
              <td v-if="editingPaymentId !== payment.id">
                {{ payment.student_name }}
              </td>
              <td v-else>
                <select v-model="editPaymentForm.student_id" class="edit-input">
                  <option v-for="student in studentsList" :key="student.id" :value="student.id">
                    {{ student.profile?.user?.first_name || student.user?.first_name || student.username }}
                  </option>
                </select>
              </td>
              
              <td v-if="editingPaymentId !== payment.id" class="amount-cell">
                {{ formatMoney(payment.amount) }}
              </td>
              <td v-else>
                <input type="number" v-model="editPaymentForm.amount" class="edit-input">
              </td>
              
              <td v-if="editingPaymentId !== payment.id">
                {{ payment.purpose || '-' }}
              </td>
              <td v-else>
                <input type="text" v-model="editPaymentForm.purpose" class="edit-input">
              </td>
              
              <td v-if="editingPaymentId !== payment.id">
                {{ getPaymentMethodIcon(payment.payment_method) }}
              </td>
              <td v-else>
                <select v-model="editPaymentForm.payment_method" class="edit-input">
                  <option value="cash">💵 Наличные</option>
                  <option value="card">💳 Карта</option>
                  <option value="transfer">🏦 Перевод</option>
                </select>
              </td>
              
              <td>
                <div v-if="editingPaymentId !== payment.id" class="action-buttons">
                  <button @click="startEditPayment(payment)" class="edit-btn" title="Редактировать">✏️</button>
                  <button @click="deletePayment(payment.id)" class="delete-btn" title="Удалить">🗑️</button>
                </div>
                <div v-else class="action-buttons">
                  <button @click="saveEditPayment" class="save-btn" title="Сохранить">💾</button>
                  <button @click="cancelEditPayment" class="cancel-btn" title="Отмена">❌</button>
                </div>
              </td>
            </tr>
            <tr v-if="paymentsData.length === 0">
              <td colspan="6" class="empty">Нет платежей</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Должники -->
    <div v-if="activeTab === 'debtors' && !loading">
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr><th>Студент</th><th>Сумма долга</th><th>Последний платеж</th></tr>
          </thead>
          <tbody>
            <tr v-for="debtor in debtorsData" :key="debtor.student_id">
              <td>{{ debtor.student_name }}</td>
              <td class="debt-cell">{{ formatMoney(debtor.debt) }}</td>
              <td>{{ debtor.last_payment_date || 'Нет платежей' }} ({{ formatMoney(debtor.last_payment_amount) }})</td>
            </tr>
            <tr v-if="debtorsData.length === 0">
              <td colspan="3" class="empty">Нет должников 🎉</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Зарплаты преподавателей -->
    <div v-if="activeTab === 'salaries' && !loading">
      <div class="salary-summary">
        <div class="summary-card">
          <h4>Всего часов</h4>
          <p>{{ salariesData.total_hours || 0 }} ч</p>
        </div>
        <div class="summary-card">
          <h4>Общая зарплата</h4>
          <p>{{ formatMoney(salariesData.total_salary || 0) }}</p>
        </div>
      </div>
      
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr><th>Преподаватель</th><th>Часы</th><th>Ставка (₽/час)</th><th>Итого</th></tr>
          </thead>
          <tbody>
            <tr v-for="teacher in salariesData.teachers || []" :key="teacher.teacher_id">
              <td>{{ teacher.teacher_name }}</td>
              <td>{{ teacher.hours }} ч</td>
              <td>{{ formatMoney(teacher.hourly_rate) }}</td>
              <td class="amount-cell">{{ formatMoney(teacher.amount) }}</td>
            </tr>
            <tr v-if="!salariesData.teachers || salariesData.teachers.length === 0">
              <td colspan="4" class="empty">Нет данных о занятиях</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Расходы (список с редактированием) -->
    <div v-if="activeTab === 'expenses' && !loading">
      <div class="add-form">
        <h3>➕ Добавить расход</h3>
        <div class="form-row">
          <select v-model="newExpense.category">
            <option value="">-- Выберите категорию --</option>
            <option v-for="cat in expenseCategories" :key="cat" :value="cat">{{ cat }}</option>
          </select>
          <input type="number" v-model="newExpense.amount" placeholder="Сумма">
          <select v-model="newExpense.payment_method">
            <option value="cash">💵 Наличные</option>
            <option value="card">💳 Карта</option>
            <option value="transfer">🏦 Перевод</option>
          </select>
          <input type="text" v-model="newExpense.comment" placeholder="Комментарий">
          <button @click="addExpense" class="add-btn">➕ Добавить</button>
        </div>
      </div>
      
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr><th>Дата</th><th>Категория</th><th>Сумма</th><th>Способ</th><th>Комментарий</th><th>Действия</th></tr>
          </thead>
          <tbody>
            <tr v-for="expense in expensesData" :key="expense.id">
              <td v-if="editingExpenseId !== expense.id">
                {{ expense.date }}
              </td>
              <td v-else>
                <input type="date" v-model="editExpenseForm.date" class="edit-input">
              </td>
              
              <td v-if="editingExpenseId !== expense.id">
                {{ expense.category }}
              </td>
              <td v-else>
                <select v-model="editExpenseForm.category" class="edit-input">
                  <option v-for="cat in expenseCategories" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </td>
              
              <td v-if="editingExpenseId !== expense.id" class="debt-cell">
                {{ formatMoney(expense.amount) }}
              </td>
              <td v-else>
                <input type="number" v-model="editExpenseForm.amount" class="edit-input">
              </td>
              
              <td v-if="editingExpenseId !== expense.id">
                {{ getPaymentMethodIcon(expense.payment_method) }}
              </td>
              <td v-else>
                <select v-model="editExpenseForm.payment_method" class="edit-input">
                  <option value="cash">💵 Наличные</option>
                  <option value="card">💳 Карта</option>
                  <option value="transfer">🏦 Перевод</option>
                </select>
              </td>
              
              <td v-if="editingExpenseId !== expense.id">
                {{ expense.comment || '-' }}
              </td>
              <td v-else>
                <input type="text" v-model="editExpenseForm.comment" class="edit-input">
              </td>
              
              <td>
                <div v-if="editingExpenseId !== expense.id" class="action-buttons">
                  <button @click="startEditExpense(expense)" class="edit-btn" title="Редактировать">✏️</button>
                  <button @click="deleteExpense(expense.id)" class="delete-btn" title="Удалить">🗑️</button>
                </div>
                <div v-else class="action-buttons">
                  <button @click="saveEditExpense" class="save-btn" title="Сохранить">💾</button>
                  <button @click="cancelEditExpense" class="cancel-btn" title="Отмена">❌</button>
                </div>
              </td>
            </tr>
            <tr v-if="expensesData.length === 0">
              <td colspan="6" class="empty">Нет расходов</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const loading = ref(false)
const addingPayment = ref(false)
const activeTab = ref('finance')
const branches = ref([])
const studentsList = ref([])
const paymentSuccess = ref(false)
const paymentError = ref('')

// Модальное окно
const showDetailsModal = ref(false)
const modalTitle = ref('')
const modalDetails = ref([])

// Редактирование платежей
const editingPaymentId = ref(null)
const editPaymentForm = ref({
  id: null,
  student_id: null,
  amount: '',
  payment_method: 'cash',
  purpose: '',
  lessons_paid: 1,
  date: ''
})

// Редактирование расходов
const editingExpenseId = ref(null)
const editExpenseForm = ref({
  id: null,
  category: '',
  amount: '',
  payment_method: 'cash',
  comment: '',
  date: ''
})

const filters = ref({
  period: 'month',
  branch: null
})

const financeData = ref({
  total_income: 0,
  total_expenses: 0,
  profit: 0
})

const paymentsData = ref([])
const debtorsData = ref([])
const salariesData = ref({
  total_hours: 0,
  total_salary: 0,
  teachers: []
})

const expensesData = ref([])
const expenseCategories = ref([])

const newPayment = ref({
  student_id: null,
  amount: '',
  payment_method: 'cash',
  purpose: '',
  lessons_paid: 1,
  date: ''
})

const newExpense = ref({
  category: '',
  amount: '',
  payment_method: 'cash',
  comment: ''
})

const goBack = () => {
  router.push('/dashboard')
}

const formatMoney = (amount) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(amount || 0)
}

const getPaymentMethodIcon = (method) => {
  const icons = { cash: '💵 Наличные', card: '💳 Карта', transfer: '🏦 Перевод' }
  return icons[method] || method
}

const resetPaymentForm = () => {
  newPayment.value = {
    student_id: null,
    amount: '',
    payment_method: 'cash',
    purpose: '',
    lessons_paid: 1,
    date: ''
  }
  paymentSuccess.value = false
  paymentError.value = ''
}

// Детали доходов
const showIncomeDetails = () => {
  modalTitle.value = '💰 Детали доходов'
  const paymentsCount = paymentsData.value.length
  const averagePayment = paymentsCount > 0 ? financeData.value.total_income / paymentsCount : 0
  
  modalDetails.value = [
    { label: 'Общая сумма доходов:', value: formatMoney(financeData.value.total_income), class: 'income-value' },
    { label: 'Количество платежей:', value: paymentsCount, class: '' },
    { label: 'Средний платеж:', value: formatMoney(averagePayment), class: '' },
    { label: '📅 Период:', value: filters.value.period === 'week' ? 'Неделя' : filters.value.period === 'month' ? 'Месяц' : 'Год', class: '' }
  ]
  
  if (paymentsData.value.length > 0) {
    modalDetails.value.push({ label: '--- Топ-5 платежей ---', value: '', class: 'separator' })
    const topPayments = [...paymentsData.value].sort((a, b) => b.amount - a.amount).slice(0, 5)
    topPayments.forEach((payment, idx) => {
      modalDetails.value.push({
        label: `  ${idx + 1}. ${payment.student_name}:`,
        value: formatMoney(payment.amount),
        class: 'category-value'
      })
    })
  }
  showDetailsModal.value = true
}

// Детали расходов
const showExpensesDetails = () => {
  const categoriesTotal = {}
  expensesData.value.forEach(expense => {
    if (!categoriesTotal[expense.category]) {
      categoriesTotal[expense.category] = 0
    }
    categoriesTotal[expense.category] += expense.amount
  })
  
  const expensesCount = expensesData.value.length
  const averageExpense = expensesCount > 0 ? financeData.value.total_expenses / expensesCount : 0
  
  modalTitle.value = '📉 Детали расходов'
  modalDetails.value = [
    { label: 'Общая сумма расходов:', value: formatMoney(financeData.value.total_expenses), class: 'expense-value' },
    { label: 'Количество расходов:', value: expensesCount, class: '' },
    { label: 'Средний расход:', value: formatMoney(averageExpense), class: '' },
    { label: '📅 Период:', value: filters.value.period === 'week' ? 'Неделя' : filters.value.period === 'month' ? 'Месяц' : 'Год', class: '' },
    { label: '--- Расходы по категориям ---', value: '', class: 'separator' },
    ...Object.entries(categoriesTotal).map(([cat, sum]) => ({
      label: `  ${cat}:`,
      value: formatMoney(sum),
      class: 'category-value'
    }))
  ]
  showDetailsModal.value = true
}

// Детали прибыли
const showProfitDetails = () => {
  const profitMargin = financeData.value.total_income > 0 
    ? ((financeData.value.profit / financeData.value.total_income) * 100).toFixed(1)
    : 0
  
  modalTitle.value = '📈 Детали прибыли'
  modalDetails.value = [
    { label: '💰 Доходы:', value: formatMoney(financeData.value.total_income), class: 'income-value' },
    { label: '📉 Расходы:', value: formatMoney(financeData.value.total_expenses), class: 'expense-value' },
    { label: '💎 Прибыль:', value: formatMoney(financeData.value.profit), class: 'profit-value' },
    { label: '📊 Маржа прибыли:', value: `${profitMargin}%`, class: profitMargin >= 0 ? 'positive' : 'negative' },
    { label: '', value: '', class: '' },
    { label: '📅 Период:', value: filters.value.period === 'week' ? 'Неделя' : filters.value.period === 'month' ? 'Месяц' : 'Год', class: '' },
  ]
  
  let efficiency = ''
  if (profitMargin >= 30) {
    efficiency = '✅ Отлично! Высокая прибыльность'
  } else if (profitMargin >= 15) {
    efficiency = '👍 Хорошо, но есть потенциал роста'
  } else if (profitMargin >= 0) {
    efficiency = '⚠️ Низкая маржинальность, стоит оптимизировать расходы'
  } else {
    efficiency = '🔴 Убыток! Необходимо срочно увеличить доходы или сократить расходы'
  }
  modalDetails.value.push({ label: '📊 Оценка:', value: efficiency, class: 'efficiency-value' })
  
  showDetailsModal.value = true
}

const closeModal = () => {
  showDetailsModal.value = false
}

// Редактирование платежа
const startEditPayment = (payment) => {
  editingPaymentId.value = payment.id
  editPaymentForm.value = {
    id: payment.id,
    student_id: payment.student_id,
    amount: payment.amount,
    payment_method: payment.payment_method || 'cash',
    purpose: payment.purpose || '',
    lessons_paid: payment.lessons_paid || 1,
    date: payment.date
  }
}

const saveEditPayment = async () => {
  try {
    await api.put(`payments/${editPaymentForm.value.id}/`, {
      student: editPaymentForm.value.student_id,
      amount: editPaymentForm.value.amount,
      payment_method: editPaymentForm.value.payment_method,
      purpose: editPaymentForm.value.purpose,
      lessons_paid: editPaymentForm.value.lessons_paid,
      date: editPaymentForm.value.date
    })
    editingPaymentId.value = null
    await loadAllReports()
    alert('Платеж обновлен!')
  } catch (error) {
    alert('Ошибка обновления: ' + (error.response?.data?.detail || error.message))
  }
}

const cancelEditPayment = () => {
  editingPaymentId.value = null
}

const deletePayment = async (id) => {
  if (confirm('Удалить этот платеж?')) {
    try {
      await api.delete(`payments/${id}/`)
      await loadAllReports()
      alert('Платеж удален!')
    } catch (error) {
      alert('Ошибка удаления')
    }
  }
}

// Редактирование расхода
const startEditExpense = (expense) => {
  editingExpenseId.value = expense.id
  editExpenseForm.value = {
    id: expense.id,
    category: expense.category,
    amount: expense.amount,
    payment_method: expense.payment_method || 'cash',
    comment: expense.comment || '',
    date: expense.date
  }
}

const saveEditExpense = async () => {
  try {
    await api.put(`expenses/${editExpenseForm.value.id}/`, {
      category: editExpenseForm.value.category,
      amount: editExpenseForm.value.amount,
      payment_method: editExpenseForm.value.payment_method,
      comment: editExpenseForm.value.comment,
      date: editExpenseForm.value.date
    })
    editingExpenseId.value = null
    await loadAllReports()
    alert('Расход обновлен!')
  } catch (error) {
    alert('Ошибка обновления: ' + (error.response?.data?.detail || error.message))
  }
}

const cancelEditExpense = () => {
  editingExpenseId.value = null
}

const deleteExpense = async (id) => {
  if (confirm('Удалить расход?')) {
    try {
      await api.delete(`expenses/${id}/`)
      await loadExpenses()
      await loadFinanceReport()
      alert('Расход удален!')
    } catch (error) {
      alert('Ошибка удаления')
    }
  }
}

const loadStudents = async () => {
  try {
    const response = await api.get('students/')
    studentsList.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки студентов:', error)
  }
}

const addPayment = async () => {
  if (!newPayment.value.student_id) {
    paymentError.value = 'Выберите студента'
    return
  }
  if (!newPayment.value.amount || newPayment.value.amount <= 0) {
    paymentError.value = 'Введите сумму платежа'
    return
  }
  
  addingPayment.value = true
  paymentError.value = ''
  paymentSuccess.value = false
  
  try {
    const paymentData = {
      student: newPayment.value.student_id,
      amount: newPayment.value.amount,
      payment_method: newPayment.value.payment_method,
      purpose: newPayment.value.purpose || 'Оплата занятий',
      lessons_paid: newPayment.value.lessons_paid || 1,
    }
    
    if (newPayment.value.date) {
      paymentData.date = newPayment.value.date
    }
    
    await api.post('payments/', paymentData)
    paymentSuccess.value = true
    resetPaymentForm()
    await loadAllReports()
    
    setTimeout(() => {
      paymentSuccess.value = false
    }, 3000)
  } catch (error) {
    paymentError.value = error.response?.data?.detail || 'Ошибка при добавлении платежа'
  } finally {
    addingPayment.value = false
  }
}

const loadBranches = async () => {
  try {
    const response = await api.get('branches/')
    branches.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки филиалов:', error)
  }
}

const loadFinanceReport = async () => {
  try {
    const params = new URLSearchParams()
    params.append('period', filters.value.period)
    if (filters.value.branch) params.append('branch', filters.value.branch)
    
    const response = await api.get(`reports/finance/?${params.toString()}`)
    financeData.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки финансов:', error)
  }
}

const loadPaymentsReport = async () => {
  try {
    const params = new URLSearchParams()
    params.append('period', filters.value.period)
    if (filters.value.branch) params.append('branch', filters.value.branch)
    
    const response = await api.get(`reports/payments/?${params.toString()}`)
    paymentsData.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки платежей:', error)
  }
}

const loadDebtorsReport = async () => {
  try {
    const params = new URLSearchParams()
    if (filters.value.branch) params.append('branch', filters.value.branch)
    
    const response = await api.get(`reports/debtors/?${params.toString()}`)
    debtorsData.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки должников:', error)
  }
}

const loadSalariesReport = async () => {
  try {
    const params = new URLSearchParams()
    params.append('period', filters.value.period)
    if (filters.value.branch) params.append('branch', filters.value.branch)
    
    const response = await api.get(`reports/teacher-salaries/?${params.toString()}`)
    salariesData.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки зарплат:', error)
  }
}

const loadExpenses = async () => {
  try {
    const params = new URLSearchParams()
    params.append('period', filters.value.period)
    const response = await api.get(`expenses/?${params.toString()}`)
    expensesData.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки расходов:', error)
  }
}

const loadExpenseCategories = async () => {
  try {
    const response = await api.get('expenses-categories/')
    expenseCategories.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки категорий:', error)
    expenseCategories.value = ['Аренда', 'Зарплата', 'Коммунальные услуги', 'Канцелярия', 'Учебные материалы', 'Реклама', 'Налоги', 'Обслуживание', 'Другое']
  }
}

const addExpense = async () => {
  if (!newExpense.value.category || !newExpense.value.amount) {
    alert('Заполните категорию и сумму')
    return
  }
  try {
    await api.post('expenses/', newExpense.value)
    newExpense.value = { category: '', amount: '', payment_method: 'cash', comment: '' }
    await loadExpenses()
    await loadFinanceReport()
    alert('Расход добавлен!')
  } catch (error) {
    alert('Ошибка: ' + (error.response?.data?.detail || error.message))
  }
}

const loadAllReports = async () => {
  loading.value = true
  try {
    await Promise.all([
      loadFinanceReport(),
      loadPaymentsReport(),
      loadDebtorsReport(),
      loadSalariesReport(),
      loadExpenses()
    ])
  } finally {
    loading.value = false
  }
}

watch([() => filters.value.period, () => filters.value.branch], () => {
  loadAllReports()
})

onMounted(() => {
  loadBranches()
  loadStudents()
  loadExpenseCategories()
  loadAllReports()
})
</script>

<style scoped>
.reports-container {
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
  min-width: 140px;
}

.refresh-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.teachers-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: transform 0.2s;
}

.teachers-btn:hover {
  transform: translateY(-2px);
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
  flex-wrap: wrap;
}

.tabs button {
  padding: 10px 20px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  border-radius: 5px;
}

.tabs button.active {
  background: #007bff;
  color: white;
}

.finance-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  color: white;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

.card.income {
  background: linear-gradient(135deg, #28a745, #20c997);
}

.card.expenses {
  background: linear-gradient(135deg, #dc3545, #fd7e14);
}

.card.profit {
  background: linear-gradient(135deg, #007bff, #6610f2);
}

.card h3 {
  margin: 0 0 10px 0;
  font-size: 18px;
}

.card .amount {
  font-size: 32px;
  font-weight: bold;
  margin: 0;
}

.click-hint {
  font-size: 10px;
  margin-top: 8px;
  opacity: 0.7;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background: #f8f9fa;
  font-weight: bold;
}

.data-table tr:hover {
  background: #f8f9fa;
}

.amount-cell {
  font-weight: bold;
  color: #28a745;
}

.debt-cell {
  font-weight: bold;
  color: #dc3545;
}

.empty {
  text-align: center;
  color: #999;
  padding: 40px;
}

.loading {
  text-align: center;
  padding: 50px;
  font-size: 18px;
}

.salary-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.summary-card {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
}

.summary-card h4 {
  margin: 0 0 5px 0;
  color: #666;
}

.summary-card p {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.add-form,
.add-payment-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.add-form h3,
.add-payment-form h3 {
  margin: 0 0 15px 0;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #555;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.submit-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.reset-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.add-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.action-buttons {
  display: flex;
  gap: 5px;
}

.edit-btn, .delete-btn, .save-btn, .cancel-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 5px;
}

.edit-btn { color: #ffc107; }
.delete-btn { color: #dc3545; }
.save-btn { color: #28a745; }
.cancel-btn { color: #6c757d; }

.edit-input {
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 100%;
  min-width: 100px;
}

.success-message {
  background: #d4edda;
  color: #155724;
  padding: 10px;
  border-radius: 4px;
  margin-top: 15px;
  text-align: center;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 10px;
  border-radius: 4px;
  margin-top: 15px;
  text-align: center;
}

/* Модальное окно */
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
  padding: 25px;
  border-radius: 12px;
  min-width: 350px;
  max-width: 500px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.modal-content h2 {
  margin: 0 0 20px 0;
  text-align: center;
  color: #333;
}

.modal-details {
  margin-bottom: 20px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.detail-label {
  font-weight: normal;
  color: #666;
}

.detail-value {
  font-weight: bold;
  color: #333;
}

.detail-value.income-value {
  color: #28a745;
}

.detail-value.expense-value {
  color: #dc3545;
}

.detail-value.profit-value {
  color: #007bff;
}

.detail-value.positive {
  color: #28a745;
}

.detail-value.negative {
  color: #dc3545;
}

.detail-value.category-value {
  color: #17a2b8;
}

.detail-value.efficiency-value {
  color: #6f42c1;
  font-size: 14px;
}

.detail-value.separator {
  font-weight: bold;
  color: #333;
  margin-top: 10px;
}

.modal-close-btn {
  width: 100%;
  padding: 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.modal-close-btn:hover {
  background: #0056b3;
}
</style>