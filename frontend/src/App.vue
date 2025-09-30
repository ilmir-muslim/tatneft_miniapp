<template>
  <div class="app" :class="{ 'app-dark': theme === 'dark' }">
    <header class="header">
      <h1>{{ appTitle }}</h1>
      <p>Оплата топлива на АЗС «Татнефть»</p>

      <div class="header-controls">
        <div class="theme-toggle">
          <button @click="toggleTheme" class="btn secondary">
            {{ theme === 'light' ? '🌙' : '☀️' }}
          </button>
        </div>

        <div v-if="currentUser" class="user-menu">
          <span class="user-greeting">Привет, {{ currentUser.first_name || currentUser.username }}!</span>
          <button @click="handleLogout" class="btn secondary">Выйти</button>
        </div>
      </div>
    </header>

    <main class="main">
      <!-- Экран авторизации -->
      <div v-if="!currentUser && showAuth" class="auth-screen">
        <!-- Форма входа -->
        <div v-if="authMode === 'login'" class="card">
          <h2>Вход в систему</h2>

          <form @submit.prevent="handleLogin">
            <div class="input-group">
              <label>Логин, email или телефон:</label>
              <input v-model="loginData.login" type="text" required class="input-field">
            </div>

            <div class="input-group">
              <label>Пароль:</label>
              <input v-model="loginData.password" type="password" required class="input-field">
            </div>

            <button type="submit" class="btn primary" :disabled="loading">
              <span v-if="loading" class="button-loading">
                <span class="mini-spinner"></span>
                Вход...
              </span>
              <span v-else>Войти</span>
            </button>
          </form>

          <div class="auth-links">
            <p>Нет аккаунта? <a href="#" @click="authMode = 'register'">Зарегистрироваться</a></p>
          </div>
        </div>

        <!-- Форма регистрации -->
        <div v-else class="card">
          <h2>Регистрация</h2>

          <form @submit.prevent="handleRegister">
            <div class="input-group">
              <label>Имя пользователя *:</label>
              <input v-model="userData.username" type="text" required class="input-field">
            </div>

            <div class="input-group">
              <label>Телефон:</label>
              <input v-model="userData.phone" type="tel" class="input-field" placeholder="+7 XXX XXX XX XX">
            </div>

            <div class="input-group">
              <label>Email:</label>
              <input v-model="userData.email" type="email" class="input-field">
            </div>

            <div class="input-group">
              <label>Имя:</label>
              <input v-model="userData.first_name" type="text" class="input-field">
            </div>

            <div class="input-group">
              <label>Фамилия:</label>
              <input v-model="userData.last_name" type="text" class="input-field">
            </div>

            <div class="input-group">
              <label>Пароль *:</label>
              <input v-model="userData.password" type="password" required class="input-field">
            </div>

            <button type="submit" class="btn primary" :disabled="loading">
              <span v-if="loading" class="button-loading">
                <span class="mini-spinner"></span>
                Регистрация...
              </span>
              <span v-else>Зарегистрироваться</span>
            </button>
          </form>

          <div class="auth-links">
            <p>Уже есть аккаунт? <a href="#" @click="authMode = 'login'">Войти</a></p>
          </div>
        </div>

        <button class="btn secondary" @click="showAuth = false; authMode = 'login'">
          Назад к приложению
        </button>
      </div>

      <!-- Основной интерфейс приложения -->
      <div v-else>
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

          <div v-if="!selectedStationForMap" class="station-selection">
            <p>Найдено несколько АЗС с этим номером:</p>

            <div class="station-list">
              <div v-for="station in matchingStations" :key="station.id" class="station-item"
                :class="{ 'selected': selectedStationForMap && selectedStationForMap.id === station.id }"
                @click="selectStationForMap(station)">
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

          <!-- Выбранная АЗС с картой -->
          <transition name="station-expand">
            <div v-if="selectedStationForMap" class="selected-station-with-map">
              <div class="selected-station-card">
                <div class="station-header">
                  <h3>АЗС №{{ selectedStationForMap.number }}</h3>
                  <button class="btn secondary small" @click="deselectStation">
                    ← Выбрать другую
                  </button>
                </div>
                <p class="station-address">{{ selectedStationForMap.address }}</p>
                <p class="station-region">{{ selectedStationForMap.region }}</p>
              </div>

              <!-- Яндекс карта -->
              <div class="map-container">
                <div id="yandex-map" ref="yandexMap" class="yandex-map"></div>
                <div class="map-overlay">
                  <p>📍 {{ selectedStationForMap.address }}</p>
                </div>
              </div>

              <button class="btn primary confirm-btn" @click="confirmStationSelection">
                Подтвердить выбор этой АЗС
              </button>
            </div>
          </transition>
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
      </div>
    </main>

    <footer class="footer">
      <p>АЗС «Татнефть» © {{ new Date().getFullYear() }}</p>
      <button v-if="!currentUser && !showAuth" @click="showAuth = true" class="btn secondary">
        Войти / Зарегистрироваться
      </button>
    </footer>

    <!-- Уведомление -->
    <div v-if="showNotification" class="notification" :class="notificationType">
      {{ notificationMessage }}
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import api from './services/api'

