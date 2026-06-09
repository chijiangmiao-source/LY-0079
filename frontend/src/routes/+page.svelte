<script lang="ts">
  import { onMount } from 'svelte';
  import { dashboardApi, reviewsApi, complaintsApi } from '$lib/api';
  import type { DashboardResponse, ReviewDashboardStats, ComplaintDashboardStats } from '$lib/types';
  import { formatDate, formatDateTime, lockStatusMap, getStatusBadge, orderStatusMap, followUpStatusMap, complaintStatusMap, complaintTypeMap } from '$lib/utils';
  import {
    FileText,
    Image,
    Lock,
    Unlock,
    AlertTriangle,
    Package,
    TrendingUp,
    Calendar,
    Camera,
    MapPin,
    Clock,
    Star,
    MessageSquare,
    AlertCircle,
    Clock3,
    CheckCircle2,
    BarChart3,
    AlertOctagon,
    DollarSign,
    Users,
    XCircle,
  } from 'lucide-svelte';

  let data: DashboardResponse | null = null;
  let reviewStats: ReviewDashboardStats | null = null;
  let complaintStats: ComplaintDashboardStats | null = null;
  let loading = true;

  function formatShootTime(start?: string, end?: string): string {
    if (!start && !end) return '-';
    if (start && end) {
      return `${formatDateTime(start, 'HH:mm')} - ${formatDateTime(end, 'HH:mm')}`;
    }
    return formatDateTime(start || end, 'HH:mm');
  }

  onMount(async () => {
    try {
      const [stats, rStats, cStats] = await Promise.all([
        dashboardApi.stats(),
        reviewsApi.getDashboardStats().catch(() => null),
        complaintsApi.getDashboardStats().catch(() => null),
      ]);
      data = stats;
      reviewStats = rStats;
      complaintStats = cStats;
    } finally {
      loading = false;
    }
  });
</script>

