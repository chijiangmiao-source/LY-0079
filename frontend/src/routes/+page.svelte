<script lang="ts">
  import { onMount } from 'svelte';
  import { dashboardApi } from '$lib/api';
  import type { DashboardResponse } from '$lib/types';
  import { formatDate, formatDateTime, lockStatusMap, getStatusBadge, orderStatusMap } from '$lib/utils';
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
  } from 'lucide-svelte';

  let data: DashboardResponse | null = null;
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
      data = await dashboardApi.stats();
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
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
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
