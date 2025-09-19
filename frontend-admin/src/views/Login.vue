<template>
    <div class="login-container">
        <div class="login-form">
            <h2>Вход в админ-панель</h2>
            <form @submit.prevent="handleSubmit">
                <div class="form-group">
                    <label for="username">Логин:</label>
                    <input id="username" v-model="username" type="text" required autocomplete="username">
                </div>
                <div class="form-group">
                    <label for="password">Пароль:</label>
                    <input id="password" v-model="password" type="password" required autocomplete="current-password">
                </div>
                <button type="submit" :disabled="isLoading">
                    {{ isLoading ? 'Вход...' : 'Войти' }}
                </button>
                <p v-if="error" class="error">{{ error }}</p>
            </form>
        </div>
    </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

export default {
    name: 'LoginView',
    setup() {
        const username = ref('')
        const password = ref('')
        const isLoading = ref(false)
        const error = ref('')

        const authStore = useAuthStore()
        const router = useRouter()

        const handleSubmit = async () => {
            isLoading.value = true
            error.value = ''

            const result = await authStore.login({
                username: username.value,
                password: password.value
            })

            if (result.success) {
                router.push('/')
            } else {
                error.value = result.error
            }

            isLoading.value = false
        }

        return {
            username,
            password,
            isLoading,
            error,
            handleSubmit
        }
    }
}
</script>

<style scoped>
.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background-color: #f5f5f5;
}

.login-form {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
}

h2 {
    text-align: center;
    margin-bottom: 1.5rem;
    color: #333;
}

.form-group {
    margin-bottom: 1rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

button {
    width: 100%;
    padding: 0.75rem;
    background-color: #40a7e3;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
}

button:hover:not(:disabled) {
    background-color: #2d92cc;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.error {
    color: #e74c3c;
    margin-top: 1rem;
    text-align: center;
}
</style>