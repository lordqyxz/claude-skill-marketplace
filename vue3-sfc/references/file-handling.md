# Vue 3 文件处理模式

## 目录

1. [文件上传](#文件上传)
2. [文件下载](#文件下载)
3. [文件预览](#文件预览)
4. [拖拽调整面板](#拖拽调整面板)

---

## 文件上传

### 方式一：UI 框架上传组件（自动上传）

大多数 UI 框架提供上传组件，自动处理请求：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ui-framework' // 替换为实际框架

const fileList = ref([])

const handleChange = (info: any) => {
  if (info.file.status === 'done') {
    message.success('上传成功')
  } else if (info.file.status === 'error') {
    message.error('上传失败')
  }
}
</script>

<template>
  <Upload
    action="/api/upload"
    :file-list="fileList"
    @change="handleChange"
  >
    <Button>点击上传</Button>
  </Upload>
</template>
```

### 方式二：手动控制上传（before-upload 阻止自动上传）

需要自定义上传逻辑时（加密、压缩、分片、带额外参数），用 `before-upload` 阻止自动上传，然后手动 POST：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { message } from 'ui-framework'

const fileList = ref([])
const uploading = ref(false)

// 阻止自动上传 — 返回 false 或 Upload.LIST_IGNORE
const beforeUpload = (file: File) => {
  // 校验文件类型
  const isValidType = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)
  if (!isValidType) {
    message.error('仅支持 PDF 和 DOCX 文件')
    return false // 或 Upload.LIST_IGNORE
  }

  // 校验文件大小（10MB）
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('文件大小不能超过 10MB')
    return false
  }

  return false // 阻止自动上传
}

const handleManualUpload = async () => {
  const formData = new FormData()
  fileList.value.forEach((file: any) => {
    formData.append('files', file.originFileObj || file)
  })
  // 添加额外参数
  formData.append('projectId', currentProjectId.value)

  uploading.value = true
  try {
    await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    })
    message.success('上传成功')
  } catch (error) {
    message.error('上传失败')
  } finally {
    uploading.value = false
  }
}
</script>
```

### 拖拽上传区域

```vue
<template>
  <Upload.Dragger
    :before-upload="beforeUpload"
    :file-list="fileList"
    @change="handleChange"
  >
    <p class="upload-icon">📂</p>
    <p>点击或拖拽文件到此区域上传</p>
    <p class="upload-hint">支持 PDF、DOCX、Excel 格式</p>
  </Upload.Dragger>
</template>
```

---

## 文件下载

### Blob 下载（最通用）

适用于 API 返回二进制流或需要生成文件内容的场景：

```ts
async function downloadFile(fileId: string, fileName: string) {
  try {
    const response = await fetch(`/api/files/${fileId}/download`)
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    link.click()

    // 释放 Blob URL 防止内存泄漏
    URL.revokeObjectURL(url)
  } catch (error) {
    message.error('下载失败')
  }
}
```

### 封装为 composable

```ts
// composables/useFileDownload.ts
export function useFileDownload() {
  const downloading = ref(false)

  async function download(url: string, fileName: string) {
    downloading.value = true
    try {
      const response = await fetch(url)
      const blob = await response.blob()
      const objectUrl = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = objectUrl
      link.download = fileName
      link.click()

      URL.revokeObjectURL(objectUrl)
    } finally {
      downloading.value = false
    }
  }

  return { downloading, download }
}
```

### 注意

- `URL.createObjectURL()` 创建的 URL 必须在不需要时调用 `URL.revokeObjectURL()` 释放，否则会内存泄漏
- 大文件下载应考虑进度展示（使用 `ReadableStream` 读取 + 统计已下载字节）

---

## 文件预览

根据文件类型动态选择渲染器：

```vue
<script setup lang="ts">
const props = defineProps<{
  fileUrl: string
  fileName: string
}>()

const fileType = computed(() => {
  const ext = props.fileName.split('.').pop()?.toLowerCase()
  if (['pdf'].includes(ext!)) return 'pdf'
  if (['doc', 'docx'].includes(ext!)) return 'docx'
  if (['xls', 'xlsx'].includes(ext!)) return 'excel'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext!)) return 'image'
  return 'unknown'
})
</script>

<template>
  <div class="file-preview">
    <PdfRenderer v-if="fileType === 'pdf'" :src="fileUrl" />
    <DocxRenderer v-else-if="fileType === 'docx'" :src="fileUrl" />
    <ExcelRenderer v-else-if="fileType === 'excel'" :src="fileUrl" />
    <img v-else-if="fileType === 'image'" :src="fileUrl" />
    <p v-else>不支持预览此文件类型</p>
  </div>
</template>
```

### 常用预览库

| 文件类型 | 库 | 说明 |
|----------|-----|------|
| PDF | `@vue-office/pdf` 或 `vue-pdf-embed` | 渲染 PDF 页面 |
| DOCX | `@vue-office/docx` | 渲染 Word 文档 |
| Excel | `@vue-office/excel` | 渲染 Excel 表格 |
| 图片 | 原生 `<img>` | 无需额外库 |

`@vue-office/*` 系列库 API 统一，适合多种文件类型的预览场景。

---

## 拖拽调整面板

多面板可调整宽度的布局是常见的 UI 模式，应提取为 composable：

```ts
// composables/useResizablePanels.ts
export function useResizablePanels(options: {
  initialWidths: number[]  // 初始宽度百分比
  minWidths?: number[]     // 最小宽度百分比
}) {
  const widths = ref(options.initialWidths)
  const isResizing = ref(false)
  let startIndex = -1

  function startResize(index: number, event: MouseEvent) {
    startIndex = index
    isResizing.value = true
    event.preventDefault()

    const handleMove = (e: MouseEvent) => {
      const container = (event.target as HTMLElement).parentElement
      if (!container) return
      const containerWidth = container.offsetWidth
      const deltaX = e.clientX - event.clientX
      const deltaPercent = (deltaX / containerWidth) * 100

      const newWidths = [...widths.value]
      const minWidth = options.minWidths?.[startIndex] ?? 10

      if (newWidths[startIndex] + deltaPercent >= minWidth &&
          newWidths[startIndex + 1] - deltaPercent >= minWidth) {
        newWidths[startIndex] += deltaPercent
        newWidths[startIndex + 1] -= deltaPercent
        widths.value = newWidths
      }
    }

    const handleUp = () => {
      isResizing.value = false
      startIndex = -1
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleUp)
    }

    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleUp)
  }

  return { widths, isResizing, startResize }
}
```

### 关键点

- `mouseup` 时必须移除 `mousemove` 和 `mouseup` 事件监听
- 限制最小宽度防止面板被完全压缩
- 拖拽过程中用 `user-select: none` 防止文本选中干扰