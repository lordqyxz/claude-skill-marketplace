---
name: vue3-sfc
description: |
  Vue 3 SFC 开发、修改、评审通用技能。用于编写、修改、审查 *.vue 文件，遵循 Vue 3 Composition API + script setup 最佳实践。覆盖响应式、类型安全、性能优化、实时通信、文件处理等核心场景。

  TRIGGER when: 创建或编写 Vue 组件、修改 .vue 文件、评审 Vue 代码、重构 Vue 组件、Vue 文件 code review、修复 Vue 组件 bug、优化 Vue 性能、添加 Vue 组件功能。即使用户没有明确说"Vue skill"，只要涉及 .vue 文件操作就应触发。

  Keywords: .vue, Vue, SFC, Composition API, script setup, component, 组件, Pinia, reactive, ref, defineProps, defineEmits, computed, watch, composable
---

# Vue 3 SFC 开发规范与评审指南

## Role

你是 Vue 3 SFC 专家，精通 Composition API + `<script setup>` 规范。处理 .vue 文件时，严格遵循本技能的规范和模式，产出高质量、类型安全、性能优良的代码。

## Workflow

### 创建新组件

1. 按"一、SFC 结构规范"搭建文件骨架
2. 确定状态管理方式（ref/reactive/computed/外部 store）
3. 编写代码，遵循响应式、类型安全、性能规范
4. 用"十、评审检查清单"自检

### 修改现有组件

1. 先读取目标 .vue 文件理解现有结构
2. 保持与文件现有风格一致（除非违反规范）
3. 应用修改，注意不破坏响应性链路
4. 用评审检查清单验证变更部分

### 评审 .vue 文件

1. 读取目标文件
2. 逐项对照"十、评审检查清单"
3. 按以下格式输出评审报告：

```markdown
## [文件名] 评审报告

### 🔴 必须修复
- **[行号]** 问题描述 → 修复建议（含代码片段）

### 🟡 建议改进
- **[行号]** 问题描述 → 建议做法

### 🟢 推荐优化
- 优化建议

### 总结
- 总体评分：X/10
- 关键改进方向
```

## 一、SFC 结构规范

### 文件元素顺序

```vue
<script setup lang="ts">
// 1. 类型导入 (import type)
// 2. 值导入 (import)
// 3. 宏定义 (defineOptions, defineProps, defineEmits, defineExpose, defineSlots)
// 4. 组合式函数调用 (composables)
// 5. 响应式状态 (ref, reactive)
// 6. 计算属性 (computed)
// 7. 方法 (普通函数)
// 8. 侦听器 (watch, watchEffect)
// 9. 生命周期钩子 (onMounted, onUnmounted, 等)
</script>

<template>
  <!-- 模板 -->
</template>

<style scoped>
  /* 样式 */
</style>
```

### 关键规则

- 始终使用 `<script setup lang="ts">`，不使用 Options API
- `<style>` 始终在最后
- 每个组件文件只包含一个组件
- 所有组件名必须是多词组合（避免与 HTML 元素冲突）

## 二、响应式数据

### ref vs reactive 决策

| 场景 | 选择 | 原因 |
|------|------|------|
| 基本类型值 | `ref()` | `reactive` 不支持基本类型 |
| 需要整体替换的对象/数组 | `ref()` | `reactive` 不能直接重新赋值 |
| 表单等分组相关状态 | `reactive()` | 更简洁，无需 `.value` |
| 模板引用 | `ref()` 或 `useTemplateRef()` | 专用场景 |
| 组合式函数返回值 | `ref()` | 可安全解构 |
| 不确定时 | `ref()` | ref 是更安全的选择 |

### 常见陷阱

