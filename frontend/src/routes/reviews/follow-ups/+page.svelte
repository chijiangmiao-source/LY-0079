<script lang="ts">
  import { onMount } from 'svelte';
  import { reviewsApi, usersApi } from '$lib/api';
  import type { FollowUpListItem, FollowUpStatus, UserListItem } from '$lib/types';
  import {
    formatDate,
    formatDateTime,
    followUpStatusMap,
    getStatusBadge,
  } from '$lib/utils';
  import { ArrowLeft, Search, Filter, Star, MessageSquare, Calendar } from 'lucide-svelte';

  let records: FollowUpListItem[] = [];
  let photographers: UserListItem[] = [];
  let loading = true;

  let filters = {
    status: '' as FollowUpStatus | '',
    satisfaction_min: '' as string,
    satisfaction_max: '' as string,
    photographer_id: '' as string,
    order_no: '' as string,
  };

  async function loadData() {
    loading = true;
    try {
      const params: any = {};
      if (filters.status) params.status = filters.status;
      if (filters.satisfaction_min) params.satisfaction_min = parseInt(filters.satisfaction_min);
      if (filters.satisfaction_max) params.satisfaction_max = parseInt(filters.satisfaction_max);
      if (filters.photographer_id) params.photographer_id = parseInt(filters.photographer_id);

      let list = await reviewsApi.listFollowUps(params);
      if (filters.order_no) {
        list = list.filter((r) => r.order_no.toLowerCase().includes(filters.order_no.toLowerCase()));
      }
      records = list;
    } finally {
      loading = false;
    }
  }

  function renderStars(count?: number) {
    if (!count) return '-';
    return '★'.repeat(count) + '☆'.repeat(5 - count);
  }

  onMount(async () => {
    try {
      photographers = await usersApi.listPhotographers();
    } catch (e) {}
    await loadData();
  });
</script>

<div class="p-8">
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-gray-900 flex items-center">
      <MessageSquare class="w-7 h-7 mr-3 text-primary-600" />
      回访管理
    </h1>
    <p class="text-gray-500 mt-1">管理订单交付后的客户回访记录</p>
  </div>

  <div class="card p-5 mb-6">
    <div class="flex items-center gap-2 mb-4">
      <Filter class="w-5 h-5 text-gray-500" />
      <span class="font-medium text-gray-700">筛选条件</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      <div>
        <label class="label">回访状态</label>
        <select class="input" bind:value={filters.status}>
          <option value="">全部状态</option>
          <option value="pending">待回访</option>
          <option value="in_progress">回访中</option>
          <option value="completed">已完成</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>
      <div>
        <label class="label">最低满意度</label>
        <select class="input" bind:value={filters.satisfaction_min}>
          <option value="">不限</option>
          <option value="1">1星及以上</option>
          <option value="2">2星及以上</option>
          <option value="3">3星及以上</option>
          <option value="4">4星及以上</option>
          <option value="5">5星</option>
        </select>
      </div>
      <div>
        <label class="label">最高满意度</label>
        <select class="input" bind:value={filters.satisfaction_max}>
          <option value="">不限</option>
          <option value="1">1星</option>
          <option value="2">2星及以下</option>
          <option value="3">3星及以下</option>
          <option value="4">4星及以下</option>
          <option value="5">5星及以下</option>
        </select>
      </div>
      <div>
        <label class="label">摄影师</label>
        <select class="input" bind:value={filters.photographer_id}>
          <option value="">全部摄影师</option>
          {#each photographers as p}
            <option value={p.id}>{p.full_name}</option>
          {/each}
        </select>
      </div>
      <div>
        <label class="label">订单号</label>
        <div class="relative">
          <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input class="input pl-9" placeholder="搜索订单号" bind:value={filters.order_no} />
        </div>
      </div>
    </div>
    <div class="flex gap-3 mt-4">
      <button class="btn btn-primary" on:click={loadData}>
        <Search class="w-4 h-4" />
        筛选
      </button>
      <button
        class="btn btn-secondary"
        on:click={() => {
          filters = { status: '', satisfaction_min: '', satisfaction_max: '', photographer_id: '', order_no: '' };
          loadData();
        }}
      >
        重置
      </button>
    </div>
  </div>

  <div class="card">
    {#if loading}
      <div class="p-12 text-center text-gray-500">加载中...</div>
    {:else if records.length === 0}
      <div class="p-12 text-center text-gray-500">暂无回访记录</div>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">订单号</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">摄影师</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">拍摄日期</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">回访状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">回访满意度</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户评分</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">评价截止</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">回访时间</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            {#each records as r}
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 text-sm font-medium text-gray-900">
                  <a href="/orders/{r.order_id}" class="text-primary-600 hover:text-primary-900">
                    {r.order_no}
                  </a>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">{r.customer_name || '-'}</td>
                <td class="px-6 py-4 text-sm text-gray-600">{r.photographer_name || '-'}</td>
                <td class="px-6 py-4 text-sm text-gray-600">{formatDate(r.shoot_date)}</td>
                <td class="px-6 py-4">
                  <span class="badge {getStatusBadge(followUpStatusMap, r.status).color}">
                    {getStatusBadge(followUpStatusMap, r.status).label}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-yellow-600 font-medium">
                  {renderStars(r.satisfaction)}
                </td>
                <td class="px-6 py-4 text-sm text-yellow-600 font-medium">
                  {renderStars(r.customer_rating)}
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">
                  <div class="flex items-center">
                    <Calendar class="w-4 h-4 mr-1 text-gray-400" />
                    {formatDateTime(r.review_deadline, 'MM-DD')}
                  </div>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">{formatDateTime(r.follow_up_time, 'MM-DD HH:mm')}</td>
                <td class="px-6 py-4">
                  <a href="/reviews/follow-ups/{r.id}" class="text-primary-600 hover:text-primary-900 text-sm font-medium">
                    查看详情
                  </a>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>
