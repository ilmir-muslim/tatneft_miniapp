<template>
    <div class="register-form">
        <div class="card">
            <h2>Регистрация</h2>

            <form @submit.prevent="handleRegister">
                <div class="input-group">
                    <label>Имя пользователя *:</label>
                    <input v-model="userData.username" type="text" required class="input-field">
                </div>

                <div class="input-group">
                    <label>Телефон:</label>
                    <input v-model="userData.phone" type="tel" class="input-field" placeholder="+7 XXX XXX XX XX">
                </div>

                <div class="input-group">
                    <label>Email:</label>
                    <input v-model="userData.email" type="email" class="input-field">
                </div>

                <div class="input-group">
                    <label>Имя:</label>
                    <input v-model="userData.first_name" type="text" class="input-field">
                </div>

                <div class="input-group">
                    <label>Фамилия:</label>
                    <input v-model="userData.last_name" type="text" class="input-field">
                </div>

                <div class="input-group">
                    <label>Пароль *:</label>
                    <input v-model="userData.password" type="password" required class="input-field">
                </div>

                <button type="submit" class="btn primary" :disabled="loading">
                    <span v-if="loading" class="button-loading">
                        <span class="mini-spinner"></span>
                        Регистрация...
                    </span>
                    <span v-else>Зарегистрироваться</span>
                </button>
            </form>

            <div class="auth-links">
                <p>Уже есть аккаунт? <a href="#" @click="switchToLogin">Войти</a></p>
            </div>
        </div>
    </div>
</template>

<script>
import { ref } from 'vue'
import api from '../services/api'

export default {
    name: 'RegisterForm',
    emits: ['switch-to-login', 'register-success'],
    setup(props, { emit }) {
        const userData = ref({
            username: '',
            phone: '',
            email: '',
            first_name: '',
            last_name: '',
            password: ''
        })
        const loading = ref(false)

        const handleRegister = async () => {
            if (!userData.value.username || !userData.value.password) {
                alert('Заполните обязательные поля (имя пользователя и пароль)')
                return
            }

            loading.value = true

            try {
                const response = await api.register(userData.value)
                emit('register-success', response.data)

                // Автоматически входим после регистрации
                const loginResponse = await api.login({
                    login: userData.value.username,
                    password: userData.value.password
                })

                localStorage.setItem('user_token', loginResponse.data.access_token)
                localStorage.setItem('user_data', JSON.stringify(loginResponse.data.user))

                emit('switch-to-login')
            } catch (error) {
                console.error('Registration error:', error)
                alert(error.response?.data?.detail || 'Ошибка регистрации')
            } finally {
                loading.value = false
            }
        }

        const switchToLogin = () => {
            emit('switch-to-login')
        }

        return {
            userData,
            loading,
            handleRegister,
            switchToLogin
        }
    }
}
</script>