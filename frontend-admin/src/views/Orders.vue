<template>
    <div class="orders">
        <div class="header">
            <h1>Управление заявками</h1>
            <button @click="refreshOrders" :disabled="isLoading">
                Обновить
            </button>
        </div>

        <div v-if="isLoading" class="loading">Загрузка...</div>
        <div v-else-if="error" class="error">{{ error }}</div>
        <OrdersTable v-else :orders="orders" @status-updated="handleStatusUpdate" />
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useOrdersStore } from '../stores/orders'
import OrdersTable from '../components/OrdersTable.vue'

export default {
    name: 'OrdersView',
    components: {
        OrdersTable
    },
    setup() {
        const ordersStore = useOrdersStore()
        const isLoading = ref(false)

        onMounted(() => {
            ordersStore.fetchOrders()
        })

        const refreshOrders = async () => {
            isLoading.value = true
            await ordersStore.fetchOrders()
            isLoading.value = false
        }

        const handleStatusUpdate = () => {
            // Можно добавить обработку обновления статуса
            console.log('Статус заявки обновлен')
        }

        return {
            orders: ordersStore.orders,
            isLoading: ordersStore.isLoading,
            error: ordersStore.error,
            refreshOrders,
            handleStatusUpdate
        }
    }
}
</script>

<style scoped>
.orders {
    padding: 2rem;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

button {
    padding: 0.5rem 1rem;
    background-color: #40a7e3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

button:hover:not(:disabled) {
    background-color: #2d92cc;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.loading,
.error {
    text-align: center;
    padding: 2rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.error {
    color: #e74c3c;
}
</style>