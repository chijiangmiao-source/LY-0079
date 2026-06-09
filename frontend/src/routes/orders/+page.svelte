<script lang="ts">
  import { onMount } from 'svelte';
  import { ordersApi, usersApi } from '$lib/api';
  import type { OrderListItem, OrderStatus, UserListItem, ScheduleConflict } from '$lib/types';
  import { formatDate, formatDateTime, orderStatusMap, getStatusBadge } from '$lib/utils';
  import { getUser } from '$lib/utils/auth';
  import { Plus, Search, Filter, UserPlus, X, AlertCircle, CalendarCheck, MapPin, Clock, Camera } from 'lucide-svelte';

  let orders: OrderListItem[] = [];
  let customers: UserListItem[] = [];
  let photographers: UserListItem[] = [];
  let loading = true;
  let showCreateModal = false;
  let showAddCustomerModal = false;
  let statusFilter: OrderStatus | '' = '';
  let shootDateFrom: string = '';
  let shootDateTo: string = '';
  let photographerFilter: number | '' = '';
  let cityFilter: string = '';
  let keyword: string = '';

  let scheduleConflict: ScheduleConflict | null = null;
  let checkingSchedule = false;

  const user = getUser();
  const canCreate = user && ['admin', 'photographer'].includes(user.role);

  let form = {
    customer_id: 0,
    photographer_id: user?.role === 'photographer' ? user.id : undefined as number | undefined,
    shoot_type: '',
    shoot_date: '',
    shoot_time_start: '',
    shoot_time_end: '',
    city: '',
    service_package: '',
    location: '',
    total_photos: 0,
    included_retouches: 0,
    notes: '',
  };

  let newCustomerForm = {
    full_name: '',
    phone: '',
  };

  let formErrors: Record<string, string> = {};
  let newCustomerErrors: Record<string, string> = {};

  function validateChineseName(name: string): string | null {
    if (!name || !name.trim()) return '姓名不能为空';
    if (/\s/.test(name)) return '姓名不能包含空格';
    if (/[a-zA-Z0-9]/.test(name)) return '姓名不能包含英文或数字';
    if (!/^[\u4e00-\u9fa5·]+$/.test(name.trim())) return '姓名只能包含中文字符';
    return null;
  }

  function validateOrderForm(): boolean {
    formErrors = {};
    if (!form.customer_id || form.customer_id === 0) {
      formErrors.customer_id = '请选择客户';
    }
    if (form.included_retouches > form.total_photos) {
      formErrors.included_retouches = '精修数量不能超过照片总数';
    }
    if (form.shoot_time_start && form.shoot_time_end) {
      if (new Date(form.shoot_time_end) <= new Date(form.shoot_time_start)) {
        formErrors.shoot_time_end = '结束时间必须晚于开始时间';
      }
    }
    if (form.shoot_date && form.shoot_time_start) {
      const d = new Date(form.shoot_time_start);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      const startDate = `${yyyy}-${mm}-${dd}`;
      if (form.shoot_date !== startDate) {
        formErrors.shoot_date = '拍摄日期必须与开始时间的日期一致';
      }
    }
    if (form.shoot_date && form.shoot_time_end) {
      const d = new Date(form.shoot_time_end);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      const endDate = `${yyyy}-${mm}-${dd}`;
      if (form.shoot_date !== endDate) {
        formErrors.shoot_date = '拍摄日期必须与结束时间的日期一致';
      }
    }
    if (scheduleConflict?.has_conflict) {
      formErrors.schedule = '摄影师档期存在冲突，请调整时间或更换摄影师';
    }
    return Object.keys(formErrors).length === 0;
  }

  function validateNewCustomerForm(): boolean {
    newCustomerErrors = {};
    const nameError = validateChineseName(newCustomerForm.full_name);
    if (nameError) {
      newCustomerErrors.full_name = nameError;
    }
    return Object.keys(newCustomerErrors).length === 0;
  }

  $: customerNameError = validateChineseName(newCustomerForm.full_name);

  async function checkSchedule() {
    if (!form.photographer_id || !form.shoot_time_start || !form.shoot_time_end) {
      scheduleConflict = null;
      return;
    }
    if (new Date(form.shoot_time_end) <= new Date(form.shoot_time_start)) {
      scheduleConflict = null;
      return;
    }
    checkingSchedule = true;
    try {
      scheduleConflict = await ordersApi.checkSchedule({
        photographer_id: form.photographer_id,
        shoot_time_start: form.shoot_time_start,
        shoot_time_end: form.shoot_time_end,
      });
    } catch (err) {
      scheduleConflict = null;
    } finally {
      checkingSchedule = false;
    }
  }

  $: {
    if (form.photographer_id && form.shoot_time_start && form.shoot_time_end) {
      checkSchedule();
    } else {
      scheduleConflict = null;
    }
  }

  async function loadData() {
    loading = true;
    try {
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      if (shootDateFrom) params.shoot_date_from = shootDateFrom;
      if (shootDateTo) params.shoot_date_to = shootDateTo;
      if (photographerFilter) params.photographer_id = photographerFilter;
      if (cityFilter) params.city = cityFilter;
      orders = await ordersApi.list(params);
      photographers = await usersApi.listPhotographers();
      if (canCreate) {
        customers = await usersApi.listCustomers();
      }
    } finally {
      loading = false;
    }
  }

  function resetForm() {
    form = {
      customer_id: 0,
      photographer_id: user?.role === 'photographer' ? user.id : undefined,
      shoot_type: '',
      shoot_date: '',
      shoot_time_start: '',
      shoot_time_end: '',
      city: '',
      service_package: '',
      location: '',
      total_photos: 0,
      included_retouches: 0,
      notes: '',
    };
    formErrors = {};
    scheduleConflict = null;
  }

  async function handleCreate() {
    if (!validateOrderForm()) return;
    try {
      const submitData: any = { ...form };
      if (!submitData.shoot_time_start) delete submitData.shoot_time_start;
      if (!submitData.shoot_time_end) delete submitData.shoot_time_end;
      if (!submitData.city) delete submitData.city;
      if (!submitData.service_package) delete submitData.service_package;
      if (!submitData.shoot_date) delete submitData.shoot_date;
      if (!submitData.shoot_type) delete submitData.shoot_type;
      if (!submitData.location) delete submitData.location;
      if (!submitData.notes) delete submitData.notes;
      await ordersApi.create(submitData);
      showCreateModal = false;
      resetForm();
      await loadData();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') {
        alert(detail);
      } else if (Array.isArray(detail)) {
        alert(detail.map((e: any) => e.msg || JSON.stringify(e)).join('\n'));
      } else {
        alert('创建失败');
      }
    }
  }

  async function handleAddCustomer() {
    if (!validateNewCustomerForm()) return;
    try {
      const newCustomer = await usersApi.quickCreateCustomer(newCustomerForm);
      customers = [...customers, newCustomer];
      form.customer_id = newCustomer.id;
      showAddCustomerModal = false;
      newCustomerForm = { full_name: '', phone: '' };
      newCustomerErrors = {};
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') {
        newCustomerErrors.full_name = detail;
      } else if (Array.isArray(detail)) {
        detail.forEach((e: any) => {
          if (e.loc && e.loc[1]) {
            newCustomerErrors[e.loc[1]] = e.msg;
          }
        });
      } else {
        alert('创建客户失败');
      }
    }
  }

  $: filteredOrders = orders.filter((o) => {
    if (!keyword) return true;
    const kw = keyword.toLowerCase();
    return (
      o.order_no.toLowerCase().includes(kw) ||
      (o.customer_name || '').toLowerCase().includes(kw) ||
      (o.shoot_type || '').toLowerCase().includes(kw) ||
      (o.city || '').toLowerCase().includes(kw) ||
      (o.service_package || '').toLowerCase().includes(kw)
    );
  });

  function formatTimeRange(start?: string, end?: string): string {
    if (!start && !end) return '-';
    if (start && end) {
      return `${formatDateTime(start, 'HH:mm')} - ${formatDateTime(end, 'HH:mm')}`;
    }
    return formatDateTime(start || end, 'HH:mm');
  }

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
            placeholder="搜索订单号、客户、拍摄类型、城市、套餐..."
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
      <div>
        <div class="relative">
          <CalendarCheck class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="date"
            class="input pl-10"
            placeholder="开始日期"
            bind:value={shootDateFrom}
            on:change={loadData}
          />
        </div>
      </div>
      <div>
        <input
          type="date"
          class="input"
          placeholder="结束日期"
          bind:value={shootDateTo}
          on:change={loadData}
        />
      </div>
      <div>
        <div class="relative">
          <Camera class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <select class="input pl-10" bind:value={photographerFilter} on:change={loadData}>
            <option value="">全部摄影师</option>
            {#each photographers as p}
              <option value={p.id}>{p.full_name}</option>
            {/each}
          </select>
        </div>
      </div>
      <div>
        <div class="relative">
          <MapPin class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            class="input pl-10"
            placeholder="拍摄城市"
            bind:value={cityFilter}
            on:change={loadData}
          />
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
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">摄影师</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">拍摄类型</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">套餐</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">拍摄日期</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间段</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">城市</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">照片数量</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each filteredOrders as order}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 text-sm font-medium text-gray-900">{order.order_no}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.customer_name || '-'}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.photographer_name || '-'}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.shoot_type || '-'}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.service_package || '-'}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{formatDate(order.shoot_date)}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{formatTimeRange(order.shoot_time_start, order.shoot_time_end)}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.city || '-'}</td>
              <td class="px-6 py-4 text-sm text-gray-600">{order.total_photos}</td>
              <td class="px-6 py-4">
                <span class="badge {getStatusBadge(orderStatusMap, order.status).color}">
                  {getStatusBadge(orderStatusMap, order.status).label}
                </span>
              </td>
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
      <div class="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-auto">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">新建订单</h2>
          <button class="text-gray-400 hover:text-gray-600" on:click={() => { showCreateModal = false; resetForm(); }}>
            <X class="w-5 h-5" />
          </button>
        </div>
        <form on:submit|preventDefault={handleCreate} class="p-6 space-y-4">
          <div>
            <div class="flex items-end gap-2">
              <div class="flex-1">
                <label class="label">客户 <span class="text-red-500">*</span></label>
                <select class="input {formErrors.customer_id ? 'border-red-500' : ''}" bind:value={form.customer_id}>
                  <option value={0}>请选择客户</option>
                  {#each customers as c}
                    <option value={c.id}>{c.full_name}</option>
                  {/each}
                </select>
                {#if formErrors.customer_id}
                  <p class="text-red-500 text-xs mt-1">{formErrors.customer_id}</p>
                {/if}
              </div>
              <button
                type="button"
                class="btn btn-secondary"
                on:click={() => (showAddCustomerModal = true)}
                title="新增客户"
              >
                <UserPlus class="w-5 h-5" />
              </button>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">摄影师</label>
              <select class="input" bind:value={form.photographer_id}>
                <option value={undefined}>请选择摄影师</option>
                {#each photographers as p}
                  <option value={p.id}>{p.full_name}</option>
                {/each}
              </select>
            </div>
            <div>
              <label class="label">拍摄类型</label>
              <input type="text" class="input" bind:value={form.shoot_type} placeholder="如：婚纱照、写真等" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">服务套餐</label>
              <input type="text" class="input" bind:value={form.service_package} placeholder="如：基础套餐、豪华套餐等" />
            </div>
            <div>
              <label class="label">拍摄城市</label>
              <div class="relative">
                <MapPin class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input type="text" class="input pl-9" bind:value={form.city} placeholder="如：北京、上海等" />
              </div>
            </div>
          </div>

          <div>
            <label class="label">拍摄地点</label>
            <input type="text" class="input" bind:value={form.location} placeholder="详细拍摄地址" />
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="label">拍摄日期</label>
              <input type="date" class="input {formErrors.shoot_date ? 'border-red-500' : ''}" bind:value={form.shoot_date} />
              {#if formErrors.shoot_date}
                <p class="text-red-500 text-xs mt-1">{formErrors.shoot_date}</p>
              {/if}
            </div>
            <div>
              <label class="label">
                <Clock class="w-4 h-4 inline mr-1" />开始时间
              </label>
              <input type="datetime-local" class="input" bind:value={form.shoot_time_start} />
            </div>
            <div>
              <label class="label">
                <Clock class="w-4 h-4 inline mr-1" />结束时间
              </label>
              <input
                type="datetime-local"
                class="input {formErrors.shoot_time_end ? 'border-red-500' : ''}"
                bind:value={form.shoot_time_end}
              />
              {#if formErrors.shoot_time_end}
                <p class="text-red-500 text-xs mt-1">{formErrors.shoot_time_end}</p>
              {/if}
            </div>
          </div>

          {#if checkingSchedule}
            <div class="p-3 bg-blue-50 rounded-lg text-blue-700 text-sm flex items-center">
              <Clock class="w-4 h-4 mr-2 animate-spin" />
              正在检测档期冲突...
            </div>
          {:else if scheduleConflict?.has_conflict}
            <div class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div class="flex items-start">
                <AlertCircle class="w-5 h-5 text-red-500 mr-3 mt-0.5 flex-shrink-0" />
                <div class="flex-1">
                  <p class="text-sm font-medium text-red-800">档期冲突！该摄影师在以下时间段已有预约：</p>
                  <ul class="mt-2 space-y-1">
                    {#each scheduleConflict.conflicting_orders as co}
                      <li class="text-sm text-red-700">
                        <span class="font-medium">{co.order_no}</span>
                        {#if co.customer_name}
                          （{co.customer_name}）
                        {/if}
                        ：{formatDateTime(co.shoot_time_start, 'MM-DD HH:mm')} - {formatDateTime(co.shoot_time_end, 'HH:mm')}
                        {#if co.city}
                          · {co.city}
                        {/if}
                      </li>
                    {/each}
                  </ul>
                  {#if formErrors.schedule}
                    <p class="text-red-500 text-xs mt-2">{formErrors.schedule}</p>
                  {/if}
                </div>
              </div>
            </div>
          {:else if form.photographer_id && form.shoot_time_start && form.shoot_time_end}
            <div class="p-3 bg-green-50 rounded-lg text-green-700 text-sm flex items-center">
              <CalendarCheck class="w-4 h-4 mr-2" />
              该时间段摄影师档期空闲
            </div>
          {/if}

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">照片总数</label>
              <input
                type="number"
                class="input"
                bind:value={form.total_photos}
                min="0"
                on:input={() => {
                  if (form.included_retouches > form.total_photos) {
                    formErrors.included_retouches = '精修数量不能超过照片总数';
                  } else {
                    delete formErrors.included_retouches;
                  }
                }}
              />
            </div>
            <div>
              <label class="label">含精修数量</label>
              <input
                type="number"
                class="input {formErrors.included_retouches ? 'border-red-500' : ''}"
                bind:value={form.included_retouches}
                min="0"
                max={form.total_photos}
                on:input={() => {
                  if (form.included_retouches > form.total_photos) {
                    formErrors.included_retouches = '精修数量不能超过照片总数';
                  } else {
                    delete formErrors.included_retouches;
                  }
                }}
              />
              {#if formErrors.included_retouches}
                <p class="text-red-500 text-xs mt-1">{formErrors.included_retouches}</p>
              {:else if form.total_photos > 0}
                <p class="text-gray-500 text-xs mt-1">最多 {form.total_photos} 张</p>
              {/if}
            </div>
          </div>
          <div>
            <label class="label">备注</label>
            <textarea class="input" rows="3" bind:value={form.notes}></textarea>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => { showCreateModal = false; resetForm(); }}>
              取消
            </button>
            <button
              type="submit"
              class="btn btn-primary flex-1"
              disabled={scheduleConflict?.has_conflict}
            >
              创建订单
            </button>
          </div>
        </form>
      </div>
    </div>
  {/if}

  {#if showAddCustomerModal}
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4">
      <div class="bg-white rounded-xl w-full max-w-md">
        <div class="p-6 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">新增客户</h2>
          <button class="text-gray-400 hover:text-gray-600" on:click={() => (showAddCustomerModal = false)}>
            <X class="w-5 h-5" />
          </button>
        </div>
        <form on:submit|preventDefault={handleAddCustomer} class="p-6 space-y-4">
          <div>
            <label class="label">客户姓名 <span class="text-red-500">*</span></label>
            <input
              type="text"
              class="input {newCustomerErrors.full_name || customerNameError ? 'border-red-500' : ''}"
              bind:value={newCustomerForm.full_name}
              placeholder="请输入中文姓名"
            />
            {#if newCustomerErrors.full_name}
              <p class="text-red-500 text-xs mt-1">{newCustomerErrors.full_name}</p>
            {:else if customerNameError && newCustomerForm.full_name}
              <p class="text-red-500 text-xs mt-1">{customerNameError}</p>
            {:else}
              <p class="text-gray-500 text-xs mt-1">仅限中文字符，不能包含空格、英文或数字</p>
            {/if}
          </div>
          <div>
            <label class="label">联系电话</label>
            <input
              type="text"
              class="input"
              bind:value={newCustomerForm.phone}
              placeholder="选填"
            />
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" class="btn btn-secondary flex-1" on:click={() => (showAddCustomerModal = false)}>
              取消
            </button>
            <button
              type="submit"
              class="btn btn-primary flex-1"
              disabled={!newCustomerForm.full_name || !!validateChineseName(newCustomerForm.full_name)}
            >
              添加客户
            </button>
          </div>
        </form>
      </div>
    </div>
  {/if}
</div>
