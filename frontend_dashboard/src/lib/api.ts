import axios from 'axios';

// Get base URL depending on environment
const getBaseUrl = () => {
    let url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

    // Normalize: Ensure it ends with /api if it's a Vercel URL
    if (url.includes('vercel.app')) {
        if (!url.includes('/api')) {
            url = url.endsWith('/') ? `${url}api` : `${url}/api`;
        }
    }

    // Strip final slash from the base URL itself if present
    if (url.endsWith('/')) {
        url = url.slice(0, -1);
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
        // Systemic fix: Strip trailing slashes from endpoints to avoid 307 redirects (FastAPI)
        // Redirects often break CORS on Vercel.
        if (config.url && config.url.length > 1 && config.url.endsWith('/')) {
            config.url = config.url.slice(0, -1);
        }

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
