<script lang="ts">
  import { onMount } from 'svelte';
  import { deliveryApi, usersApi } from '$lib/api';
  import type { DeliveryVersion, UserListItem } from '$lib/types';
  import { formatDateTime } from '$lib/utils';
  import { getUser } from '$lib/utils/auth';
  import { Plus, Shield, Package } from 'lucide-svelte';

  let versions: DeliveryVersion[] = [];
  let customers: UserListItem[] = [];
  let loading = true;
  let showCreateModal = false;

  const user = getUser();
  const canCreate = user && ['admin', 'photographer'].includes(user.role);

  let form = {
    order_id: 0,
    description: '',
    storage_path: '',
    photo_count: 0,
    is_protected: false,
  };

  async function loadData() {
    loading = true;
    try {
      versions = await deliveryApi.list();
    } finally {
      loading = false;
    }
  }

  async function handleCreate() {
    try {
      await deliveryApi.create(form);
      showCreateModal = false;
      form = {
        order_id: 0,
        description: '',
        storage_path: '',
        photo_count: 0,
        is_protected: false,
      };
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '创建失败');
    }
  }

  onMount(loadData);
</script>

<div class="p-8">
  <div class="flex items-center justify-between mb-8">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">交付版本</h1>
      <p class="text-gray-500 mt-1">追踪所有订单的交付版本历史</p>
    </div>
    {#if canCreate}
      <button class="btn btn-primary" on:click={() => (showCreateModal = true)}>
        <Plus class="w-5 h-5" />
        新建交付
      </button>
    {/if}
  </div>

  <div class="card overflow-hidden">
    {#if loading}
      <div class="p-12 text-center text-gray-500">加载中...</div>
    {:else if versions.length === 0}
      <div class="p-12 text-center text-gray-500">暂无交付版本数据</div>
    {:else}
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">订单号</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">版本</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">照片数</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">交付时间</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">说明</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">保护状态</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each versions as v}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 text-sm font-medium text-gray-900">
                <a href="/orders/{v.order_id}" class="text-primary-600 hover:text-primary-900">
                  订单 #{v.order_id}
                </a>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800">
                  <Package class="w-3 h-3 mr-1" />
                  V{v.version}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-gray-600">{v.photo_count} 张</td>
              <td class="px-6 py-4 text-sm text-gray-500">{formatDateTime(v.delivery_date)}</td>
              <td class="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                {v.description || '-'}
              </td>
              <td class="px-6 py-4">
                {#if v.is_protected}
                  <span class="badge bg-amber-100 text-amber-800 flex items-center gap-1">
                    <Shield class="w-3 h-3" />
                    受保护
                  </span>
                {:else}
                  <span class="badge bg-gray-100 text-gray-800">普通</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  {#if showCreateModal}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-xl font-semibold text-gray-900">新建交付版本</h2>
        </div>
        <form on:submit|preventDefault={handleCreate} class="p-6 space-y-4">
          <div>
            <label class="label">订单ID <span class="text-red-500">*</span></label>
            <input type="number" class="input" bind:value={form.order_id} min="1" required />
          </div>
          <div>
            <label class="label">照片数量</label>
            <input type="number" class="input" bind:value={form.photo_count} min="0" />
          </div>
          <div>
            <label class="label">存储路径</label>
            <input type="text" class="input" bind:value={form.storage_path} />
          </div>
          <div>
            <label class="label">说明</label>
            <textarea class="input" rows="3" bind:value={form.description}></textarea>
          </div>
          <div class="flex items-center">
            <input type="checkbox" id="is_protected" class="w-4 h-4" bind:checked={form.is_protected} />
            <label for="is_protected" class="ml-2 text-sm text-gray-700">
              设为受保护版本（不可覆盖/删除）
            </label>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => (showCreateModal = false)}>
              取消
            </button>
            <button type="submit" class="btn btn-primary flex-1">创建交付</button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</div>
