import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

export const formatDate = (date?: string, format: string = 'YYYY-MM-DD') => {
  if (!date) return '-';
  return dayjs(date).format(format);
};

export const formatDateTime = (date?: string, format: string = 'YYYY-MM-DD HH:mm:ss') => {
  if (!date) return '-';
  return dayjs(date).format(format);
};

export const fromNow = (date?: string) => {
  if (!date) return '-';
  return dayjs(date).fromNow();
};

export const isOverdue = (deadline?: string) => {
  if (!deadline) return false;
  return dayjs(deadline).isBefore(dayjs());
};

export const orderStatusMap: Record<string, { label: string; color: string }> = {
  pending: { label: '待拍摄', color: 'bg-gray-100 text-gray-800' },
  shooting: { label: '拍摄中', color: 'bg-blue-100 text-blue-800' },
  shot: { label: '已拍摄', color: 'bg-indigo-100 text-indigo-800' },
  retouching: { label: '修图中', color: 'bg-yellow-100 text-yellow-800' },
  selecting: { label: '选片中', color: 'bg-purple-100 text-purple-800' },
  locked: { label: '已锁定', color: 'bg-green-100 text-green-800' },
  delivered: { label: '已交付', color: 'bg-emerald-100 text-emerald-800' },
  cancelled: { label: '已取消', color: 'bg-red-100 text-red-800' },
};

export const retouchStatusMap: Record<string, { label: string; color: string }> = {
  not_started: { label: '未开始', color: 'bg-gray-100 text-gray-800' },
  in_progress: { label: '进行中', color: 'bg-yellow-100 text-yellow-800' },
  completed: { label: '已完成', color: 'bg-green-100 text-green-800' },
};

export const lockStatusMap: Record<string, { label: string; color: string }> = {
  unlocked: { label: '未锁定', color: 'bg-gray-100 text-gray-800' },
  locked: { label: '已锁定', color: 'bg-green-100 text-green-800' },
  follow_up: { label: '待跟进', color: 'bg-red-100 text-red-800' },
};

export const retouchRequestStatusMap: Record<string, { label: string; color: string }> = {
  pending: { label: '待处理', color: 'bg-gray-100 text-gray-800' },
  in_progress: { label: '处理中', color: 'bg-yellow-100 text-yellow-800' },
  completed: { label: '已完成', color: 'bg-green-100 text-green-800' },
};

export const userRoleMap: Record<string, { label: string; color: string }> = {
  admin: { label: '管理员', color: 'bg-red-100 text-red-800' },
  photographer: { label: '摄影师', color: 'bg-blue-100 text-blue-800' },
  retoucher: { label: '修图师', color: 'bg-purple-100 text-purple-800' },
  customer: { label: '客户', color: 'bg-gray-100 text-gray-800' },
};

export const followUpStatusMap: Record<string, { label: string; color: string }> = {
  pending: { label: '待回访', color: 'bg-yellow-100 text-yellow-800' },
  in_progress: { label: '回访中', color: 'bg-blue-100 text-blue-800' },
  completed: { label: '已完成', color: 'bg-green-100 text-green-800' },
  cancelled: { label: '已取消', color: 'bg-gray-100 text-gray-800' },
};

export const afterSalesResultMap: Record<string, { label: string; color: string }> = {
  resolved: { label: '已解决', color: 'bg-green-100 text-green-800' },
  partially_resolved: { label: '部分解决', color: 'bg-yellow-100 text-yellow-800' },
  unresolved: { label: '未解决', color: 'bg-red-100 text-red-800' },
  no_issues: { label: '无问题', color: 'bg-gray-100 text-gray-800' },
};

export function getStatusBadge(statusMap: Record<string, { label: string; color: string }>, status: string) {
  const info = statusMap[status] || { label: status, color: 'bg-gray-100 text-gray-800' };
  return info;
}
