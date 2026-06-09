<script lang="ts">
  import { onMount } from 'svelte';
  import { complaintsApi, usersApi, ordersApi } from '$lib/api';
  import type { ComplaintTicketListItem, ComplaintType, ComplaintStatus, UserListItem, OrderListItem } from '$lib/types';
  import {
    formatDate,
    formatDateTime,
    complaintStatusMap,
    complaintTypeMap,
    complaintSourceMap,
    getStatusBadge,
  } from '$lib/utils';
  import { AlertOctagon, Search, Filter, User as UserIcon, Camera, Clock, AlertTriangle, CheckCircle, DollarSign } from 'lucide-svelte';
  import { getUser, isAuthenticated } from '$lib/utils/auth';
  import { goto } from '$app/navigation';

  let records: ComplaintTicketListItem[] = [];
  let photographers: UserListItem[] = [];
  let customerOrders: OrderListItem[] = [];
  let loading = true;
  let user = getUser();

  let filters = {
    complaint_type: '' as ComplaintType | '',
    status: '' as ComplaintStatus | '',
    photographer_id: '' as string,
    has_compensation: '' as string,
    order_no: '' as string,
  };

  let showCreateModal = false;
  let newComplaint = {
    order_id: 0,
    complaint_type: 'other' as ComplaintType,
    title: '',
    description: '',
  };

  async function loadData() {
    loading = true;
    try {
      const params: any = {};
      if (filters.complaint_type) params.complaint_type = filters.complaint_type;
      if (filters.status) params.status = filters.status;
      if (filters.photographer_id) params.photographer_id = parseInt(filters.photographer_id);
      if (filters.has_compensation !== '') params.has_compensation = filters.has_compensation === 'true';

      let list = await complaintsApi.list(params);
      if (filters.order_no) {
        list = list.filter((r) => (r.order_no || '').toLowerCase().includes(filters.order_no.toLowerCase()));
      }
      records = list;
    } finally {
      loading = false;
    }
  }

  async function createComplaint() {
    if (!newComplaint.order_id || !newComplaint.title || !newComplaint.description) {
      alert('请填写完整的投诉信息');
      return;
    }
    try {
      await complaintsApi.create(newComplaint);
      showCreateModal = false;
      newComplaint = { order_id: 0, complaint_type: 'other', title: '', description: '' };
      await loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || '创建投诉工单失败');
    }
  }

  onMount(async () => {
    try {
      if (user && (user.role === 'admin' || user.role === 'photographer')) {
        photographers = await usersApi.listPhotographers();
      }
      if (user && user.role === 'customer') {
        customerOrders = await ordersApi.list({ skip: 0, limit: 100 });
      }
    } catch (e) {}
    await loadData();
  });
</script>

