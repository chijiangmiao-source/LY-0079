import api from './client';
import type { User, UserListItem, UserRole } from '$lib/types';

export interface LoginData {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const authApi = {
  login: (data: LoginData) => api.post<TokenResponse>('/auth/login', data).then((r) => r.data),
  register: (data: any) => api.post<User>('/auth/register', data).then((r) => r.data),
  me: () => api.get<User>('/auth/me').then((r) => r.data),
};

export interface UserListParams {
  role?: UserRole;
  skip?: number;
  limit?: number;
}

export const usersApi = {
  list: (params?: UserListParams) =>
    api
      .get<UserListItem[]>('/users/', { params: params && Object.keys(params).length ? params : undefined })
      .then((r) => r.data),
  listRetouchers: () => api.get<UserListItem[]>('/users/retouchers').then((r) => r.data),
  listPhotographers: () => api.get<UserListItem[]>('/users/photographers').then((r) => r.data),
  listCustomers: () => api.get<UserListItem[]>('/users/customers').then((r) => r.data),
  get: (id: number) => api.get<User>(`/users/${id}`).then((r) => r.data),
  create: (data: any) => api.post<User>('/users/', data).then((r) => r.data),
  quickCreateCustomer: (data: { full_name: string; phone?: string }) =>
    api.post<UserListItem>('/users/quick-customer', data).then((r) => r.data),
  update: (id: number, data: any) => api.put<User>(`/users/${id}`, data).then((r) => r.data),
  delete: (id: number) => api.delete(`/users/${id}`).then((r) => r.data),
};
