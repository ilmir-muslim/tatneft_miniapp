<template>
  <div class="app" :class="{ 'app-dark': theme === 'dark' }">
    <header class="header">
      <h1>{{ appTitle }}</h1>
      <p>Оплата топлива на АЗС «Татнефть»</p>
    </header>

    <main class="main">
      <!-- Экран 1: Ввод номера АЗС -->
      <div v-if="currentScreen === 'station'" class="card">
        <h2>Введите номер АЗС</h2>
        <div class="input-group">
          <input v-model="stationNumber" type="number" min="1" max="999" placeholder="Номер АЗС" class="input-field">
          <button class="btn primary" @click="validateStation" :disabled="!stationNumber">
            Далее
          </button>
        </div>
      </div>

      <!-- Экран 2: Выбор топлива и ввод данных -->
      <div v-if="currentScreen === 'fuel'" class="card">
        <h2>Выбор топлива</h2>
        <div class="input-group">
          <label>Вид топлива:</label>
          <select v-model="selectedFuel" @change="calculateTotal" class="input-field">
            <option v-for="fuel in fuels" :key="fuel.id" :value="fuel">
              {{ fuel.name }} - {{ fuel.price }} ₽/л
            </option>
          </select>
        </div>

        <div class="input-group">
          <label>Номер колонки:</label>
          <input v-model="columnNumber" type="number" min="1" class="input-field">
        </div>

        <div class="input-group">
          <label>Тип заправки:</label>
          <div class="toggle-group">
            <button :class="['toggle-btn', { active: isVolume }]" @click="isVolume = true">
              По объёму
            </button>
            <button :class="['toggle-btn', { active: !isVolume }]" @click="isVolume = false">
              По сумме
            </button>
          </div>
        </div>

        <div class="input-group">
          <label>{{ isVolume ? 'Объем (л)' : 'Сумма (₽)' }}:</label>
          <input v-model="amount" @input="calculateTotal" type="number" min="1" class="input-field">
        </div>

        <div class="total">
          <h3>Итого к оплате: {{ total }} ₽</h3>
        </div>

        <button class="btn primary" @click="goToPayment">
          Перейти к оплате
        </button>
        <button class="btn secondary" @click="currentScreen = 'station'">
          Назад
        </button>
      </div>

      <!-- Экран 3: Инструкция по оплате -->
      <div v-if="currentScreen === 'payment'" class="card">
        <h2>Инструкция по оплате</h2>
        <div class="payment-instructions" v-html="paymentInstructions"></div>

        <div class="input-group">
          <label>Загрузите скриншот чека:</label>
          <input type="file" accept="image/*" @change="handleReceiptUpload" class="input-field">
        </div>

        <button class="btn primary" @click="submitPayment" :disabled="!receiptImage">
          Чек отправлен на проверку
        </button>
        <button class="btn secondary" @click="currentScreen = 'fuel'">
          Назад
        </button>
      </div>

      <!-- Экран 4: Ожидание проверки -->
      <div v-if="currentScreen === 'waiting'" class="card">
        <h2>Ожидание проверки</h2>
        <div class="loading-spinner"></div>
        <p>Ожидайте подтверждения оплаты администратором</p>
      </div>

      <!-- Экран 5: Результат проверки -->
      <div v-if="currentScreen === 'result'" class="card">
        <h2>Результат проверки</h2>
        <div v-if="orderStatus === 'approved'">
          <p class="success-message">Оплата принята! Можете заправляться. Хорошей дороги!</p>
        </div>
        <div v-else>
          <p class="error-message">В оплате отказано. Причина: {{ rejectionReason }}</p>
        </div>
        <button class="btn primary" @click="resetApp">
          Создать новый заказ
        </button>
      </div>
    </main>

    <footer class="footer">
      <p>АЗС «Татнефть»</p>
    </footer>
  </div>
</template>

<script>
import { onMounted, ref, computed } from 'vue'

