<template>
    <div class="login-form">
        <div class="card">
            <h2>Вход в систему</h2>

            <form @submit.prevent="handleLogin">
                <div class="input-group">
                    <label>Логин, email или телефон:</label>
                    <input v-model="loginData.login" type="text" required class="input-field">
                </div>

                <div class="input-group">
                    <label>Пароль:</label>
                    <input v-model="loginData.password" type="password" required class="input-field">
                </div>

                <button type="submit" class="btn primary" :disabled="loading">
                    <span v-if="loading" class="button-loading">
                        <span class="mini-spinner"></span>
                        Вход...
                    </span>
                    <span v-else>Войти</span>
                </button>
            </form>

            <div class="auth-links">
                <p>Нет аккаунта? <a href="#" @click="switchToRegister">Зарегистрироваться</a></p>
            </div>
        </div>
    </div>
</template>

<script>
import { ref } from 'vue'
import api from '../services/api'

export default {
    name: 'LoginForm',
    emits: ['switch-to-register', 'login-success'],
    setup(props, { emit }) {
        const loginData = ref({
            login: '',
            password: ''
        })
        const loading = ref(false)

        const handleLogin = async () => {
            if (!loginData.value.login || !loginData.value.password) {
                alert('Заполните все поля')
                return
            }

            loading.value = true

            try {
                const response = await api.login(loginData.value)

                // Сохраняем токен и данные пользователя
                localStorage.setItem('user_token', response.data.access_token)
                localStorage.setItem('user_data', JSON.stringify(response.data.user))

                emit('login-success', response.data.user)
            } catch (error) {
                console.error('Login error:', error)
                alert(error.response?.data?.detail || 'Ошибка входа')
            } finally {
                loading.value = false
            }
        }

        const switchToRegister = () => {
            emit('switch-to-register')
        }

        return {
            loginData,
            loading,
            handleLogin,
            switchToRegister
        }
    }
}
</script>

<style scoped>
.auth-links {
    margin-top: 1rem;
    text-align: center;
}

.auth-links a {
    color: var(--primary-color);
    text-decoration: none;
}

.auth-links a:hover {
    text-decoration: underline;
}
</style>