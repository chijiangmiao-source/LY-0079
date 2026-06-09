export type UserRole = 'admin' | 'photographer' | 'retoucher' | 'customer';

export type OrderStatus =
  | 'pending'
  | 'shooting'
  | 'shot'
  | 'retouching'
  | 'selecting'
  | 'locked'
  | 'delivered'
  | 'cancelled';

export type RetouchStatus = 'not_started' | 'in_progress' | 'completed';

export type LockStatus = 'unlocked' | 'locked' | 'follow_up';

export type RetouchRequestStatus = 'pending' | 'in_progress' | 'completed';

export interface User {
  id: number;
  username: string;
  email?: string;
  full_name: string;
  role: UserRole;
  phone?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserListItem {
  id: number;
  username: string;
  full_name: string;
  role: UserRole;
  email?: string;
  phone?: string;
  is_active: boolean;
}

export interface Order {
  id: number;
  order_no: string;
  customer_id: number;
  photographer_id?: number;
  shoot_type?: string;
  shoot_date?: string;
  shoot_time_start?: string;
  shoot_time_end?: string;
  city?: string;
  service_package?: string;
  location?: string;
  total_photos: number;
  included_retouches: number;
  status: OrderStatus;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface OrderDetail extends Order {
  customer_name?: string;
  photographer_name?: string;
  sheet_count: number;
  photo_count: number;
}

export interface OrderListItem {
  id: number;
  order_no: string;
  customer_name?: string;
  photographer_name?: string;
  photographer_id?: number;
  shoot_type?: string;
  shoot_date?: string;
  shoot_time_start?: string;
  shoot_time_end?: string;
  city?: string;
  service_package?: string;
  status: OrderStatus;
  total_photos: number;
  created_at: string;
}

export interface ScheduleConflictOrder {
  order_id: number;
  order_no: string;
  customer_name?: string;
  shoot_time_start?: string;
  shoot_time_end?: string;
  city?: string;
}

export interface ScheduleConflict {
  has_conflict: boolean;
  conflicting_orders: ScheduleConflictOrder[];
}

export interface PhotoSheet {
  id: number;
  sheet_no: string;
  order_id: number;
  total_photos: number;
  selectable_count: number;
  retouch_status: RetouchStatus;
  retoucher_id?: number;
  selection_deadline?: string;
  lock_status: LockStatus;
  locked_at?: string;
  locked_by?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface PhotoSheetDetail extends PhotoSheet {
  order_no?: string;
  retoucher_name?: string;
  customer_name?: string;
  selection_count: number;
  is_overdue: boolean;
}

export interface PhotoSheetListItem {
  id: number;
  sheet_no: string;
  order_id: number;
  order_no?: string;
  total_photos: number;
  retouch_status: RetouchStatus;
  lock_status: LockStatus;
  selection_deadline?: string;
  retoucher_name?: string;
  created_at: string;
}

export interface PhotoBatch {
  id: number;
  batch_no: string;
  order_id: number;
  sheet_id?: number;
  photo_count: number;
  storage_path?: string;
  batch_type: string;
  description?: string;
  uploaded_by?: number;
  created_at: string;
}

export interface SelectionRecord {
  id: number;
  sheet_id: number;
  customer_name: string;
  selection_time: string;
  selected_count: number;
  selected_photo_ids?: string;
  retouch_notes?: string;
  final_confirm_time?: string;
  created_at: string;
  updated_at: string;
}

export interface RetouchRequest {
  id: number;
  sheet_id: number;
  selection_id: number;
  version: number;
  description?: string;
  retoucher_id?: number;
  status: RetouchRequestStatus;
  storage_path?: string;
  created_at: string;
  updated_at: string;
}

export interface DeliveryVersion {
  id: number;
  order_id: number;
  version: number;
  delivery_date: string;
  storage_path?: string;
  description?: string;
  photo_count: number;
  delivered_by?: number;
  is_protected: boolean;
  created_at: string;
}

export interface RetoucherWorkload {
  retoucher_id: number;
  retoucher_name: string;
  assigned_sheets: number;
  in_progress_sheets: number;
  completed_sheets: number;
  total_photos: number;
}

export interface OrderSelectionProgress {
  order_id: number;
  order_no: string;
  customer_name?: string;
  total_sheets: number;
  locked_sheets: number;
  unlocked_sheets: number;
  follow_up_sheets: number;
  progress: number;
}

export interface OverdueSheet {
  sheet_id: number;
  sheet_no: string;
  order_id: number;
  order_no: string;
  customer_name?: string;
  selection_deadline?: string;
  overdue_days: number;
  lock_status: string;
}

export interface UpcomingShootOrder {
  order_id: number;
  order_no: string;
  customer_name?: string;
  photographer_id?: number;
  photographer_name?: string;
  shoot_date?: string;
  shoot_time_start?: string;
  shoot_time_end?: string;
  city?: string;
  service_package?: string;
  status: string;
}

export interface PhotographerScheduleStat {
  photographer_id: number;
  photographer_name: string;
  total_orders: number;
  occupied_days: number;
  upcoming_orders: UpcomingShootOrder[];
}

export interface DashboardStats {
  total_orders: number;
  total_sheets: number;
  locked_sheets: number;
  unlocked_sheets: number;
  follow_up_sheets: number;
  total_deliveries: number;
  retouchers_workload: RetoucherWorkload[];
  selection_progress: OrderSelectionProgress[];
  overdue_sheets: OverdueSheet[];
  upcoming_shoots: UpcomingShootOrder[];
  photographer_schedule_stats: PhotographerScheduleStat[];
}

export interface DashboardResponse {
  stats: DashboardStats;
  generated_at: string;
}
