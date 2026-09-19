<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import SlideVerify from 'vue3-slide-verify'
import 'vue3-slide-verify/dist/style.css'
import { X } from 'lucide-vue-next'

const router = useRouter()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const errorMsg = ref('')
const successMsg = ref('')
const loading = ref(false)
const showModal = ref(false)
const sliderKey = ref(0)
const slideVerifyRef = ref<InstanceType<typeof SlideVerify> | null>(null)

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const checkForm = () => {
  errorMsg.value = ''
  successMsg.value = ''
  
  if (!username.value.trim()) {
    errorMsg.value = '请输入用户名'
    return false
  }
  
  if (!password.value) {
    errorMsg.value = '请输入密码'
    return false
  }
  
  if (!confirmPassword.value) {
    errorMsg.value = '请确认密码'
    return false
  }
  
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return false
  }

  return true
}

const handleRegisterClick = () => {
  if (checkForm()) {
    sliderKey.value++
    showModal.value = true
  }
}

const closeModal = () => {
  showModal.value = false
}

const onSlideSuccess = () => {
  closeModal()
  submitRegister()
}

const onSlideFail = () => {
  nextTick(() => {
    if (slideVerifyRef.value && typeof slideVerifyRef.value.reset === 'function') {
      slideVerifyRef.value.reset()
    }
  })
}

const onRefresh = () => {
  nextTick(() => {
    if (slideVerifyRef.value && typeof slideVerifyRef.value.reset === 'function') {
      slideVerifyRef.value.reset()
    }
  })
}

const submitRegister = async () => {
  loading.value = true

  try {
    const response = await fetch(`${apiBaseUrl}/api/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username.value.trim(),
        password: password.value,
        role: 2,
      }),
    })

    const data = await response.json()
    if (!response.ok) {
      errorMsg.value = data.detail || '注册失败，请检查输入信息'
      return
    }

    successMsg.value = '注册成功，请登录'
    setTimeout(() => router.push({ path: '/login' }), 800)
  } catch (error) {
    errorMsg.value = '无法连接到后端，请检查后端是否启动'
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen grid place-items-center px-4 py-10" style="background: radial-gradient(circle at top, rgba(0, 212, 170, 0.18), transparent 32%), linear-gradient(180deg, #0b111e 0%, #0f1727 100%);">
    <div class="w-full max-w-md rounded-[28px] border border-[rgba(255,255,255,0.08)] bg-[rgba(15,23,42,0.92)] p-8 shadow-[0_24px_80px_rgba(0,0,0,0.25)] backdrop-blur-xl">
      <div class="mb-8 text-center">
        <img src="/favicon.png" alt="AQ" class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-3xl bg-transparent text-2xl font-bold text-white shadow-lg shadow-[#00d4aa]/20" />
        <h1 class="text-3xl font-semibold text-white">注册新用户</h1>
        <p class="mt-2 text-sm text-white">创建账号，完成注册后登录系统。</p>
      </div>

      <div class="space-y-5">
        <label class="block text-sm font-medium text-white">
          用户名
          <input
            v-model="username"
            type="text"
            placeholder="输入用户名"
            class="mt-2 w-full rounded-2xl border border-[rgba(255,255,255,0.1)] bg-[rgba(255,255,255,0.05)] px-4 py-3 text-sm text-white placeholder-gray-400 outline-none transition-all duration-200 focus:border-[#00d4aa] focus:ring-2 focus:ring-[rgba(0,212,170,0.16)]"
          />
        </label>

        <label class="block text-sm font-medium text-white">
          密码
          <input
            v-model="password"
            type="password"
            placeholder="输入密码"
            class="mt-2 w-full rounded-2xl border border-[rgba(255,255,255,0.1)] bg-[rgba(255,255,255,0.05)] px-4 py-3 text-sm text-white placeholder-gray-400 outline-none transition-all duration-200 focus:border-[#00d4aa] focus:ring-2 focus:ring-[rgba(0,212,170,0.16)]"
          />
        </label>

        <label class="block text-sm font-medium text-white">
          确认密码
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="再次输入密码"
            class="mt-2 w-full rounded-2xl border border-[rgba(255,255,255,0.1)] bg-[rgba(255,255,255,0.05)] px-4 py-3 text-sm text-white placeholder-gray-400 outline-none transition-all duration-200 focus:border-[#00d4aa] focus:ring-2 focus:ring-[rgba(0,212,170,0.16)]"
          />
        </label>

        <div v-if="errorMsg" class="rounded-2xl border border-[#ff4d67] bg-[#ff4d67]/10 px-4 py-3 text-sm text-white">
          {{ errorMsg }}
        </div>
        <div v-if="successMsg" class="rounded-2xl border border-[#00d4aa] bg-[rgba(0,212,170,0.12)] px-4 py-3 text-sm text-white">
          {{ successMsg }}
        </div>

        <button
          type="button"
          :disabled="loading"
          @click="handleRegisterClick"
          class="w-full rounded-2xl bg-[#00d4aa] px-5 py-3 text-sm font-semibold text-white transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60 hover:bg-[#00d4aa]/80"
        >
          <span v-if="!loading">注册</span>
          <span v-else>注册中...</span>
        </button>

        <div class="pt-2 text-center text-sm text-white">
          已有账号？
          <router-link to="/login" class="text-[#00d4aa] hover:text-[#00d4aa]/80">立即登录</router-link>
        </div>
      </div>
    </div>

    <!-- 滑块验证弹窗 -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center" style="background: rgba(0,0,0,0.6);">
      <div class="relative rounded-[16px] bg-white p-4 shadow-[0_24px_80px_rgba(0,0,0,0.4)]" style="width: 340px;">
        <button 
          @click="closeModal" 
          class="absolute -top-3 -right-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-md text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
        
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-lg font-semibold text-gray-800">安全验证</h3>
        </div>
        <p class="text-xs text-gray-500 mb-3">请拖动滑块完成安全验证</p>
        
        <SlideVerify
          ref="slideVerifyRef"
          :key="sliderKey"
          :length="200"
          :accuracy="10"
          :show="true"
          slider-text="向右滑动验证"
          @success="onSlideSuccess"
          @fail="onSlideFail"
          @refresh="onRefresh"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}
</style>