<template>
    <div class="orders-table">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>АЗС</th>
                    <th>Колонка</th>
                    <th>Топливо</th>
                    <th>Объем/Сумма</th>
                    <th>Статус</th>
                    <th>Дата</th>
                    <th>Действия</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="order in orders" :key="order.id">
                    <td>{{ order.id }}</td>
                    <td>{{ order.azs_number }}</td>
                    <td>{{ order.column_number }}</td>
                    <td>{{ order.fuel_type }}</td>
                    <td>
                        <span v-if="order.volume">{{ order.volume }} л</span>
                        <span v-else>{{ order.amount }} руб</span>
                    </td>
                    <td>
                        <span :class="['status', order.status]">
                            {{ getStatusText(order.status) }}
                        </span>
                    </td>
                    <td>{{ formatDate(order.created_at) }}</td>
                    <td>
                        <div class="actions">
                            <button v-if="order.status === 'ожидание'" @click="acceptOrder(order.id)"
                                class="btn-accept">
                                Принять
                            </button>
                            <button v-if="order.status === 'ожидание'" @click="rejectOrder(order.id)"
                                class="btn-reject">
                                Отклонить
                            </button>
                            <button @click="showDetails(order)" class="btn-details">
                                Детали
                            </button>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>

        <!-- Модальное окно деталей заявки -->
        <div v-if="selectedOrder" class="modal-overlay" @click="closeModal">
            <div class="modal" @click.stop>
                <div class="modal-header">
                    <h2>Детали заявки #{{ selectedOrder.id }}</h2>
                    <button class="close-btn" @click="closeModal">×</button>
                </div>
                <div class="modal-body">
                    <div class="order-details">
                        <div class="detail-row">
                            <span class="label">АЗС:</span>
                            <span class="value">{{ selectedOrder.azs_number }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Колонка:</span>
                            <span class="value">{{ selectedOrder.column_number }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Топливо:</span>
                            <span class="value">{{ selectedOrder.fuel_type }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Объем:</span>
                            <span class="value">{{ selectedOrder.volume }} л</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Сумма:</span>
                            <span class="value">{{ selectedOrder.amount }} руб</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Статус:</span>
                            <span :class="['value', 'status', selectedOrder.status]">
                                {{ getStatusText(selectedOrder.status) }}
                            </span>
                        </div>
                        <div v-if="selectedOrder.rejection_reason" class="detail-row">
                            <span class="label">Причина отказа:</span>
                            <span class="value">{{ selectedOrder.rejection_reason }}</span>
                        </div>
                        <div class="detail-row" v-if="selectedOrder.cheque_image_url">
                            <span class="label">Чек:</span>
                            <img :src="selectedOrder.cheque_image_url" alt="Чек об оплате" class="cheque-image">
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Модальное окно отказа -->
        <div v-if="showRejectModal" class="modal-overlay" @click="closeRejectModal">
            <div class="modal" @click.stop>
                <div class="modal-header">
                    <h2>Укажите причину отказа</h2>
                    <button class="close-btn" @click="closeRejectModal">×</button>
                </div>
                <div class="modal-body">
                    <textarea v-model="rejectionReason" placeholder="Причина отказа..."></textarea>
                    <div class="modal-actions">
                        <button @click="confirmReject" class="btn-confirm">Подтвердить</button>
                        <button @click="closeRejectModal" class="btn-cancel">Отмена</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref } from 'vue'
import { useOrdersStore } from '../stores/orders'

export default {
    name: 'OrdersTable',
    props: {
        orders: {
            type: Array,
            required: true
        }
    },
    emits: ['status-updated'],
    setup(props, { emit }) {
        const ordersStore = useOrdersStore()
        const selectedOrder = ref(null)
        const showRejectModal = ref(false)
        const rejectionReason = ref('')
        const orderToReject = ref(null)

        const getStatusText = (status) => {
            const statusMap = {
                'ожидание': 'На рассмотрении',
                'принято': 'Принято',
                'отказано': 'Отклонено'
            }
            return statusMap[status] || status
        }

        const formatDate = (dateString) => {
            return new Date(dateString).toLocaleString('ru-RU')
        }

        const acceptOrder = async (orderId) => {
            const result = await ordersStore.updateOrderStatus(orderId, 'принято')
            if (result.success) {
                emit('status-updated')
            }
        }

        const rejectOrder = (orderId) => {
            orderToReject.value = orderId
            showRejectModal.value = true
        }

        const confirmReject = async () => {
            if (!rejectionReason.value.trim()) {
                alert('Укажите причину отказа')
                return
            }

            const result = await ordersStore.updateOrderStatus(
                orderToReject.value,
                'отказано',
                rejectionReason.value
            )

            if (result.success) {
                showRejectModal.value = false
                rejectionReason.value = ''
                orderToReject.value = null
                emit('status-updated')
            }
        }

        const showDetails = (order) => {
            selectedOrder.value = order
        }

        const closeModal = () => {
            selectedOrder.value = null
        }

        const closeRejectModal = () => {
            showRejectModal.value = false
            rejectionReason.value = ''
            orderToReject.value = null
        }

        return {
            selectedOrder,
            showRejectModal,
            rejectionReason,
            getStatusText,
            formatDate,
            acceptOrder,
            rejectOrder,
            confirmReject,
            showDetails,
            closeModal,
            closeRejectModal
        }
    }
}
</script>

<style scoped>
.orders-table {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

th,
td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid #eee;
}

th {
    background-color: #f8f9fa;
    font-weight: 600;
}

.status {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
}

.status.ожидание {
    background-color: #fff3cd;
    color: #856404;
}

.status.принято {
    background-color: #d4edda;
    color: #155724;
}

status.отказано {
    background-color: #f8d7da;
    color: #721c24;
}

.actions {
    display: flex;
    gap: 0.5rem;
}

.actions button {
    padding: 0.25rem 0.5rem;
    border: none;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
}

.btn-accept {
    background-color: #28a745;
    color: white;
}

.btn-reject {
    background-color: #dc3545;
    color: white;
}

.btn-details {
    background-color: #6c757d;
    color: white;
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal {
    background: white;
    border-radius: 8px;
    width: 90%;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #eee;
}

.close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #999;
}

.modal-body {
    padding: 1.5rem;
}

.order-details {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.detail-row {
    display: flex;
}

.detail-row .label {
    font-weight: 600;
    min-width: 120px;
}

.cheque-image {
    max-width: 100%;
    max-height: 300px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

textarea {
    width: 100%;
    min-height: 100px;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    resize: vertical;
}

.modal-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 1rem;
}

.btn-confirm {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.btn-cancel {
    padding: 0.5rem 1rem;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
</style>