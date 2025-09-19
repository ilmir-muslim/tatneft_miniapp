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
            <option v-for="fuel in fuels" :key="fuel.fuel_type_id" :value="fuel">
              {{ fuel.name }} - {{ fuel.discount_price || fuel.price }} ₽/л
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
        <div class="payment-instructions" v-html="formattedInstructions"></div>

        <div class="input-group">
          <label>Загрузите скриншот чека:</label>
          <input type="file" accept="image/*,application/pdf" @change="handleReceiptUpload" class="input-field">
          <img v-if="receiptPreview" :src="receiptPreview" alt="Предпросмотр чека" class="receipt-preview">
        </div>

        <button class="btn primary" @click="submitPayment" :disabled="!receiptImage">
          Отправить чек на проверку
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
        <p>Номер вашей заявки: #{{ orderId }}</p>
      </div>

      <!-- Экран 5: Результат проверки -->
      <div v-if="currentScreen === 'result'" class="card">
        <h2>Результат проверки</h2>
        <div v-if="orderStatus === 'принято'" class="result-content">
          <div class="success-icon">✓</div>
          <p class="success-message">Оплата принята! Можете заправляться. Хорошей дороги!</p>
        </div>
        <div v-else class="result-content">
          <div class="error-icon">✗</div>
          <p class="error-message">В оплате отказано.</p>
          <p v-if="rejectionReason" class="rejection-reason">Причина: {{ rejectionReason }}</p>
        </div>
        <button class="btn primary" @click="resetApp">
          Создать новый заказ
        </button>
      </div>
    </main>

    <footer class="footer">
      <p>АЗС «Татнефть» © {{ new Date().getFullYear() }}</p>
    </footer>

    <!-- Уведомление -->
    <div v-if="showNotification" class="notification" :class="notificationType">
      {{ notificationMessage }}
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import api from './services/api'

