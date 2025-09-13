<template>
    <div class="user-card">
        <h3>User Information</h3>
        <div class="user-info">
            <div class="avatar" v-if="user.photo_url">
                <img :src="user.photo_url" alt="User avatar" />
            </div>
            <div class="details">
                <p><strong>Name:</strong> {{ user.first_name }} {{ user.last_name || '' }}</p>
                <p v-if="user.username"><strong>Username:</strong> @{{ user.username }}</p>
                <p v-if="user.language_code"><strong>Language:</strong> {{ user.language_code }}</p>
                <p v-if="user.is_premium"><span class="premium-badge">Premium User</span></p>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'UserCard',
    props: {
        user: {
            type: Object,
            required: true
        }
    }
}
</script>

<style scoped>
.user-card {
    margin: 20px 0;
    padding: 16px;
    background-color: var(--secondary-color);
    border-radius: 10px;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 15px;
}

.avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    overflow: hidden;
}

.avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.details {
    flex: 1;
}

.premium-badge {
    display: inline-block;
    background-color: gold;
    color: black;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 12px;
    font-weight: bold;
}
</style>