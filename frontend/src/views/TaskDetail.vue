<template>
  <div class="page">
    <div class="back-link" @click="$router.push(`/courses/${task?.course_id}`)">← 返回课程</div>

    <div v-if="loading" class="center">加载中...</div>
    <template v-else-if="task">
      <header>
        <div class="task-header-row">
          <h1>{{ task.title }}</h1>
          <span :class="['badge', `badge-${task.status}`]">{{ statusLabel(task.status) }}</span>
        </div>
        <p class="muted">{{ task.description }}</p>
      </header>

      <!-- Uploaded files -->
      <section v-if="task.files.length" class="section">
        <h3>上传的文件</h3>
        <ul class="file-list">
          <li v-for="f in task.files" :key="f.id">{{ f.filename }}</li>
        </ul>
      </section>

      <!-- Running state -->
      <div v-if="task.status === 'running'" class="status-box running">
        <div class="spinner" />
        <span>AI 正在生成作业，请稍候...</span>
      </div>

      <!-- Failed state -->
      <div v-else-if="task.status === 'failed'" class="status-box failed">
        <p>生成失败</p>
        <pre v-if="task.result?.error_message" class="error-msg">{{ task.result.error_message }}</pre>
      </div>

      <!-- Done: PDF preview -->
      <section v-else-if="task.status === 'done' && task.result?.pdf_path" class="section">
        <h3>生成结果</h3>
        <iframe :src="pdfUrl" class="pdf-preview" />
      </section>

      <!-- Retry -->
      <section v-if="task.status === 'done' || task.status === 'failed'" class="section">
        <div v-if="!showRetry">
          <button class="btn-secondary" @click="showRetry = true">不满意？重新生成</button>
        </div>
        <div v-else class="retry-box">
          <label>告诉 AI 哪里不满意（可选）</label>
          <textarea v-model="retryFeedback" rows="3" placeholder="例如：格式不对，请用更清晰的符号..." />
          <div class="modal-actions">
            <button class="btn-secondary" @click="showRetry = false">取消</button>
            <button class="btn-primary" @click="submitRetry">重新生成</button>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getTask, getTaskStatus, retryTask, runTask, getPdfUrl, type Task } from '../api'

const route = useRoute()
const taskId = Number(route.params.id)

const task = ref<Task | null>(null)
const loading = ref(true)
const showRetry = ref(false)
const retryFeedback = ref('')
let pollTimer: ReturnType<typeof setInterval> | null = null

const pdfUrl = computed(() => task.value ? getPdfUrl(task.value.id) : '')

onMounted(async () => {
  task.value = await getTask(taskId)
  loading.value = false
  startPolling()
})

onUnmounted(() => stopPolling())

function startPolling() {
  if (task.value?.status === 'running' || task.value?.status === 'pending') {
    pollTimer = setInterval(poll, 3000)
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function poll() {
  const s = await getTaskStatus(taskId)
  if (task.value) task.value.status = s.status
  if (s.status === 'done' || s.status === 'failed') {
    stopPolling()
    task.value = await getTask(taskId)
  }
}

async function submitRetry() {
  await retryTask(taskId, retryFeedback.value)
  await runTask(taskId)
  showRetry.value = false
  retryFeedback.value = ''
  task.value = await getTask(taskId)
  startPolling()
}

function statusLabel(s: string) {
  return { pending: '等待中', running: '生成中', done: '已完成', failed: '失败' }[s] ?? s
}
</script>
