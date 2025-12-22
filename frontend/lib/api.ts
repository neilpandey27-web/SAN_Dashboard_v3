/**
 * API client configuration with JWT authentication
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear tokens and redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');

        // Only redirect if not already on auth page
        if (!window.location.pathname.startsWith('/auth')) {
          window.location.href = '/auth';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),

  signup: (data: {
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    password: string;
    tenant_id: number;
  }) => api.post('/auth/signup', data),

  logout: () => api.post('/auth/logout'),

  me: () => api.get('/auth/me'),

  getTenants: () => api.get('/auth/tenants'),

  changePassword: (old_password: string, new_password: string) =>
    api.post('/auth/change-password', { old_password, new_password }),
};

// Data API
export const dataAPI = {
  getOverview: (reportDate?: string) =>
    api.get('/data/overview', { params: { report_date: reportDate } }),

  // Enhanced dashboard endpoint (v1.4.4)
  getEnhancedOverview: (reportDate?: string, tenant?: string) =>
    api.get('/data/overview/enhanced', {
      params: {
        report_date: reportDate,
        ...(tenant && { tenant })  // 🆕 v6.1.0 - Tenant filtering
      }
    }),

  // 🆕 v6.1.0 - Tenant list for admin users
  getTenantList: () =>
    api.get('/data/tenants/list'),

  getDashboardPools: (reportDate?: string, limit?: number) =>
    api.get('/data/dashboard/pools', { params: { report_date: reportDate, limit } }),

  getDashboardHosts: (reportDate?: string, limit?: number) =>
    api.get('/data/dashboard/hosts', { params: { report_date: reportDate, limit } }),

  getSystems: (params?: {
    report_date?: string;
    search?: string;
    sort_by?: string;
    sort_order?: string;
    page?: number;
    page_size?: number;
    tenant?: string;  // 🆕 v6.1.0 - Tenant filtering
  }) => api.get('/data/systems', { params }),

  getStorageSystems: (params?: {
    report_date?: string;
    search?: string;
    sort_by?: string;
    sort_order?: string;
    page?: number;
    page_size?: number;
    tenant?: string;  // 🆕 v6.1.0 - Tenant filtering
  }) => api.get('/data/systems', { params }),

  getSystemDetail: (systemId: number) =>
    api.get(`/data/systems/${systemId}`),

  getSystemPools: (systemName: string) =>
    api.get(`/data/systems/${systemName}/pools`),

  getPoolVolumes: (poolName: string) =>
    api.get(`/data/pools/${poolName}/volumes`),

  getHistorical: (startDate: string, endDate: string, tenant?: string) =>
    api.get('/data/historical', { 
      params: { 
        start_date: startDate, 
        end_date: endDate,
        ...(tenant && { tenant })  // 🆕 v6.1.0 - Tenant filtering
      } 
    }),

  getReportDates: () => api.get('/data/report-dates'),

  uploadExcel: (file: File, reportDate?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (reportDate) {
      formData.append('report_date', reportDate);
    }
    return api.post('/data/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // 2 minutes for large uploads
    });
  },

  deleteUpload: (uploadId: number) =>
    api.delete(`/data/upload/${uploadId}`),

  getUploadLogs: (params?: { limit?: number }) =>
    api.get('/data/upload-logs', { params }),

  getTables: () => api.get('/data/tables'),

  getTableSchema: (tableName: string) =>
    api.get(`/data/tables/${tableName}/schema`),

  getTableData: (tableName: string, params?: {
    limit?: number;
    offset?: number;
    sort_by?: string;
    sort_order?: string;
    filter_column?: string;
    filter_value?: string;
  }) => api.get(`/data/tables/${tableName}`, { params }),
};

// Alerts API
export const alertsAPI = {
  getAlerts: (params?: { acknowledged?: boolean; level?: string; limit?: number }) =>
    api.get('/alerts/list', { params }),

  getUnacknowledged: () => api.get('/alerts/unacknowledged'),

  getCount: () => api.get('/alerts/count'),

  acknowledge: (alertId: number) => api.post(`/alerts/acknowledge/${alertId}`),

  acknowledgeAll: () => api.post('/alerts/acknowledge-all'),
};

// Users API
export const usersAPI = {
  getUsers: (params?: { status_filter?: string; role_filter?: string }) =>
    api.get('/users/list', { params }),

  getPending: () => api.get('/users/pending'),

  getPendingCount: () => api.get('/users/pending/count'),

  approveUser: (userId: number) => api.post(`/users/approve/${userId}`),

  rejectUser: (userId: number) => api.post(`/users/reject/${userId}`),

  editUser: (userId: number, data: any) => api.put(`/users/edit/${userId}`, data),

  deleteUser: (userId: number) => api.delete(`/users/${userId}`),

  deactivateUser: (userId: number) => api.put(`/users/deactivate/${userId}`),

  activateUser: (userId: number) => api.put(`/users/activate/${userId}`),

  getActivityLogs: (params?: { user_id?: number; limit?: number }) =>
    api.get('/users/activity-logs', { params }),

  getUploadLogs: (params?: { limit?: number }) =>
    api.get('/users/upload-logs', { params }),

  getTenants: () => api.get('/users/tenants'),

  createTenant: (name: string, description?: string) =>
    api.post('/users/tenants', null, { params: { name, description } }),

  updateTenant: (tenantId: number, name: string, description?: string) =>
    api.put(`/users/tenants/${tenantId}`, null, { params: { name, description } }),
};

// Mappings API
export const mappingsAPI = {
  getTenantPoolMappings: (tenantId?: number) =>
    api.get('/mappings/tenant-pools', { params: { tenant_id: tenantId } }),

  createTenantPoolMapping: (data: { tenant_id: number; pool_name: string; storage_system?: string }) =>
    api.post('/mappings/tenant-pools', data),

  // 🆕 NEW: CSV Upload for Tenant-Pool Mappings
  uploadTenantPoolCSV: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/mappings/tenant-pools/upload-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  deleteTenantPoolMapping: (mappingId: number) =>
    api.delete(`/mappings/tenant-pools/${mappingId}`),

  getAvailablePools: () => api.get('/mappings/available-pools'),

  getHostTenantMappings: (tenantId?: number) =>
    api.get('/mappings/host-tenants', { params: { tenant_id: tenantId } }),

  createHostTenantMapping: (data: { tenant_id: number; host_name: string }) =>
    api.post('/mappings/host-tenants', data),

  uploadHostTenantCSV: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/mappings/host-tenants/upload-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  deleteHostTenantMapping: (mappingId: number) =>
    api.delete(`/mappings/host-tenants/${mappingId}`),

  getMdiskSystemMappings: () => api.get('/mappings/mdisk-systems'),

  createMdiskSystemMapping: (data: { mdisk_name: string; system_name: string }) =>
    api.post('/mappings/mdisk-systems', data),

  deleteMdiskSystemMapping: (mappingId: number) =>
    api.delete(`/mappings/mdisk-systems/${mappingId}`),
};

export default api;
