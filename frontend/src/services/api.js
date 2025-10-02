import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const getToken = () => {
    return localStorage.getItem('user_token');
};

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Интерцептор для добавления токена к запросам
apiClient.interceptors.request.use(
    (config) => {
        const token = getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Интерцептор для обработки ошибок авторизации
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Токен истек или невалиден
            localStorage.removeItem('user_token');
            localStorage.removeItem('user_data');
            window.location.reload();
        }
        return Promise.reject(error);
    }
);


export default {
    getNearbyAzs(lat, lon) {
        return apiClient.get(`/azs/nearby?lat=${lat}&lon=${lon}`);
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

    // Общий метод для GET запросов
    get(url) {
        return apiClient.get(url);
    },

    register(userData) {
        return apiClient.post('/auth/register', userData);
    },

    login(loginData) {
        return apiClient.post('/auth/login', loginData);
    },

    logout() {
        return apiClient.post('/auth/logout', {}, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
    },

    getCurrentUser() {
        return apiClient.get('/auth/me');
    }
};