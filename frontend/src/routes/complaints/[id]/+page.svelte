<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { complaintsApi, usersApi } from '$lib/api';
  import type {
    ComplaintTicketDetail,
    ComplaintStatus,
    ComplaintType,
    CompensationType,
    UserListItem,
  } from '$lib/types';
  import {
    formatDate,
    formatDateTime,
    complaintStatusMap,
    complaintTypeMap,
    complaintSourceMap,
    compensationTypeMap,
    getStatusBadge,
  } from '$lib/utils';
  import {
    ArrowLeft,
    AlertOctagon,
    User as UserIcon,
    Camera,
    Clock,
    AlertTriangle,
    UserPlus,
    MessageSquare,
    CheckCircle,
    DollarSign,
    FileText,
    Star,
    ThumbsUp,
    FolderKanban,
  } from 'lucide-svelte';
  import { getUser } from '$lib/utils/auth';
  import { goto } from '$app/navigation';

  let ticket: ComplaintTicketDetail | null = null;
  let staffUsers: UserListItem[] = [];
  let loading = true;
  let user = getUser();

  let assignForm = {
    assigned_to: 0,
    process_deadline: '',
  };

  let processNote = '';
  let processStatus = '' as ComplaintStatus | '';

  let resolveForm = {
    final_conclusion: '',
    status: 'resolved' as ComplaintStatus,
  };

  let compensationForm = {
    compensation_type: 'refund' as CompensationType,
    amount: 0,
    description: '',
  };

  async function loadData() {
    loading = true;
    try {
      const id = parseInt($page.params.id);
      ticket = await complaintsApi.get(id);
      if (user && (user.role === 'admin' || user.role === 'photographer')) {
        staffUsers = await usersApi.list();
      }
    } finally {
      loading = false;
    }
  }

  async function assignTicket() {
    if (!assignForm.assigned_to) {
      alert('请选择处理人');
      return;
    }
    try {
      const data: any = { assigned_to: assignForm.assigned_to };
      if (assignForm.process_deadline) {
        data.process_deadline = assignForm.process_deadline;
      }
      await complaintsApi.assign(ticket!.id, data);
      await loadData();
      assignForm = { assigned_to: 0, process_deadline: '' };
    } catch (e: any) {
      alert(e.response?.data?.detail || '分配失败');
    }
  }

  async function addProcessNote() {
    if (!processNote) {
      alert('请填写处理记录');
      return;
    }
    try {
      const data: any = { progress_notes: processNote };
      if (processStatus) data.status = processStatus;
      await complaintsApi.process(ticket!.id, data);
      processNote = '';
      processStatus = '';
      await loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || '提交失败');
    }
  }

  async function resolveTicket() {
    if (!resolveForm.final_conclusion) {
      alert('请填写最终结论');
      return;
    }
    try {
      await complaintsApi.resolve(ticket!.id, resolveForm);
      await loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || '提交失败');
    }
  }

  async function createCompensation() {
    if (!compensationForm.compensation_type) {
      alert('请选择补偿类型');
      return;
    }
    try {
      await complaintsApi.createCompensation(ticket!.id, compensationForm);
      await loadData();
      compensationForm = { compensation_type: 'refund', amount: 0, description: '' };
    } catch (e: any) {
      alert(e.response?.data?.detail || '创建补偿方案失败');
    }
  }

  async function approveCompensation() {
    try {
      await complaintsApi.approveCompensation(ticket!.id);
      await loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || '审批失败');
    }
  }

  async function executeCompensation() {
    try {
      await complaintsApi.executeCompensation(ticket!.id);
      await loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || '执行失败');
    }
  }

  onMount(loadData);
</script>

