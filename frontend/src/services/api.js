import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    getFuelPrices(azsNumber) {
        return apiClient.get(`/azs/${azsNumber}`);
    },

    getSpecificAzs(azsNumber, azsId) {
        return apiClient.get(`/azs/${azsNumber}/${azsId}`);
    },

    createOrder(orderData) {
        return apiClient.post('/orders/', orderData); 
    },

    createPayment(orderId, returnUrl) {
        return apiClient.post(`/orders/${orderId}/payment`, {
            return_url: returnUrl
        });
    },

    getOrderStatus(orderId) {
        return apiClient.get(`/orders/${orderId}`);
    },

    getSettings() {
        return apiClient.get('/settings/');
    },
};
