# Vue 3 性能优化详细指南

## 目录

1. [响应式优化](#响应式优化)
2. [渲染优化](#渲染优化)
3. [代码分割与懒加载](#代码分割与懒加载)
4. [组件缓存](#组件缓存)
5. [大列表优化](#大列表优化)
6. [网络与数据层优化](#网络与数据层优化)

---

## 响应式优化

### shallowRef 与 shallowReactive

当处理大型数据结构时（10000+ 属性访问），深响应式的 Proxy 代理开销显著。

```ts
// 大型表格数据 — 只需在整体替换时触发更新
const tableData = shallowRef<Record[]>([])

// ❌ 不会触发更新
tableData.value.push(newRow)
tableData.value[0].name = 'changed'

// ✅ 替换整个值触发更新
tableData.value = [...tableData.value, newRow]
tableData.value = tableData.value.map((row, i) =>
  i === 0 ? { ...row, name: 'changed' } : row
)
```

### 避免不必要的响应式

```ts
// ❌ 不会变化的数据不需要响应式
const statusMap = reactive({
  active: '启用',
  inactive: '停用'
})

// ✅ 用普通对象
const statusMap = {
  active: '启用',
  inactive: '停用'
} as const
```

### watch 精确追踪

```ts
// ❌ 深度监听整个对象 — 性能差
watch(
  () => state,
  (newVal) => { /* ... */ },
  { deep: true }
)

// ✅ 只监听需要的路径
watch(
  () => state.user.email,
  (newEmail) => { /* ... */ }
)
```

### computed 缓存

```ts
// ✅ computed 自动缓存 — 依赖不变就不会重算
const filteredList = computed(() =>
  list.value.filter(item => item.active)
)

// ❌ 方法调用 — 每次渲染都执行
function getFilteredList() {
  return list.value.filter(item => item.active)
}
```

---

## 渲染优化

### v-memo 指令 (Vue 3.2+)

```vue
<!-- 只有 selectedId 变化时才重新渲染该项 -->
<div
  v-for="item in list"
  :key="item.id"
  v-memo="[item.id === selectedId]"
>
  <span>{{ item.name }}</span>
  <span v-if="item.id === selectedId">已选中</span>
</div>
```

- 必须和 `v-for` 在同一元素上
- `v-memo="[]"` 等同于 `v-once`
- **先分析再优化** — 几百项的列表不需要 v-memo

### v-once 指令

```vue
<!-- 只渲染一次，后续更新跳过 -->
<h1 v-once>{{ siteTitle }}</h1>
```

### 稳定的 Props

```vue
<!-- ❌ 每次渲染都创建新对象 — 子组件总认为 props 变了 -->
<Child :config="{ theme: 'dark' }" />

<!-- ✅ 用 computed 返回稳定引用 -->
<script setup>
const childConfig = computed(() => ({ theme: theme.value }))
</script>
<Child :config="childConfig" />
```

---

## 代码分割与懒加载

### 路由级懒加载

```ts
// router/routes.ts
const routes = [
  {
    path: '/dashboard',
    component: () => import('@/views/dashboard/index.vue')
  },
  {
    path: '/report',
    component: () => import('@/views/report/index.vue')
  }
]
```

### 组件级异步加载

```ts
// 非首屏必需的重量级组件
const HeavyChart = defineAsyncComponent(() =>
  import('@/components/HeavyChart.vue')
)
```

### 动态 import 配合条件渲染

```vue
<script setup>
import { defineAsyncComponent, ref } from 'vue'

const showDialog = ref(false)
const HeavyModal = defineAsyncComponent(() =>
  import('./HeavyModal.vue')
)
</script>

<template>
  <!-- 只在需要时才加载 -->
  <HeavyModal v-if="showDialog" />
</template>
```

---

## 组件缓存

### KeepAlive

```vue
<!-- 缓存切换的标签页组件 -->
<KeepAlive :include="['ProjectList', 'EventList']" :max="5">
  <component :is="currentTab" />
</KeepAlive>
```

**注意：**
- 组件必须声明 `name` 选项才能被 `include`/`exclude` 匹配
- 设置 `max` 限制缓存数量，防止内存泄漏
- 在 `onDeactivated` 中清理定时器/监听器（不仅是 `onUnmounted`）
- 不要缓存敏感页面（登录、支付等）

---

## 大列表优化

### 虚拟滚动

当列表超过 1000 项时，考虑虚拟滚动——只渲染可视区域内的 DOM 节点。

```ts
// 使用 @tanstack/vue-virtual 或 vue-virtual-scroller
import { useVirtualizer } from '@tanstack/vue-virtual'

const virtualizer = useVirtualizer({
  count: items.value.length,
  getScrollElement: () => scrollRef.value,
  estimateSize: () => 48,
})
```

### 分页加载

```ts
// 滚动到底部加载更多
const { data, loadMore, hasMore } = useInfiniteScroll(fetchAPI)
```

---

## 网络与数据层优化

### 请求去重与缓存

```ts
// 使用 vue-request（项目已有此依赖）
import { useRequest } from 'vue-request'

const { data, loading, error } = useRequest(fetchProjectList, {
  cacheKey: 'project-list',
  cacheTime: 300000, // 5分钟缓存
})
```

### 请求取消

```ts
// 组件卸载时取消未完成的请求
const controller = new AbortController()

onMounted(async () => {
  const data = await fetch('/api/data', { signal: controller.signal })
})

onUnmounted(() => {
  controller.abort()
})
```

### 并行请求

```ts
// ❌ 串行等待
const users = await fetchUsers()
const projects = await fetchProjects()

// ✅ 并行请求
const [users, projects] = await Promise.all([
  fetchUsers(),
  fetchProjects()
])
```