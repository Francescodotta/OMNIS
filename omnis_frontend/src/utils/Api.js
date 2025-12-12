import axios from 'axios';
const apiUrL = process.env.REACT_APP_AUTH_API_URL;


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
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        clearTokens();
        window.location.href = '/';
        return Promise.reject(error);
      }
      try {
        const { data } = await axios.post(
          apiUrL + 'api/token/refresh',
          {},
          {
            headers: {
              Authorization: `Bearer ${refreshToken}`,
            },
          }
        );
        localStorage.setItem('access_token', data.access_token);
        api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        console.error('Refresh token error:', refreshError);
        clearTokens();
        window.location.href = '/';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

// Funzione per pulire tutti i token
const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  delete api.defaults.headers.common['Authorization'];
};

// Funzione per gestire il logout
export const logout = async () => {
  console.log("=== LOGOUT STARTED ===");
  
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      console.log("Calling /api/logout with refresh token...");
      const response = await axios.post(
        apiUrL + 'api/logout',
        {},
        {
          headers: {
            Authorization: `Bearer ${refreshToken}`,
          },
        }
      );
      console.log("Logout response:", response.data);
    }
  } catch (error) {
    console.error('Logout error:', error.response?.data || error.message);
  } finally {
    // Pulisci TUTTO
    clearTokens();
    console.log("=== LOGOUT COMPLETED ===");
    
    // Forza reload completo della pagina
    window.location.href = '/';
  }
};

export default api;