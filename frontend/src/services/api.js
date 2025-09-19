// frontend/src/services/api.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    // Получить цены на топливо для АЗС
    getFuelPrices(azsNumber) {
        return apiClient.get(`/azs/${azsNumber}`);
    },

    // Создать новый заказ
    createOrder(orderData) {
        const formData = new FormData();
        Object.keys(orderData).forEach(key => {
            if (orderData[key] !== undefined && orderData[key] !== null) {
                formData.append(key, orderData[key]);
            }
        });

        return apiClient.post('/orders/', formData);
    },

    // Получить статус заказа
    getOrderStatus(orderId) {
        return apiClient.get(`/orders/${orderId}`);
    },

    // Получить настройки (инструкции по оплате)
    getSettings() {
        return apiClient.get('/settings/');
    },

};