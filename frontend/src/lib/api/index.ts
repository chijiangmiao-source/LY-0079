import api from './client';
import type {
  Order,
  OrderDetail,
  OrderListItem,
  OrderStatus,
  ScheduleConflict,
  PhotoSheet,
  PhotoSheetDetail,
  PhotoSheetListItem,
  RetouchStatus,
  LockStatus,
  PhotoBatch,
  SelectionRecord,
  RetouchRequest,
  RetouchRequestStatus,
  DeliveryVersion,
  DashboardResponse,
  RetoucherWorkload,
  OrderSelectionProgress,
  OverdueSheet,
  UpcomingShootOrder,
  PhotographerScheduleStat,
  FollowUpStatus,
  AfterSalesResult,
  CustomerReview,
  CustomerReviewDetail,
  FollowUpRecord,
  FollowUpRecordDetail,
  FollowUpListItem,
  ReviewDashboardStats,
} from '$lib/types';
export { authApi, usersApi } from './auth';

export const ordersApi = {
  list: (params?: {
    status?: OrderStatus;
    customer_id?: number;
    photographer_id?: number;
    shoot_date_from?: string;
    shoot_date_to?: string;
    city?: string;
    skip?: number;
    limit?: number;
  }) => api.get<OrderListItem[]>('/orders/', { params }).then((r) => r.data),
  get: (id: number) => api.get<OrderDetail>(`/orders/${id}`).then((r) => r.data),
  create: (data: any) => api.post<Order>('/orders/', data).then((r) => r.data),
  update: (id: number, data: any) => api.put<Order>(`/orders/${id}`, data).then((r) => r.data),
  delete: (id: number) => api.delete(`/orders/${id}`).then((r) => r.data),
  checkSchedule: (params: {
    photographer_id: number;
    shoot_time_start: string;
    shoot_time_end: string;
    order_id?: number;
  }) => api.get<ScheduleConflict>('/orders/check-schedule', { params }).then((r) => r.data),
};

export const sheetsApi = {
  list: (params?: {
    order_id?: number;
    retouch_status?: RetouchStatus;
    lock_status?: LockStatus;
    retoucher_id?: number;
    skip?: number;
    limit?: number;
  }) => api.get<PhotoSheetListItem[]>('/photo-sheets/', { params }).then((r) => r.data),
  get: (id: number) => api.get<PhotoSheetDetail>(`/photo-sheets/${id}`).then((r) => r.data),
  create: (data: any) => api.post<PhotoSheet>('/photo-sheets/', data).then((r) => r.data),
  update: (id: number, data: any) => api.put<PhotoSheet>(`/photo-sheets/${id}`, data).then((r) => r.data),
  lock: (id: number) => api.post<PhotoSheet>(`/photo-sheets/${id}/lock`).then((r) => r.data),
  delete: (id: number) => api.delete(`/photo-sheets/${id}`).then((r) => r.data),
};

export const batchesApi = {
  list: (params?: { order_id?: number; sheet_id?: number; batch_type?: string }) =>
    api.get<PhotoBatch[]>('/batches/', { params }).then((r) => r.data),
  get: (id: number) => api.get<PhotoBatch>(`/batches/${id}`).then((r) => r.data),
  create: (data: any) => api.post<PhotoBatch>('/batches/', data).then((r) => r.data),
  update: (id: number, data: any) => api.put<PhotoBatch>(`/batches/${id}`, data).then((r) => r.data),
  delete: (id: number) => api.delete(`/batches/${id}`).then((r) => r.data),
};

export const selectionsApi = {
  list: (params?: { sheet_id?: number; skip?: number; limit?: number }) =>
    api.get<SelectionRecord[]>('/selections/', { params }).then((r) => r.data),
  get: (id: number) => api.get<SelectionRecord>(`/selections/${id}`).then((r) => r.data),
  create: (data: any) => api.post<SelectionRecord>('/selections/', data).then((r) => r.data),
  update: (id: number, data: any) => api.put<SelectionRecord>(`/selections/${id}`, data).then((r) => r.data),
  confirm: (id: number, data?: { final_confirm_time?: string }) =>
    api.post<SelectionRecord>(`/selections/${id}/confirm`, data || {}).then((r) => r.data),
};

