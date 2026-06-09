<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';
  import { isAuthenticated, getUser, clearAuth } from '$lib/utils/auth';
  import { goto } from '$app/navigation';
  import { userRoleMap } from '$lib/utils';
  import {
    LayoutDashboard,
    FolderKanban,
    Image,
    Package,
    Users,
    LogOut,
    Camera,
  } from 'lucide-svelte';

  let user = getUser();
  let isLoggedIn = isAuthenticated();

  const navItems = [
    { path: '/', label: '数据看板', icon: LayoutDashboard, roles: ['admin', 'photographer', 'retoucher', 'customer'] },
    { path: '/orders', label: '订单管理', icon: FolderKanban, roles: ['admin', 'photographer', 'retoucher', 'customer'] },
    { path: '/sheets', label: '片单管理', icon: Image, roles: ['admin', 'photographer', 'retoucher', 'customer'] },
    { path: '/delivery', label: '交付版本', icon: Package, roles: ['admin', 'photographer', 'retoucher', 'customer'] },
    { path: '/users', label: '用户管理', icon: Users, roles: ['admin'] },
  ];

  function canAccess(path: string): boolean {
    if (!user) return false;
    const item = navItems.find((i) => i.path === path);
    if (!item) return true;
    return item.roles.includes(user.role);
  }

  function handleLogout() {
    clearAuth();
    goto('/login');
  }
</script>

{#if $page.url.pathname.startsWith('/login')}
  <slot />
{:else if isLoggedIn}
  <div class="min-h-screen bg-gray-50 flex">
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div class="h-16 flex items-center px-6 border-b border-gray-200">
        <Camera class="w-8 h-8 text-primary-600" />
        <span class="ml-3 text-lg font-bold text-gray-900">摄影工作室</span>
      </div>
      <nav class="flex-1 px-4 py-6 space-y-1">
        {#each navItems as item}
          {#if canAccess(item.path)}
            <a
              href={item.path}
              class="flex items-center px-4 py-2.5 text-sm font-medium rounded-lg transition-colors {
                $page.url.pathname === item.path
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }"
            >
              <svelte:component this={item.icon} class="w-5 h-5 mr-3" />
              {item.label}
            </a>
          {/if}
        {/each}
      </nav>
      <div class="p-4 border-t border-gray-200">
        <div class="flex items-center px-2 py-3">
          <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-semibold">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div class="ml-3 flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
            <p class="text-xs text-gray-500">
              <span class="badge {userRoleMap[user?.role || 'customer'].color}">
                {userRoleMap[user?.role || 'customer'].label}
              </span>
            </p>
          </div>
        </div>
        <button on:click={handleLogout} class="btn btn-secondary w-full mt-2 text-sm">
          <LogOut class="w-4 h-4" />
          退出登录
        </button>
      </div>
    </aside>
    <main class="flex-1 overflow-auto">
      <slot />
    </main>
  </div>
{:else}
  <slot />
{/if}
