<template>
    <div class="notifications-panel">
        <div class="notifications-header">
            <h3>Уведомления</h3>
            <div class="header-actions">
                <button @click="markAllAsRead" :disabled="unreadCount === 0">
                    Отметить все как прочитанные
                </button>
                <button @click="clearNotifications" :disabled="notifications.length === 0">
                    Очистить
                </button>
            </div>
        </div>

        <div class="notifications-list">
            <div v-if="notifications.length === 0" class="empty-state">
                Нет уведомлений
            </div>

            <div v-for="notification in notifications" :key="notification.id"
                :class="['notification-item', { unread: !notification.read }]" @click="markAsRead(notification.id)">
                <div class="notification-content">
                    <div class="notification-title">{{ notification.title }}</div>
                    <div class="notification-message">{{ notification.message }}</div>
                    <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
                </div>
                <div v-if="!notification.read" class="unread-indicator"></div>
            </div>
        </div>

        <div class="notifications-footer">
            <div class="connection-status" :class="{ connected: isConnected }">
                {{ isConnected ? 'Подключено' : 'Отключено' }}
            </div>
        </div>
    </div>
</template>

<script>
import { useWebSocketStore } from '../stores/websocket'
import { computed } from 'vue'

export default {
    name: 'NotificationsPanel',
    setup() {
        const websocketStore = useWebSocketStore()

        const unreadCount = computed(() => {
            return websocketStore.notifications.filter(n => !n.read).length
        })

        const formatTime = (timestamp) => {
            const date = new Date(timestamp)
            return date.toLocaleTimeString('ru-RU')
        }

        return {
            notifications: websocketStore.notifications,
            isConnected: websocketStore.isConnected,
            unreadCount,
            markAsRead: websocketStore.markAsRead,
            markAllAsRead: websocketStore.markAllAsRead,
            clearNotifications: websocketStore.clearNotifications,
            formatTime
        }
    }
}
</script>

<style scoped>
.notifications-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.notifications-header {
    padding: 1rem;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.notifications-header h3 {
    margin: 0;
    font-size: 1.1rem;
}

.header-actions {
    display: flex;
    gap: 0.5rem;
}

.header-actions button {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    cursor: pointer;
}

.header-actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.notifications-list {
    flex: 1;
    overflow-y: auto;
    max-height: 400px;
}

.empty-state {
    padding: 2rem;
    text-align: center;
    color: #999;
}

.notification-item {
    display: flex;
    padding: 1rem;
    border-bottom: 1px solid #f0f0f0;
    cursor: pointer;
    transition: background-color 0.2s;
}

.notification-item:hover {
    background-color: #f9f9f9;
}

.notification-item.unread {
    background-color: #f0f7ff;
}

.notification-content {
    flex: 1;
}

.notification-title {
    font-weight: 600;
    margin-bottom: 0.25rem;
}

.notification-message {
    color: #666;
    margin-bottom: 0.5rem;
}

.notification-time {
    font-size: 0.8rem;
    color: #999;
}

.unread-indicator {
    width: 8px;
    height: 8px;
    background-color: #40a7e3;
    border-radius: 50%;
    margin-left: 0.5rem;
    align-self: center;
}

.notifications-footer {
    padding: 0.5rem 1rem;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
}

.connection-status {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
}

.connection-status.connected {
    background-color: #d4edda;
    color: #155724;
}

.connection-status:not(.connected) {
    background-color: #f8d7da;
    color: #721c24;
}
</style>