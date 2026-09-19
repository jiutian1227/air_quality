import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router'
import Clustering from '@/pages/Clustering.vue'
import EdaAnalysis from '@/pages/EdaAnalysis.vue'
import FeatureEngineering from '@/pages/FeatureEngineering.vue'
import PredictionAnalysis from '@/pages/PredictionAnalysis.vue'
import OnlinePrediction from '@/pages/OnlinePrediction.vue'
import HyperparameterTuning from '@/pages/HyperparameterTuning.vue'
import Login from '@/pages/Login.vue'
import Register from '@/pages/Register.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: Login, meta: { title: '登录', hideLayout: true } },
  { path: '/register', name: 'register', component: Register, meta: { title: '注册', hideLayout: true } },
  { path: '/eda', name: 'eda', component: EdaAnalysis, meta: { title: 'EDA数据分析' } },
  { path: '/feature', name: 'feature', component: FeatureEngineering, meta: { title: '特征工程' } },
  { path: '/clustering', name: 'clustering', component: Clustering, meta: { title: '聚类分析' } },
  { path: '/tuning', name: 'tuning', component: HyperparameterTuning, meta: { title: '超参数调优' } },
  { path: '/prediction', name: 'prediction', component: PredictionAnalysis, meta: { title: '预测分析' } },
  { path: '/online-prediction', name: 'online-prediction', component: OnlinePrediction, meta: { title: '在线预测' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const getCurrentUser = () => {
  try {
    return JSON.parse(window.localStorage.getItem('currentUser') || 'null')
  } catch {
    return null
  }
}

router.beforeEach((to, from, next) => {
  const currentUser = getCurrentUser()
  const publicPages = ['/login', '/register']
  const isPublicPage = publicPages.includes(to.path)

  if (!currentUser && !isPublicPage) {
    return next({ path: '/login' })
  }

  if (currentUser && to.path === '/login') {
    return next({ path: '/eda' })
  }

  return next()
})

export default router
