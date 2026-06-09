<script lang="ts">
  import { onMount } from 'svelte';
  import { ordersApi, usersApi } from '$lib/api';
  import type { OrderListItem, OrderStatus, UserListItem } from '$lib/types';
  import { formatDate, orderStatusMap, getStatusBadge } from '$lib/utils';
  import { getUser } from '$lib/utils/auth';
  import { Plus, Search, Filter } from 'lucide-svelte';

  let orders: OrderListItem[] = [];
  let customers: UserListItem[] = [];
  let loading = true;
  let showCreateModal = false;
  let statusFilter: OrderStatus | '' = '';
  let keyword = '';

  const user = getUser();
  const canCreate = user && ['admin', 'photographer'].includes(user.role);

  let form = {
    customer_id: 0,
    photographer_id: user?.role === 'photographer' ? user.id : undefined as number | undefined,
    shoot_type: '',
    shoot_date: '',
    location: '',
    total_photos: 0,
    included_retouches: 0,
    notes: '',
  };

  async function loadData() {
    loading = true;
    try {
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      orders = await ordersApi.list(params);
      if (canCreate) {
        customers = await usersApi.listCustomers();
      }
    } finally {
      loading = false;
    }
  }

  async function handleCreate() {
    try {
      await ordersApi.create(form);
      showCreateModal = false;
      form = {
        customer_id: 0,
        photographer_id: user?.role === 'photographer' ? user.id : undefined,
        shoot_type: '',
        shoot_date: '',
        location: '',
        total_photos: 0,
        included_retouches: 0,
        notes: '',
      };
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '创建失败');
    }
  }

  $: filteredOrders = orders.filter((o) => {
    if (!keyword) return true;
    const kw = keyword.toLowerCase();
    return (
      o.order_no.toLowerCase().includes(kw) ||
      (o.customer_name || '').toLowerCase().includes(kw) ||
      (o.shoot_type || '').toLowerCase().includes(kw)
    );
  });

  onMount(loadData);
</script>

<div class="p-8">
  <div class="flex items-center justify-between mb-8">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">订单管理</h1>
      <p class="text-gray-500 mt-1">管理所有拍摄订单</p>
    </div>
    {#if canCreate}
      <button class="btn btn-primary" on:click={() => (showCreateModal = true)}>
        <Plus class="w-5 h-5" />
        新建订单
      </button>
    {/if}
  </div>

  <div class="card mb-6 p-4">
    <div class="flex flex-wrap gap-4">
      <div class="flex-1 min-w-[200px]">
        <div class="relative">
          <Search class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            class="input pl-10"
            placeholder="搜索订单号、客户、拍摄类型..."
            bind:value={keyword}
          />
        </div>
      </div>
      <div>
        <div class="relative">
          <Filter class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <select class="input pl-10" bind:value={statusFilter} on:change={loadData}>
            <option value="">全部状态</option>
            {#each Object.entries(orderStatusMap) as [value, { label }]}
              <option value={value}>{label}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>
  </div>

  <div class="card overflow-hidden">
    {#if loading}
      <div class="p-12 text-center text-gray-500">加载中...</div>
    {:else if filteredOrders.length === 0}
      <div class="p-12 text-center text-gray-500">暂无订单数据</div>
    {:else}
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">订单号</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">拍摄类型</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">拍摄日期</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">照片数量</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each filteredOrders as order}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 text-sm font-medium text-gray-900">{order.order_no}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.customer_name || '-'}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.shoot_type || '-'}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{formatDate(order.shoot_date)}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.total_photos}</td>
              <td class="px-6 py-4">
                <span class="badge {getStatusBadge(orderStatusMap, order.status).color}">
                  {getStatusBadge(orderStatusMap, order.status).label}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-500">{formatDate(order.created_at)}</td>
              <td class="px-6 py-4">
                <a href="/orders/{order.id}" class="text-primary-600 hover:text-primary-900 text-sm font-medium">
                  查看详情
                </a>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  {#if showCreateModal}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-auto">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-xl font-semibold text-gray-900">新建订单</h2>
        </div>
        <form on:submit|preventDefault={handleCreate} class="p-6 space-y-4">
          <div>
            <label class="label">客户 <span class="text-red-500">*</span></label>
            <select class="input" bind:value={form.customer_id} required>
              <option value={0}>请选择客户</option>
              {#each customers as c}
                <option value={c.id}>{c.full_name}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="label">拍摄类型</label>
            <input type="text" class="input" bind:value={form.shoot_type} placeholder="如：婚纱照、写真等" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">拍摄日期</label>
              <input type="date" class="input" bind:value={form.shoot_date} />
            </div>
            <div>
              <label class="label">拍摄地点</label>
              <input type="text" class="input" bind:value={form.location} />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">照片总数</label>
              <input type="number" class="input" bind:value={form.total_photos} min="0" />
            </div>
            <div>
              <label class="label">含精修数量</label>
              <input type="number" class="input" bind:value={form.included_retouches} min="0" />
            </div>
          </div>
          <div>
            <label class="label">备注</label>
            <textarea class="input" rows="3" bind:value={form.notes}></textarea>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => (showCreateModal = false)}>
              取消
            </button>
            <button type="submit" class="btn btn-primary flex-1">创建订单</button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</div>
