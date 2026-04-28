<template>
  <AppPage width="narrow">
    <AppPageHeader :title="t('comments.title')" :subtitle="t('comments.subtitle')" />

    <div class="comments-form">
      <div class="app-field">
        <label class="app-field__label">{{ t('comments.new') }}</label>
        <Textarea
          v-model="newContent"
          :placeholder="t('comments.placeholder')"
          rows="4"
          class="w-full"
          :disabled="submitting"
        />
      </div>
      <div class="comments-form__actions">
        <Button
          :label="t('comments.submit')"
          icon="pi pi-send"
          :loading="submitting"
          :disabled="!newContent.trim()"
          @click="submitComment"
        />
      </div>
    </div>

    <div class="comments-list">
      <h2 class="comments-list__title">
        {{ isAdmin ? t('comments.all_comments') : t('comments.your_comments') }}
      </h2>

      <div v-if="loading" class="comments-loading">
        <i class="pi pi-spin pi-spinner" />
      </div>

      <p v-else-if="comments.length === 0" class="comments-empty">
        {{ t('comments.empty') }}
      </p>

      <div v-else class="comments-items">
        <div v-for="comment in comments" :key="comment.id" class="comment-card">
          <div class="comment-card__meta">
            <span v-if="isAdmin" class="comment-card__author">
              {{ t('comments.by', { user: comment.user_name }) }}
            </span>
            <span class="comment-card__date">{{ formatDateTime(comment.created_at) }}</span>
          </div>
          <p class="comment-card__content">{{ comment.content }}</p>
        </div>
      </div>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import { listCommentsApi, createCommentApi, type AppComment } from '@/api/app_comment'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const toast = useToast()
const auth = useAuthStore()

const comments = ref<AppComment[]>([])
const loading = ref(false)
const submitting = ref(false)
const newContent = ref('')
const isAdmin = auth.user?.role === 'admin'

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadComments(): Promise<void> {
  loading.value = true
  try {
    comments.value = await listCommentsApi()
  } finally {
    loading.value = false
  }
}

async function submitComment(): Promise<void> {
  if (!newContent.value.trim()) return
  submitting.value = true
  try {
    const created = await createCommentApi(newContent.value.trim())
    comments.value.unshift(created)
    newContent.value = ''
    toast.add({ severity: 'success', summary: t('comments.added'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    submitting.value = false
  }
}

onMounted(loadComments)
</script>

<style scoped>
.comments-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
  margin-bottom: var(--app-space-8);
}

.comments-form__actions {
  display: flex;
  justify-content: flex-end;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.comments-list__title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--app-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.comments-loading {
  color: var(--app-text-muted);
  padding: var(--app-space-4);
}

.comments-empty {
  color: var(--app-text-muted);
  font-style: italic;
}

.comments-items {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.comment-card {
  background: var(--p-surface-50);
  border: 1px solid var(--p-surface-200);
  border-radius: 6px;
  padding: 12px 16px;
}

.comment-card__meta {
  display: flex;
  gap: var(--app-space-4);
  align-items: center;
  margin-bottom: var(--app-space-2);
}

.comment-card__author {
  font-weight: 600;
  font-size: 0.875rem;
}

.comment-card__date {
  font-size: 0.8125rem;
  color: var(--app-text-muted);
}

.comment-card__content {
  font-size: 0.9375rem;
  line-height: 1.6;
  white-space: pre-wrap;
  margin: 0;
}
</style>