export default {
  name: 'App',
  setup() {
    const theme = ref('light')
    const currentScreen = ref('station')
    const stationNumber = ref('')
    const fuels = ref([])
    const selectedFuel = ref(null)
    const columnNumber = ref('')
    const isVolume = ref(true)
    const amount = ref('')
    const total = ref(0)
    const paymentInstructions = ref('')
    const receiptImage = ref(null)
    const orderStatus = ref('')
    const rejectionReason = ref('')
    const orderId = ref(null)
    const discount = ref(null)
    const isLoading = ref(false)

    // Загрузка данных при инициализации
    onMounted(() => {
      initTelegramApp()
      loadPaymentInstructions()
    })

    const initTelegramApp = () => {
      if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp
        tg.expand()
        theme.value = tg.colorScheme
        tg.onEvent('themeChanged', () => {
          theme.value = tg.colorScheme
        })
      }
    }

    const validateStation = async () => {
      isLoading.value = true
      try {
        // Здесь будет реальный API запрос
        const mockResponse = {
          fuels: [
            { id: 1, name: 'АИ-92', price: 45.30 },
            { id: 2, name: 'АИ-95', price: 48.90 },
            { id: 3, name: 'ДТ', price: 47.50 }
          ],
          discount: { type: 'percent', value: 5 } // Пример скидки 5%
        }

        fuels.value = mockResponse.fuels
        discount.value = mockResponse.discount
        selectedFuel.value = fuels.value[0]
        currentScreen.value = 'fuel'
      } catch (error) {
        alert('Ошибка загрузки данных АЗС')
      } finally {
        isLoading.value = false
      }
    }

    const calculateTotal = () => {
      if (!selectedFuel.value || !amount.value) {
        total.value = 0
        return
      }

      let finalPrice = selectedFuel.value.price

      // Применение скидки
      if (discount.value) {
        if (discount.value.type === 'percent') {
          finalPrice = finalPrice * (1 - discount.value.value / 100)
        } else if (discount.value.type === 'fixed') {
          finalPrice = Math.max(0, finalPrice - discount.value.value)
        }
      }

      if (isVolume.value) {
        total.value = (finalPrice * amount.value).toFixed(2)
      } else {
        total.value = amount.value
      }
    }

    const goToPayment = () => {
      if (!selectedFuel.value || !columnNumber.value || !amount.value) {
        alert('Заполните все поля')
        return
      }
      loadPaymentInstructions()
      currentScreen.value = 'payment'
    }

    const loadPaymentInstructions = async () => {
      try {
        // Здесь будет API запрос
        paymentInstructions.value = `
      <p>Для оплаты переведите <strong>${total.value} ₽</strong> на:</p>
      <p>СБП: +7 (XXX) XXX-XX-XX</p>
      <p>Карта: XXXX XXXX XXXX XXXX</p>
      <p>В комментарии укажите: АЗС-${stationNumber.value}, Колонка-${columnNumber.value}</p>
      <p>Скидка: ${discount.value ? discount.value.value + (discount.value.type === 'percent' ? '%' : '₽') : '0%'}</p>
    `
      } catch (error) {
        paymentInstructions.value = 'Не удалось загрузить инструкцию. Попробуйте позже.'
      }
    }

    const handleReceiptUpload = (event) => {
      const file = event.target.files[0]
      if (file && file.type.startsWith('image/')) {
        receiptImage.value = file
      } else {
        alert('Пожалуйста, выберите изображение')
      }
    }

    const submitPayment = async () => {
      try {
        // Здесь будет API запрос для создания заказа
        currentScreen.value = 'waiting'

        // Заглушка - в реальности будет WebSocket или polling
        setTimeout(() => {
          orderStatus.value = 'approved' // или 'rejected'
          rejectionReason.value = 'Нечитаемый чек'
          currentScreen.value = 'result'
        }, 3000)
      } catch (error) {
        alert('Ошибка отправки чека')
      }
    }

    const resetApp = () => {
      currentScreen.value = 'station'
      stationNumber.value = ''
      fuels.value = []
      selectedFuel.value = null
      columnNumber.value = ''
      amount.value = ''
      receiptImage.value = null
    }

    return {
      theme,
      currentScreen,
      stationNumber,
      fuels,
      selectedFuel,
      columnNumber,
      isVolume,
      amount,
      total,
      paymentInstructions,
      receiptImage,
      orderStatus,
      rejectionReason,
      validateStation,
      calculateTotal,
      goToPayment,
      handleReceiptUpload,
      submitPayment,
      resetApp
    }
  }
}
</script>

<style scoped>
.input-group {
  margin-bottom: 16px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.input-field {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: var(--card-bg);
  color: var(--text-color);
}

.toggle-group {
  display: flex;
  gap: 8px;
}

.toggle-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--secondary-color);
  cursor: pointer;
}

.toggle-btn.active {
  background-color: var(--primary-color);
  color: white;
}

.total {
  margin: 20px 0;
  padding: 16px;
  background-color: var(--secondary-color);
  border-radius: 8px;
  text-align: center;
}

.payment-instructions {
  padding: 16px;
  background-color: var(--secondary-color);
  border-radius: 8px;
  margin-bottom: 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top: 4px solid var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 20px auto;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.success-message {
  color: green;
  font-weight: bold;
  text-align: center;
  margin: 20px 0;
}

.error-message {
  color: red;
  text-align: center;
  margin: 20px 0;
}
</style>