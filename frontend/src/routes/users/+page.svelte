<script lang="ts">
  import { onMount } from 'svelte';
  import { usersApi } from '$lib/api';
  import type { UserListItem, UserRole } from '$lib/types';
  import { userRoleMap, getStatusBadge } from '$lib/utils';
  import { Plus, Search, Filter, UserPlus } from 'lucide-svelte';

  let users: UserListItem[] = [];
  let loading = true;
  let showCreateModal = false;
  let roleFilter: UserRole | '' = '';
  let keyword = '';

  let form = {
    username: '',
    full_name: '',
    email: '',
    password: '',
    phone: '',
    role: 'customer' as UserRole,
  };

  async function loadData() {
    loading = true;
    try {
      const params: any = {};
      if (roleFilter) params.role = roleFilter;
      users = await usersApi.list(params);
    } finally {
      loading = false;
    }
  }

  async function handleCreate() {
    try {
      await usersApi.create(form);
      showCreateModal = false;
      form = {
        username: '',
        full_name: '',
        email: '',
        password: '',
        phone: '',
        role: 'customer',
      };
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '创建失败');
    }
  }

  $: filteredUsers = users.filter((u) => {
    if (!keyword) return true;
    const kw = keyword.toLowerCase();
    return (
      u.username.toLowerCase().includes(kw) ||
      u.full_name.toLowerCase().includes(kw) ||
      (u.email || '').toLowerCase().includes(kw)
    );
  });

  onMount(loadData);
</script>

<div class="p-8">
  <div class="flex items-center justify-between mb-8">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">用户管理</h1>
      <p class="text-gray-500 mt-1">管理系统用户和权限</p>
    </div>
    <button class="btn btn-primary" on:click={() => (showCreateModal = true)}>
      <Plus class="w-5 h-5" />
      新建用户
    </button>
  </div>

  <div class="card mb-6 p-4">
    <div class="flex flex-wrap gap-4">
      <div class="flex-1 min-w-[200px]">
        <div class="relative">
          <Search class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            class="input pl-10"
            placeholder="搜索用户名、姓名、邮箱..."
            bind:value={keyword}
          />
        </div>
      </div>
      <div>
        <div class="relative">
          <Filter class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <select class="input pl-10" bind:value={roleFilter} on:change={loadData}>
            <option value="">全部角色</option>
            {#each Object.entries(userRoleMap) as [value, { label }]}
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
    {:else if filteredUsers.length === 0}
      <div class="p-12 text-center text-gray-500">暂无用户数据</div>
    {:else}
      <table class="w-full">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户名</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">姓名</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">邮箱</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">角色</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each filteredUsers as u}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 text-sm font-medium text-gray-900">{u.username}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{u.full_name}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{u.email || '-'}</td>
              <td class="px-6 py-4">
                <span class="badge {getStatusBadge(userRoleMap, u.role).color}">
                  {getStatusBadge(userRoleMap, u.role).label}
                </span>
              </td>
              <td class="px-6 py-4">
                {#if u.is_active}
                  <span class="badge bg-green-100 text-green-800">启用</span>
                {:else}
                  <span class="badge bg-red-100 text-red-800">禁用</span>
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
      <div class="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-auto">
        <div class="p-6 border-b border-gray-200 flex items-center gap-2">
          <UserPlus class="w-5 h-5 text-primary-600" />
          <h2 class="text-xl font-semibold text-gray-900">新建用户</h2>
        </div>
        <form on:submit|preventDefault={handleCreate} class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">用户名 <span class="text-red-500">*</span></label>
              <input type="text" class="input" bind:value={form.username} required />
            </div>
            <div>
              <label class="label">密码 <span class="text-red-500">*</span></label>
              <input type="password" class="input" bind:value={form.password} minlength="6" required />
            </div>
          </div>
          <div>
            <label class="label">姓名 <span class="text-red-500">*</span></label>
            <input type="text" class="input" bind:value={form.full_name} required />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">邮箱</label>
              <input type="email" class="input" bind:value={form.email} />
            </div>
            <div>
              <label class="label">电话</label>
              <input type="text" class="input" bind:value={form.phone} />
            </div>
          </div>
          <div>
            <label class="label">角色</label>
            <select class="input" bind:value={form.role}>
              {#each Object.entries(userRoleMap) as [value, { label }]}
                <option value={value}>{label}</option>
              {/each}
            </select>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => (showCreateModal = false)}>
              取消
            </button>
            <button type="submit" class="btn btn-primary flex-1">创建用户</button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</div>