export const retouchApi = {
  list: (params?: {
    sheet_id?: number;
    selection_id?: number;
    status?: RetouchRequestStatus;
    retoucher_id?: number;
  }) => api.get<RetouchRequest[]>('/retouch/', { params }).then((r) => r.data),
  get: (id: number) => api.get<RetouchRequest>(`/retouch/${id}`).then((r) => r.data),
  create: (data: any) => api.post<RetouchRequest>('/retouch/', data).then((r) => r.data),
  update: (id: number, data: any) => api.put<RetouchRequest>(`/retouch/${id}`, data).then((r) => r.data),
  createNewVersion: (id: number, data: any) =>
    api.post<RetouchRequest>(`/retouch/${id}/new-version`, data).then((r) => r.data),
};

export const deliveryApi = {
  list: (params?: { order_id?: number; skip?: number; limit?: number }) =>
    api.get<DeliveryVersion[]>('/delivery/', { params }).then((r) => r.data),
  get: (id: number) => api.get<DeliveryVersion>(`/delivery/${id}`).then((r) => r.data),
  create: (data: any) => api.post<DeliveryVersion>('/delivery/', data).then((r) => r.data),
  update: (id: number, data: any) => api.put<DeliveryVersion>(`/delivery/${id}`, data).then((r) => r.data),
  delete: (id: number) => api.delete(`/delivery/${id}`).then((r) => r.data),
};

export const dashboardApi = {
  stats: () => api.get<DashboardResponse>('/dashboard/stats').then((r) => r.data),
  retouchersWorkload: () => api.get<RetoucherWorkload[]>('/dashboard/retouchers-workload').then((r) => r.data),
  selectionProgress: () => api.get<OrderSelectionProgress[]>('/dashboard/selection-progress').then((r) => r.data),
  overdueSheets: () => api.get<OverdueSheet[]>('/dashboard/overdue-sheets').then((r) => r.data),
  upcomingShoots: () => api.get<UpcomingShootOrder[]>('/dashboard/upcoming-shoots').then((r) => r.data),
  photographerScheduleStats: () =>
    api.get<PhotographerScheduleStat[]>('/dashboard/photographer-schedule-stats').then((r) => r.data),
};

export const reviewsApi = {
  listFollowUps: (params?: {
    status?: FollowUpStatus;
    satisfaction_min?: number;
    satisfaction_max?: number;
    photographer_id?: number;
    order_id?: number;
    skip?: number;
    limit?: number;
  }) => api.get<FollowUpListItem[]>('/reviews/follow-ups', { params }).then((r) => r.data),
  getFollowUp: (id: number) => api.get<FollowUpRecordDetail>(`/reviews/follow-ups/${id}`).then((r) => r.data),
  createFollowUp: (data: {
    order_id: number;
    follow_up_time?: string;
    satisfaction?: number;
    tags?: string;
    feedback?: string;
    after_sales_result?: AfterSalesResult;
    after_sales_notes?: string;
    status?: FollowUpStatus;
    review_deadline?: string;
  }) => api.post<FollowUpRecord>('/reviews/follow-ups', data).then((r) => r.data),
  updateFollowUp: (id: number, data: {
    follow_up_time?: string;
    satisfaction?: number;
    tags?: string;
    feedback?: string;
    after_sales_result?: AfterSalesResult;
    after_sales_notes?: string;
    status?: FollowUpStatus;
    review_deadline?: string;
  }) => api.put<FollowUpRecord>(`/reviews/follow-ups/${id}`, data).then((r) => r.data),
  deleteFollowUp: (id: number) => api.delete(`/reviews/follow-ups/${id}`).then((r) => r.data),
  listCustomerReviews: (params?: {
    order_id?: number;
    rating_min?: number;
    rating_max?: number;
    photographer_id?: number;
    skip?: number;
    limit?: number;
  }) => api.get<CustomerReviewDetail[]>('/reviews/customer', { params }).then((r) => r.data),
  getCustomerReview: (id: number) => api.get<CustomerReviewDetail>(`/reviews/customer/${id}`).then((r) => r.data),
  createCustomerReview: (data: {
    order_id: number;
    rating: number;
    tags?: string;
    feedback?: string;
    is_anonymous?: boolean;
  }) => api.post<CustomerReview>('/reviews/customer', data).then((r) => r.data),
  updateCustomerReview: (id: number, data: {
    rating?: number;
    tags?: string;
    feedback?: string;
    is_anonymous?: boolean;
  }) => api.put<CustomerReview>(`/reviews/customer/${id}`, data).then((r) => r.data),
  getDashboardStats: () => api.get<ReviewDashboardStats>('/reviews/dashboard-stats').then((r) => r.data),
};
