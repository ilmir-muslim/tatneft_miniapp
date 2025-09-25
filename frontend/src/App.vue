<template>
  <div class="app" :class="{ 'app-dark': theme === 'dark' }">
    <header class="header">
      <h1>{{ appTitle }}</h1>
      <p>Оплата топлива на АЗС «Татнефть» через Альфа-Банк</p>
    </header>

    <main class="main">
      <!-- Экран 1: Ввод номера АЗС -->
      <div v-if="currentScreen === 'station'" class="card">
        <h2>Введите номер АЗС</h2>
        <div class="input-group">
          <input v-model="stationNumber" type="number" min="1" max="999" placeholder="Номер АЗС" class="input-field"
            :disabled="loadingStation">
          <button class="btn primary" @click="validateStation" :disabled="!stationNumber || loadingStation">
            <span v-if="loadingStation" class="button-loading">
              <span class="mini-spinner"></span>
              Загрузка...
            </span>
            <span v-else>Далее</span>
          </button>
        </div>

        <!-- Индикатор загрузки под кнопкой -->
        <div v-if="loadingStation" class="loading-indicator">
          <p>Ищем АЗС №{{ stationNumber }}...</p>
          <div class="loading-spinner"></div>
        </div>
      </div>
      <!-- Экран 2: Выбор топлива и ввод данных -->
      <div v-if="currentScreen === 'fuel'" class="card">
        <h2>Выбор топлива</h2>

        <div v-if="fuels.length === 0" class="loading-indicator">
          <p>Загрузка данных о топливе...</p>
          <div class="loading-spinner"></div>
        </div>

        <div v-else>
          <div class="input-group">
            <label>Вид топлива:</label>
            <select v-model="selectedFuel" @change="calculateTotal" class="input-field">
              <option v-for="fuel in fuels" :key="fuel.fuel_type_id" :value="fuel">
                {{ fuel.name }} - {{ fuel.discount_price || fuel.price }} ₽/л
              </option>
            </select>
          </div>
        </div>
        <div class="input-group">
          <label>Номер колонки:</label>
          <input v-model="columnNumber" type="number" class="input-field" placeholder="Введите номер колонки">
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

      <!-- Экран 3: Выбор конкретной АЗС -->
      <div v-if="currentScreen === 'select_station'" class="card">
        <h2>Выберите АЗС №{{ stationNumber }}</h2>
        <p>Найдено несколько АЗС с этим номером:</p>

        <div class="station-list">
          <div v-for="station in matchingStations" :key="station.id" class="station-item"
            @click="selectSpecificStation(station)">
            <div class="station-info">
              <h3>АЗС №{{ station.number }}</h3>
              <p class="station-address">{{ formatAddress(station.address) }}</p>
              <p class="station-region">{{ station.region }}</p>
            </div>
            <div class="station-arrow">→</div>
          </div>
        </div>

        <button class="btn secondary" @click="currentScreen = 'station'">
          Назад к вводу номера
        </button>
      </div>

      <!-- Экран 4: Подтверждение и оплата через Альфа-Банк -->
      <div v-if="currentScreen === 'payment'" class="card">
        <h2>Подтверждение заказа</h2>

        <div class="order-summary">
          <h3>Детали заказа:</h3>
          <p><strong>АЗС:</strong> №{{ stationNumber }}</p>
          <p><strong>Колонка:</strong> {{ columnNumber }}</p>
          <p><strong>Топливо:</strong> {{ selectedFuel.name }}</p>
          <p><strong>Сумма:</strong> {{ total }} ₽</p>
        </div>

        <div class="payment-info">
          <p>Оплата будет произведена через безопасный шлюз Альфа-Банка.</p>
          <p>После подтверждения вы будете перенаправлены на страницу оплаты.</p>
        </div>

        <button class="btn primary" @click="processPayment">
          Оплатить через Альфа-Банк
        </button>
        <button class="btn secondary" @click="currentScreen = 'fuel'">
          Назад
        </button>
      </div>

      <!-- Экран 5: Ожидание подтверждения платежа -->
      <div v-if="currentScreen === 'processing'" class="card">
        <h2>Обработка платежа</h2>
        <div class="loading-spinner"></div>
        <p>Пожалуйста, не закрывайте страницу</p>
        <p>Происходит перенаправление в платежную систему...</p>
      </div>

      <!-- Экран 6: Перенаправление на страницу банка -->
      <div v-if="currentScreen === 'redirect'" class="card">
        <h2>Перенаправление в Альфа-Банк</h2>
        <div class="redirect-info">
          <p>Вы будете перенаправлены на безопасную страницу оплаты Альфа-Банка.</p>
          <p>Если перенаправление не произошло автоматически, нажмите кнопку ниже:</p>
          <button class="btn primary" @click="redirectToBank">
            Перейти к оплате
          </button>
        </div>
      </div>

      <!-- Экран 7: Ожидание подтверждения от банка -->
      <div v-if="currentScreen === 'waiting'" class="card">
        <h2>Ожидание подтверждения</h2>
        <div class="loading-spinner"></div>
        <p>Ожидаем подтверждение оплаты от банка</p>
        <p>Номер вашей заявки: #{{ orderId }}</p>
      </div>

      <!-- Экран 8: Результат оплаты -->
      <div v-if="currentScreen === 'result'" class="card">
        <h2>Результат оплаты</h2>
        <div v-if="orderStatus === 'принято'" class="result-content">
          <div class="success-icon">✓</div>
          <p class="success-message">Оплата прошла успешно! Можете заправляться.</p>
          <p class="transaction-info">Номер транзакции: {{ transactionId }}</p>
        </div>
        <div v-else class="result-content">
          <div class="error-icon">✗</div>
          <p class="error-message">Оплата не прошла.</p>
          <p v-if="rejectionReason" class="rejection-reason">Причина: {{ rejectionReason }}</p>
          <button class="btn secondary" @click="retryPayment">
            Попробовать снова
          </button>
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
import { ref, computed, onMounted } from 'vue'
import api from './services/api'

