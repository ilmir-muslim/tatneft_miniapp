<template>
    <div class="dashboard">
        <h1>Панель управления</h1>
        <div class="stats">
            <div class="stat-card">
                <h3>Всего заявок</h3>
                <p class="count">{{ orders.length }}</p>
            </div>
            <div class="stat-card">
                <h3>На ожидании</h3>
                <p class="count pending">{{ pendingOrders.length }}</p>
            </div>
            <div class="stat-card">
                <h3>Принято</h3>
                <p class="count accepted">{{ acceptedOrders.length }}</p>
            </div>
            <div class="stat-card">
                <h3>Отклонено</h3>
                <p class="count rejected">{{ rejectedOrders.length }}</p>
            </div>
        </div>

        <div class="recent-orders">
            <h2>Последние заявки</h2>
            <OrdersTable :orders="recentOrders" />
            <router-link to="/orders" class="view-all">Все заявки →</router-link>
        </div>
    </div>
</template>

<script>
import { computed } from 'vue'
import { useOrdersStore } from '../stores/orders'
import OrdersTable from '../components/OrdersTable.vue'

export default {
    name: 'DashboardView',
    components: {
        OrdersTable
    },
    setup() {
        const ordersStore = useOrdersStore()

        // Загружаем заявки при монтировании компонента
        ordersStore.fetchOrders()

        const pendingOrders = computed(() =>
            ordersStore.orders.filter(order => order.status === 'ожидание')
        )

        const acceptedOrders = computed(() =>
            ordersStore.orders.filter(order => order.status === 'принято')
        )

        const rejectedOrders = computed(() =>
            ordersStore.orders.filter(order => order.status === 'отказано')
        )

        const recentOrders = computed(() =>
            [...ordersStore.orders]
                .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                .slice(0, 5)
        )

        return {
            orders: ordersStore.orders,
            pendingOrders,
            acceptedOrders,
            rejectedOrders,
            recentOrders
        }
    }
}
</script>

<style scoped>
.dashboard {
    padding: 2rem;
}

.stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.stat-card h3 {
    margin: 0 0 0.5rem 0;
    color: #666;
    font-size: 0.9rem;
    text-transform: uppercase;
}

.count {
    font-size: 2rem;
    font-weight: bold;
    margin: 0;
}

.count.pending {
    color: #f39c12;
}

.count.accepted {
    color: #27ae60;
}

.count.rejected {
    color: #e74c3c;
}

.recent-orders {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.view-all {
    display: block;
    text-align: right;
    margin-top: 1rem;
    color: #40a7e3;
    text-decoration: none;
}

.view-all:hover {
    text-decoration: underline;
}
</style>