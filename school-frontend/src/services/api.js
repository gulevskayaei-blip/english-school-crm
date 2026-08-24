import axios from 'axios';

const api = axios.create({
    baseURL: '/api/',
});

// Получаем CSRF-токен из куки
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

api.interceptors.request.use(config => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Token ${token}`;
    }
    // Добавляем CSRF-токен
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
}, error => Promise.reject(error));

api.interceptors.response.use(response => response, error => {
    if (error.response && error.response.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
    }
    return Promise.reject(error);
});

export default api;

export const authAPI = {
    login: (credentials) => api.post('auth/login/', credentials),
    getProfile: () => api.get('users/me/'),
};
