<script lang="ts">
  import { onMount } from 'svelte';
  import { sheetsApi, usersApi } from '$lib/api';
  import type { PhotoSheetListItem, LockStatus, RetouchStatus, UserListItem } from '$lib/types';
  import {
    formatDateTime,
    retouchStatusMap,
    lockStatusMap,
    getStatusBadge,
    isOverdue,
  } from '$lib/utils';
  import { Search, Filter, AlertTriangle } from 'lucide-svelte';

  let sheets: PhotoSheetListItem[] = [];
  let retouchers: UserListItem[] = [];
  let loading = true;
  let lockFilter: LockStatus | '' = '';
  let retouchFilter: RetouchStatus | '' = '';
  let retoucherFilter: number | '' = '';
  let keyword = '';

  async function loadData() {
    loading = true;
    try {
      const params: any = {};
      if (lockFilter) params.lock_status = lockFilter;
      if (retouchFilter) params.retouch_status = retouchFilter;
      if (retoucherFilter) params.retoucher_id = retoucherFilter;
      sheets = await sheetsApi.list(params);
      retouchers = await usersApi.listRetouchers();
    } finally {
      loading = false;
    }
  }

  $: filteredSheets = sheets.filter((s) => {
    if (!keyword) return true;
    const kw = keyword.toLowerCase();
    return (
      s.sheet_no.toLowerCase().includes(kw) ||
      (s.order_no || '').toLowerCase().includes(kw) ||
      (s.retoucher_name || '').toLowerCase().includes(kw)
    );
  });

  onMount(loadData);
</script>

<div class="p-8">
  <div class="mb-8">
    <h1 class="text-2xl font-bold text-gray-900">片单管理</h1>
    <p class="text-gray-500 mt-1">管理所有片单、修图进度和选片状态</p>
  </div>

  <div class="card mb-6 p-4">
    <div class="flex flex-wrap gap-4">
      <div class="flex-1 min-w-[200px]">
        <div class="relative">
          <Search class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            class="input pl-10"
            placeholder="搜索片单号、订单号、修图师..."
            bind:value={keyword}
          />
        </div>
      </div>
      <div>
        <div class="relative">
          <Filter class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <select class="input pl-10" bind:value={lockFilter} on:change={loadData}>
            <option value="">全部锁定状态</option>
            {#each Object.entries(lockStatusMap) as [value, { label }]}
              <option value={value}>{label}</option>
            {/each}
          </select>
        </div>
      </div>
      <div>
        <div class="relative">
          <Filter class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <select class="input pl-10" bind:value={retouchFilter} on:change={loadData}>
            <option value="">全部修图状态</option>
            {#each Object.entries(retouchStatusMap) as [value, { label }]}
              <option value={value}>{label}</option>
            {/each}
          </select>
        </div>
      </div>
      <div>
        <div class="relative">
          <Filter class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <select class="input pl-10" bind:value={retoucherFilter} on:change={loadData}>
            <option value="">全部修图师</option>
            {#each retouchers as r}
              <option value={r.id}>{r.full_name}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>
  </div>

  <div class="card overflow-hidden">
    {#if loading}
      <div class="p-12 text-center text-gray-500">加载中...</div>
    {:else if filteredSheets.length === 0}
      <div class="p-12 text-center text-gray-500">暂无片单数据</div>
    {:else}
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">片单编号</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">所属订单</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">照片数</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">修图状态</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">锁定状态</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">修图师</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">选片截止</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each filteredSheets as sheet}
            {@const overdue = isOverdue(sheet.selection_deadline) && sheet.lock_status !== 'locked'}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 text-sm font-medium text-gray-900">
                {sheet.sheet_no}
                {#if overdue}
                  <AlertTriangle class="w-4 h-4 text-red-500 inline ml-1" />
                {/if}
              </td>
              <td class="px-6 py-4 text-sm text-gray-600">{sheet.order_no || '-'}</td>
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
              <td class="px-6 py-4 text-sm {overdue ? 'text-red-600 font-medium' : 'text-gray-500'}">
                {formatDateTime(sheet.selection_deadline)}
              </td>
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
</div>
