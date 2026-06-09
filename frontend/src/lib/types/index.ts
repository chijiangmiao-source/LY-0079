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

export type FollowUpStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

export type AfterSalesResult = 'resolved' | 'partially_resolved' | 'unresolved' | 'no_issues';

export interface CustomerReview {
  id: number;
  order_id: number;
  rating: number;
  tags?: string;
  feedback?: string;
  submitted_at: string;
  is_anonymous: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerReviewDetail extends CustomerReview {
  order_no?: string;
  customer_name?: string;
  photographer_name?: string;
}

export interface FollowUpRecord {
  id: number;
  order_id: number;
  follow_up_time?: string;
  satisfaction?: number;
  tags?: string;
  feedback?: string;
  after_sales_result?: AfterSalesResult;
  after_sales_notes?: string;
  status: FollowUpStatus;
  follow_up_by?: number;
  review_deadline?: string;
  created_at: string;
  updated_at: string;
}

export interface FollowUpRecordDetail extends FollowUpRecord {
  order_no?: string;
  customer_name?: string;
  photographer_id?: number;
  photographer_name?: string;
  shoot_date?: string;
  follow_up_by_name?: string;
  customer_rating?: number;
  review_submitted: boolean;
}

export interface FollowUpListItem {
  id: number;
  order_id: number;
  order_no: string;
  customer_name?: string;
  photographer_id?: number;
  photographer_name?: string;
  shoot_date?: string;
  status: FollowUpStatus;
  satisfaction?: number;
  follow_up_time?: string;
  review_deadline?: string;
  customer_rating?: number;
  created_at: string;
}

export interface SatisfactionTrendItem {
  date: string;
  avg_satisfaction: number;
  review_count: number;
}

export interface LowScoreOrder {
  order_id: number;
  order_no: string;
  customer_name?: string;
  photographer_name?: string;
  rating: number;
  feedback?: string;
  tags?: string;
  submitted_at: string;
  follow_up_status?: string;
}

export interface PendingFollowUpStat {
  total_pending: number;
  pending_7d: number;
  pending_overdue: number;
  in_progress: number;
  completed_last_7d: number;
}

export interface ReviewDashboardStats {
  avg_rating_30d: number;
  review_count_30d: number;
  satisfaction_trend: SatisfactionTrendItem[];
  low_score_orders: LowScoreOrder[];
  pending_follow_up: PendingFollowUpStat;
}

export type ComplaintType = 'quality' | 'service' | 'delivery' | 'attitude' | 'other';

export type ComplaintStatus =
  | 'pending'
  | 'assigned'
  | 'processing'
  | 'compensated'
  | 'resolved'
  | 'closed'
  | 'cancelled';

export type ComplaintSource = 'auto_low_rating' | 'customer_initiated' | 'manual';

export type CompensationType = 'refund' | 'discount' | 'retake' | 'gift' | 'other';

export interface CompensationRecord {
  id: number;
  complaint_id: number;
  compensation_type: CompensationType;
  amount: number;
  description?: string;
  approved_by?: number;
  approved_at?: string;
  is_executed: boolean;
  executed_at?: string;
  executed_by?: number;
  created_at: string;
  updated_at: string;
}

export interface CompensationDetail extends CompensationRecord {
  approver_name?: string;
  executor_name?: string;
}

export interface ComplaintTicket {
  id: number;
  ticket_no: string;
  order_id: number;
  customer_id: number;
  complaint_type: ComplaintType;
  source: ComplaintSource;
  title: string;
  description: string;
  status: ComplaintStatus;
  rating_trigger?: number;
  assigned_to?: number;
  assigned_at?: string;
  process_deadline?: string;
  progress_notes?: string;
  final_conclusion?: string;
  resolved_at?: string;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface ComplaintTicketListItem {
  id: number;
  ticket_no: string;
  order_id: number;
  order_no?: string;
  customer_id: number;
  customer_name?: string;
  photographer_id?: number;
  photographer_name?: string;
  complaint_type: ComplaintType;
  source: ComplaintSource;
  title: string;
  status: ComplaintStatus;
  rating_trigger?: number;
  assigned_to?: number;
  assignee_name?: string;
  process_deadline?: string;
  has_compensation: boolean;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface ComplaintTicketDetail extends ComplaintTicket {
  order_no?: string;
  customer_name?: string;
  photographer_id?: number;
  photographer_name?: string;
  shoot_date?: string;
  assignee_name?: string;
  creator_name?: string;
  compensation?: CompensationDetail;
  is_overdue: boolean;
}

export interface ComplaintTrendItem {
  date: string;
  complaint_count: number;
  resolved_count: number;
}

export interface OverdueComplaintItem {
  id: number;
  ticket_no: string;
  order_no?: string;
  customer_name?: string;
  status: ComplaintStatus;
  overdue_days: number;
  process_deadline?: string;
  assigned_to?: number;
  assignee_name?: string;
}

export interface ComplaintDashboardStats {
  total_complaints_30d: number;
  pending_count: number;
  processing_count: number;
  resolved_count_30d: number;
  overdue_count: number;
  total_compensation_amount: number;
  compensation_count: number;
  avg_resolve_hours: number;
  complaint_trend: ComplaintTrendItem[];
  overdue_complaints: OverdueComplaintItem[];
  type_distribution: Record<string, number>;
}