export default {
  name: 'App',
  setup() {
    // Инициализация Telegram WebApp
    const initTelegramApp = () => {
      if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp
        tg.expand()
        tg.enableClosingConfirmation()

        // Установка цветовой схемы из Telegram
        if (tg.themeParams) {
          document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff')
          document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#222222')
          document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#40a7e3')
          document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff')
          document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#40a7e3')
          document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f0f0f0')
        }

        return tg
      }
      return null
    }

    const tgApp = ref(initTelegramApp())
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
    const receiptPreview = ref(null)
    const orderStatus = ref('')
    const rejectionReason = ref('')
    const orderId = ref(null)
    const showNotification = ref(false)
    const notificationMessage = ref('')
    const notificationType = ref('info')

    // Вычисляемое свойство для форматирования инструкций
    const formattedInstructions = computed(() => {
      return paymentInstructions.value.replace(/\n/g, '<br>')
    })

    // Загрузка данных при инициализации
    onMounted(() => {
      loadPaymentInstructions()

      // Следим за изменением темы в Telegram
      if (tgApp.value) {
        tgApp.value.onEvent('themeChanged', () => {
          theme.value = tgApp.value.colorScheme
        })
        theme.value = tgApp.value.colorScheme
      }
    })

    const showNotify = (message, type = 'info') => {
      notificationMessage.value = message
      notificationType.value = type
      showNotification.value = true

      setTimeout(() => {
        showNotification.value = false
      }, 3000)
    }

    const validateStation = async () => {
      if (!stationNumber.value) {
        showNotify('Введите номер АЗС', 'error')
        return
      }

      try {
        const azsResponse = await api.getFuelPrices(stationNumber.value)

        if (azsResponse.data && azsResponse.data.fuel && azsResponse.data.fuel.length > 0) {
          fuels.value = azsResponse.data.fuel
          selectedFuel.value = fuels.value[0]
          currentScreen.value = 'fuel'
        } else {
          showNotify('АЗС с таким номером не найдена', 'error')
        }
      } catch (error) {
        console.error('Error loading AZS data:', error)
        showNotify('Ошибка загрузки данных АЗС', 'error')
      }
    }

    const calculateTotal = () => {
      if (!selectedFuel.value || !amount.value) {
        total.value = 0
        return
      }

      const price = selectedFuel.value.discount_price || selectedFuel.value.price

      if (isVolume.value) {
        total.value = (price * parseFloat(amount.value)).toFixed(2)
      } else {
        // Если оплата по сумме, вычисляем объем
        const volume = parseFloat(amount.value) / price
        total.value = parseFloat(amount.value).toFixed(2)
      }
    }

    const goToPayment = () => {
      if (!selectedFuel.value || !columnNumber.value || !amount.value) {
        showNotify('Заполните все поля', 'error')
        return
      }

      currentScreen.value = 'payment'
    }

    const loadPaymentInstructions = async () => {
      try {
        const response = await api.getSettings()
        paymentInstructions.value = response.data.payment_instructions
      } catch (error) {
        console.error('Error loading payment instructions:', error)
        paymentInstructions.value = 'Оплатите заказ по реквизитам:\n- Номер карты: 0000 0000 0000 0000\n- Телефон: +7 000 000-00-00'
      }
    }

    const handleReceiptUpload = (event) => {
      const file = event.target.files[0]
      if (file && (file.type.startsWith('image/') || file.type === 'application/pdf')) {
        receiptImage.value = file

        // Создаем превью для изображений
        if (file.type.startsWith('image/')) {
          const reader = new FileReader()
          reader.onload = (e) => {
            receiptPreview.value = e.target.result
          }
          reader.readAsDataURL(file)
        } else {
          // Для PDF показываем иконку
          receiptPreview.value = '/pdf-icon.png' // Добавьте иконку PDF в папку public
        }
      } else {
        showNotify('Пожалуйста, выберите изображение или PDF-файл', 'error')
      }
    }

    const checkOrderStatus = async () => {
      if (!orderId.value) return

      try {
        const response = await api.getOrderStatus(orderId.value)
        const status = response.data.status

        if (status !== 'ожидание') {
          orderStatus.value = status
          rejectionReason.value = response.data.rejection_reason
          currentScreen.value = 'result'
        } else {
          // Если статус еще "ожидание", проверяем снова через 5 секунд
          setTimeout(checkOrderStatus, 5000)
        }
      } catch (error) {
        console.error('Ошибка проверки статуса:', error)
        setTimeout(checkOrderStatus, 5000)
      }
    }

    const submitPayment = async () => {
      try {
        // Проверяем обязательные поля
        if (!stationNumber.value || !columnNumber.value || !selectedFuel.value || !amount.value) {
          showNotify('Заполните все обязательные поля', 'error');
          return;
        }

        // Получаем данные пользователя из Telegram
        const userData = tgApp.value ? tgApp.value.initDataUnsafe.user : null;
        const userId = userData ? userData.id : Math.floor(Math.random() * 1000000);

        const formData = new FormData();
        formData.append('user_id', userId);
        formData.append('azs_number', parseInt(stationNumber.value));
        formData.append('column_number', parseInt(columnNumber.value));
        formData.append('fuel_type', selectedFuel.value.name);

        // Добавляем объем или сумму
        const numericValue = parseFloat(amount.value);
        if (isVolume.value) {
          formData.append('volume', numericValue);
        } else {
          formData.append('amount', numericValue);
        }

        // Добавляем файл если есть
        if (receiptImage.value) {
          formData.append('cheque_image', receiptImage.value);
        }

        const response = await api.createOrder(formData);
        orderId.value = response.data.id;
        currentScreen.value = 'waiting';

        // Запускаем опрос статуса заказа
        setTimeout(checkOrderStatus, 5000);
      } catch (error) {
        console.error('Ошибка отправки чека:', error);
        showNotify('Ошибка отправки чека: ' + (error.response?.data?.detail || error.message), 'error');
      }
    }
    
    const resetApp = () => {
      currentScreen.value = 'station'
      stationNumber.value = ''
      fuels.value = []
      selectedFuel.value = null
      columnNumber.value = ''
      amount.value = ''
      total.value = 0
      receiptImage.value = null
      receiptPreview.value = null
      orderStatus.value = ''
      rejectionReason.value = ''
      orderId.value = null
    }

    return {
      tgApp,
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
      formattedInstructions,
      receiptImage,
      receiptPreview,
      orderStatus,
      rejectionReason,
      orderId,
      showNotification,
      notificationMessage,
      notificationType,
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
/* Стили для всех экранов */
.card {
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.input-group {
  margin-bottom: 16px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--tg-theme-text-color, #222222);
}

.input-field {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--tg-theme-hint-color, #aaaaaa);
  border-radius: 8px;
  background-color: var(--tg-theme-bg-color, #ffffff);
  color: var(--tg-theme-text-color, #222222);
  font-size: 16px;
}

.toggle-group {
  display: flex;
  gap: 8px;
}

.toggle-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--tg-theme-hint-color, #aaaaaa);
  border-radius: 8px;
  background: var(--tg-theme-secondary-bg-color, #f0f0f0);
  color: var(--tg-theme-text-color, #222222);
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn.active {
  background-color: var(--tg-theme-button-color, #40a7e3);
  color: var(--tg-theme-button-text-color, #ffffff);
}

.btn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-right: 10px;
  margin-bottom: 10px;
}

.btn.primary {
  background-color: var(--tg-theme-button-color, #40a7e3);
  color: var(--tg-theme-button-text-color, #ffffff);
}

.btn.secondary {
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
  color: var(--tg-theme-text-color, #222222);
  border: 1px solid var(--tg-theme-hint-color, #aaaaaa);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.total {
  margin: 20px 0;
  padding: 16px;
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
  border-radius: 8px;
  text-align: center;
}

.payment-instructions {
  padding: 16px;
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
  border-radius: 8px;
  margin-bottom: 20px;
  color: var(--tg-theme-text-color, #222222);
}

.receipt-preview {
  max-width: 100%;
  max-height: 200px;
  margin-top: 10px;
  border-radius: 8px;
  border: 1px solid var(--tg-theme-hint-color, #aaaaaa);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--tg-theme-secondary-bg-color, #f0f0f0);
  border-top: 4px solid var(--tg-theme-button-color, #40a7e3);
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

.result-content {
  text-align: center;
  margin: 20px 0;
}

.success-icon,
.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.success-icon {
  color: #27ae60;
}

.error-icon {
  color: #e74c3c;
}

.success-message {
  color: #27ae60;
  font-weight: bold;
}

.error-message {
  color: #e74c3c;
  font-weight: bold;
}

.rejection-reason {
  color: var(--tg-theme-text-color, #222222);
  margin-top: 10px;
}

.notification {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 20px;
  border-radius: 8px;
  z-index: 1000;
  max-width: 80%;
  text-align: center;
}

.notification.info {
  background-color: var(--tg-theme-button-color, #40a7e3);
  color: var(--tg-theme-button-text-color, #ffffff);
}

.notification.error {
  background-color: #e74c3c;
  color: white;
}

.notification.success {
  background-color: #27ae60;
  color: white;
}

/* Адаптивность */
@media (max-width: 480px) {
  .card {
    padding: 16px;
  }

  .btn {
    width: 100%;
    margin-right: 0;
  }

  .toggle-group {
    flex-direction: column;
  }
}
</style>