```ts
// ❌ 解构 reactive 对象 — 丢失响应性
const { name, age } = reactive(user)
// ✅ 用 toRefs 保持响应性
const { name, age } = toRefs(reactive(user))

// ❌ 直接重新赋值 reactive
state = newState
// ✅ 用 Object.assign 或切换为 ref
Object.assign(state, newState)

// ❌ 将 props 属性直接传入组合式函数
useFetch(props.url)  // 丢失响应性
// ✅ 用 toRefs 或 toRef
const { url } = toRefs(props)
useFetch(url)

// ❌ 不必要的响应式包装
const staticConfig = reactive({ ... })  // 不会变化的数据
// ✅ 只对实际变化的数据使用响应式
const staticConfig = { ... }
```

## 三、Props 和 Emits

### 类型声明方式（优先）

```vue
<script setup lang="ts">
// Props — 类型声明 + 解构默认值 (Vue 3.5+)
const { title, count = 0, items = [] } = defineProps<{
  title: string
  count?: number
  items?: string[]
}>()

// Emits — 命名元组语法 (Vue 3.3+)
const emit = defineEmits<{
  change: [id: number]
  update: [value: string]
}>()
</script>
```

### 规则

- 必须为 props 定义类型（Priority A 规则）
- Props 在 JS 中用 camelCase，在模板中用 kebab-case
- 运行时声明仅当需要 validator 时使用
- 优先使用类型声明，而非运行时声明

## 四、组合式函数 (Composables)

```ts
// composables/useFetch.ts — 文件以 use 前缀命名
export function useFetch<T>(url: string | Ref<string>) {
  const data = ref<T | null>(null)
  const error = ref<Error | null>(null)
  const loading = ref(false)

  async function execute() {
    loading.value = true
    try {
      data.value = await fetch(toValue(url)).then(r => r.json())
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  onMounted(execute)
  // 返回普通对象 — 支持解构且保持响应性
  return { data, error, loading, execute }
}
```

### 规则

- 文件名和函数名以 `use` 开头
- 接受 Ref 或 Getter 作为参数时，用 `toValue()` 转换
- 返回普通对象（非 reactive），包含多个 ref
- DOM 副效应在 `onMounted` 中执行，在 `onUnmounted` 中清理
- 只在 `<script setup>` 或 `setup()` 中同步调用
- 无响应式状态的纯函数，导出为普通工具函数即可
- 发现重复逻辑跨多个组件时，提取为 composable

## 五、实时通信模式

详情 → `references/realtime-patterns.md`

| 模式 | 适用场景 |
|------|----------|
| WebSocket | 双向实时通信（任务进度、协同编辑） |
| SSE (fetch + ReadableStream) | 服务端推送流（AI 对话、日志流） |
| `fetchEventSource` | SSE 的增强库（自动重连、事件解析） |
| `AbortController` | 取消进行中的请求或流式响应 |

关键原则：所有实时连接必须在 `onUnmounted` 中清理（关闭连接、清除定时器、中止请求）。

## 六、文件处理模式

详情 → `references/file-handling.md`

| 模式 | 要点 |
|------|------|
| 文件上传 | `before-upload` 阻止自动上传 + 手动 POST (FormData)，或使用 UI 框架上传组件 |
| 文件下载 | Blob + `URL.createObjectURL()` + 触发下载 |
| 文件预览 | 根据文件类型动态选择渲染器（PDF/Office/图片） |

## 七、性能优化

| 技术 | 适用场景 | 详情 |
|------|----------|------|
| `v-memo` | 大列表中只有部分项需要更新 | → `references/performance.md` |
| `shallowRef` | 大型数据结构（10000+ 属性访问） | 替代深响应式 |
| `defineAsyncComponent` | 非首屏必需的重量级组件 | 按需加载 |
| `KeepAlive` | 频繁切换的标签页组件 | 配合 `max` 限制缓存数量 |
| 虚拟滚动 | 超长列表（1000+ 项） | 使用 vue-virtual-scroller |

原则：先分析性能瓶颈，再优化。Vue 的响应式系统对几百项的列表已经足够快。

## 八、模板与样式规范

### 模板

