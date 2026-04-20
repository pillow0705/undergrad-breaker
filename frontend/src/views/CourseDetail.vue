<template>
  <div class="page">
    <div class="back-link" @click="$router.push('/')">← 返回课程列表</div>

    <div v-if="loading" class="center">加载中...</div>
    <template v-else-if="course">
      <header>
        <h1>{{ course.name }}</h1>
        <p class="muted">{{ course.description }}</p>
      </header>

      <!-- Public materials -->
      <section class="section">
        <div class="section-header">
          <h2>公共资料区</h2>
          <label class="btn-secondary file-btn">
            上传资料
            <input type="file" multiple @change="handleMaterialUpload" hidden />
          </label>
        </div>
        <div v-if="course.materials.length === 0" class="muted">暂无资料，上传讲义、课本等文件</div>
        <ul class="file-list">
          <li v-for="m in course.materials" :key="m.id">
            <span>{{ m.filename }}</span>
            <button class="btn-danger-sm" @click="removeMaterial(m.id)">删除</button>
          </li>
        </ul>
      </section>

      <!-- Tasks -->
      <section class="section">
        <div class="section-header">
          <h2>任务列表</h2>
          <button class="btn-primary" @click="showNewTask = true">+ 新建任务</button>
        </div>
        <div v-if="course.tasks.length === 0" class="muted">暂无任务</div>
        <div class="task-list">
          <div
            v-for="t in course.tasks"
            :key="t.id"
            class="task-row"
            @click="$router.push(`/tasks/${t.id}`)"
          >
            <div class="task-info">
              <span class="task-title">{{ t.title }}</span>
              <span class="task-date muted">{{ formatDate(t.created_at) }}</span>
            </div>
            <span :class="['badge', `badge-${t.status}`]">{{ statusLabel(t.status) }}</span>
          </div>
        </div>
      </section>
    </template>

    <!-- New task modal -->
    <div v-if="showNewTask" class="modal-overlay" @click.self="showNewTask = false">
      <div class="modal">
        <h2>新建任务</h2>
        <label>任务标题</label>
        <input v-model="taskTitle" placeholder="例如：第一次作业" />
        <label>任务描述 / 要求</label>
        <textarea v-model="taskDesc" placeholder="描述本次作业的要求..." rows="4" />
        <label>上传作业文件（可选）</label>
        <input type="file" multiple @change="handleTaskFiles" />
        <div class="modal-actions">
          <button class="btn-secondary" @click="showNewTask = false">取消</button>
          <button class="btn-primary" :disabled="!taskTitle.trim()" @click="submitTask">创建并提交</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getCourse, uploadMaterial, deleteMaterial,
  createTask, runTask, type CourseDetail,
} from '../api'

const route = useRoute()
const router = useRouter()
const courseId = Number(route.params.id)

const course = ref<CourseDetail | null>(null)
const loading = ref(true)
const showNewTask = ref(false)
const taskTitle = ref('')
const taskDesc = ref('')
const taskFiles = ref<File[]>([])

onMounted(async () => {
  course.value = await getCourse(courseId)
  loading.value = false
})

async function handleMaterialUpload(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files) return
  for (const f of Array.from(files)) {
    const m = await uploadMaterial(courseId, f)
    course.value!.materials.push(m)
  }
}

async function removeMaterial(mid: number) {
  await deleteMaterial(courseId, mid)
  course.value!.materials = course.value!.materials.filter(m => m.id !== mid)
}

function handleTaskFiles(e: Event) {
  const files = (e.target as HTMLInputElement).files
  taskFiles.value = files ? Array.from(files) : []
}

async function submitTask() {
  const task = await createTask(courseId, taskTitle.value.trim(), taskDesc.value.trim(), taskFiles.value)
  await runTask(task.id)
  showNewTask.value = false
  taskTitle.value = ''
  taskDesc.value = ''
  taskFiles.value = []
  router.push(`/tasks/${task.id}`)
}

function statusLabel(s: string) {
  return { pending: '等待中', running: '生成中', done: '已完成', failed: '失败' }[s] ?? s
}
function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN')
}
</script>