<div class="p-8">
  <div class="mb-8">
    <h1 class="text-2xl font-bold text-gray-900">数据看板</h1>
    <p class="text-gray-500 mt-1">
      系统概览 · 最后更新: {data ? formatDateTime(data.generated_at) : '-'}
    </p>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-20">
      <div class="text-gray-500">加载中...</div>
    </div>
  {:else if data}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-2 bg-blue-100 rounded-lg">
            <FileText class="w-6 h-6 text-blue-600" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-gray-500">订单总数</p>
            <p class="text-2xl font-bold text-gray-900">{data.stats.total_orders}</p>
          </div>
        </div>
      </div>
      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-2 bg-purple-100 rounded-lg">
            <Image class="w-6 h-6 text-purple-600" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-gray-500">片单总数</p>
            <p class="text-2xl font-bold text-gray-900">{data.stats.total_sheets}</p>
          </div>
        </div>
      </div>
      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-2 bg-green-100 rounded-lg">
            <Lock class="w-6 h-6 text-green-600" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-gray-500">已锁定</p>
            <p class="text-2xl font-bold text-gray-900">{data.stats.locked_sheets}</p>
          </div>
        </div>
      </div>
      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-2 bg-gray-100 rounded-lg">
            <Unlock class="w-6 h-6 text-gray-600" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-gray-500">未锁定</p>
            <p class="text-2xl font-bold text-gray-900">{data.stats.unlocked_sheets}</p>
          </div>
        </div>
      </div>
      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-2 bg-red-100 rounded-lg">
            <AlertTriangle class="w-6 h-6 text-red-600" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-gray-500">待跟进</p>
            <p class="text-2xl font-bold text-gray-900">{data.stats.follow_up_sheets}</p>
          </div>
        </div>
      </div>
      <div class="card p-5">
        <div class="flex items-center">
          <div class="p-2 bg-emerald-100 rounded-lg">
            <Package class="w-6 h-6 text-emerald-600" />
          </div>
          <div class="ml-4">
            <p class="text-sm text-gray-500">交付版本</p>
            <p class="text-2xl font-bold text-gray-900">{data.stats.total_deliveries}</p>
          </div>
        </div>
      </div>
    </div>

    {#if reviewStats}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-yellow-100 rounded-lg">
              <Star class="w-6 h-6 text-yellow-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">近30天平均评分</p>
              <p class="text-2xl font-bold text-gray-900">
                {reviewStats.avg_rating_30d.toFixed(1)}
                <span class="text-sm font-normal text-gray-500">/5</span>
              </p>
            </div>
          </div>
        </div>
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-blue-100 rounded-lg">
              <BarChart3 class="w-6 h-6 text-blue-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">近30天评价数</p>
              <p class="text-2xl font-bold text-gray-900">{reviewStats.review_count_30d}</p>
            </div>
          </div>
        </div>
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-orange-100 rounded-lg">
              <MessageSquare class="w-6 h-6 text-orange-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">待回访订单</p>
              <p class="text-2xl font-bold text-gray-900">{reviewStats.pending_follow_up.total_pending}</p>
            </div>
          </div>
        </div>
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-red-100 rounded-lg">
              <AlertCircle class="w-6 h-6 text-red-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">低分评价（≤3星）</p>
              <p class="text-2xl font-bold text-gray-900">{reviewStats.low_score_orders.length}</p>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div class="card lg:col-span-2">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900 flex items-center">
            <Calendar class="w-5 h-5 mr-2 text-orange-500" />
            未来7天待拍摄订单
          </h2>
          <span class="text-sm text-gray-500">共 {data.stats.upcoming_shoots.length} 单</span>
        </div>
        <div class="overflow-x-auto">
          {#if data.stats.upcoming_shoots.length === 0}
            <p class="text-gray-500 text-center py-8">暂无待拍摄订单</p>
          {:else}
            <table class="w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">订单号</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">摄影师</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">套餐</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">日期</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间段</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">城市</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                {#each data.stats.upcoming_shoots as shoot}
                  <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 text-sm font-medium text-gray-900">
                      <a href="/orders/{shoot.order_id}" class="text-primary-600 hover:text-primary-900">
                        {shoot.order_no}
                      </a>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-600">{shoot.customer_name || '-'}</td>
                    <td class="px-6 py-4 text-sm text-gray-600">
                      <div class="flex items-center">
                        <Camera class="w-4 h-4 mr-1 text-gray-400" />
                        {shoot.photographer_name || '-'}
                      </div>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-600">{shoot.service_package || '-'}</td>
                    <td class="px-6 py-4 text-sm text-gray-600">{formatDate(shoot.shoot_date)}</td>
                    <td class="px-6 py-4 text-sm text-gray-600">
                      <div class="flex items-center">
                        <Clock class="w-4 h-4 mr-1 text-gray-400" />
                        {formatShootTime(shoot.shoot_time_start, shoot.shoot_time_end)}
                      </div>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-600">
                      <div class="flex items-center">
                        <MapPin class="w-4 h-4 mr-1 text-gray-400" />
                        {shoot.city || '-'}
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      <span class="badge {getStatusBadge(orderStatusMap, shoot.status).color}">
                        {getStatusBadge(orderStatusMap, shoot.status).label}
                      </span>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </div>
      </div>
    </div>

    {#if reviewStats}
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="card lg:col-span-2">
          <div class="p-6 border-b border-gray-200 flex items-center justify-between flex-wrap gap-3">
            <h2 class="text-lg font-semibold text-gray-900 flex items-center">
              <TrendingUp class="w-5 h-5 mr-2 text-yellow-500" />
              近30天客户满意度趋势
            </h2>
            <div class="flex items-center gap-4 text-sm text-gray-500">
              <span>平均评分: <span class="font-semibold text-gray-900">{reviewStats.avg_rating_30d.toFixed(2)}</span></span>
              <span>评价总数: <span class="font-semibold text-gray-900">{reviewStats.review_count_30d}</span></span>
            </div>
          </div>
          <div class="p-6">
            {#if reviewStats.satisfaction_trend.length === 0 || reviewStats.review_count_30d === 0}
              <p class="text-gray-500 text-center py-8">暂无评价数据</p>
            {:else}
              <div class="space-y-3">
                {#each reviewStats.satisfaction_trend.slice(-14) as item}
                  <div class="flex items-center gap-3">
                    <span class="text-xs text-gray-500 w-20 shrink-0">{formatDate(item.date, 'MM-DD')}</span>
                    <div class="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden relative">
                      <div
                        class="h-full bg-gradient-to-r from-yellow-400 to-yellow-500 rounded-full transition-all"
                        style="width: {(item.avg_satisfaction / 5) * 100}%;"
                      ></div>
                    </div>
                    <div class="w-28 text-right shrink-0">
                      <span class="text-sm font-semibold text-gray-900">{item.avg_satisfaction.toFixed(1)}</span>
                      {#if item.review_count > 0}
                        <span class="text-xs text-gray-500 ml-1">({item.review_count}条)</span>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        </div>

        <div class="card">
          <div class="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 flex items-center">
              <AlertCircle class="w-5 h-5 mr-2 text-red-500" />
              低分订单预警
            </h2>
            <a href="/reviews/customer" class="text-sm text-primary-600 hover:text-primary-700">查看全部</a>
          </div>
          <div class="overflow-x-auto">
            {#if reviewStats.low_score_orders.length === 0}
              <p class="text-gray-500 text-center py-8">近30天暂无低分评价</p>
            {:else}
              <table class="w-full">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">订单</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">评分</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">回访</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                  {#each reviewStats.low_score_orders.slice(0, 5) as lo}
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3">
                        <a href="/orders/{lo.order_id}" class="text-sm font-medium text-primary-600 hover:text-primary-900">
                          {lo.order_no}
                        </a>
                        <p class="text-xs text-gray-500 mt-0.5">{lo.customer_name || '匿名'}</p>
                      </td>
                      <td class="px-4 py-3">
                        <div class="flex items-center gap-0.5">
                          {#each Array(5) as _, i}
                            <Star
                              class={`w-4 h-4 ${i < lo.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                            />
                          {/each}
                        </div>
                      </td>
                      <td class="px-4 py-3">
                        {#if lo.follow_up_status}
                          <span class="badge {getStatusBadge(followUpStatusMap, lo.follow_up_status).color}">
                            {getStatusBadge(followUpStatusMap, lo.follow_up_status).label}
                          </span>
                        {:else}
                          <span class="text-xs text-red-600">待处理</span>
                        {/if}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {/if}
          </div>
        </div>

        <div class="card">
          <div class="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 flex items-center">
              <MessageSquare class="w-5 h-5 mr-2 text-orange-500" />
              待回访订单统计
            </h2>
            <a href="/reviews/follow-ups" class="text-sm text-primary-600 hover:text-primary-700">查看全部</a>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div class="text-center p-3 bg-yellow-50 rounded-lg">
                <Clock3 class="w-6 h-6 text-yellow-600 mx-auto mb-1" />
                <p class="text-2xl font-bold text-gray-900">{reviewStats.pending_follow_up.total_pending}</p>
                <p class="text-xs text-gray-500">待回访</p>
              </div>
              <div class="text-center p-3 bg-blue-50 rounded-lg">
                <MessageSquare class="w-6 h-6 text-blue-600 mx-auto mb-1" />
                <p class="text-2xl font-bold text-gray-900">{reviewStats.pending_follow_up.in_progress}</p>
                <p class="text-xs text-gray-500">回访中</p>
              </div>
              <div class="text-center p-3 bg-green-50 rounded-lg">
                <CheckCircle2 class="w-6 h-6 text-green-600 mx-auto mb-1" />
                <p class="text-2xl font-bold text-gray-900">{reviewStats.pending_follow_up.completed_last_7d}</p>
                <p class="text-xs text-gray-500">近7天已完成</p>
              </div>
              <div class="text-center p-3 bg-red-50 rounded-lg">
                <AlertTriangle class="w-6 h-6 text-red-600 mx-auto mb-1" />
                <p class="text-2xl font-bold text-gray-900">{reviewStats.pending_follow_up.pending_overdue}</p>
                <p class="text-xs text-gray-500">已超期待回访</p>
              </div>
            </div>
            <div class="text-center text-sm text-gray-500">
              7天内待回访: <span class="font-semibold text-gray-900">{reviewStats.pending_follow_up.pending_7d}</span> 单
            </div>
          </div>
        </div>
      </div>
    {/if}

    {#if complaintStats}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-red-100 rounded-lg">
              <AlertOctagon class="w-6 h-6 text-red-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">近30天投诉数</p>
              <p class="text-2xl font-bold text-gray-900">{complaintStats.total_complaints_30d}</p>
            </div>
          </div>
        </div>
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-yellow-100 rounded-lg">
              <Clock3 class="w-6 h-6 text-yellow-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">待处理</p>
              <p class="text-2xl font-bold text-gray-900">{complaintStats.pending_count}</p>
            </div>
          </div>
        </div>
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-blue-100 rounded-lg">
              <MessageSquare class="w-6 h-6 text-blue-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">处理中</p>
              <p class="text-2xl font-bold text-gray-900">{complaintStats.processing_count}</p>
            </div>
          </div>
        </div>
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-green-100 rounded-lg">
              <CheckCircle2 class="w-6 h-6 text-green-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">超时未处理</p>
              <p class="text-2xl font-bold text-gray-900">
                <span class={complaintStats.overdue_count > 0 ? 'text-red-600' : ''}>{complaintStats.overdue_count}</span>
              </p>
            </div>
          </div>
        </div>
        <div class="card p-5">
          <div class="flex items-center">
            <div class="p-2 bg-emerald-100 rounded-lg">
              <DollarSign class="w-6 h-6 text-emerald-600" />
            </div>
            <div class="ml-4">
              <p class="text-sm text-gray-500">补偿成本（30天）</p>
              <p class="text-2xl font-bold text-gray-900">¥{complaintStats.total_compensation_amount.toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="card lg:col-span-2">
          <div class="p-6 border-b border-gray-200 flex items-center justify-between flex-wrap gap-3">
            <h2 class="text-lg font-semibold text-gray-900 flex items-center">
              <TrendingUp class="w-5 h-5 mr-2 text-red-500" />
              近30天投诉趋势
            </h2>
            <div class="flex items-center gap-4 text-sm text-gray-500">
              <span>总投诉: <span class="font-semibold text-gray-900">{complaintStats.total_complaints_30d}</span></span>
              <span>已解决: <span class="font-semibold text-green-600">{complaintStats.resolved_count_30d}</span></span>
              <span>平均耗时: <span class="font-semibold text-gray-900">{complaintStats.avg_resolve_hours.toFixed(1)}h</span></span>
            </div>
          </div>
          <div class="p-6">
            {#if complaintStats.complaint_trend.length === 0 || complaintStats.total_complaints_30d === 0}
              <p class="text-gray-500 text-center py-8">暂无投诉数据</p>
            {:else}
              <div class="space-y-3">
                {#each complaintStats.complaint_trend.slice(-14) as item}
                  <div class="flex items-center gap-3">
                    <span class="text-xs text-gray-500 w-20 shrink-0">{formatDate(item.date, 'MM-DD')}</span>
                    <div class="flex-1 h-5 bg-gray-100 rounded-full overflow-hidden relative">
                      <div
                        class="h-full bg-gradient-to-r from-red-400 to-red-500 rounded-full transition-all"
                        style="width: {item.complaint_count > 0 ? Math.min((item.complaint_count / Math.max(...complaintStats.complaint_trend.map(t => t.complaint_count), 1)) * 100, 100) : 0}%;"
                      ></div>
                    </div>
                    <div class="w-36 text-right shrink-0 flex items-center justify-end gap-2">
                      <span class="text-sm font-semibold text-red-600">{item.complaint_count} 投诉</span>
                      {#if item.resolved_count > 0}
                        <span class="text-xs text-green-600">({item.resolved_count}已解)</span>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        </div>

        <div class="card">
          <div class="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 flex items-center">
              <XCircle class="w-5 h-5 mr-2 text-red-500" />
              超时未处理预警
            </h2>
            <a href="/complaints" class="text-sm text-primary-600 hover:text-primary-700">查看全部</a>
          </div>
          <div class="overflow-x-auto">
            {#if complaintStats.overdue_complaints.length === 0}
              <p class="text-gray-500 text-center py-8">暂无超时工单</p>
            {:else}
              <table class="w-full">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">工单</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">超时</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                  {#each complaintStats.overdue_complaints as oc}
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3">
                        <a href="/complaints/{oc.id}" class="text-sm font-medium text-primary-600 hover:text-primary-900">
                          {oc.ticket_no}
                        </a>
                        <p class="text-xs text-gray-500 mt-0.5">{oc.order_no}</p>
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-600">{oc.customer_name || '-'}</td>
                      <td class="px-4 py-3">
                        <span class="badge {getStatusBadge(complaintStatusMap, oc.status).color}">
                          {getStatusBadge(complaintStatusMap, oc.status).label}
                        </span>
                      </td>
                      <td class="px-4 py-3">
                        <span class="text-red-600 font-medium text-sm">{oc.overdue_days} 天</span>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {/if}
          </div>
        </div>

        <div class="card">
          <div class="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900 flex items-center">
              <DollarSign class="w-5 h-5 mr-2 text-emerald-500" />
              补偿成本统计
            </h2>
            <a href="/complaints" class="text-sm text-primary-600 hover:text-primary-700">查看全部</a>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div class="text-center p-3 bg-red-50 rounded-lg">
                <AlertOctagon class="w-6 h-6 text-red-600 mx-auto mb-1" />
                <p class="text-2xl font-bold text-gray-900">{complaintStats.compensation_count}</p>
                <p class="text-xs text-gray-500">补偿工单</p>
              </div>
              <div class="text-center p-3 bg-emerald-50 rounded-lg">
                <DollarSign class="w-6 h-6 text-emerald-600 mx-auto mb-1" />
                <p class="text-2xl font-bold text-gray-900">¥{complaintStats.total_compensation_amount.toFixed(0)}</p>
                <p class="text-xs text-gray-500">总补偿金额</p>
              </div>
            </div>
            {#if Object.keys(complaintStats.type_distribution).length > 0}
              <div class="pt-4 border-t border-gray-100">
                <p class="text-sm font-medium text-gray-700 mb-3">投诉类型分布</p>
                <div class="space-y-2">
                  {#each Object.entries(complaintStats.type_distribution) as [type, count]}
                    {#if count > 0}
                      <div class="flex items-center justify-between">
                        <span class="text-sm text-gray-600">{getStatusBadge(complaintTypeMap, type).label}</span>
                        <span class="text-sm font-medium text-gray-900">{count} 件</span>
                      </div>
                    {/if}
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}

    {#if data.stats.photographer_schedule_stats.length > 0}
      <div class="card mb-6">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900 flex items-center">
            <Camera class="w-5 h-5 mr-2 text-blue-500" />
            摄影师档期占用统计
          </h2>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {#each data.stats.photographer_schedule_stats as ps}
              <div class="border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center">
                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span class="text-blue-600 font-semibold">{ps.photographer_name.charAt(0)}</span>
                    </div>
                    <div class="ml-3">
                      <p class="font-medium text-gray-900">{ps.photographer_name}</p>
                      <p class="text-xs text-gray-500">累计 {ps.total_orders} 单 · 占用 {ps.occupied_days} 天</p>
                    </div>
                  </div>
                </div>
                {#if ps.upcoming_orders.length > 0}
                  <div class="space-y-2">
                    <p class="text-xs font-medium text-gray-500">未来7天档期 ({ps.upcoming_orders.length}单)：</p>
                    {#each ps.upcoming_orders as uo}
                      <div class="text-sm bg-gray-50 rounded p-2">
                        <div class="flex items-center justify-between">
                          <span class="text-gray-900 font-medium">{uo.customer_name || '-'}</span>
                          <span class="badge {getStatusBadge(orderStatusMap, uo.status).color} text-xs">
                            {getStatusBadge(orderStatusMap, uo.status).label}
                          </span>
                        </div>
                        <div class="text-xs text-gray-500 mt-1 flex items-center flex-wrap gap-2">
                          <span class="flex items-center"><Calendar class="w-3 h-3 mr-1" />{formatDate(uo.shoot_date)}</span>
                          <span class="flex items-center"><Clock class="w-3 h-3 mr-1" />{formatShootTime(uo.shoot_time_start, uo.shoot_time_end)}</span>
                          {#if uo.city}
                            <span class="flex items-center"><MapPin class="w-3 h-3 mr-1" />{uo.city}</span>
                          {/if}
                        </div>
                      </div>
                    {/each}
                  </div>
                {:else}
                  <p class="text-sm text-gray-400">未来7天暂无拍摄安排</p>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      </div>
    {/if}

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">修图师负载</h2>
        </div>
        <div class="p-6">
          {#if data.stats.retouchers_workload.length === 0}
            <p class="text-gray-500 text-center py-8">暂无修图师数据</p>
          {:else}
            <div class="space-y-4">
              {#each data.stats.retouchers_workload as rw}
                <div>
                  <div class="flex justify-between mb-2">
                    <span class="font-medium text-gray-900">{rw.retoucher_name}</span>
                    <span class="text-sm text-gray-500">
                      进行中 {rw.in_progress_sheets} / 共 {rw.assigned_sheets}
                    </span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div
                      class="bg-primary-600 h-2 rounded-full transition-all"
                      style="width: {rw.assigned_sheets ? (rw.completed_sheets / rw.assigned_sheets) * 100 : 0}%"
                    ></div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <div class="card">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">延期未锁片订单</h2>
        </div>
        <div class="overflow-x-auto">
          {#if data.stats.overdue_sheets.length === 0}
            <p class="text-gray-500 text-center py-8">暂无延期片单</p>
          {:else}
            <table class="w-full">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">片单编号</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">延期天数</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200">
                {#each data.stats.overdue_sheets as sheet}
                  <tr>
                    <td class="px-6 py-4 text-sm font-medium text-gray-900">{sheet.sheet_no}</td>
                    <td class="px-6 py-4 text-sm text-gray-600">{sheet.customer_name || '-'}</td>
                    <td class="px-6 py-4">
                      <span class="text-red-600 font-medium">{sheet.overdue_days} 天</span>
                    </td>
                    <td class="px-6 py-4">
                      <span class="badge {getStatusBadge(lockStatusMap, sheet.lock_status).color}">
                        {getStatusBadge(lockStatusMap, sheet.lock_status).label}
                      </span>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </div>
      </div>

      <div class="card lg:col-span-2">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">订单选片进度</h2>
        </div>
        <div class="p-6">
          {#if data.stats.selection_progress.length === 0}
            <p class="text-gray-500 text-center py-8">暂无订单数据</p>
          {:else}
            <div class="space-y-4">
              {#each data.stats.selection_progress as sp}
                <div>
                  <div class="flex justify-between mb-2">
                    <div>
                      <span class="font-medium text-gray-900">{sp.order_no}</span>
                      <span class="text-gray-500 ml-2">{sp.customer_name || '-'}</span>
                    </div>
                    <span class="text-sm text-gray-500">
                      <TrendingUp class="w-4 h-4 inline mr-1" />
                      {sp.progress.toFixed(1)}% ({sp.locked_sheets}/{sp.total_sheets})
                    </span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-3">
                    <div
                      class="bg-green-500 h-3 rounded-full transition-all"
                      style="width: {sp.progress}%"
                    ></div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>
