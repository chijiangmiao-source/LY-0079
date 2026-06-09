<script lang="ts">
  import { onMount } from 'svelte';
  import { sheetsApi, selectionsApi, retouchApi, usersApi, batchesApi } from '$lib/api';
  import type {
    PhotoSheetDetail,
    SelectionRecord,
    RetouchRequest,
    PhotoBatch,
    UserListItem,
  } from '$lib/types';
  import {
    formatDateTime,
    retouchStatusMap,
    lockStatusMap,
    retouchRequestStatusMap,
    getStatusBadge,
  } from '$lib/utils';
  import { getUser } from '$lib/utils/auth';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import {
    ArrowLeft,
    Lock,
    CheckCircle,
    Plus,
    Image as ImageIcon,
    Edit3,
    AlertCircle,
  } from 'lucide-svelte';

  let sheet: PhotoSheetDetail | null = null;
  let selections: SelectionRecord[] = [];
  let retouchRequests: RetouchRequest[] = [];
  let batches: PhotoBatch[] = [];
  let retouchers: UserListItem[] = [];
  let loading = true;

  let showSelectionModal = false;
  let showRetouchModal = false;
  let showBatchModal = false;
  let editingSelection: SelectionRecord | null = null;

  const user = getUser();
  const canLock = user && ['admin', 'photographer'].includes(user.role);
  const canEdit = user && ['admin', 'photographer', 'customer'].includes(user.role);

  let selectionForm = {
    customer_name: '',
    selected_count: 0,
    selected_photo_ids: '',
    retouch_notes: '',
  };

  let retouchForm = {
    selection_id: 0,
    description: '',
    retoucher_id: undefined as number | undefined,
    storage_path: '',
  };

  let batchForm = {
    photo_count: 0,
    storage_path: '',
    batch_type: 'original',
    description: '',
  };

  async function loadData() {
    loading = true;
    try {
      const id = parseInt($page.params.id || '0');
      sheet = await sheetsApi.get(id);
      selections = await selectionsApi.list({ sheet_id: id });
      retouchRequests = await retouchApi.list({ sheet_id: id });
      batches = await batchesApi.list({ sheet_id: id });
      retouchers = await usersApi.listRetouchers();
    } finally {
      loading = false;
    }
  }

  function openSelectionModal(existing?: SelectionRecord) {
    editingSelection = existing || null;
    if (existing) {
      selectionForm = {
        customer_name: existing.customer_name,
        selected_count: existing.selected_count,
        selected_photo_ids: existing.selected_photo_ids || '',
        retouch_notes: existing.retouch_notes || '',
      };
    } else {
      selectionForm = {
        customer_name: user?.full_name || sheet?.customer_name || '',
        selected_count: 0,
        selected_photo_ids: '',
        retouch_notes: '',
      };
    }
    showSelectionModal = true;
  }

  async function handleSaveSelection() {
    try {
      if (editingSelection) {
        await selectionsApi.update(editingSelection.id, selectionForm);
      } else {
        await selectionsApi.create({
          sheet_id: sheet?.id,
          ...selectionForm,
        });
      }
      showSelectionModal = false;
      editingSelection = null;
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '操作失败');
    }
  }

  async function handleConfirmSelection(sel: SelectionRecord) {
    if (!confirm('确认最终选片？确认后将无法修改。')) return;
    try {
      await selectionsApi.confirm(sel.id);
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '操作失败');
    }
  }

  async function handleLockSheet() {
    if (!confirm('确定锁定该片单？锁定后将无法修改任何内容。')) return;
    try {
      await sheetsApi.lock(sheet!.id);
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '操作失败');
    }
  }

  function openRetouchModal(sel: SelectionRecord) {
    retouchForm = {
      selection_id: sel.id,
      description: '',
      retoucher_id: undefined,
      storage_path: '',
    };
    showRetouchModal = true;
  }

  async function handleSaveRetouch() {
    try {
      await retouchApi.create({
        sheet_id: sheet?.id,
        ...retouchForm,
      });
      showRetouchModal = false;
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '操作失败');
    }
  }

  async function handleSaveBatch() {
    try {
      await batchesApi.create({
        order_id: sheet?.order_id,
        sheet_id: sheet?.id,
        ...batchForm,
      });
      showBatchModal = false;
      loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || '操作失败');
    }
  }

  onMount(loadData);
</script>

