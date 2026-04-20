import { createRouter, createWebHistory } from 'vue-router'
import CourseList from '../views/CourseList.vue'
import CourseDetail from '../views/CourseDetail.vue'
import TaskDetail from '../views/TaskDetail.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: CourseList },
    { path: '/courses/:id', component: CourseDetail },
    { path: '/tasks/:id', component: TaskDetail },
  ],
})
