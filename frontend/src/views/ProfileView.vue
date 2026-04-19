<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('profile.title')"
      :subtitle="t('profile.subtitle')"
    />

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('profile.stats.role')"
        :value="displayedRole"
        :caption="t('profile.stats.role_caption')"
      />
      <AppStatCard
        :label="t('profile.stats.username')"
        :value="auth.user?.username ?? '—'"
        :caption="t('profile.stats.username_caption')"
        tone="success"
      />
      <AppStatCard
        :label="t('profile.stats.created_at')"
        :value="createdAtLabel"
        :caption="t('profile.stats.created_at_caption')"
        tone="warn"
      />
    </section>

    <div class="profile-grid">
      <AppPanel :title="t('profile.account_title')" :subtitle="t('profile.account_subtitle')">
        <form class="app-form-stack" @submit.prevent="submitProfile">
          <div class="app-field">
            <label class="app-field__label" for="profile-username">{{
              t('profile.username')
            }}</label>
            <InputText
              id="profile-username"
              :model-value="auth.user?.username ?? ''"
              disabled
              class="w-full"
            />
            <small class="app-field__help">{{ t('profile.username_help') }}</small>
          </div>

          <div class="app-field">
            <label class="app-field__label" for="profile-email">{{ t('profile.email') }}</label>
            <InputText id="profile-email" v-model="profileForm.email" type="email" class="w-full" />
          </div>

          <div class="app-form-actions">
            <Button
              type="submit"
              :label="t('profile.save_profile')"
              :disabled="!canSaveProfile"
              :loading="savingProfile"
            />
          </div>
        </form>
      </AppPanel>

      <AppPanel :title="t('profile.password_title')" :subtitle="t('profile.password_subtitle')">
        <form class="app-form-stack" @submit.prevent="submitPassword">
          <div class="app-field">
            <label class="app-field__label" for="profile-current-password">
              {{ t('profile.current_password') }}
            </label>
            <Password
              id="profile-current-password"
              v-model="passwordForm.current_password"
              :feedback="false"
              toggle-mask
              class="w-full"
              input-class="w-full"
            />
          </div>

          <div class="app-field">
            <label class="app-field__label" for="profile-new-password">
              {{ t('profile.new_password') }}
            </label>
            <Password
              id="profile-new-password"
              v-model="passwordForm.new_password"
              :feedback="false"
              toggle-mask
              class="w-full"
              input-class="w-full"
            />
          </div>

          <div class="app-field">
            <label class="app-field__label" for="profile-confirm-password">
              {{ t('profile.confirm_password') }}
            </label>
            <Password
              id="profile-confirm-password"
              v-model="passwordForm.confirm_password"
              :feedback="false"
              toggle-mask
              class="w-full"
              input-class="w-full"
            />
            <small class="app-field__help">{{ t('profile.password_help') }}</small>
          </div>

          <Message v-if="passwordMismatch" severity="warn" :closable="false">
            {{ t('profile.password_mismatch') }}
          </Message>

          <div class="app-form-actions">
            <Button
              type="submit"
              :label="t('profile.change_password')"
              :disabled="!canChangePassword"
              :loading="savingPassword"
            />
          </div>
        </form>
      </AppPanel>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import { useToast } from 'primevue/usetoast'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import { changeMyPasswordApi, updateMyProfileApi } from '@/api/auth'
import { PASSWORD_MIN_LENGTH } from '@/constants/auth'
import { useAuthStore } from '@/stores/auth'

interface ProfileForm {
  email: string
}

interface PasswordForm {
  current_password: string
  new_password: string
  confirm_password: string
}

interface ApiErrorDetail {
  code?: string
}

const { t } = useI18n()
const router = useRouter()
const toast = useToast()
const auth = useAuthStore()

const savingProfile = ref(false)
const savingPassword = ref(false)
const profileForm = ref<ProfileForm>({ email: auth.user?.email ?? '' })
const passwordForm = ref<PasswordForm>({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

watch(
  () => auth.user,
  (user) => {
    profileForm.value.email = user?.email ?? ''
  },
  { immediate: true },
)

const profileApiErrorMessages: Record<string, string> = {
  email_exists: 'profile.api_errors.email_exists',
  email_required: 'profile.api_errors.email_required',
  no_changes: 'profile.api_errors.no_changes',
  invalid_current_password: 'profile.api_errors.invalid_current_password',
  same_password: 'profile.api_errors.same_password',
}

const displayedRole = computed(() => (auth.user?.role ? t(`user.role.${auth.user.role}`) : '—'))
const createdAtLabel = computed(() => {
  if (!auth.user?.created_at) return '—'
  return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium' }).format(
    new Date(auth.user.created_at),
  )
})
const canSaveProfile = computed(() => {
  const email = profileForm.value.email.trim()
  return email.length > 0 && email !== (auth.user?.email ?? '')
})
const passwordMismatch = computed(() => {
  return (
    passwordForm.value.confirm_password.length > 0 &&
    passwordForm.value.confirm_password !== passwordForm.value.new_password
  )
})
const canChangePassword = computed(() => {
  return (
    passwordForm.value.current_password.length > 0 &&
    passwordForm.value.new_password.length >= PASSWORD_MIN_LENGTH &&
    passwordForm.value.confirm_password.length > 0 &&
    !passwordMismatch.value
  )
})

function getApiErrorSummary(error: unknown): string {
  const status = (error as { response?: { status?: number } }).response?.status
  const detail = (error as { response?: { data?: { detail?: ApiErrorDetail | string } } }).response
    ?.data?.detail

  if (typeof detail === 'object' && detail !== null && typeof detail.code === 'string') {
    const translationKey = profileApiErrorMessages[detail.code]
    if (translationKey) {
      return t(translationKey)
    }
  }

  if (status === 403) {
    return t('common.error.forbidden')
  }
  if (status === 404) {
    return t('common.error.notFound')
  }

  return t('common.error.unknown')
}

async function submitProfile(): Promise<void> {
  if (!canSaveProfile.value) return

  savingProfile.value = true
  try {
    const updatedUser = await updateMyProfileApi({ email: profileForm.value.email.trim() })
    auth.user = updatedUser
    toast.add({ severity: 'success', summary: t('profile.profile_updated'), life: 3000 })
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getApiErrorSummary(error), life: 3500 })
  } finally {
    savingProfile.value = false
  }
}

async function submitPassword(): Promise<void> {
  if (!canChangePassword.value) return

  savingPassword.value = true
  try {
    await changeMyPasswordApi({
      current_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password,
    })
    toast.add({ severity: 'success', summary: t('profile.password_changed'), life: 3500 })
    auth.logout({ preventDevAutoLogin: true })
    await router.push('/login')
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getApiErrorSummary(error), life: 3500 })
  } finally {
    savingPassword.value = false
  }
}
</script>

<style scoped>
.profile-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
}
</style>
