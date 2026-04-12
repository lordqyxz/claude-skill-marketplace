# Vue 3 实时通信模式

## 目录

1. [WebSocket 模式](#websocket-模式)
2. [SSE 流式模式](#sse-流式模式)
3. [AbortController 取消模式](#abortcontroller-取消模式)
4. [通用原则](#通用原则)

---

## WebSocket 模式

适用于双向实时通信：任务进度推送、协同编辑、实时通知等。

```ts
// composables/useWebSocket.ts
export function useWebSocket(url: string | Ref<string>) {
  const data = ref<any>(null)
  const status = ref<'connecting' | 'open' | 'closed' | 'error'>('closed')
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let pingTimer: ReturnType<typeof setInterval> | null = null

  function connect() {
    const wsUrl = toValue(url)
    ws = new WebSocket(wsUrl)
    status.value = 'connecting'

    ws.onopen = () => {
      status.value = 'open'
      startHeartbeat()
    }

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.type === 'pong') return
      data.value = msg
    }

    ws.onclose = (event) => {
      status.value = 'closed'
      // 非正常关闭时自动重连
      if (!event.wasClean) {
        reconnectTimer = setTimeout(connect, 3000)
      }
    }

    ws.onerror = () => {
      status.value = 'error'
    }
  }

  function startHeartbeat() {
    pingTimer = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  function send(message: any) {
    ws?.send(JSON.stringify(message))
  }

  function disconnect() {
    reconnectTimer && clearTimeout(reconnectTimer)
    pingTimer && clearInterval(pingTimer)
    ws?.close()
    ws = null
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { data, status, send, disconnect, connect }
}
```

### 关键点

- `onUnmounted` 中必须清理：关闭连接、清除心跳定时器、取消重连定时器
- 心跳机制防止连接因空闲被关闭（30 秒间隔常见）
- 非正常关闭（`!event.wasClean`）时自动重连
- 将 WebSocket 逻辑封装为 composable，避免在组件中直接管理连接生命周期

---

## SSE 流式模式

适用于服务端单向推送：AI 对话流、日志流、实时通知等。

### 方式一：fetch + ReadableStream（原生，最灵活）

```ts
// 适用于需要精细控制解析逻辑的场景
async function streamChat(messages: Message[]) {
  const controller = new AbortController()

  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
    signal: controller.signal,
  })

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      // 解析 SSE 格式：data: {...}\n\n
      const lines = chunk.split('\n').filter(line => line.startsWith('data: '))
      for (const line of lines) {
        const jsonStr = line.slice(6) // 去掉 "data: " 前缀
        if (jsonStr === '[DONE]') return
        const data = JSON.parse(jsonStr)
        // 处理数据...
      }
    }
  } finally {
    reader.releaseLock()
  }
}
```

### 方式二：fetchEventSource（推荐，自动重连 + 事件解析）

```ts
import { fetchEventSource } from '@microsoft/fetch-event-source'

async function streamChat(messages: Message[]) {
  const controller = new AbortController()

  await fetchEventSource('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
    signal: controller.signal,

    onmessage(event) {
      if (event.event === 'FatalError') {
        throw new Error(event.data)
      }
      const data = JSON.parse(event.data)
      // 处理数据...
    },

    onerror(err) {
      // 返回 undefined 自动重连，抛出错误停止
      if (err instanceof FatalError) throw err
    },

    open() {
      // 连接建立
    },

    close() {
      // 连接关闭
    },
  })
}
```

### 方式选择

| 方式 | 优势 | 劣势 |
|------|------|------|
| `fetch` + `ReadableStream` | 零依赖、完全控制 | 需手动解析 SSE 格式、无自动重连 |
| `fetchEventSource` | 自动重连、事件解析、标准 SSE | 额外依赖 |

---

## AbortController 取消模式

用于取消进行中的请求或流式响应，防止组件卸载后仍在消费资源。

```ts
const controller = ref<AbortController | null>(null)

async function startStream() {
  // 取消之前未完成的请求
  controller.value?.abort()
  controller.value = new AbortController()

  try {
    const response = await fetch('/api/stream', {
      signal: controller.value.signal,
    })
    // 处理响应...
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      // 正常取消，不需要处理
      return
    }
    throw err
  }
}

function stopStream() {
  controller.value?.abort()
  controller.value = null
}

onUnmounted(() => {
  controller.value?.abort()
})
```

### 关键点

- 每次新请求前取消前一个未完成的请求，避免竞态
- `AbortError` 是正常的取消行为，不要当作错误上报
- 在 `onUnmounted` 中确保中止所有进行中的请求

---

## 通用原则

1. **所有实时连接必须在 `onUnmounted` 中清理** — 关闭 WebSocket、中止 fetch、清除定时器
2. **封装为 composable** — 将连接管理、重连逻辑、清理逻辑集中管理
3. **处理重连** — 网络不稳定时自动重连，但需要退避策略避免无限重试
4. **心跳机制** — WebSocket 长连接需要心跳 ping 防止空闲断开
5. **竞态防护** — 使用 AbortController 或版本号确保不会处理过期响应
6. **错误上报** — 连接失败、重连失败等应有用户可见的提示