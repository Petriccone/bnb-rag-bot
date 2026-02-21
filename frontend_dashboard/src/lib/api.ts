import axios from 'axios';

// Get base URL depending on environment
const getBaseUrl = () => {
    let url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    // Ensure the URL ends with /api if it's a vercel URL
    if (url.includes('vercel.app') && !url.endsWith('/api')) {
        url = url.endsWith('/') ? `${url}api` : `${url}/api`;
        return url;
    }
    return url;
};

export const apiClient = axios.create({
    baseURL: getBaseUrl(),
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to inject the token
apiClient.interceptors.request.use(
    (config) => {
        // If running in browser, get token from localStorage
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('access_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            // Also inject tenant_id if available to help backend routers
            const tenantId = localStorage.getItem('tenant_id');
            if (tenantId && !config.headers['x-tenant-id']) {
                config.headers['x-tenant-id'] = tenantId;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor to handle token expiration/refresh later
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // If we are not already on the login page, redirect
            if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
                localStorage.removeItem('access_token');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);