export default {
  name: 'App',
  setup() {
    const tgApp = ref(null)
    const theme = ref('light')
    const currentScreen = ref('station')
    const stationNumber = ref('')
    const fuels = ref([])
    const selectedFuel = ref(null)
    const columnNumber = ref('')
    const isVolume = ref(true)
    const amount = ref('')
    const total = ref(0)
    const orderStatus = ref('')
    const rejectionReason = ref('')
    const orderId = ref(null)
    const transactionId = ref(null)
    const paymentUrl = ref('')
    const showNotification = ref(false)
    const notificationMessage = ref('')
    const notificationType = ref('info')
    const matchingStations = ref([])
    const selectedStation = ref(null)
    const loadingStation = ref(false)
    

    const initTelegramApp = () => {
      if (window.Telegram && window.Telegram.WebApp) {
        // Реальный Telegram MiniApp
        const tg = window.Telegram.WebApp
        tg.expand()
        tg.enableClosingConfirmation()
        return tg
      } else {
        // Режим отладки в браузере
        console.log('Режим отладки: Заглушка для Telegram WebApp')
        return {
          initDataUnsafe: {
            user: {
              id: Math.floor(Math.random() * 1000000),
              first_name: 'Test',
              last_name: 'User',
              username: 'test_user'
            }
          },
          colorScheme: 'light'
        }
      }
    }

    onMounted(() => {
      tgApp.value = initTelegramApp()
      if (tgApp.value) {
        theme.value = tgApp.value.colorScheme
      }
    })

    const formatAddress = (address) => {
      if (!address) return 'Адрес не указан'
      // Убираем повторяющиеся части (например, регион)
      return address.replace(selectedStation.value?.region + ', ', '')
    }

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

      // Включаем индикатор загрузки
      loadingStation.value = true

      try {
        const azsResponse = await api.getFuelPrices(stationNumber.value)

        // Обрабатываем оба формата ответа
        if (azsResponse.data.need_selection) {
          matchingStations.value = azsResponse.data.azs_list;
          currentScreen.value = 'select_station';
        } else if (azsResponse.data.fuel) {
          // Если АЗС одна и данные о топливе пришли сразу
          selectedStation.value = {
            id: azsResponse.data.id || azsResponse.data.azs_number,
            number: azsResponse.data.azs_number,
            address: azsResponse.data.address,
            region: azsResponse.data.region,
            fuel: azsResponse.data.fuel
          };
          fuels.value = azsResponse.data.fuel;
          selectedFuel.value = fuels.value[0];
          currentScreen.value = 'fuel';
        } else {
          showNotify('АЗС с таким номером не найдена', 'error');
        }
      } catch (error) {
        console.error('Error loading AZS data:', error);
        // Пробуем использовать кэшированные данные как fallback
        try {
          const cachedResponse = await api.getSpecificAzs(stationNumber.value, stationNumber.value)
          if (cachedResponse.data && cachedResponse.data.fuel) {
            selectedStation.value = {
              id: cachedResponse.data.id,
              number: cachedResponse.data.azs_number,
              address: cachedResponse.data.address,
              region: cachedResponse.data.region,
              fuel: cachedResponse.data.fuel
            };
            fuels.value = cachedResponse.data.fuel;
            selectedFuel.value = fuels.value[0];
            currentScreen.value = 'fuel';
            showNotify('Используются кэшированные данные', 'info');
          } else {
            showNotify('АЗС с таким номером не найдена', 'error');
          }
        } catch (fallbackError) {
          showNotify('Ошибка загрузки данных АЗС', 'error');
        }
      } finally {
        // Выключаем индикатор загрузки в любом случае
        loadingStation.value = false
      }
    }

    const selectSpecificStation = async (station) => {
      try {
        loadingStation.value = true;

        // Делаем запрос за данными конкретной АЗС с топливом
        const response = await api.getSpecificAzs(station.number, station.id);

        if (response.data && response.data.fuel) {
          selectedStation.value = {
            id: station.id,
            number: station.number,
            address: station.address,   
            region: station.region,
            fuel: response.data.fuel
          };

          fuels.value = response.data.fuel;
          selectedFuel.value = fuels.value[0];
          currentScreen.value = 'fuel';

          console.log('Данные АЗС загружены:', {
            id: station.id,
            fuels: fuels.value.length
          });
        } else {
          showNotify('Не удалось загрузить данные по топливу', 'error');
        }
      } catch (error) {
        console.error('Ошибка загрузки данных АЗС:', error);
        showNotify('Ошибка загрузки данных АЗС', 'error');
      } finally {
        loadingStation.value = false;
      }
    }
            
    const calculateTotal = () => {
      if (!selectedFuel.value || !amount.value || !fuels.value || fuels.value.length === 0) {
        total.value = 0;
        return;
      }

      const price = selectedFuel.value.discount_price || selectedFuel.value.price;
      if (isVolume.value) {
        total.value = (price * parseFloat(amount.value)).toFixed(2);
      } else {
        total.value = parseFloat(amount.value).toFixed(2);
      }
    }

    const goToPayment = () => {
      if (!selectedStation.value || !selectedFuel.value || !columnNumber.value || !amount.value) {
        showNotify('Заполните все поля', 'error')
        return
      }
      currentScreen.value = 'payment'
    }


const processPayment = async () => {
      try {
        currentScreen.value = 'processing'

        const fuelPrice = selectedFuel.value.discount_price || selectedFuel.value.price

        const orderData = {
          user_id: tgApp.value?.initDataUnsafe?.user?.id || 1,
          azs_number: parseInt(stationNumber.value),
          azs_id: selectedStation.value.id, // Добавляем ID конкретной АЗС
          azs_address: selectedStation.value.address, // И адрес для ясности
          column_number: parseInt(columnNumber.value),
          fuel_type: selectedFuel.value.name,
          fuel_price: parseFloat(fuelPrice),
          volume: isVolume.value ? parseFloat(amount.value) : null,
          amount: !isVolume.value ? parseFloat(amount.value) : null,
        }

        const orderResponse = await api.createOrder(orderData)
        orderId.value = orderResponse.data.id

        // Создаем платеж в Альфа-Банке
        const returnUrl = `${window.location.origin}/payment-result`
        const paymentResponse = await api.createPayment(orderId.value, returnUrl)

        paymentUrl.value = paymentResponse.data.payment_url
        transactionId.value = paymentResponse.data.payment_id

        // Переходим к перенаправлению
        currentScreen.value = 'redirect'

      } catch (error) {
        console.error('Ошибка создания платежа:', error)
        showNotify('Ошибка создания платежа', 'error')
        currentScreen.value = 'payment'
      }
    }

    const redirectToBank = () => {
      if (paymentUrl.value) {
        // Проверяем, это эмулятор или реальный URL
        if (paymentUrl.value.includes('/payment-emulator/')) {
          // Для эмулятора открываем в том же окне
          window.open(paymentUrl.value, '_blank', 'width=600,height=700')
        } else {
          // Для реального банка открываем в новом окне
          window.open(paymentUrl.value, '_blank')
        }
        currentScreen.value = 'waiting'
        checkOrderStatus()
      }
    }

    const checkOrderStatus = async () => {
      if (!orderId.value) return

      try {
        // Пробуем получить статус через эмулятор
        const emulatorResponse = await api.get(`/payment-emulator/status/${orderId.value}`)
        if (emulatorResponse.data.status === 'found') {
          const paymentStatus = emulatorResponse.data.payment_status

          if (paymentStatus === 'COMPLETED') {
            orderStatus.value = 'принято'
            transactionId.value = emulatorResponse.data.transaction_id
            currentScreen.value = 'result'
            return
          } else if (paymentStatus === 'DECLINED' || paymentStatus === 'CANCELLED') {
            orderStatus.value = 'отказано'
            rejectionReason.value = emulatorResponse.data.failure_reason || 'Платеж не прошел'
            currentScreen.value = 'result'
            return
          }
        }

        // Если через эмулятор не нашли, используем стандартный API
        const response = await api.getOrderStatus(orderId.value)
        const status = response.data.status

        if (status !== 'ожидание') {
          orderStatus.value = status
          rejectionReason.value = response.data.rejection_reason
          transactionId.value = response.data.transaction_id
          currentScreen.value = 'result'
        } else {
          setTimeout(checkOrderStatus, 2000) // Проверяем каждые 2 секунды
        }
      } catch (error) {
        console.error('Ошибка проверки статуса:', error)
        setTimeout(checkOrderStatus, 5000)
      }
    }

    // Добавьте обработчик сообщений от эмулятора
    onMounted(() => {
      window.addEventListener('message', (event) => {
        if (event.data.type === 'payment_completed') {
          // Обрабатываем сообщение от эмулятора
          if (event.data.status === 'COMPLETED') {
            orderStatus.value = 'принято'
            showNotify('Платеж успешно завершен!', 'success')
          } else {
            orderStatus.value = 'отказано'
            rejectionReason.value = event.data.message
            showNotify('Платеж не прошел', 'error')
          }
          currentScreen.value = 'result'
        }
      })
    })
    const retryPayment = () => {
      currentScreen.value = 'payment'
    }

    const resetApp = () => {
      currentScreen.value = 'station'
      stationNumber.value = ''
      fuels.value = []
      selectedFuel.value = null
      columnNumber.value = ''
      amount.value = ''
      total.value = 0
      orderStatus.value = ''
      rejectionReason.value = ''
      orderId.value = null
      transactionId.value = null
      paymentUrl.value = ''
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
      orderStatus,
      rejectionReason,
      orderId,
      transactionId,
      showNotification,
      notificationMessage,
      notificationType,
      validateStation,
      calculateTotal,
      goToPayment,
      processPayment,
      redirectToBank,
      retryPayment,
      resetApp,
      matchingStations,
      selectedStation,
      formatAddress,
      selectSpecificStation,
      loadingStation
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

.loading-indicator {
  text-align: center;
  margin-top: 20px;
  padding: 15px;
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
  border-radius: 8px;
}

.loading-indicator p {
  margin-bottom: 10px;
  color: var(--tg-theme-text-color, #222222);
}

/* Мини-спиннер для кнопки */
.button-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.mini-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input-field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
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

.order-summary {
  padding: 16px;
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
  border-radius: 8px;
  margin-bottom: 20px;
}

.order-summary h3 {
  margin-bottom: 10px;
}

.payment-info {
  padding: 16px;
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
}

.redirect-info {
  text-align: center;
  padding: 20px;
}

.transaction-info {
  font-size: 14px;
  color: #666;
  margin-top: 10px;
}

.station-list {
  margin: 1rem 0;
}

.station-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  margin-bottom: 0.5rem;
  border: 1px solid var(--tg-theme-hint-color, #aaaaaa);
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.station-item:hover {
  background-color: var(--tg-theme-secondary-bg-color, #f0f0f0);
}

.station-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
}

.station-address {
  margin: 0 0 0.25rem 0;
  font-size: 0.9rem;
  color: var(--tg-theme-hint-color, #aaaaaa);
}

.station-region {
  margin: 0;
  font-size: 0.8rem;
  color: var(--tg-theme-hint-color, #aaaaaa);
}

.station-arrow {
  font-size: 1.2rem;
  color: var(--tg-theme-hint-color, #aaaaaa);
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