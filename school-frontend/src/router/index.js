import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import ScheduleView from '@/views/ScheduleView.vue'
import CreateStudentForm from '@/components/CreateStudentForm.vue'
import ReportsView from '@/views/ReportsView.vue'
import StudentList from '@/views/StudentList.vue'
import TeachersList from '@/views/TeachersList.vue'
import PublicSchedule from '@/views/PublicSchedule.vue'
import LevelTest from '@/views/LevelTest.vue'
import PaymentsView from '@/views/PaymentsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true }
    },
    {
      path: '/schedule',
      name: 'schedule',
      component: ScheduleView,
      meta: { requiresAuth: true }
    },
    {
      path: '/create-student',
      name: 'CreateStudent',
      component: CreateStudentForm,
      meta: { requiresAuth: true }
    },
    {
      path: '/reports',
      name: 'Reports',
      component: ReportsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/students',
      name: 'StudentList',
      component: StudentList,
      meta: { requiresAuth: true }
    },
    {
      path: '/teachers',
      name: 'TeachersList',
      component: TeachersList,
      meta: { requiresAuth: true }
    },
    {
      path: '/level-test',
      name: 'LevelTest',
      component: LevelTest
    },
    {
      path: '/payments',
      name: 'payments',
      component: PaymentsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/booking',
      name: 'PublicSchedule',
      component: PublicSchedule
    },
    {
      path: '/teacher/:id',
      name: 'TeacherDetail',
      component: () => import('@/views/TeacherDetail.vue'),
      meta: { requiresAuth: true }
    },
 {
    path: '/attendance',
    name: 'Attendance',
    component: () => import('@/views/AttendanceView.vue'),
    meta: { requiresAuth: true }
  }
]
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('auth_token')

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' })
  } else {
    next()
  }
})

export default router
