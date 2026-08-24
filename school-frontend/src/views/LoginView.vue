<template>
  <div class="login-container">
    <div class="login-card">
      <h1>🏫 English School CRM</h1>
      <p class="subtitle">Система управления школой английского языка</p>
      
      <div class="login-form">
        <input 
          v-model="credentials.username"
          type="text" 
          placeholder="Логин" 
          class="input-field"
        >
        <input 
          v-model="credentials.password"
          type="password" 
          placeholder="Пароль" 
          class="input-field"
        >
        <button 
          @click="handleLogin" 
          :disabled="loading"
          class="login-btn"
        >
          {{ loading ? 'Вход...' : 'Войти' }}
        </button>
      </div>

      <div class="demo-accounts">
        <h3>Тестовые аккаунты:</h3>
        <p><strong>Админ:</strong> admin / admin123</p>
        <p><strong>Преподаватель:</strong> teacher1 / teacher123</p>
        <p><strong>Студент:</strong> student1 / student123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '@/services/api'

const router = useRouter()

const credentials = ref({
  username: '',
  password: ''
})
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  
  try {
    const response = await authAPI.login(credentials.value)
    const token = response.data.token
    
    // Сохраняем токен
    localStorage.setItem('auth_token', token)
    
    // Перенаправляем на дашборд
    router.push('/dashboard')
    
  } catch (error) {
    alert('Ошибка входа: ' + (error.response?.data?.non_field_errors?.[0] || 'Неверные данные'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  padding: 40px;
  border-radius: 15px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  text-align: center;
  max-width: 400px;
  width: 100%;
}

h1 {
  color: #333;
  margin-bottom: 10px;
}

.subtitle {
  color: #666;
  margin-bottom: 30px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 30px;
}

.input-field {
  padding: 12px 15px;
  border: 2px solid #e1e1e1;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.input-field:focus {
  outline: none;
  border-color: #667eea;
}

.login-btn {
  padding: 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.3s;
}

.login-btn:hover:not(:disabled) {
  background: #5a6fd8;
}

.login-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.demo-accounts {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  text-align: left;
}

.demo-accounts h3 {
  margin-bottom: 10px;
  color: #333;
}

.demo-accounts p {
  margin: 5px 0;
  color: #666;
  font-size: 14px;
}
</style>