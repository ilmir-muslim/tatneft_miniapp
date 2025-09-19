<template>
    <div class="settings">
        <h1>Настройки системы</h1>

        <div class="settings-form">
            <div class="form-section">
                <h2>Настройки скидок</h2>
                <div class="form-group">
                    <label for="discountType">Тип скидки:</label>
                    <select id="discountType" v-model="settings.discount_type">
                        <option value="percent">Процентная</option>
                        <option value="fixed">Фиксированная</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="discountValue">Значение скидки:</label>
                    <input id="discountValue" v-model="settings.discount_value" type="number" step="0.01" min="0">
                </div>
            </div>

            <div class="form-section">
                <h2>Инструкция по оплате</h2>
                <div class="form-group">
                    <label for="paymentInstructions">Текст инструкции:</label>
                    <textarea id="paymentInstructions" v-model="settings.payment_instructions" rows="6"></textarea>
                </div>
            </div>

            <button @click="saveSettings" :disabled="isSaving">
                {{ isSaving ? 'Сохранение...' : 'Сохранить настройки' }}
            </button>
            <p v-if="saveMessage" class="save-message">{{ saveMessage }}</p>
        </div>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
    name: 'SettingsView',
    setup() {
        const settings = ref({
            discount_type: 'percent',
            discount_value: 5,
            payment_instructions: 'Оплатите заказ по реквизитам:\n- Номер карты: 0000 0000 0000 0000\n- Телефон: +7 000 000-00-00'
        })

        const isSaving = ref(false)
        const saveMessage = ref('')

        // Загрузка настроек с сервера
        onMounted(async () => {
            try {
                const response = await api.get('/admin/settings/')
                settings.value = response.data
            } catch (error) {
                console.error('Ошибка загрузки настроек:', error)
            }
        })

        const saveSettings = async () => {
            isSaving.value = true
            try {
                await api.put('/admin/settings/', settings.value)
                saveMessage.value = 'Настройки успешно сохранены!'
            } catch (error) {
                saveMessage.value = 'Ошибка при сохранении настроек'
            } finally {
                isSaving.value = false
            }
        }
        
        return {
            settings,
            isSaving,
            saveMessage,
            saveSettings
        }
    }
}
</script>

<style scoped>
.settings {
    padding: 2rem;
}

.settings-form {
    max-width: 600px;
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-section {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #eee;
}

.form-section:last-child {
    border-bottom: none;
}

h2 {
    margin-top: 0;
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

select,
input,
textarea {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

textarea {
    resize: vertical;
    min-height: 120px;
}

button {
    padding: 0.75rem 1.5rem;
    background-color: #27ae60;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
}

button:hover:not(:disabled) {
    background-color: #219653;
}

button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.save-message {
    margin-top: 1rem;
    padding: 0.5rem;
    border-radius: 4px;
    text-align: center;
}
</style>