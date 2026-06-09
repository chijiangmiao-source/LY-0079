<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { ordersApi, sheetsApi, reviewsApi } from '$lib/api';
  import type { OrderDetail, PhotoSheetListItem, CustomerReviewDetail } from '$lib/types';
  import {
    formatDate,
    formatDateTime,
    orderStatusMap,
    retouchStatusMap,
    lockStatusMap,
    getStatusBadge,
  } from '$lib/utils';
  import { getUser } from '$lib/utils/auth';
  import { ArrowLeft, Plus, X, Star, Send, AlertCircle, CheckCircle2 } from 'lucide-svelte';

  let order: OrderDetail | null = null;
  let sheets: PhotoSheetListItem[] = [];
  let loading = true;
  let showCreateSheet = false;
  let sheetFormErrors: Record<string, string> = {};
  let user = getUser();
  let customerReview: CustomerReviewDetail | null = null;
  let showReviewForm = false;
  let savingReview = false;
  let reviewError = '';

  let reviewForm = {
    rating: 0,
    tags: '',
    feedback: '',
    is_anonymous: false,
  };

  let sheetForm = {
    total_photos: 0,
    selectable_count: 0,
    selection_deadline: '',
    retoucher_id: undefined as number | undefined,
    notes: '',
  };

  function validateSheetForm(): boolean {
    sheetFormErrors = {};
    if (sheetForm.total_photos < 0) {
      sheetFormErrors.total_photos = '照片总数不能为负数';
    }
    if (sheetForm.selectable_count < 0) {
      sheetFormErrors.selectable_count = '可选数量不能为负数';
    }
    if (sheetForm.selectable_count > sheetForm.total_photos) {
      sheetFormErrors.selectable_count = '可选数量不能超过照片总数';
    }
    return Object.keys(sheetFormErrors).length === 0;
  }

  async function loadData() {
    loading = true;
    try {
      const id = parseInt($page.params.id || '0');
      order = await ordersApi.get(id);
      const newSheets = await sheetsApi.list({ order_id: id });
      sheets = newSheets;

      if (order?.status === 'delivered') {
        try {
          const reviews = await reviewsApi.listCustomerReviews({ order_id: id });
          if (reviews.length > 0) {
            customerReview = reviews[0];
          }
        } catch (e) {}
      }
    } finally {
      loading = false;
    }
  }

  function setReviewRating(val: number) {
    reviewForm.rating = val;
  }

  async function handleSubmitReview() {
    if (reviewForm.rating === 0) {
      reviewError = '请选择评分';
      return;
    }
    savingReview = true;
    reviewError = '';
    try {
      const id = parseInt($page.params.id || '0');
      const data: any = {
        order_id: id,
        rating: reviewForm.rating,
        is_anonymous: reviewForm.is_anonymous,
      };
      if (reviewForm.tags.trim()) data.tags = reviewForm.tags.trim();
      if (reviewForm.feedback.trim()) data.feedback = reviewForm.feedback.trim();

      await reviewsApi.createCustomerReview(data);
      showReviewForm = false;
      reviewForm = { rating: 0, tags: '', feedback: '', is_anonymous: false };
      await loadData();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      reviewError = typeof detail === 'string' ? detail : '提交失败，请重试';
    } finally {
      savingReview = false;
    }
  }

  async function handleCreateSheet() {
    if (!validateSheetForm()) return;
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
      sheetFormErrors = {};
      await loadData();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') {
        alert(detail);
      } else if (Array.isArray(detail)) {
        alert(detail.map((e: any) => e.msg || JSON.stringify(e)).join('\n'));
      } else {
        alert('创建片单失败');
      }
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
      <div class="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl font-bold text-gray-900">
              {order.order_no}
              <span class="ml-3 badge {getStatusBadge(orderStatusMap, order.status).color}">
                {getStatusBadge(orderStatusMap, order.status).label}
              </span>
            </h1>
          </div>
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
          <p class="text-lg font-semibold mt-1">{sheets.length} / {sheets.reduce((sum, s) => sum + s.total_photos, 0)}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">服务套餐</p>
          <p class="text-lg font-semibold mt-1">{order.service_package || '-'}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">拍摄类型</p>
          <p class="text-lg font-semibold mt-1">{order.shoot_type || '-'}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">拍摄城市</p>
          <p class="text-lg font-semibold mt-1">{order.city || '-'}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">拍摄时间段</p>
          <p class="text-lg font-semibold mt-1">
            {#if order.shoot_time_start && order.shoot_time_end}
              {formatDateTime(order.shoot_time_start, 'HH:mm')} - {formatDateTime(order.shoot_time_end, 'HH:mm')}
            {:else if order.shoot_time_start}
              {formatDateTime(order.shoot_time_start, 'HH:mm')}
            {:else}
              -
            {/if}
          </p>
        </div>
      </div>
      {#if order.location}
        <div class="card p-4 mt-4">
          <p class="text-sm text-gray-500 mb-2">拍摄地点</p>
          <p class="text-gray-800">{order.location}</p>
        </div>
      {/if}

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
            {#each sheets as sheet (sheet.id)}
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

    {#if order && order.status === 'delivered'}
      <div class="card mt-6">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between flex-wrap gap-3">
          <h2 class="text-lg font-semibold text-gray-900 flex items-center">
            <Star class="w-5 h-5 mr-2 text-yellow-500" />
            客户评价
          </h2>
          {#if !customerReview && user?.role === 'customer' && !showReviewForm}
            <button class="btn btn-primary" on:click={() => (showReviewForm = true)}>
              <Send class="w-4 h-4" />
              提交评价
            </button>
          {/if}
        </div>
        <div class="p-6">
          {#if customerReview}
            <div class="space-y-4">
              <div class="flex items-center gap-2">
                {#each Array(5) as _, i}
                  <Star
                    class={`w-6 h-6 ${i < customerReview.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                  />
                {/each}
                <span class="ml-2 text-lg font-semibold text-gray-900">{customerReview.rating}/5</span>
                {#if customerReview.is_anonymous}
                  <span class="badge bg-gray-100 text-gray-600">匿名评价</span>
                {/if}
              </div>
              <p class="text-sm text-gray-500">提交时间: {formatDateTime(customerReview.submitted_at)}</p>
              {#if customerReview.tags}
                <div class="flex flex-wrap gap-2">
                  {#each customerReview.tags.split(',').filter((t) => t.trim()) as tag}
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                      {tag.trim()}
                    </span>
                  {/each}
                </div>
              {/if}
              {#if customerReview.feedback}
                <p class="text-gray-700 leading-relaxed whitespace-pre-wrap">{customerReview.feedback}</p>
              {/if}
            </div>
          {:else if showReviewForm && user?.role === 'customer'}
            {#if reviewError}
              <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center">
                <AlertCircle class="w-5 h-5 mr-2" />
                {reviewError}
              </div>
            {/if}
            <div class="space-y-4">
              <div>
                <label class="label">整体评分 <span class="text-red-500">*</span></label>
                <div class="flex items-center gap-2 py-2">
                  {#each Array(5) as _, i}
                    <button
                      type="button"
                      class="focus:outline-none transition-transform hover:scale-110"
                      on:click={() => setReviewRating(i + 1)}
                    >
                      <Star
                        class={`w-9 h-9 ${i < reviewForm.rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300 hover:text-yellow-300'}`}
                      />
                    </button>
                  {/each}
                  {#if reviewForm.rating > 0}
                    <span class="ml-2 text-lg font-semibold text-gray-700">{reviewForm.rating}/5</span>
                  {/if}
                </div>
              </div>
              <div>
                <label class="label">评价标签（逗号分隔，选填）</label>
                <input
                  type="text"
                  class="input"
                  placeholder="如：服务好,照片精美,沟通顺畅"
                  bind:value={reviewForm.tags}
                />
              </div>
              <div>
                <label class="label">评价内容（选填）</label>
                <textarea
                  class="input"
                  rows="4"
                  placeholder="分享您的体验和感受..."
                  bind:value={reviewForm.feedback}
                ></textarea>
              </div>
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="anonymous"
                  class="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                  bind:checked={reviewForm.is_anonymous}
                />
                <label for="anonymous" class="ml-2 text-sm text-gray-700">匿名评价</label>
              </div>
              <div class="flex gap-3 pt-2">
                <button
                  type="button"
                  class="btn btn-secondary flex-1"
                  on:click={() => {
                    showReviewForm = false;
                    reviewError = '';
                    reviewForm = { rating: 0, tags: '', feedback: '', is_anonymous: false };
                  }}
                >
                  取消
                </button>
                <button type="button" class="btn btn-primary flex-1" on:click={handleSubmitReview} disabled={savingReview}>
                  {#if savingReview}
                    提交中...
                  {:else}
                    <CheckCircle2 class="w-5 h-5" />
                    提交评价
                  {/if}
                </button>
              </div>
            </div>
          {:else}
            <p class="text-gray-500 text-center py-4">
              {user?.role === 'customer' ? '您尚未提交评价，点击右上角按钮提交评价' : '客户暂未提交评价'}
            </p>
          {/if}
        </div>
      </div>
    {/if}
  {/if}

  {#if showCreateSheet && order}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-auto">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">新建片单</h2>
          <button class="text-gray-400 hover:text-gray-600" on:click={() => (showCreateSheet = false)}>
            <X class="w-5 h-5" />
          </button>
        </div>
        <form on:submit|preventDefault={handleCreateSheet} class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">照片总数</label>
              <input
                type="number"
                class="input {sheetFormErrors.total_photos ? 'border-red-500' : ''}"
                bind:value={sheetForm.total_photos}
                min="0"
                on:input={() => {
                  if (sheetForm.selectable_count > sheetForm.total_photos) {
                    sheetFormErrors.selectable_count = '可选数量不能超过照片总数';
                  } else {
                    delete sheetFormErrors.selectable_count;
                  }
                }}
              />
              {#if sheetFormErrors.total_photos}
                <p class="text-red-500 text-xs mt-1">{sheetFormErrors.total_photos}</p>
              {/if}
            </div>
            <div>
              <label class="label">可选数量</label>
              <input
                type="number"
                class="input {sheetFormErrors.selectable_count ? 'border-red-500' : ''}"
                bind:value={sheetForm.selectable_count}
                min="0"
                max={sheetForm.total_photos}
                on:input={() => {
                  if (sheetForm.selectable_count > sheetForm.total_photos) {
                    sheetFormErrors.selectable_count = '可选数量不能超过照片总数';
                  } else {
                    delete sheetFormErrors.selectable_count;
                  }
                }}
              />
              {#if sheetFormErrors.selectable_count}
                <p class="text-red-500 text-xs mt-1">{sheetFormErrors.selectable_count}</p>
              {:else if sheetForm.total_photos > 0}
                <p class="text-gray-500 text-xs mt-1">最多 {sheetForm.total_photos} 张</p>
              {/if}
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
