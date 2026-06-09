<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { reviewsApi } from '$lib/api';
  import type { FollowUpRecordDetail, AfterSalesResult, FollowUpStatus } from '$lib/types';
  import {
    formatDate,
    formatDateTime,
    followUpStatusMap,
    afterSalesResultMap,
    getStatusBadge,
  } from '$lib/utils';
  import {
    ArrowLeft,
    Save,
    Star,
    MessageSquare,
    Calendar,
    User,
    Camera,
    AlertCircle,
    CheckCircle2,
  } from 'lucide-svelte';

  let detail: FollowUpRecordDetail | null = null;
  let loading = true;
  let isEditing = false;
  let saving = false;
  let saveError = '';

  let form = {
    follow_up_time: '',
    satisfaction: 0,
    tags: '',
    feedback: '',
    after_sales_result: '' as AfterSalesResult | '',
    after_sales_notes: '',
    status: 'pending' as FollowUpStatus,
    review_deadline: '',
  };

  function formatDateTimeLocal(dateStr?: string): string {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  function loadFormFromDetail() {
    if (!detail) return;
    form = {
      follow_up_time: formatDateTimeLocal(detail.follow_up_time),
      satisfaction: detail.satisfaction || 0,
      tags: detail.tags || '',
      feedback: detail.feedback || '',
      after_sales_result: detail.after_sales_result || '',
      after_sales_notes: detail.after_sales_notes || '',
      status: detail.status,
      review_deadline: formatDateTimeLocal(detail.review_deadline),
    };
  }

  function setSatisfaction(val: number) {
    form.satisfaction = val;
  }

  async function handleSave() {
    saving = true;
    saveError = '';
    try {
      const id = parseInt($page.params.id || '0');
      const data: any = {
        status: form.status,
      };
      if (form.follow_up_time) data.follow_up_time = new Date(form.follow_up_time).toISOString();
      if (form.satisfaction > 0) data.satisfaction = form.satisfaction;
      if (form.tags) data.tags = form.tags;
      if (form.feedback) data.feedback = form.feedback;
      if (form.after_sales_result) data.after_sales_result = form.after_sales_result;
      if (form.after_sales_notes) data.after_sales_notes = form.after_sales_notes;
      if (form.review_deadline) data.review_deadline = new Date(form.review_deadline).toISOString();

      await reviewsApi.updateFollowUp(id, data);
      isEditing = false;
      await loadData();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      saveError = typeof detail === 'string' ? detail : '保存失败，请重试';
    } finally {
      saving = false;
    }
  }

  async function loadData() {
    loading = true;
    try {
      const id = parseInt($page.params.id || '0');
      detail = await reviewsApi.getFollowUp(id);
      loadFormFromDetail();
    } finally {
      loading = false;
    }
  }

  onMount(loadData);
</script>

<div class="p-8">
  <a href="/reviews/follow-ups" class="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6">
    <ArrowLeft class="w-5 h-5 mr-2" />
    返回回访列表
  </a>

  {#if loading}
    <div class="p-12 text-center text-gray-500">加载中...</div>
  {:else if detail}
    <div class="mb-6">
      <div class="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl font-bold text-gray-900 flex items-center">
              <MessageSquare class="w-7 h-7 mr-3 text-primary-600" />
              回访详情
            </h1>
            <span class="badge {getStatusBadge(followUpStatusMap, detail.status).color}">
              {getStatusBadge(followUpStatusMap, detail.status).label}
            </span>
          </div>
          <p class="text-gray-500 mt-1">订单: {detail.order_no}</p>
        </div>
        {#if !isEditing}
          <button class="btn btn-primary" on:click={() => (isEditing = true)}>
            <Save class="w-5 h-5" />
            编辑回访
          </button>
        {/if}
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <div class="card p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">订单信息</h2>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-sm text-gray-500 mb-1">客户</p>
              <div class="flex items-center">
                <User class="w-4 h-4 mr-1 text-gray-400" />
                <span class="font-medium text-gray-900">{detail.customer_name || '-'}</span>
              </div>
            </div>
            <div>
              <p class="text-sm text-gray-500 mb-1">摄影师</p>
              <div class="flex items-center">
                <Camera class="w-4 h-4 mr-1 text-gray-400" />
                <span class="font-medium text-gray-900">{detail.photographer_name || '-'}</span>
              </div>
            </div>
            <div>
              <p class="text-sm text-gray-500 mb-1">拍摄日期</p>
              <span class="font-medium text-gray-900">{formatDate(detail.shoot_date)}</span>
            </div>
            <div>
              <p class="text-sm text-gray-500 mb-1">回访处理人</p>
              <span class="font-medium text-gray-900">{detail.follow_up_by_name || '-'}</span>
            </div>
          </div>
        </div>

        {#if !isEditing}
          <div class="card p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">回访记录</h2>
            <div class="space-y-4">
              <div>
                <p class="text-sm text-gray-500 mb-1">回访满意度</p>
                <div class="flex items-center gap-1">
                  {#if detail.satisfaction}
                    {#each Array(5) as _, i}
                      <Star
                        class={`w-6 h-6 ${i < detail.satisfaction ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                      />
                    {/each}
                    <span class="ml-2 text-lg font-semibold text-gray-900">{detail.satisfaction}/5</span>
                  {:else}
                    <span class="text-gray-400">暂未评分</span>
                  {/if}
                </div>
              </div>
              <div>
                <p class="text-sm text-gray-500 mb-1">回访时间</p>
                <span class="font-medium text-gray-900">{formatDateTime(detail.follow_up_time) || '-'}</span>
              </div>
              <div>
                <p class="text-sm text-gray-500 mb-1">评价标签</p>
                <span class="font-medium text-gray-900">{detail.tags || '-'}</span>
              </div>
              <div>
                <p class="text-sm text-gray-500 mb-1">文字反馈</p>
                <span class="text-gray-700 whitespace-pre-wrap">{detail.feedback || '-'}</span>
              </div>
              <div>
                <p class="text-sm text-gray-500 mb-1">售后处理结果</p>
                {#if detail.after_sales_result}
                  <span class="badge {getStatusBadge(afterSalesResultMap, detail.after_sales_result).color}">
                    {getStatusBadge(afterSalesResultMap, detail.after_sales_result).label}
                  </span>
                {:else}
                  <span class="text-gray-400">-</span>
                {/if}
              </div>
              <div>
                <p class="text-sm text-gray-500 mb-1">售后备注</p>
                <span class="text-gray-700 whitespace-pre-wrap">{detail.after_sales_notes || '-'}</span>
              </div>
              <div>
                <p class="text-sm text-gray-500 mb-1">客户评价截止时间</p>
                <div class="flex items-center">
                  <Calendar class="w-4 h-4 mr-1 text-gray-400" />
                  <span class="font-medium text-gray-900">{formatDateTime(detail.review_deadline) || '-'}</span>
                </div>
              </div>
            </div>
          </div>
        {:else}
          <div class="card p-6">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">编辑回访记录</h2>
            {#if saveError}
              <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center">
                <AlertCircle class="w-5 h-5 mr-2" />
                {saveError}
              </div>
            {/if}
            <div class="space-y-4">
              <div>
                <label class="label">回访状态</label>
                <select class="input" bind:value={form.status}>
                  <option value="pending">待回访</option>
                  <option value="in_progress">回访中</option>
                  <option value="completed">已完成</option>
                  <option value="cancelled">已取消</option>
                </select>
              </div>
              <div>
                <label class="label">回访时间</label>
                <input type="datetime-local" class="input" bind:value={form.follow_up_time} />
              </div>
              <div>
                <label class="label">客户满意度</label>
                <div class="flex items-center gap-2 py-2">
                  {#each Array(5) as _, i}
                    <button
                      type="button"
                      class="focus:outline-none transition-transform hover:scale-110"
                      on:click={() => setSatisfaction(i + 1)}
                    >
                      <Star
                        class={`w-8 h-8 ${i < form.satisfaction ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300 hover:text-yellow-300'}`}
                      />
                    </button>
                  {/each}
                  {#if form.satisfaction > 0}
                    <span class="ml-2 text-lg font-semibold text-gray-700">{form.satisfaction}/5</span>
                  {/if}
                </div>
              </div>
              <div>
                <label class="label">评价标签（逗号分隔）</label>
                <input
                  type="text"
                  class="input"
                  placeholder="如：服务好,照片精美,沟通顺畅"
                  bind:value={form.tags}
                />
              </div>
              <div>
                <label class="label">文字反馈</label>
                <textarea class="input" rows="4" placeholder="记录客户的反馈意见..." bind:value={form.feedback}></textarea>
              </div>
              <div>
                <label class="label">售后处理结果</label>
                <select class="input" bind:value={form.after_sales_result}>
                  <option value="">未处理</option>
                  <option value="no_issues">无问题</option>
                  <option value="resolved">已解决</option>
                  <option value="partially_resolved">部分解决</option>
                  <option value="unresolved">未解决</option>
                </select>
              </div>
              <div>
                <label class="label">售后备注</label>
                <textarea class="input" rows="3" placeholder="记录售后处理详情..." bind:value={form.after_sales_notes}></textarea>
              </div>
              <div>
                <label class="label">客户评价截止时间</label>
                <input type="datetime-local" class="input" bind:value={form.review_deadline} />
              </div>
              <div class="flex gap-3 pt-4">
                <button
                  type="button"
                  class="btn btn-secondary flex-1"
                  on:click={() => {
                    loadFormFromDetail();
                    isEditing = false;
                    saveError = '';
                  }}
                >
                  取消
                </button>
                <button type="button" class="btn btn-primary flex-1" on:click={handleSave} disabled={saving}>
                  {#if saving}
                    保存中...
                  {:else}
                    <CheckCircle2 class="w-5 h-5" />
                    保存修改
                  {/if}
                </button>
              </div>
            </div>
          </div>
        {/if}
      </div>

      <div class="space-y-6">
        <div class="card p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">客户评价</h2>
          {#if detail.review_submitted && detail.customer_rating}
            <div class="space-y-3">
              <div class="flex items-center gap-1">
                {#each Array(5) as _, i}
                  <Star
                    class={`w-5 h-5 ${i < detail.customer_rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                  />
                {/each}
                <span class="ml-1 font-semibold">{detail.customer_rating}/5</span>
              </div>
              <p class="text-sm text-green-600 flex items-center">
                <CheckCircle2 class="w-4 h-4 mr-1" />
                客户已提交评价
              </p>
            </div>
          {:else}
            <div class="text-center py-4">
              <p class="text-gray-400 mb-2">客户暂未评价</p>
              {#if detail.review_deadline}
                <p class="text-xs text-gray-500">
                  评价截止: {formatDateTime(detail.review_deadline)}
                </p>
              {/if}
            </div>
          {/if}
        </div>

        <div class="card p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">操作记录</h2>
          <div class="space-y-3 text-sm">
            <div>
              <p class="text-gray-500">创建时间</p>
              <p class="text-gray-900">{formatDateTime(detail.created_at)}</p>
            </div>
            <div>
              <p class="text-gray-500">最后更新</p>
              <p class="text-gray-900">{formatDateTime(detail.updated_at)}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>
