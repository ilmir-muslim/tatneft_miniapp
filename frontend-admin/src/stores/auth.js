import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
    const isAuthenticated = ref(false)
    const user = ref(null)
    const token = ref(localStorage.getItem('admin_token'))

    if (token.value) {
        isAuthenticated.value = true
        // Можно добавить проверку валидности токена
    }

    const login = async (credentials) => {
        try {
            const formData = new URLSearchParams()
            formData.append('username', credentials.username)
            formData.append('password', credentials.password)

            const response = await api.post('/admin/login', formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })

            const { access_token } = response.data
            localStorage.setItem('admin_token', access_token)
            token.value = access_token
            isAuthenticated.value = true
            user.value = { username: credentials.username }
            return { success: true }
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || 'Ошибка сервера'
            }
        }
    }
    
    const logout = () => {
        localStorage.removeItem('admin_token')
        isAuthenticated.value = false
        user.value = null
        token.value = null
    }

    return {
        isAuthenticated,
        user,
        token,
        login,
        logout
    }
})