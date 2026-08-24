<template>
  <div class="create-student-form">
    <h2>👨‍🎓 Создание нового студента</h2>
    
    <div class="form-group">
      <label>Логин пользователя *</label>
      <input v-model="formData.username" type="text" class="form-input" placeholder="student_ivanov">
    </div>

    <div class="form-group">
      <label>Пароль *</label>
      <input v-model="formData.password" type="password" class="form-input" placeholder="******">
    </div>

    <div class="form-group">
      <label>Имя</label>
      <input v-model="formData.first_name" type="text" class="form-input" placeholder="Иван">
    </div>

    <div class="form-group">
      <label>Фамилия</label>
      <input v-model="formData.last_name" type="text" class="form-input" placeholder="Иванов">
    </div>

    <div class="form-group">
      <label>Email</label>
      <input v-model="formData.email" type="email" class="form-input" placeholder="ivan@example.com">
    </div>

    <div class="form-group">
      <label>Телефон</label>
      <input v-model="formData.phone_number" type="tel" class="form-input" placeholder="+7 (999) 123-45-67">
    </div>

    <div class="form-group">
      <label>Филиал *</label>
      <select v-model="formData.branch" class="form-input">
        <option :value="null">-- Выберите филиал --</option>
        <option v-for="branch in branches" :key="branch.id" :value="branch.id">
          {{ branch.name }}
        </option>
      </select>
    </div>

    <div class="form-group">
      <label>ФИО родителя</label>
      <input v-model="formData.parent_name" type="text" class="form-input" placeholder="Иванова Мария Петровна">
    </div>

    <div class="form-group">
      <label>Формат обучения</label>
      <select v-model="formData.format" class="form-input">
        <option value="offline">Офлайн</option>
        <option value="online">Онлайн</option>
      </select>
    </div>

    <div class="form-group">
      <label>Скидка (%)</label>
      <input v-model.number="formData.discount" type="number" min="0" max="100" class="form-input" placeholder="0">
    </div>

    <div class="form-actions">
      <button @click="handleSubmit" :disabled="loading" class="submit-btn">
        {{ loading ? 'Создание...' : '✅ Создать студента' }}
      </button>
      <button @click="goBack" class="cancel-btn">Отмена</button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="success" class="success-message">
      🎉 Студент успешно создан! Перенаправление...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const success = ref(false)
const branches = ref([])

const formData = ref({
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  branch: null,
  parent_name: '',
  format: 'offline',
  discount: 0
})

onMounted(async () => {
  await loadBranches()
})

const loadBranches = async () => {
  try {
    const response = await api.get('branches/')
    branches.value = response.data
    if (branches.value.length > 0) {
      formData.value.branch = branches.value[0].id
    }
  } catch (err) {
    console.error('Ошибка загрузки филиалов:', err)
  }
}

const goBack = () => {
  router.push('/dashboard')
}

const handleSubmit = async () => {
  if (!formData.value.username) {
    error.value = 'Введите логин'
    return
  }
  if (!formData.value.password) {
    error.value = 'Введите пароль'
    return
  }
  if (!formData.value.branch) {
    error.value = 'Выберите филиал'
    return
  }
  
  loading.value = true
  error.value = ''
  success.value = false

  try {
    const response = await api.post('create-student/', formData.value)
    success.value = true
    
    // Очищаем форму
    formData.value = {
      username: '',
      password: '',
      first_name: '',
      last_name: '',
      email: '',
      phone_number: '',
      branch: branches.value[0]?.id || null,
      parent_name: '',
      format: 'offline',
      discount: 0
    }

    // Через 2 секунды возвращаемся на дашборд
    setTimeout(() => {
      router.push('/dashboard')
    }, 2000)

  } catch (err) {
    error.value = err.response?.data?.error || 'Ошибка при создании студента'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-student-form {
  max-width: 500px;
  margin: 0 auto;
  padding: 30px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-top: 50px;
}

h2 {
  margin-bottom: 20px;
  color: #333;
  text-align: center;
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

.form-input {
  width: 100%;
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

.submit-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  flex: 1;
}

.submit-btn:hover:not(:disabled) {
  background: #218838;
}

.submit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.cancel-btn:hover {
  background: #5a6268;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 10px;
  border-radius: 6px;
  margin-top: 15px;
  border: 1px solid #f5c6cb;
}

.success-message {
  background: #d4edda;
  color: #155724;
  padding: 10px;
  border-radius: 6px;
  margin-top: 15px;
  border: 1px solid #c3e6cb;
  text-align: center;
}
</style>