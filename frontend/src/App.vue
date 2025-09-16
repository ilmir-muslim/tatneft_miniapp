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
import api from './services/api'; // Импорт API сервиса

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
      isLoading.value = true;
      try {
        // Сначала получаем данные об АЗС
        const azsResponse = await api.getFuelPrices(stationNumber.value);
        console.log('AZS Response:', azsResponse.data); // Для отладки

        if (azsResponse.data.fuel && azsResponse.data.fuel.length > 0) {
          // Преобразуем данные в нужный формат
          fuels.value = azsResponse.data.fuel.map((item) => ({
            id: item.fuel_type_id,
            name: item.name,
            price: item.price, // оригинальная цена
            discount_price: item.discount_price, // цена со скидкой
            color: item.color,
            filterGroup: item.filter_group
          }));

          // Затем получаем настройки
          const settingsResponse = await api.getSettings();
          discount.value = {
            type: settingsResponse.data.discount_type,
            value: settingsResponse.data.discount_value
          };

          selectedFuel.value = fuels.value[0];
          currentScreen.value = 'fuel';
        } else {
          alert('АЗС с таким номером не найдена');
        }
      } catch (error) {
        alert('Ошибка загрузки данных АЗС');
        console.error('Error loading AZS data:', error);
      } finally {
        isLoading.value = false;
      }
    };
    
    const calculateTotal = () => {
      console.log('Selected fuel:', selectedFuel.value)
      console.log('Amount:', amount.value)
      console.log('Total:', total.value)
      if (!selectedFuel.value || !amount.value) {
        total.value = 0
        return
      }

      // Используем discount_price если доступен, иначе price
      const finalPrice = selectedFuel.value.discount_price !== null && selectedFuel.value.discount_price !== undefined
        ? selectedFuel.value.discount_price
        : selectedFuel.value.price

      if (isVolume.value) {
        total.value = (finalPrice * amount.value).toFixed(2)
      } else {
        // Если оплата по сумме, вычисляем объем
        total.value = amount.value
      }
    }

    const goToPayment = () => {
      if (!selectedFuel.value || !columnNumber.value || !amount.value) {
        alert('Заполните все поля')
        return
      }

      // Передаем правильные данные
      const finalPrice = selectedFuel.value.discount_price !== null && selectedFuel.value.discount_price !== undefined
        ? selectedFuel.value.discount_price
        : selectedFuel.value.price

      console.log('Final price:', finalPrice) // Для отладки
      loadPaymentInstructions()
      currentScreen.value = 'payment'
    }

    const loadPaymentInstructions = async () => {
      try {
        const response = await api.getSettings();
        paymentInstructions.value = response.data.payment_instructions;
      } catch (error) {
        paymentInstructions.value = 'Не удалось загрузить инструкцию. Попробуйте позже.';
      }
    };

    const handleReceiptUpload = (event) => {
      const file = event.target.files[0]
      if (file && file.type.startsWith('image/')) {
        receiptImage.value = file
      } else {
        alert('Пожалуйста, выберите изображение')
      }
    }

    const checkOrderStatus = async () => {
      const checkStatus = async () => {
        try {
          const response = await api.getOrderStatus(orderId.value);
          const status = response.data.status;

          if (status !== 'ожидание') {
            orderStatus.value = status === 'принято' ? 'approved' : 'rejected';
            rejectionReason.value = response.data.rejection_reason;
            currentScreen.value = 'result';
          } else {
            // Если статус еще "ожидание", проверяем снова через 5 секунд
            setTimeout(checkStatus, 5000);
          }
        } catch (error) {
          console.error('Ошибка проверки статуса:', error);
          setTimeout(checkStatus, 5000);
        }
      };

      checkStatus();
    };


    const submitPayment = async () => {
      try {
        const formData = {
          user_id: window.Telegram.WebApp.initDataUnsafe.user?.id || 1, // ID из Telegram
          azs_number: parseInt(stationNumber.value),
          column_number: parseInt(columnNumber.value),
          fuel_type: selectedFuel.value.name,
          volume: isVolume.value ? parseFloat(amount.value) : null,
          amount: isVolume.value ? null : parseFloat(amount.value),
        };

        if (receiptImage.value) {
          formData.cheque_image = receiptImage.value;
        }

        const response = await api.createOrder(formData);
        orderId.value = response.data.id;
        currentScreen.value = 'waiting';

        // Запускаем опрос статуса заказа
        checkOrderStatus();
      } catch (error) {
        alert('Ошибка отправки чека');
      }
    };

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