<div class="p-8">
  <div class="mb-6">
    <button on:click={() => goto('/complaints')} class="text-gray-500 hover:text-gray-700 flex items-center mb-4">
      <ArrowLeft class="w-4 h-4 mr-1" />
      返回投诉列表
    </button>
    {#if loading}
      <div class="p-12 text-center text-gray-500">加载中...</div>
    {:else if !ticket}
      <div class="p-12 text-center text-gray-500">投诉工单不存在</div>
    {:else}
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 flex items-center">
            <AlertOctagon class="w-7 h-7 mr-3 text-red-600" />
            投诉工单详情
            <span class="ml-3 text-base font-normal text-gray-500">{ticket.ticket_no}</span>
          </h1>
          <p class="text-gray-500 mt-1">
            创建时间: {formatDateTime(ticket.created_at)}
            {#if ticket.is_overdue}
              <span class="ml-3 inline-flex items-center text-red-600">
                <AlertTriangle class="w-4 h-4 mr-1" />
                已超时
              </span>
            {/if}
          </p>
        </div>
        <span class="badge text-lg px-4 py-2 {getStatusBadge(complaintStatusMap, ticket.status).color}">
          {getStatusBadge(complaintStatusMap, ticket.status).label}
        </span>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <div class="lg:col-span-2 space-y-6">
          <div class="card">
            <div class="p-6 border-b border-gray-200 flex items-center gap-2">
              <FileText class="w-5 h-5 text-gray-500" />
              <h2 class="text-lg font-semibold text-gray-900">投诉信息</h2>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm text-gray-500">投诉标题</p>
                  <p class="text-base font-medium text-gray-900 mt-1">{ticket.title}</p>
                </div>
                <div class="flex gap-4">
                  <div>
                    <p class="text-sm text-gray-500">投诉类型</p>
                    <span class="badge mt-1 {getStatusBadge(complaintTypeMap, ticket.complaint_type).color}">
                      {getStatusBadge(complaintTypeMap, ticket.complaint_type).label}
                    </span>
                  </div>
                  <div>
                    <p class="text-sm text-gray-500">来源</p>
                    <span class="badge mt-1 {getStatusBadge(complaintSourceMap, ticket.source).color}">
                      {getStatusBadge(complaintSourceMap, ticket.source).label}
                    </span>
                  </div>
                </div>
              </div>
              {#if ticket.rating_trigger}
                <div>
                  <p class="text-sm text-gray-500 mb-1">触发评分</p>
                  <div class="flex items-center">
                    {#each Array(5) as _, i}
                      <Star
                        class={`w-5 h-5 ${i < ticket.rating_trigger ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
                      />
                    {/each}
                    <span class="ml-2 text-sm font-medium text-gray-700">{ticket.rating_trigger}/5</span>
                  </div>
                </div>
              {/if}
              <div>
                <p class="text-sm text-gray-500 mb-1">详细描述</p>
                <div class="bg-gray-50 rounded-lg p-4 text-gray-700 whitespace-pre-wrap">
                  {ticket.description}
                </div>
              </div>
              {#if ticket.final_conclusion}
                <div>
                  <p class="text-sm text-gray-500 mb-1 flex items-center">
                    <CheckCircle class="w-4 h-4 mr-1 text-green-500" />
                    最终结论
                  </p>
                  <div class="bg-green-50 rounded-lg p-4 text-gray-700 whitespace-pre-wrap border border-green-100">
                    {ticket.final_conclusion}
                  </div>
                </div>
              {/if}
            </div>
          </div>

          <div class="card">
            <div class="p-6 border-b border-gray-200 flex items-center gap-2">
              <MessageSquare class="w-5 h-5 text-gray-500" />
              <h2 class="text-lg font-semibold text-gray-900">处理进度记录</h2>
            </div>
            <div class="p-6">
              {#if !ticket.progress_notes}
                <p class="text-gray-400 text-center py-4">暂无处理记录</p>
              {:else}
                <div class="space-y-3 whitespace-pre-wrap">{ticket.progress_notes}</div>
              {/if}
              {#if user && (user.role === 'admin' || user.role === 'photographer') && ticket.status !== 'resolved' && ticket.status !== 'closed' && ticket.status !== 'cancelled'}
                <div class="mt-4 pt-4 border-t border-gray-100 space-y-3">
                  <div>
                    <label class="label">添加处理记录</label>
                    <textarea
                      class="input h-24"
                      bind:value={processNote}
                      placeholder="请填写本次处理进展..."
                    ></textarea>
                  </div>
                  <div class="flex items-center gap-3 flex-wrap">
                    <div class="flex-1 min-w-48">
                      <label class="label">更新状态（可选）</label>
                      <select class="input" bind:value={processStatus}>
                        <option value="">不更新状态</option>
                        <option value="processing">处理中</option>
                        <option value="resolved">已解决</option>
                        <option value="closed">已关闭</option>
                      </select>
                    </div>
                    <button class="btn btn-primary self-end" on:click={addProcessNote}>
                      <MessageSquare class="w-4 h-4" />
                      提交记录
                    </button>
                  </div>
                </div>
              {/if}
            </div>
          </div>

          {#if user && (user.role === 'admin' || user.role === 'photographer') && !ticket.compensation && ticket.status !== 'resolved' && ticket.status !== 'closed' && ticket.status !== 'cancelled'}
            <div class="card">
              <div class="p-6 border-b border-gray-200 flex items-center gap-2">
                <DollarSign class="w-5 h-5 text-gray-500" />
                <h2 class="text-lg font-semibold text-gray-900">创建补偿方案</h2>
              </div>
              <div class="p-6 space-y-4">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="label">补偿类型</label>
                    <select class="input" bind:value={compensationForm.compensation_type}>
                      <option value="refund">退款</option>
                      <option value="discount">折扣</option>
                      <option value="retake">重拍</option>
                      <option value="gift">赠品</option>
                      <option value="other">其他</option>
                    </select>
                  </div>
                  <div>
                    <label class="label">补偿金额（元）</label>
                    <input class="input" type="number" bind:value={compensationForm.amount} min="0" step="0.01" />
                  </div>
                </div>
                <div>
                  <label class="label">补偿说明</label>
                  <textarea class="input h-24" bind:value={compensationForm.description} placeholder="请说明补偿方案详情..."></textarea>
                </div>
                <button class="btn btn-primary" on:click={createCompensation}>
                  <DollarSign class="w-4 h-4" />
                  创建补偿方案
                </button>
              </div>
            </div>
          {/if}

          {#if user && (user.role === 'admin' || user.role === 'photographer') && !ticket.final_conclusion && ticket.status !== 'cancelled'}
            <div class="card">
              <div class="p-6 border-b border-gray-200 flex items-center gap-2">
                <CheckCircle class="w-5 h-5 text-gray-500" />
                <h2 class="text-lg font-semibold text-gray-900">结案处理</h2>
              </div>
              <div class="p-6 space-y-4">
                <div>
                  <label class="label">结案状态</label>
                  <select class="input" bind:value={resolveForm.status}>
                    <option value="resolved">已解决</option>
                    <option value="closed">已关闭</option>
                  </select>
                </div>
                <div>
                  <label class="label">最终结论</label>
                  <textarea
                    class="input h-24"
                    bind:value={resolveForm.final_conclusion}
                    placeholder="请填写最终处理结论..."
                  ></textarea>
                </div>
                <button class="btn btn-primary" on:click={resolveTicket}>
                  <CheckCircle class="w-4 h-4" />
                  提交结案
                </button>
              </div>
            </div>
          {/if}
        </div>

        <div class="space-y-6">
          <div class="card">
            <div class="p-6 border-b border-gray-200 flex items-center gap-2">
              <FolderKanban class="w-5 h-5 text-gray-500" />
              <h2 class="text-lg font-semibold text-gray-900">订单信息</h2>
            </div>
            <div class="p-6 space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500">订单号</span>
                <a href="/orders/{ticket.order_id}" class="text-primary-600 hover:text-primary-900 font-medium">
                  {ticket.order_no}
                </a>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500">拍摄日期</span>
                <span class="text-sm text-gray-900">{formatDate(ticket.shoot_date)}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500">客户</span>
                <div class="flex items-center">
                  <UserIcon class="w-4 h-4 mr-1 text-gray-400" />
                  <span class="text-sm text-gray-900">{ticket.customer_name || '-'}</span>
                </div>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500">责任摄影师</span>
                <div class="flex items-center">
                  <Camera class="w-4 h-4 mr-1 text-gray-400" />
                  <span class="text-sm text-gray-900">{ticket.photographer_name || '-'}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="p-6 border-b border-gray-200 flex items-center gap-2">
              <UserPlus class="w-5 h-5 text-gray-500" />
              <h2 class="text-lg font-semibold text-gray-900">处理分配</h2>
            </div>
            <div class="p-6 space-y-3">
              {#if ticket.assignee_name}
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm text-gray-500">当前处理人</span>
                  <span class="text-sm font-medium text-gray-900">{ticket.assignee_name}</span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-500">分配时间</span>
                  <span class="text-sm text-gray-600">{formatDateTime(ticket.assigned_at)}</span>
                </div>
              {:else}
                <p class="text-gray-400 text-sm">暂未分配处理人</p>
              {/if}
              {#if ticket.process_deadline}
                <div class="flex items-center justify-between mt-2">
                  <span class="text-sm text-gray-500">处理截止</span>
                  <div class="flex items-center">
                    <Clock class="w-4 h-4 mr-1 {ticket.is_overdue ? 'text-red-500' : 'text-gray-400'}" />
                    <span class={ticket.is_overdue ? 'text-red-600 font-medium' : 'text-sm text-gray-900'}>
                      {formatDateTime(ticket.process_deadline, 'MM-DD HH:mm')}
                    </span>
                  </div>
                </div>
              {/if}
              {#if user?.role === 'admin' && ticket.status !== 'resolved' && ticket.status !== 'closed' && ticket.status !== 'cancelled'}
                <div class="mt-4 pt-4 border-t border-gray-100 space-y-3">
                  <div>
                    <label class="label">分配处理人</label>
                    <select class="input" bind:value={assignForm.assigned_to}>
                      <option value={0}>请选择处理人</option>
                      {#each staffUsers as u}
                        {#if u.role === 'admin' || u.role === 'photographer'}
                          <option value={u.id}>{u.full_name} ({u.role === 'admin' ? '管理员' : '摄影师'})</option>
                        {/if}
                      {/each}
                    </select>
                  </div>
                  <div>
                    <label class="label">截止时间（可选）</label>
                    <input class="input" type="datetime-local" bind:value={assignForm.process_deadline} />
                  </div>
                  <button class="btn btn-primary w-full" on:click={assignTicket}>
                    <UserPlus class="w-4 h-4" />
                    分配处理
                  </button>
                </div>
              {/if}
            </div>
          </div>

          {#if ticket.compensation}
            <div class="card">
              <div class="p-6 border-b border-gray-200 flex items-center gap-2">
                <ThumbsUp class="w-5 h-5 text-gray-500" />
                <h2 class="text-lg font-semibold text-gray-900">补偿方案</h2>
              </div>
              <div class="p-6 space-y-3">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-500">补偿类型</span>
                  <span class="badge {getStatusBadge(compensationTypeMap, ticket.compensation.compensation_type).color}">
                    {getStatusBadge(compensationTypeMap, ticket.compensation.compensation_type).label}
                  </span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-500">补偿金额</span>
                  <span class="text-lg font-bold text-green-600">¥{ticket.compensation.amount.toFixed(2)}</span>
                </div>
                {#if ticket.compensation.description}
                  <div>
                    <span class="text-sm text-gray-500">补偿说明</span>
                    <p class="text-sm text-gray-700 mt-1 bg-gray-50 p-3 rounded">{ticket.compensation.description}</p>
                  </div>
                {/if}
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-500">审批状态</span>
                  {#if ticket.compensation.approved_by}
                    <span class="badge bg-green-100 text-green-800">
                      已审批 ({ticket.compensation.approver_name})
                    </span>
                  {:else}
                    <span class="badge bg-yellow-100 text-yellow-800">待审批</span>
                  {/if}
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-500">执行状态</span>
                  {#if ticket.compensation.is_executed}
                    <span class="badge bg-green-100 text-green-800">
                      已执行 ({ticket.compensation.executor_name})
                    </span>
                  {:else}
                    <span class="badge bg-gray-100 text-gray-800">待执行</span>
                  {/if}
                </div>
                {#if user?.role === 'admin'}
                  <div class="pt-3 border-t border-gray-100 flex gap-2">
                    {#if !ticket.compensation.approved_by}
                      <button class="btn btn-primary flex-1" on:click={approveCompensation}>
                        <CheckCircle class="w-4 h-4" />
                        审批通过
                      </button>
                    {/if}
                    {#if !ticket.compensation.is_executed}
                      <button class="btn btn-secondary flex-1" on:click={executeCompensation}>
                        <DollarSign class="w-4 h-4" />
                        执行补偿
                      </button>
                    {/if}
                  </div>
                {/if}
              </div>
            </div>
          {/if}

          {#if ticket.creator_name}
            <div class="card">
              <div class="p-6 space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-500">创建人</span>
                  <span class="text-sm text-gray-900">{ticket.creator_name}</span>
                </div>
                {#if ticket.resolved_at}
                  <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-500">结案时间</span>
                    <span class="text-sm text-gray-900">{formatDateTime(ticket.resolved_at)}</span>
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>