export default {
  name: 'App',
  setup() {
    // Переменные темы и интерфейса
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
    const selectedStationForMap = ref(null)
    const yandexMap = ref(null)
    let map = null
    let placemark = null

    // Переменные авторизации
    const currentUser = ref(null)
    const showAuth = ref(false)
    const authMode = ref('login')
    const loading = ref(false)
    const loginData = ref({
      login: '',
      password: ''
    })
    const userData = ref({
      username: '',
      phone: '',
      email: '',
      first_name: '',
      last_name: '',
      password: ''
    })

    const appTitle = computed(() => {
      return 'Татнефть - Оплата топлива'
    })

    // Проверка авторизации при загрузке
    onMounted(() => {
      checkAuth()

      window.addEventListener('message', (event) => {
        if (event.data.type === 'payment_completed') {
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

    // Методы авторизации
    const checkAuth = async () => {
      const token = localStorage.getItem('user_token')
      if (token) {
        try {
          const response = await api.getCurrentUser()
          currentUser.value = response.data
        } catch (error) {
          console.error('Auth check failed:', error)
          localStorage.removeItem('user_token')
          localStorage.removeItem('user_data')
        }
      }
    }

    const handleLogin = async () => {
      if (!loginData.value.login || !loginData.value.password) {
        showNotify('Заполните все поля', 'error')
        return
      }

      loading.value = true

      try {
        const response = await api.login(loginData.value)

        // Сохраняем токен и данные пользователя
        localStorage.setItem('user_token', response.data.access_token)
        localStorage.setItem('user_data', JSON.stringify(response.data.user))

        currentUser.value = response.data.user
        showAuth.value = false
        showNotify('Успешный вход!', 'success')

        // Сбрасываем форму
        loginData.value = { login: '', password: '' }
      } catch (error) {
        console.error('Login error:', error)
        showNotify(error.response?.data?.detail || 'Ошибка входа', 'error')
      } finally {
        loading.value = false
      }
    }

    const handleRegister = async () => {
      if (!userData.value.username || !userData.value.password) {
        showNotify('Заполните обязательные поля (имя пользователя и пароль)', 'error')
        return
      }

      loading.value = true

      try {
        const response = await api.register(userData.value)
        showNotify('Регистрация успешна! Теперь вы можете войти.', 'success')

        // Автоматически входим после регистрации
        const loginResponse = await api.login({
          login: userData.value.username,
          password: userData.value.password
        })

        localStorage.setItem('user_token', loginResponse.data.access_token)
        localStorage.setItem('user_data', JSON.stringify(loginResponse.data.user))

        currentUser.value = loginResponse.data.user
        showAuth.value = false

        // Сбрасываем форму
        userData.value = {
          username: '',
          phone: '',
          email: '',
          first_name: '',
          last_name: '',
          password: ''
        }
      } catch (error) {
        console.error('Registration error:', error)
        showNotify(error.response?.data?.detail || 'Ошибка регистрации', 'error')
      } finally {
        loading.value = false
      }
    }

    const handleLogout = async () => {
      try {
        await api.logout()
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        localStorage.removeItem('user_token')
        localStorage.removeItem('user_data')
        currentUser.value = null
        showNotify('Вы вышли из системы', 'info')
      }
    }

    const selectStationForMap = async (station) => {
      selectedStationForMap.value = station

      // Ждем следующего тика DOM для применения анимации
      await nextTick()

      // Инициализируем карту после анимации
      setTimeout(() => {
        initYandexMap(station)
      }, 500)
    }

    const deselectStation = () => {
      // Уничтожаем карту при уходе
      if (map) {
        map.destroy()
        map = null
        placemark = null
      }
      selectedStationForMap.value = null
    }
    const initYandexMap = (station) => {
      // Проверяем, загружена ли Яндекс Карта API
      if (!window.ymaps) {
        loadYandexMapsAPI().then(() => {
          createMap(station)
        })
      } else {
        createMap(station)
      }
    }

    const loadYandexMapsAPI = () => {
      return new Promise((resolve, reject) => {
        if (window.ymaps) {
          resolve()
          return
        }

        const script = document.createElement('script')
        script.src = 'https://api-maps.yandex.ru/2.1/?apikey=1da45877-c8a9-4ff3-9d61-f927482e3584&lang=ru_RU'
        script.onload = () => {
          window.ymaps.ready(resolve)
        }
        script.onerror = reject
        document.head.appendChild(script)
      })
    }

    const createMap = (station) => {
      if (!yandexMap.value) return

      // Геокодирование адреса для получения координат
      window.ymaps.geocode(station.address).then((res) => {
        const firstGeoObject = res.geoObjects.get(0)
        if (!firstGeoObject) return

        const coordinates = firstGeoObject.geometry.getCoordinates()

        // Создаем карту
        map = new window.ymaps.Map(yandexMap.value, {
          center: coordinates,
          zoom: 15,
          controls: ['zoomControl', 'fullscreenControl']
        })

        // Добавляем метку
        placemark = new window.ymaps.Placemark(coordinates, {
          hintContent: station.address,
          balloonContent: `
            <strong>АЗС №${station.number}</strong><br/>
            ${station.address}<br/>
            ${station.region || ''}
          `
        }, {
          preset: 'islands#icon',
          iconColor: '#ff0000'
        })

        map.geoObjects.add(placemark)

        // Открываем балун с информацией
        placemark.balloon.open()
      }).catch((error) => {
        console.error('Ошибка геокодирования:', error)
        // Если геокодирование не удалось, создаем карту с центром в регионе
        createDefaultMap(station)
      })
    }

    const createDefaultMap = (station) => {
      if (!yandexMap.value) return

      // Используем координаты по умолчанию для региона
      const defaultCoords = getDefaultCoordsForRegion(station.region)

      map = new window.ymaps.Map(yandexMap.value, {
        center: defaultCoords,
        zoom: 10,
        controls: ['zoomControl', 'fullscreenControl']
      })

      // Добавляем метку с текстом вместо точных координат
      placemark = new window.ymaps.Placemark(defaultCoords, {
        hintContent: station.address,
        balloonContent: `
          <strong>АЗС №${station.number}</strong><br/>
          ${station.address}<br/>
          ${station.region || ''}<br/>
          <em>Точное местоположение требует уточнения</em>
        `
      }, {
        preset: 'islands#dotIcon',
        iconColor: '#ffaa00'
      })

      map.geoObjects.add(placemark)
      placemark.balloon.open()
    }

    const getDefaultCoordsForRegion = (region) => {
      // Примерные координаты для основных регионов
      const regionCoords = {
        'Москва': [55.7558, 37.6173],
        'Санкт-Петербург': [59.9343, 30.3351],
        'Татарстан': [55.7944, 49.1114],
        'default': [55.7558, 37.6173] // Москва по умолчанию
      }

      if (!region) return regionCoords.default

      for (const [key, coords] of Object.entries(regionCoords)) {
        if (region.toLowerCase().includes(key.toLowerCase())) {
          return coords
        }
      }

      return regionCoords.default
    }

    const confirmStationSelection = async () => {
      if (!selectedStationForMap.value) return

      try {
        loadingStation.value = true
        await selectSpecificStation(selectedStationForMap.value)

        // Уничтожаем карту после перехода
        if (map) {
          map.destroy()
          map = null
          placemark = null
        }
      } catch (error) {
        console.error('Ошибка подтверждения АЗС:', error)
        showNotify('Ошибка загрузки данных АЗС', 'error')
      } finally {
        loadingStation.value = false
      }
    }

    // Очистка при размонтировании компонента
    onUnmounted(() => {
      if (map) {
        map.destroy()
      }
    })

    const toggleTheme = () => {
      theme.value = theme.value === 'light' ? 'dark' : 'light'
    }

    const formatAddress = (address) => {
      if (!address) return 'Адрес не указан'
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

      loadingStation.value = true

      try {
        const azsResponse = await api.getFuelPrices(stationNumber.value)

        if (azsResponse.data.need_selection) {
          matchingStations.value = azsResponse.data.azs_list;
          currentScreen.value = 'select_station';
        } else if (azsResponse.data.fuel) {
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
        loadingStation.value = false
      }
    }

    const selectSpecificStation = async (station) => {
      try {
        loadingStation.value = true;

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
          user_id: currentUser.value.id, // Используем ID авторизованного пользователя
          azs_number: parseInt(stationNumber.value),
          azs_id: selectedStation.value.id,
          azs_address: selectedStation.value.address,
          column_number: parseInt(columnNumber.value),
          fuel_type: selectedFuel.value.name,
          fuel_price: parseFloat(fuelPrice),
          volume: isVolume.value ? parseFloat(amount.value) : null,
          amount: !isVolume.value ? parseFloat(amount.value) : null,
        }

        const orderResponse = await api.createOrder(orderData)
        orderId.value = orderResponse.data.id

        const returnUrl = `${window.location.origin}/payment-result`
        const paymentResponse = await api.createPayment(orderId.value, returnUrl)

        paymentUrl.value = paymentResponse.data.payment_url
        transactionId.value = paymentResponse.data.payment_id

        currentScreen.value = 'redirect'

      } catch (error) {
        console.error('Ошибка создания платежа:', error)
        showNotify('Ошибка создания платежа', 'error')
        currentScreen.value = 'payment'
      }
    }

    const redirectToBank = () => {
      if (paymentUrl.value) {
        if (paymentUrl.value.includes('/payment-emulator/')) {
          window.open(paymentUrl.value, '_blank', 'width=600,height=700')
        } else {
          window.open(paymentUrl.value, '_blank')
        }
        currentScreen.value = 'waiting'
        checkOrderStatus()
      }
    }

    const checkOrderStatus = async () => {
      if (!orderId.value) return

      try {
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

        const response = await api.getOrderStatus(orderId.value)
        const status = response.data.status

        if (status !== 'ожидание') {
          orderStatus.value = status
          rejectionReason.value = response.data.rejection_reason
          transactionId.value = response.data.transaction_id
          currentScreen.value = 'result'
        } else {
          setTimeout(checkOrderStatus, 2000)
        }
      } catch (error) {
        console.error('Ошибка проверки статуса:', error)
        setTimeout(checkOrderStatus, 5000)
      }
    }

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
      appTitle,
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
      currentUser,
      showAuth,
      authMode,
      loading,
      loginData,
      userData,
      toggleTheme,
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
      loadingStation,
      handleLogin,
      handleRegister,
      handleLogout,
      selectedStationForMap,
      yandexMap,
      selectStationForMap,
      deselectStation,
      confirmStationSelection
    }
  }
}
</script>

<style scoped>
.card {
  background-color: var(--card-bg);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--border-color);
}

.input-group {
  margin-bottom: 16px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-color);
}

.input-field {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: var(--bg-color);
  color: var(--text-color);
  font-size: 16px;
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
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn.active {
  background-color: var(--primary-color);
  color: white;
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
  background-color: var(--primary-color);
  color: white;
}

.btn.secondary {
  background-color: var(--secondary-color);
  color: var(--text-color);
  border: 1px solid var(--border-color);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.total {
  margin: 20px 0;
  padding: 16px;
  background-color: var(--secondary-color);
  border-radius: 8px;
  text-align: center;
}

.payment-info {
  padding: 16px;
  background-color: var(--secondary-color);
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: center;
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

.loading-indicator {
  text-align: center;
  margin-top: 20px;
  padding: 15px;
  background-color: var(--secondary-color);
  border-radius: 8px;
}

.loading-indicator p {
  margin-bottom: 10px;
  color: var(--text-color);
}

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
  background-color: var(--secondary-color);
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
  color: var(--text-color);
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
  background-color: var(--primary-color);
  color: white;
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
  background-color: var(--secondary-color);
  border-radius: 8px;
  margin-bottom: 20px;
}

.order-summary h3 {
  margin-bottom: 10px;
}

.payment-info {
  padding: 16px;
  background-color: var(--secondary-color);
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
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.station-item:hover {
  background-color: var(--secondary-color);
}

.station-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
}

.station-address {
  margin: 0 0 0.25rem 0;
  font-size: 0.9rem;
  color: var(--text-color);
  opacity: 0.7;
}

.station-region {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.7;
}

.station-arrow {
  font-size: 1.2rem;
  color: var(--text-color);
  opacity: 0.7;
}

.header-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-greeting {
  color: var(--text-color);
  font-size: 14px;
}

.auth-screen {
  max-width: 400px;
  margin: 0 auto;
}

.auth-links {
  margin-top: 1rem;
  text-align: center;
}

.auth-links a {
  color: var(--primary-color);
  text-decoration: none;
}

.auth-links a:hover {
  text-decoration: underline;
}

.station-selection {
  transition: all 0.5s ease;
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
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: var(--card-bg);
}

.station-item:hover {
  background-color: var(--secondary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.station-item.selected {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.station-info h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
}

.station-address {
  margin: 0 0 0.25rem 0;
  font-size: 0.9rem;
  color: var(--text-color);
  opacity: 0.7;
}

.station-region {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-color);
  opacity: 0.7;
}

.station-arrow {
  font-size: 1.2rem;
  color: var(--text-color);
  opacity: 0.7;
}

/* Анимации для выбора АЗС */
.station-expand-enter-active,
.station-expand-leave-active {
  transition: all 0.5s ease;
}

.station-expand-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.station-expand-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Стили для выбранной АЗС с картой */
.selected-station-with-map {
  margin-top: 1rem;
}

.selected-station-card {
  background-color: var(--secondary-color);
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  border: 2px solid var(--primary-color);
}

.station-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.station-header h3 {
  margin: 0;
  color: var(--primary-color);
}

.btn.small {
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
}

/* Контейнер для карты */
.map-container {
  position: relative;
  margin: 1.5rem 0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.yandex-map {
  width: 100%;
  height: 300px;
  border-radius: 12px;
}

.map-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  color: white;
  padding: 1rem;
  text-align: center;
}

.map-overlay p {
  margin: 0;
  font-weight: 500;
}

.confirm-btn {
  width: 100%;
  margin-top: 1rem;
  padding: 1rem;
  font-size: 1.1rem;
  font-weight: 600;
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

  .header-controls {
    position: static;
    margin-top: 10px;
    justify-content: center;
  }

  .user-menu {
    flex-direction: column;
    gap: 5px;
  }

  .station-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }

  .yandex-map {
    height: 250px;
  }

  .selected-station-card {
    padding: 1rem;
  }

}
</style>