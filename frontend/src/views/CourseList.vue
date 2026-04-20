<template>
  <div class="page">
    <header>
      <h1>本科破局系统</h1>
      <button class="btn-primary" @click="showCreate = true">+ 新建课程</button>
    </header>

    <div v-if="loading" class="center">加载中...</div>
    <div v-else-if="courses.length === 0" class="center muted">还没有课程，点击右上角新建</div>
    <div class="course-grid" v-else>
      <div
        v-for="c in courses"
        :key="c.id"
        class="course-card"
        @click="$router.push(`/courses/${c.id}`)"
      >
        <h2>{{ c.name }}</h2>
        <p class="muted">{{ c.description || '暂无描述' }}</p>
        <span class="date">{{ formatDate(c.created_at) }}</span>
      </div>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <h2>新建课程</h2>
        <label>课程名称</label>
        <input v-model="newName" placeholder="例如：回归分析" />
        <label>描述（可选）</label>
        <textarea v-model="newDesc" placeholder="课程简介..." rows="3" />
        <div class="modal-actions">
          <button class="btn-secondary" @click="showCreate = false">取消</button>
          <button class="btn-primary" :disabled="!newName.trim()" @click="submitCreate">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCourses, createCourse, type Course } from '../api'

const router = useRouter()
const courses = ref<Course[]>([])
const loading = ref(true)
const showCreate = ref(false)
const newName = ref('')
const newDesc = ref('')

onMounted(async () => {
  courses.value = await getCourses()
  loading.value = false
})

async function submitCreate() {
  const c = await createCourse(newName.value.trim(), newDesc.value.trim())
  courses.value.unshift(c)
  showCreate.value = false
  newName.value = ''
  newDesc.value = ''
  router.push(`/courses/${c.id}`)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('zh-CN')
}
</script>
