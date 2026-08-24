<template>
  <div class="payments-page">
    <div class="payments-header">
      <h1>💳 История платежей</h1>
      <button class="back-btn" @click="$router.push('/dashboard')">← Назад в кабинет</button>
    </div>

    <div v-if="payments.length === 0" class="empty-payments">
      <p>У вас пока нет платежей</p>
    </div>

    <div v-else class="payments-table-container">
      <table class="payments-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Сумма</th>
            <th>Способ оплаты</th>
            <th>Назначение</th>
            <th>Количество занятий</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="payment in payments" :key="payment.id">
            <td>{{ payment.date }}</td>
            <td class="amount">{{ formatMoney(payment.amount) }}</td>
            <td>{{ getPaymentMethodIcon(payment.payment_method) }}</td>
            <td>{{ payment.purpose || '-' }}</td>
            <td>{{ payment.lessons_paid || 1 }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="total-row">
            <td colspan="4"><strong>Итого оплачено:</strong></td>
            <td colspan="1"><strong>{{ formatMoney(totalPaid) }}</strong></td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';

const router = useRouter();
const payments = ref([]);
const totalPaid = ref(0);

onMounted(async () => {
  await loadPayments();
});

async function loadPayments() {
  try {
    const res = await api.get('my-payments/');
    payments.value = res.data;
    totalPaid.value = res.data.reduce((sum, p) => sum + parseFloat(p.amount), 0);
  } catch (error) {
    console.error('Ошибка загрузки платежей', error);
  }
}

function formatMoney(amount) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' }).format(amount);
}

function getPaymentMethodIcon(method) {
  const icons = { 'cash': '💵 Наличные', 'card': '💳 Карта', 'transfer': '🏦 Перевод' };
  return icons[method] || method;
}
</script>

<style scoped>
.payments-page {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.payments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.back-btn {
  padding: 10px 20px;
  background: #f0f2f5;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
}

.back-btn:hover {
  background: #e4e6eb;
}

.payments-table-container {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  overflow-x: auto;
}

.payments-table {
  width: 100%;
  border-collapse: collapse;
}

.payments-table th, .payments-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #efefef;
}

.payments-table th {
  background: #fafafa;
  font-weight: 600;
  color: #8e8e8e;
}

.payments-table .amount {
  font-weight: 600;
  color: #262626;
}

.total-row {
  background: #f0f9ff;
}

.empty-payments {
  text-align: center;
  padding: 60px;
  color: #8e8e8e;
  background: white;
  border-radius: 20px;
}
</style>
