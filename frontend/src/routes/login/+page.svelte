<script lang="ts">
  import { goto } from '$app/navigation';
  import { authApi } from '$lib/api/auth';
  import { setToken, setUser } from '$lib/utils/auth';
  import { Camera } from 'lucide-svelte';

  let username = '';
  let password = '';
  let loading = false;
  let error = '';

  async function handleLogin(e: Event) {
    e.preventDefault();
    loading = true;
    error = '';
    try {
      const token = await authApi.login({ username, password });
      setToken(token.access_token);
      const user = await authApi.me();
      setUser(user);
      goto('/');
    } catch (err: any) {
      error = err?.response?.data?.detail || '登录失败，请检查用户名和密码';
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-purple-50 p-4">
  <div class="w-full max-w-md">
    <div class="text-center mb-8">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-4">
        <Camera class="w-8 h-8 text-primary-600" />
      </div>
      <h1 class="text-2xl font-bold text-gray-900">摄影工作室管理系统</h1>
      <p class="text-gray-500 mt-2">请登录以继续</p>
    </div>
    <form on:submit={handleLogin} class="card p-8 space-y-6">
      {#if error}
        <div class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">{error}</div>
      {/if}
      <div>
        <label class="label">用户名</label>
        <input
          type="text"
          class="input"
          bind:value={username}
          placeholder="请输入用户名"
          required
        />
      </div>
      <div>
        <label class="label">密码</label>
        <input
          type="password"
          class="input"
          bind:value={password}
          placeholder="请输入密码"
          required
        />
      </div>
      <button type="submit" class="btn btn-primary w-full" disabled={loading}>
        {loading ? '登录中...' : '登 录'}
      </button>
    </form>
    <div class="text-center mt-6 text-sm text-gray-500">
      <p>默认账号: admin / admin123</p>
    </div>
  </div>
</div>
