<template>
  <div id="app">
    <header class="header" v-if="$route.name !== 'Login'">
      <div class="header-content">
        <h1>Админ-панель АЗС «Татнефть»</h1>
        <nav class="nav">
          <router-link to="/">Дашборд</router-link>
          <router-link to="/orders">Заявки</router-link>
          <router-link to="/settings">Настройки</router-link>
          <div class="notifications-badge" @click="showNotifications = !showNotifications">
            <span class="icon">🔔</span>
            <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
          </div>
          <button @click="logout" class="logout-btn">Выйти</button>
        </nav>
      </div>
    </header>

    <div v-if="showNotifications" class="notifications-overlay" @click="showNotifications = false">
      <div class="notifications-container" @click.stop>
        <NotificationsPanel />
      </div>
    </div>

    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script>
import { useAuthStore } from './stores/auth'
import { useWebSocketStore } from './stores/websocket'
import { useRouter } from 'vue-router'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import NotificationsPanel from './components/NotificationsPanel.vue'

export default {
  name: 'App',
  components: {
    NotificationsPanel
  },
  setup() {
    const authStore = useAuthStore()
    const websocketStore = useWebSocketStore()
    const router = useRouter()
    const showNotifications = ref(false)

    const unreadCount = computed(() => {
      return websocketStore.notifications.filter(n => !n.read).length
    })

    const logout = () => {
      authStore.logout()
      websocketStore.disconnect()
      router.push('/login')
    }

    onMounted(() => {
      // Подключаем WebSocket при загрузке приложения
      if (authStore.isAuthenticated) {
        websocketStore.connect()

        // Периодически отправляем ping для поддержания соединения
        const pingInterval = setInterval(() => {
          websocketStore.sendPing()
        }, 30000)

        // Очищаем интервал при размонтировании
        onUnmounted(() => {
          clearInterval(pingInterval)
          websocketStore.disconnect()
        })
      }
    })

    return {
      logout,
      showNotifications,
      unreadCount
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', sans-serif;
  background-color: #f5f5f5;
  color: #333;
}

.header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  font-size: 1.5rem;
}

.nav {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.nav a:hover,
.nav a.router-link-active {
  background-color: rgba(255, 255, 255, 0.1);
}

.logout-btn {
  background: none;
  border: 1px solid white;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.main {
  min-height: calc(100vh - 80px);
}

.notifications-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
}

.notifications-container {
  width: 400px;
  height: 100vh;
  background: white;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
}

.notifications-badge {
  position: relative;
  cursor: pointer;
  padding: 0.5rem;
  margin-right: 1rem;
}

.notifications-badge .badge {
  position: absolute;
  top: 0;
  right: 0;
  background-color: #e74c3c;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  font-size: 0.7rem;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>