```vue
<!-- ✅ 指令缩写一致 -->
<a :href="url" @click="handleClick">

<!-- ✅ 多属性换行对齐 -->
<MyComponent
  :data="list"
  :loading="loading"
  @submit="handleSubmit"
>

<!-- ❌ v-if 和 v-for 不能在同一元素上 -->
<div v-for="item in list" v-if="item.active">

<!-- ✅ 用 computed 过滤 -->
<div v-for="item in activeList" :key="item.id">
```

### 样式

```vue
<style scoped>
.container {
  .title { }                    /* ✅ 类选择器 */
  :deep(.child-class) { }       /* ✅ 覆盖子组件样式 */
  :slotted(.content) { }        /* ✅ 插槽内容样式 */
  :global(.global-class) { }    /* ✅ 全局样式 */
}
</style>
```

- 避免在 scoped 样式中使用标签选择器（`p`, `div`），用类选择器替代
- 需要 CSS 变量绑定时用 `v-bind()`: `color: v-bind('theme.primary')`

## 九、错误处理

```ts
// 捕获后代组件错误 — 用于 Error Boundary 模式
onErrorCaptured((err, instance, info) => {
  hasError.value = true
  return false  // 阻止冒泡
})

// 全局错误处理（main.ts）
app.config.errorHandler = (err) => { /* 上报 */ }
```

`onErrorCaptured` 不捕获当前组件自身的错误，只捕获后代组件的错误。

## 十、组件通信

| 场景 | 方式 |
|------|------|
| 父 → 子 | Props |
| 子 → 父 | Emits |
| 跨层级 | Provide / Inject（用 `InjectionKey<T>` 保持类型安全） |
| 全局状态 | Pinia Store |
| 跨组件事件 | 事件总线或 Pinia action |

## 十一、评审检查清单

审查 .vue 文件时，逐项检查：

### 结构与规范
- [ ] 使用 `<script setup lang="ts">` 而非 Options API
- [ ] 文件元素顺序正确：script → template → style
- [ ] 组件名为多词组合
- [ ] 每文件一个组件

### 类型安全
- [ ] Props 有类型声明（非仅运行时声明）
- [ ] Emits 有类型声明
- [ ] ref/reactive 有泛型类型（避免 `any`）
- [ ] 使用 `import type` 导入纯类型

### 响应式
- [ ] 没有解构 reactive 对象（除非用 toRefs）
- [ ] 没有直接重新赋值 reactive 对象
- [ ] 组合式函数接收 Ref 参数时使用 toValue/toRefs
- [ ] 事件监听器、定时器在 onUnmounted 中清理

### 模板与样式
- [ ] v-for 有 :key（且 key 唯一稳定）
- [ ] v-if 和 v-for 不在同一元素
- [ ] 使用 `<style scoped>`（App 和 layout 除外）
- [ ] 不使用标签选择器在 scoped 样式中
- [ ] 覆盖子组件样式用 `:deep()`

### 性能
- [ ] 大列表考虑虚拟滚动或 v-memo
- [ ] 重量级组件考虑异步加载
- [ ] 不对静态数据使用响应式包装
- [ ] watch 使用精确路径而非不必要的 deep: true

### 代码质量
- [ ] 无调试遗留的 `console.log`
- [ ] API 调用风格一致（async/await 或 .then()，不混用）
- [ ] 无直接 DOM 操作（优先用 ref + 声明式方式）
- [ ] 实时连接（WebSocket/SSE）在组件卸载时正确清理
- [ ] 文件上传/下载有错误处理

### 安全
- [ ] 不在模板中直接渲染用户 HTML（v-html 需消毒）
- [ ] API 调用有错误处理
- [ ] 不暴露敏感数据到前端

---

## 参考文档

按需读取，不要一次性全部加载：
- 需要性能优化细节时 → `references/performance.md`
- 需要实时通信模式（WebSocket/SSE/流式）时 → `references/realtime-patterns.md`
- 需要文件处理模式（上传/下载/预览）时 → `references/file-handling.md`