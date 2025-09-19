import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWebSocketStore = defineStore('websocket', () => {
    const socket = ref(null)
    const isConnected = ref(false)
    const notifications = ref([])

    const connect = () => {
        if (socket.value) return

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = import.meta.env.VITE_WS_URL || `${protocol}//localhost:8000/admin/ws`

        socket.value = new WebSocket(wsUrl)

        socket.value.onopen = () => {
            console.log('WebSocket connected')
            isConnected.value = true
        }

        socket.value.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data)
                handleWebSocketMessage(message)
            } catch (error) {
                console.error('Error parsing WebSocket message:', error)
            }
        }

        socket.value.onclose = () => {
            console.log('WebSocket disconnected')
            isConnected.value = false
            socket.value = null

            // Попытка переподключения через 5 секунд
            setTimeout(() => {
                if (!isConnected.value) {
                    connect()
                }
            }, 5000)
        }

        socket.value.onerror = (error) => {
            console.error('WebSocket error:', error)
        }
    }

    const disconnect = () => {
        if (socket.value) {
            socket.value.close()
            socket.value = null
        }
        isConnected.value = false
    }

    const handleWebSocketMessage = (message) => {
        switch (message.type) {
            case 'new_order':
                addNotification('Новый заказ', `Поступил новый заказ #${message.data.id}`)
                // Здесь можно добавить логику для обновления списка заказов
                break
            case 'order_update':
                addNotification('Обновление заказа', `Статус заказа #${message.data.order_id} изменен на "${message.data.status}"`)
                // Здесь можно добавить логику для обновления статуса заказа
                break
            case 'pong':
                // Ответ на ping, ничего не делаем
                break
            default:
                console.log('Unknown message type:', message.type)
        }
    }

    const addNotification = (title, message) => {
        notifications.value.unshift({
            id: Date.now(),
            title,
            message,
            timestamp: new Date(),
            read: false
        })

        // Ограничиваем количество уведомлений до 50
        if (notifications.value.length > 50) {
            notifications.value = notifications.value.slice(0, 50)
        }
    }

    const markAsRead = (id) => {
        const notification = notifications.value.find(n => n.id === id)
        if (notification) {
            notification.read = true
        }
    }

    const markAllAsRead = () => {
        notifications.value.forEach(notification => {
            notification.read = true
        })
    }

    const clearNotifications = () => {
        notifications.value = []
    }

    const sendPing = () => {
        if (socket.value && isConnected.value) {
            socket.value.send(JSON.stringify({ type: 'ping' }))
        }
    }

    return {
        socket,
        isConnected,
        notifications,
        connect,
        disconnect,
        addNotification,
        markAsRead,
        markAllAsRead,
        clearNotifications,
        sendPing
    }
})