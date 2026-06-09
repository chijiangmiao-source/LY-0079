<script lang="ts">
  import { onMount } from 'svelte';
  import { reviewsApi, usersApi } from '$lib/api';
  import type { CustomerReviewDetail, UserListItem } from '$lib/types';
  import { formatDateTime } from '$lib/utils';
  import { Star, Search, Filter, MessageSquare, User as UserIcon, Camera } from 'lucide-svelte';
  import { getUser, isAuthenticated } from '$lib/utils/auth';

  let reviews: CustomerReviewDetail[] = [];
  let photographers: UserListItem[] = [];
  let loading = true;
  let user = getUser();

  let filters = {
    rating_min: '' as string,
    rating_max: '' as string,
    photographer_id: '' as string,
    order_no: '' as string,
  };

  async function loadData() {
    loading = true;
    try {
      const params: any = {};
      if (filters.rating_min) params.rating_min = parseInt(filters.rating_min);
      if (filters.rating_max) params.rating_max = parseInt(filters.rating_max);
      if (filters.photographer_id) params.photographer_id = parseInt(filters.photographer_id);

      let list = await reviewsApi.listCustomerReviews(params);
      if (filters.order_no) {
        list = list.filter((r) => (r.order_no || '').toLowerCase().includes(filters.order_no.toLowerCase()));
      }
      reviews = list;
    } finally {
      loading = false;
    }
  }

  function renderStars(count: number) {
    let html = '';
    for (let i = 0; i < 5; i++) {
      html += i < count ? '★' : '☆';
    }
    return html;
  }

  onMount(async () => {
    try {
      if (user && (user.role === 'admin' || user.role === 'photographer')) {
        photographers = await usersApi.listPhotographers();
      }
    } catch (e) {}
    await loadData();
  });
</script>

<div class="p-8">
  <div class="mb-6">
    <h1 class="text-2xl font-bold text-gray-900 flex items-center">
      <Star class="w-7 h-7 mr-3 text-yellow-500" />
      客户评价
    </h1>
    <p class="text-gray-500 mt-1">查看和管理客户提交的评价反馈</p>
  </div>

  {#if user && (user.role === 'admin' || user.role === 'photographer')}
    <div class="card p-5 mb-6">
      <div class="flex items-center gap-2 mb-4">
        <Filter class="w-5 h-5 text-gray-500" />
        <span class="font-medium text-gray-700">筛选条件</span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label class="label">最低评分</label>
          <select class="input" bind:value={filters.rating_min}>
            <option value="">不限</option>
            <option value="1">1星及以上</option>
            <option value="2">2星及以上</option>
            <option value="3">3星及以上</option>
            <option value="4">4星及以上</option>
            <option value="5">5星</option>
          </select>
        </div>
        <div>
          <label class="label">最高评分</label>
          <select class="input" bind:value={filters.rating_max}>
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
            filters = { rating_min: '', rating_max: '', photographer_id: '', order_no: '' };
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
    {:else if reviews.length === 0}
      <div class="p-12 text-center text-gray-500">暂无评价数据</div>
    {:else}
      <div class="divide-y divide-gray-200">
        {#each reviews as r}
          <div class="p-6 hover:bg-gray-50 transition-colors">
            <div class="flex items-start justify-between gap-4 flex-wrap">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-3 flex-wrap">
                  <a
                    href="/orders/{r.order_id}"
                    class="text-primary-600 hover:text-primary-900 font-medium"
                  >
                    {r.order_no}
                  </a>
                  <div class="flex items-center gap-0.5">
                    {#each Array(5) as _, i}
                      <Star
                        class={`w-5 h-5 ${i < r.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                      />
                    {/each}
                    <span class="ml-1 text-sm font-semibold text-gray-700">{r.rating}/5</span>
                  </div>
                  {#if r.is_anonymous}
                    <span class="badge bg-gray-100 text-gray-600">匿名评价</span>
                  {/if}
                </div>
                <div class="flex items-center gap-4 mt-2 text-sm text-gray-500 flex-wrap">
                  <div class="flex items-center">
                    <UserIcon class="w-4 h-4 mr-1" />
                    {r.customer_name || '匿名用户'}
                  </div>
                  {#if r.photographer_name}
                    <div class="flex items-center">
                      <Camera class="w-4 h-4 mr-1" />
                      {r.photographer_name}
                    </div>
                  {/if}
                  <div class="flex items-center">
                    <MessageSquare class="w-4 h-4 mr-1" />
                    {formatDateTime(r.submitted_at)}
                  </div>
                </div>
                {#if r.tags}
                  <div class="mt-3 flex flex-wrap gap-2">
                    {#each r.tags.split(',').filter((t) => t.trim()) as tag}
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                        {tag.trim()}
                      </span>
                    {/each}
                  </div>
                {/if}
                {#if r.feedback}
                  <p class="mt-3 text-gray-700 leading-relaxed whitespace-pre-wrap">{r.feedback}</p>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
