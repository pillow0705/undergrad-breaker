import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export interface Course {
  id: number
  name: string
  description: string
  created_at: string
}

export interface Material {
  id: number
  course_id: number
  filename: string
  created_at: string
}

export interface TaskSummary {
  id: number
  title: string
  description: string
  status: string
  created_at: string
}

export interface TaskFile {
  id: number
  filename: string
}

export interface TaskResult {
  id: number
  pdf_path: string | null
  latex_source: string | null
  error_message: string | null
  created_at: string
}

export interface Task extends TaskSummary {
  course_id: number
  files: TaskFile[]
  result: TaskResult | null
}

export interface CourseDetail extends Course {
  materials: Material[]
  tasks: TaskSummary[]
}

// Courses
export const getCourses = () => api.get<Course[]>('/courses').then(r => r.data)
export const createCourse = (name: string, description: string) =>
  api.post<Course>('/courses', { name, description }).then(r => r.data)
export const getCourse = (id: number) =>
  api.get<CourseDetail>(`/courses/${id}`).then(r => r.data)

// Materials
export const uploadMaterial = (courseId: number, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<Material>(`/courses/${courseId}/materials`, form).then(r => r.data)
}
export const deleteMaterial = (courseId: number, materialId: number) =>
  api.delete(`/courses/${courseId}/materials/${materialId}`)

// Tasks
export const createTask = (courseId: number, title: string, description: string, files: File[]) => {
  const form = new FormData()
  form.append('title', title)
  form.append('description', description)
  files.forEach(f => form.append('files', f))
  return api.post<Task>(`/courses/${courseId}/tasks`, form).then(r => r.data)
}
export const getTask = (id: number) =>
  api.get<Task>(`/tasks/${id}`).then(r => r.data)
export const getTaskStatus = (id: number) =>
  api.get<{ task_id: number; status: string; has_pdf: boolean }>(`/tasks/${id}/status`).then(r => r.data)
export const retryTask = (id: number, feedback: string) => {
  const form = new FormData()
  form.append('feedback', feedback)
  return api.post(`/tasks/${id}/retry`, form).then(r => r.data)
}
export const runTask = (id: number) =>
  api.post(`/tasks/${id}/run`).then(r => r.data)

export const getPdfUrl = (taskId: number) =>
  `http://localhost:8000/tasks/${taskId}/result/pdf`