<div class="p-8">
  <div class="mb-6 flex items-center justify-between flex-wrap gap-3">
    <div>
      <h1 class="text-2xl font-bold text-gray-900 flex items-center">
        <AlertOctagon class="w-7 h-7 mr-3 text-red-600" />
        投诉工单管理
      </h1>
      <p class="text-gray-500 mt-1">管理客户投诉工单、处理进度和服务补偿</p>
    </div>
    <button class="btn btn-primary" on:click={() => (showCreateModal = true)}>
      <AlertOctagon class="w-4 h-4" />
      新建投诉
    </button>
  </div>

  {#if user && (user.role === 'admin' || user.role === 'photographer')}
    <div class="card p-5 mb-6">
      <div class="flex items-center gap-2 mb-4">
        <Filter class="w-5 h-5 text-gray-500" />
        <span class="font-medium text-gray-700">筛选条件</span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div>
          <label class="label">投诉类型</label>
          <select class="input" bind:value={filters.complaint_type}>
            <option value="">全部类型</option>
            <option value="quality">照片质量</option>
            <option value="service">服务问题</option>
            <option value="delivery">交付延迟</option>
            <option value="attitude">态度问题</option>
            <option value="other">其他问题</option>
          </select>
        </div>
        <div>
          <label class="label">处理状态</label>
          <select class="input" bind:value={filters.status}>
            <option value="">全部状态</option>
            <option value="pending">待处理</option>
            <option value="assigned">已分配</option>
            <option value="processing">处理中</option>
            <option value="compensated">已补偿</option>
            <option value="resolved">已解决</option>
            <option value="closed">已关闭</option>
            <option value="cancelled">已取消</option>
          </select>
        </div>
        <div>
          <label class="label">责任摄影师</label>
          <select class="input" bind:value={filters.photographer_id}>
            <option value="">全部摄影师</option>
            {#each photographers as p}
              <option value={p.id}>{p.full_name}</option>
            {/each}
          </select>
        </div>
        <div>
          <label class="label">补偿状态</label>
          <select class="input" bind:value={filters.has_compensation}>
            <option value="">全部</option>
            <option value="true">已补偿</option>
            <option value="false">未补偿</option>
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
            filters = { complaint_type: '', status: '', photographer_id: '', has_compensation: '', order_no: '' };
            loadData();
          }}
        >
          重置
        </button>
      </div>
    </div>
  {/if}

  <div class="card">
    {#if loading}
      <div class="p-12 text-center text-gray-500">加载中...</div>
    {:else if records.length === 0}
      <div class="p-12 text-center text-gray-500">暂无投诉工单</div>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">工单编号</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">订单号</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">摄影师</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">投诉类型</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">来源</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">标题</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">处理人</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">处理状态</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">截止时间</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">补偿</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            {#each records as r}
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 text-sm font-medium text-gray-900">
                  <div class="flex items-center gap-2">
                    {r.ticket_no}
                    {#if r.is_overdue}
                      <AlertTriangle class="w-4 h-4 text-red-500" />
                    {/if}
                  </div>
                </td>
                <td class="px-6 py-4 text-sm">
                  <a href="/orders/{r.order_id}" class="text-primary-600 hover:text-primary-900">
                    {r.order_no}
                  </a>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">
                  <div class="flex items-center">
                    <UserIcon class="w-4 h-4 mr-1 text-gray-400" />
                    {r.customer_name || '-'}
                  </div>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">
                  <div class="flex items-center">
                    <Camera class="w-4 h-4 mr-1 text-gray-400" />
                    {r.photographer_name || '-'}
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span class="badge {getStatusBadge(complaintTypeMap, r.complaint_type).color}">
                    {getStatusBadge(complaintTypeMap, r.complaint_type).label}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <span class="badge {getStatusBadge(complaintSourceMap, r.source).color}">
                    {getStatusBadge(complaintSourceMap, r.source).label}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title={r.title}>
                  {r.title}
                </td>
                <td class="px-6 py-4 text-sm text-gray-600">{r.assignee_name || '-'}</td>
                <td class="px-6 py-4">
                  <span class="badge {getStatusBadge(complaintStatusMap, r.status).color}">
                    {getStatusBadge(complaintStatusMap, r.status).label}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm">
                  <div class="flex items-center">
                    <Clock class="w-4 h-4 mr-1 {r.is_overdue ? 'text-red-500' : 'text-gray-400'}" />
                    <span class={r.is_overdue ? 'text-red-600 font-medium' : 'text-gray-600'}>
                      {formatDateTime(r.process_deadline, 'MM-DD HH:mm')}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  {#if r.has_compensation}
                    <span class="badge bg-green-100 text-green-800">已补偿</span>
                  {:else}
                    <span class="text-gray-400 text-sm">-</span>
                  {/if}
                </td>
                <td class="px-6 py-4">
                  <a href="/complaints/{r.id}" class="text-primary-600 hover:text-primary-900 text-sm font-medium">
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

{#if showCreateModal}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-lg">
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">新建投诉工单</h2>
      </div>
      <div class="p-6 space-y-4">
        {#if user?.role === 'customer'}
          <div>
            <label class="label">关联订单</label>
            <select class="input" bind:value={newComplaint.order_id}>
              <option value={0}>请选择订单</option>
              {#each customerOrders as o}
                <option value={o.id}>{o.order_no} - {formatDate(o.shoot_date)}</option>
              {/each}
            </select>
          </div>
        {:else}
          <div>
            <label class="label">订单ID</label>
            <input class="input" type="number" bind:value={newComplaint.order_id} placeholder="请输入订单ID" />
          </div>
        {/if}
        <div>
          <label class="label">投诉类型</label>
          <select class="input" bind:value={newComplaint.complaint_type}>
            <option value="quality">照片质量</option>
            <option value="service">服务问题</option>
            <option value="delivery">交付延迟</option>
            <option value="attitude">态度问题</option>
            <option value="other">其他问题</option>
          </select>
        </div>
        <div>
          <label class="label">投诉标题</label>
          <input class="input" bind:value={newComplaint.title} placeholder="请简要描述投诉问题" />
        </div>
        <div>
          <label class="label">详细描述</label>
          <textarea class="input h-32" bind:value={newComplaint.description} placeholder="请详细描述投诉内容..."></textarea>
        </div>
      </div>
      <div class="p-6 border-t border-gray-200 flex justify-end gap-3">
        <button class="btn btn-secondary" on:click={() => (showCreateModal = false)}>取消</button>
        <button class="btn btn-primary" on:click={createComplaint}>提交投诉</button>
      </div>
    </div>
  </div>
{/if}
