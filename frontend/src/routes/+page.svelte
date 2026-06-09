<script lang="ts">
  import { onMount } from 'svelte';
  import { dashboardApi } from '$lib/api';
  import type { DashboardResponse } from '$lib/types';
  import { formatDateTime, lockStatusMap, getStatusBadge, orderStatusMap } from '$lib/utils';
  import {
    FileText,
    Image,
    Lock,
    Unlock,
    AlertTriangle,
    Package,
    TrendingUp,
  } from 'lucide-svelte';

  let data: DashboardResponse | null = null;
  let loading = true;

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