<div class="p-8">
  <a href="/orders" class="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6">
    <ArrowLeft class="w-5 h-5 mr-2" />
    返回
  </a>

  {#if loading}
    <div class="p-12 text-center text-gray-500">加载中...</div>
  {:else if sheet}
    <div class="mb-8">
      <div class="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl font-bold text-gray-900">{sheet.sheet_no}</h1>
            <span class="badge {getStatusBadge(retouchStatusMap, sheet.retouch_status).color}">
              {getStatusBadge(retouchStatusMap, sheet.retouch_status).label}
            </span>
            <span class="badge {getStatusBadge(lockStatusMap, sheet.lock_status).color}">
              {getStatusBadge(lockStatusMap, sheet.lock_status).label}
            </span>
            {#if sheet.is_overdue && sheet.lock_status !== 'locked'}
              <span class="badge bg-red-100 text-red-800 flex items-center gap-1">
                <AlertCircle class="w-3 h-3" />
                已逾期
              </span>
            {/if}
          </div>
          <p class="text-gray-500 mt-1">
            订单: {sheet.order_no} · 客户: {sheet.customer_name || '-'}
          </p>
        </div>
        <div class="flex gap-2">
          {#if sheet.lock_status !== 'locked'}
            <button class="btn btn-secondary" on:click={() => (showBatchModal = true)}>
              <ImageIcon class="w-5 h-5" />
              导入批次
            </button>
            {#if canEdit}
              <button class="btn btn-secondary" on:click={() => openSelectionModal()}>
                <Plus class="w-5 h-5" />
                新建选片
              </button>
            {/if}
            {#if canLock}
              <button class="btn btn-success" on:click={handleLockSheet}>
                <Lock class="w-5 h-5" />
                锁定片单
              </button>
            {/if}
          {/if}
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <div class="card p-4">
          <p class="text-sm text-gray-500">照片总数</p>
          <p class="text-lg font-semibold mt-1">{sheet.total_photos}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">可选数量</p>
          <p class="text-lg font-semibold mt-1">{sheet.selectable_count}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">修图师</p>
          <p class="text-lg font-semibold mt-1">{sheet.retoucher_name || '-'}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">选片截止</p>
          <p class="text-lg font-semibold mt-1 {sheet.is_overdue ? 'text-red-600' : ''}">
            {formatDateTime(sheet.selection_deadline)}
          </p>
        </div>
      </div>

      {#if sheet.notes}
        <div class="card p-4 mt-4">
          <p class="text-sm text-gray-500 mb-2">备注</p>
          <p class="text-gray-800">{sheet.notes}</p>
        </div>
      {/if}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">照片批次</h2>
          <span class="text-sm text-gray-500">共 {batches.length} 个批次</span>
        </div>
        <div class="p-6">
          {#if batches.length === 0}
            <p class="text-gray-500 text-center py-8">暂无批次数据</p>
          {:else}
            <div class="space-y-3">
              {#each batches as batch}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p class="font-medium text-gray-900">{batch.batch_no}</p>
                    <p class="text-sm text-gray-500">
                      {batch.batch_type} · {batch.photo_count} 张 · {formatDateTime(batch.created_at)}
                    </p>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <div class="card">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">加修请求</h2>
          <span class="text-sm text-gray-500">共 {retouchRequests.length} 条</span>
        </div>
        <div class="p-6">
          {#if retouchRequests.length === 0}
            <p class="text-gray-500 text-center py-8">暂无加修请求</p>
          {:else}
            <div class="space-y-3">
              {#each retouchRequests as req}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p class="font-medium text-gray-900">
                      版本 V{req.version}
                      <span class="ml-2 badge {getStatusBadge(retouchRequestStatusMap, req.status).color}">
                        {getStatusBadge(retouchRequestStatusMap, req.status).label}
                      </span>
                    </p>
                    <p class="text-sm text-gray-500">
                      {req.description || '无描述'} · {formatDateTime(req.created_at)}
                    </p>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>

    <div class="card mt-6">
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">选片记录</h2>
      </div>
      {#if selections.length === 0}
        <div class="p-12 text-center text-gray-500">暂无选片记录</div>
      {:else}
        <table class="w-full">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">客户</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">入选数量</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">选片时间</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">最终确认</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">加修说明</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            {#each selections as sel}
              <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 text-sm font-medium text-gray-900">{sel.customer_name}</td>
                <td class="px-6 py-4 text-sm text-gray-600">
                  {sel.selected_count}
                  {#if sheet.selectable_count > 0}
                    <span class="text-gray-400"> / {sheet.selectable_count}</span>
                  {/if}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">{formatDateTime(sel.selection_time)}</td>
                <td class="px-6 py-4">
                  {#if sel.final_confirm_time}
                    <span class="badge bg-green-100 text-green-800 flex items-center gap-1">
                      <CheckCircle class="w-3 h-3" />
                      {formatDateTime(sel.final_confirm_time)}
                    </span>
                  {:else}
                    <span class="text-gray-400">未确认</span>
                  {/if}
                </td>
                <td class="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                  {sel.retouch_notes || '-'}
                </td>
                <td class="px-6 py-4">
                  <div class="flex gap-2">
                    {#if !sel.final_confirm_time && sheet.lock_status !== 'locked' && canEdit}
                      <button
                        class="text-primary-600 hover:text-primary-900 text-sm font-medium"
                        on:click={() => openSelectionModal(sel)}
                      >
                        <Edit3 class="w-4 h-4 inline" />
                        编辑
                      </button>
                    {/if}
                    {#if !sel.final_confirm_time && sheet.lock_status !== 'locked'}
                      <button
                        class="text-green-600 hover:text-green-900 text-sm font-medium"
                        on:click={() => handleConfirmSelection(sel)}
                      >
                        <CheckCircle class="w-4 h-4 inline" />
                        确认
                      </button>
                    {/if}
                    {#if sheet.lock_status !== 'locked'}
                      <button
                        class="text-purple-600 hover:text-purple-900 text-sm font-medium"
                        on:click={() => openRetouchModal(sel)}
                      >
                        加修
                      </button>
                    {/if}
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>
  {/if}

  {#if showSelectionModal}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-xl font-semibold text-gray-900">
            {editingSelection ? '编辑选片' : '新建选片'}
          </h2>
        </div>
        <form on:submit|preventDefault={handleSaveSelection} class="p-6 space-y-4">
          <div>
            <label class="label">客户姓名 <span class="text-red-500">*</span></label>
            <input type="text" class="input" bind:value={selectionForm.customer_name} required />
          </div>
          <div>
            <label class="label">入选数量 <span class="text-red-500">*</span></label>
            <input
              type="number"
              class="input"
              bind:value={selectionForm.selected_count}
              min="0"
              max={sheet?.selectable_count || undefined}
              required
            />
            {#if sheet && sheet.selectable_count > 0}
              <p class="text-xs text-gray-500 mt-1">
                最多可选 {sheet.selectable_count} 张
              </p>
            {/if}
          </div>
          <div>
            <label class="label">选中照片ID列表</label>
            <input
              type="text"
              class="input"
              bind:value={selectionForm.selected_photo_ids}
              placeholder="如: 1,2,3,4,5"
            />
          </div>
          <div>
            <label class="label">加修说明</label>
            <textarea class="input" rows="3" bind:value={selectionForm.retouch_notes}></textarea>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => (showSelectionModal = false)}>
              取消
            </button>
            <button type="submit" class="btn btn-primary flex-1">
              {editingSelection ? '保存修改' : '创建选片'}
            </button>
          </div>
        </form>
      </div>
    </div>
  {/if}

  {#if showRetouchModal}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-xl font-semibold text-gray-900">新建加修请求</h2>
        </div>
        <form on:submit|preventDefault={handleSaveRetouch} class="p-6 space-y-4">
          <div>
            <label class="label">修图师</label>
            <select class="input" bind:value={retouchForm.retoucher_id}>
              <option value={undefined}>请选择修图师</option>
              {#each retouchers as r}
                <option value={r.id}>{r.full_name}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="label">加修说明</label>
            <textarea class="input" rows="3" bind:value={retouchForm.description} required></textarea>
          </div>
          <div>
            <label class="label">存储路径</label>
            <input type="text" class="input" bind:value={retouchForm.storage_path} />
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => (showRetouchModal = false)}>
              取消
            </button>
            <button type="submit" class="btn btn-primary flex-1">提交加修</button>
          </div>
        </form>
      </div>
    </div>
  {/if}

  {#if showBatchModal}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl w-full max-w-lg">
        <div class="p-6 border-b border-gray-200">
          <h2 class="text-xl font-semibold text-gray-900">导入照片批次</h2>
        </div>
        <form on:submit|preventDefault={handleSaveBatch} class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">照片数量 <span class="text-red-500">*</span></label>
              <input type="number" class="input" bind:value={batchForm.photo_count} min="0" required />
            </div>
            <div>
              <label class="label">批次类型</label>
              <select class="input" bind:value={batchForm.batch_type}>
                <option value="original">原片</option>
                <option value="retouched">精修</option>
                <option value="deliver">交付</option>
              </select>
            </div>
          </div>
          <div>
            <label class="label">存储路径</label>
            <input type="text" class="input" bind:value={batchForm.storage_path} />
          </div>
          <div>
            <label class="label">描述</label>
            <textarea class="input" rows="3" bind:value={batchForm.description}></textarea>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => (showBatchModal = false)}>
              取消
            </button>
            <button type="submit" class="btn btn-primary flex-1">导入批次</button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</div>
