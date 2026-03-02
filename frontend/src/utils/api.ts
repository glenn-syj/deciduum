import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add API key to requests
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('apiKey') || import.meta.env.VITE_API_KEY || '';
  // Auto-save if loaded from env
  if (!localStorage.getItem('apiKey') && import.meta.env.VITE_API_KEY) {
    localStorage.setItem('apiKey', import.meta.env.VITE_API_KEY);
  }
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

// Types
export interface Decision {
  id: string;
  title: string;
  date: string;
  status: 'completed' | 'ongoing' | 'archived';
  review_at: string | null;
  direction_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DecisionLog {
  id: string;
  decision_id: string;
  type: 'note' | 'reflection' | 'state_change';
  content: string;
  source: 'human' | 'system';
  created_at: string;
}

export interface Memo {
  id: string;
  content: string;
  date: string;
  linked_decision_id: string | null;
  linked_direction_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Direction {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export type TaskStatus = 'pending' | 'in_progress' | 'completed';

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  due_date: string | null;
  notes: string | null;
  decision_id: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

export interface TodayResponse {
  date: string;
  ongoing_decisions: Decision[];
  todays_decisions: Decision[];
  todays_memos: Memo[];
}

// API functions
export const decisionsApi = {
  list: (params?: any) => api.get<PaginatedResponse<Decision>>('/decisions', { params }),
  get: (id: string) => api.get<{ data: Decision }>(`/decisions/${id}`),
  create: (data: Partial<Decision>) => api.post<{ data: Decision }>('/decisions', data),
  update: (id: string, data: Partial<Decision>) => api.patch<{ data: Decision }>(`/decisions/${id}`, data),
  delete: (id: string) => api.delete(`/decisions/${id}`),
  listLogs: (decisionId: string, params?: any) => api.get<PaginatedResponse<DecisionLog>>(`/decisions/${decisionId}/logs`, { params }),
  createLog: (decisionId: string, data: Partial<DecisionLog>) => api.post<{ data: DecisionLog }>(`/decisions/${decisionId}/logs`, data),
};

export const memosApi = {
  list: (params?: any) => api.get<PaginatedResponse<Memo>>('/memos', { params }),
  get: (id: string) => api.get<{ data: Memo }>(`/memos/${id}`),
  create: (data: Partial<Memo>) => api.post<{ data: Memo }>('/memos', data),
  update: (id: string, data: Partial<Memo>) => api.patch<{ data: Memo }>(`/memos/${id}`, data),
  delete: (id: string) => api.delete(`/memos/${id}`),
  listByDecision: (decisionId: string, params?: { page?: number; limit?: number }) =>
    api.get<PaginatedResponse<Memo>>('/memos', { params: { ...params, linked_decision_id: decisionId } }),
};

export const directionsApi = {
  list: (params?: any) => api.get<PaginatedResponse<Direction>>('/directions', { params }),
  get: (id: string) => api.get<{ data: Direction }>(`/directions/${id}`),
  getDetails: (id: string, params?: any) => api.get(`/directions/${id}/details`, { params }),
  create: (data: Partial<Direction>) => api.post<{ data: Direction }>('/directions', data),
  update: (id: string, data: Partial<Direction>) => api.patch<{ data: Direction }>(`/directions/${id}`, data),
  delete: (id: string) => api.delete(`/directions/${id}`),
};

export const todayApi = {
  get: (date?: string) => api.get<TodayResponse>('/today', { params: { date } }),
};

export const tasksApi = {
  list: (params?: { decision_id?: string; status?: string; page?: number; limit?: number }) =>
    api.get<PaginatedResponse<Task>>('/tasks', { params }),
  get: (id: string) => api.get<{ data: Task }>(`/tasks/${id}`),
  create: (data: { title: string; status?: string; due_date?: string | null; notes?: string | null; decision_id: string }) =>
    api.post<{ data: Task }>('/tasks', data),
  update: (id: string, data: Partial<Task>) => api.patch<{ data: Task }>(`/tasks/${id}`, data),
  delete: (id: string) => api.delete(`/tasks/${id}`),
  listByDecision: (decisionId: string, params?: { status?: string; page?: number; limit?: number }) =>
    api.get<PaginatedResponse<Task>>(`/decisions/${decisionId}/tasks`, { params }),
  createForDecision: (decisionId: string, data: { title: string; status?: string; due_date?: string | null; notes?: string | null }) =>
    api.post<{ data: Task }>(`/decisions/${decisionId}/tasks`, data),
};
