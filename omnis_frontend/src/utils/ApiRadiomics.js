import axios from 'axios';
const apiUrl = 'http://localhost:5005/';

const api = axios.create({
    baseURL: apiUrl,
})

api.interceptors.request.use(async (config)=>{
    const token = localStorage.getItem('access_token');
    if (token){
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response, 
    async(error) => {
        const originalRequest = error.config;
        if (error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const refreshToken = localStorage.getItem('refresh_token');
            try{
                const{data}=await axios.post(apiUrl + 'api/refresh', {refreshToken:refreshToken})
                localStorage.setItem('access_token', data.access_token);
                api.defaults.headers.common['Authorization'] `Bearer ${data.access_token}`;
                return api(originalRequest);
            } catch (refreshError) {
                console.error('Remove token error: ', refreshError);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                // send the user to the login page
                window.location.href = '/';
            }
        }
        return Promise.reject(error);
    }
);

export default api