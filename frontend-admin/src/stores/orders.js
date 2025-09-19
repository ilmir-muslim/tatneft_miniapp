import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useOrdersStore = defineStore('orders', () => {
    const orders = ref([])
    const isLoading = ref(false)
    const error = ref(null)

    const fetchOrders = async () => {
        isLoading.value = true
        error.value = null
        try {
            const response = await api.get('/admin/orders/')
            orders.value = response.data
        } catch (err) {
            error.value = 'Не удалось загрузить заявки'
            console.error('Error fetching orders:', err)
        } finally {
            isLoading.value = false
        }
    }

    const updateOrderStatus = async (orderId, status, reason = null) => {
        try {
            await api.patch(`/admin/orders/${orderId}`, {
                status,
                rejection_reason: reason
            })
            return { success: true }
        } catch (err) {
            console.error('Error updating order:', err)
            return { success: false, error: 'Не удалось обновить статус заявки' }
        }
    }
    
    return {
        orders,
        isLoading,
        error,
        fetchOrders,
        updateOrderStatus
    }
})