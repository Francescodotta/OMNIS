import axios from 'axios';
const apiUrL = 'http://127.0.0.1:5004/'; // Cambia l'URL in base al tuo ambiente

const api = axios.create({
    baseURL: apiUrL,
    });

    api.interceptors.request.use(async (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      });
      
      api.interceptors.response.use(
        (response) => response,
        async (error) => {
          const originalRequest = error.config;
          if (error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const refreshToken = localStorage.getItem('refresh_token');
            try {
              const { data } = await axios.post(apiUrL+'api/refresh', { refresh_token: refreshToken });
              localStorage.setItem('access_token', data.access_token);
              api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
              return api(originalRequest);
            } catch (refreshError) {
              console.error('Refresh token error:', refreshError);
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/'; // Reindirizza l'utente alla pagina di login
            }
          }
          return Promise.reject(error);
    }
);
      
export default api;