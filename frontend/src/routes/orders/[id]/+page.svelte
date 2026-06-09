<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { ordersApi, sheetsApi, selectionsApi } from '$lib/api';
  import type { OrderDetail, PhotoSheetListItem, SelectionRecord } from '$lib/types';
  import {
    formatDate,
    formatDateTime,
    orderStatusMap,
    retouchStatusMap,
    lockStatusMap,
    getStatusBadge,
  } from '$lib/utils';
  import { ArrowLeft, Plus, Image } from 'lucide-svelte';

  let order: OrderDetail | null = null;
  let sheets: PhotoSheetListItem[] = [];
  let loading = true;
  let showCreateSheet = false;

  let sheetForm = {
    total_photos: 0,
    selectable_count: 0,
    selection_deadline: '',
    retoucher_id: undefined as number | undefined,
    notes: '',
  };

  async function loadData() {
    loading = true;
    try {
      const id = parseInt($page.params.id);
      order = await ordersApi.get(id);
      sheets = await sheetsApi.list({ order_id: id });
    } finally {
      loading = false;
    }
  }

  async function handleCreateSheet() {
    try {
      const data: any = {
        order_id: order?.id,
        ...sheetForm,
      };
      if (!sheetForm.selection_deadline) {
        delete data.selection_deadline;
      }
      await sheetsApi.create(data);
      showCreateSheet = false;
      sheetForm = {
        total_photos: 0,
        selectable_count: 0,
        selection_deadline: '',
        retoucher_id: undefined,
        notes: '',
      };
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '创建片单失败');
    }
  }

  onMount(loadData);
</script>

<div class="p-8">
  <a href="/orders" class="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6">
    <ArrowLeft class="w-5 h-5 mr-2" />
    返回订单列表
  </a>

  {#if loading}
    <div class="p-12 text-center text-gray-500">加载中...</div>
  {:else if order}
    <div class="mb-8">
      <div class="flex items-start justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">
            {order.order_no}
            <span class="ml-3 badge {getStatusBadge(orderStatusMap, order.status).color}">
              {getStatusBadge(orderStatusMap, order.status).label}
            </span>
          </h1>
          <p class="text-gray-500 mt-1">创建于 {formatDateTime(order.created_at)}</p>
        </div>
        <button class="btn btn-primary" on:click={() => (showCreateSheet = true)}>
          <Plus class="w-5 h-5" />
          新建片单
        </button>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <div class="card p-4">
          <p class="text-sm text-gray-500">客户</p>
          <p class="text-lg font-semibold mt-1">{order.customer_name || '-'}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">摄影师</p>
          <p class="text-lg font-semibold mt-1">{order.photographer_name || '-'}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">拍摄日期</p>
          <p class="text-lg font-semibold mt-1">{formatDate(order.shoot_date)}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">片单 / 照片</p>
          <p class="text-lg font-semibold mt-1">{order.sheet_count} / {order.photo_count}</p>
        </div>
      </div>

      {#if order.notes}
        <div class="card p-4 mt-4">
          <p class="text-sm text-gray-500 mb-2">备注</p>
          <p class="text-gray-800">{order.notes}</p>
        </div>
      {/if}
    </div>

    <div class="card">
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">片单列表</h2>
      </div>
      {#if sheets.length === 0}
        <div class="p-12 text-center text-gray-500">暂无片单数据</div>
      {:else}
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">片单编号</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">照片数量</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">修图状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">锁定状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">修图师</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">选片截止</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            {#each sheets as sheet}
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 text-sm font-medium text-gray-900">{sheet.sheet_no}</td>
                <td class="px-6 py-4 text-sm text-gray-600">{sheet.total_photos}</td>
                <td class="px-6 py-4">
                  <span class="badge {getStatusBadge(retouchStatusMap, sheet.retouch_status).color}">
                    {getStatusBadge(retouchStatusMap, sheet.retouch_status).label}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <span class="badge {getStatusBadge(lockStatusMap, sheet.lock_status).color}">
                    {getStatusBadge(lockStatusMap, sheet.lock_status).label}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">{sheet.retoucher_name || '-'}</td>
                <td class="px-6 py-4 text-sm text-gray-600">{formatDateTime(sheet.selection_deadline)}</td>
                <td class="px-6 py-4">
                  <a href="/sheets/{sheet.id}" class="text-primary-600 hover:text-primary-900 text-sm font-medium">
                    查看详情
                  </a>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>
  {/if}

  {#if showCreateSheet && order}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-auto">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-xl font-semibold text-gray-900">新建片单</h2>
        </div>
        <form on:submit|preventDefault={handleCreateSheet} class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">照片总数</label>
              <input type="number" class="input" bind:value={sheetForm.total_photos} min="0" />
            </div>
            <div>
              <label class="label">可选数量</label>
              <input type="number" class="input" bind:value={sheetForm.selectable_count} min="0" />
            </div>
          </div>
          <div>
            <label class="label">选片截止时间</label>
            <input type="datetime-local" class="input" bind:value={sheetForm.selection_deadline} />
          </div>
          <div>
            <label class="label">备注</label>
            <textarea class="input" rows="3" bind:value={sheetForm.notes}></textarea>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => (showCreateSheet = false)}>
              取消
            </button>
            <button type="submit" class="btn btn-primary flex-1">创建片单</button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</div>
