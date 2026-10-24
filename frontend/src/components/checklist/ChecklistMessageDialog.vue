<template>
  <Dialog
    :visible="visible"
    :header="t('checklist.messages.dialog_title')"
    modal
    class="app-dialog"
    @update:visible="$emit('update:visible', $event)"
  >
    <form class="app-dialog-form" @submit.prevent="submit">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__text">{{ t('checklist.messages.dialog_intro') }}</p>
      </section>

      <div class="app-field">
        <label class="app-field__label" for="checklist-message-content">
          {{ t('checklist.messages.content') }}
        </label>
        <Textarea
          id="checklist-message-content"
          v-model="draft"
          rows="3"
          auto-resize
          maxlength="2000"
          class="w-full"
        />
      </div>

      <div class="app-form-actions">
        <Button
          type="button"
          :label="t('common.cancel')"
          severity="secondary"
          text
          @click="$emit('update:visible', false)"
        />
        <Button
          type="submit"
          :label="t('checklist.messages.send')"
          :loading="busy"
          :disabled="!draft.trim()"
        />
      </div>

      <!-- The author's own messages not dealt with yet: the ones they may still withdraw. -->
      <section v-if="mine.length" class="app-dialog-section">
        <div class="app-dialog-section__header">
          <p class="app-dialog-section__title">{{ t('checklist.messages.mine_title') }}</p>
        </div>
        <ul class="message-list">
          <li v-for="message in mine" :key="message.id" class="message-list__item">
            <div class="message-list__body">
              <p class="message-list__content">{{ message.content }}</p>
              <small class="message-list__date">{{ formatDisplayDate(message.created_at) }}</small>
            </div>
            <Button
              type="button"
              icon="pi pi-trash"
              text
              rounded
              severity="danger"
              :aria-label="t('checklist.messages.withdraw')"
              :title="t('checklist.messages.withdraw')"
              :disabled="busy"
              @click="withdraw(message.id)"
            />
          </li>
        </ul>
      </section>
    </form>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import {
  addChecklistMessage,
  deleteChecklistMessage,
  listMyChecklistMessages,
  type ChecklistMessage,
} from '@/api/checklist'
import { useAuthStore } from '@/stores/auth'
import { useChecklistStore } from '@/stores/checklist'
import { formatDisplayDate } from '@/utils/format'
import { getErrorDetail } from '@/utils/errorUtils'

const props = defineProps<{ visible: boolean }>()
defineEmits<{ 'update:visible': [value: boolean] }>()

const { t } = useI18n()
const toast = useToast()
const auth = useAuthStore()
const checklistStore = useChecklistStore()

const draft = ref('')
const mine = ref<ChecklistMessage[]>([])
const busy = ref(false)

async function run(action: () => Promise<void>): Promise<void> {
  busy.value = true
  try {
    await action()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: getErrorDetail(error, t('common.error.unknown')),
      life: 4000,
    })
  } finally {
    busy.value = false
  }
}

async function submit(): Promise<void> {
  if (!draft.value.trim()) return
  await run(async () => {
    const message = await addChecklistMessage(draft.value)
    mine.value = [...mine.value, message]
    draft.value = ''
    // The accountant writing for a later self sees the message land in the session.
    if (auth.canAccessAccounting) void checklistStore.load()
    toast.add({ severity: 'success', summary: t('checklist.messages.sent'), life: 3000 })
  })
}

async function withdraw(messageId: number): Promise<void> {
  await run(async () => {
    await deleteChecklistMessage(messageId)
    mine.value = mine.value.filter((m) => m.id !== messageId)
  })
}

watch(
  () => props.visible,
  (visible) => {
    if (!visible) return
    void run(async () => {
      mine.value = await listMyChecklistMessages()
    })
  },
  { immediate: true },
)
</script>

<style scoped>
.message-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.message-list__item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.message-list__body {
  flex: 1;
  min-width: 0;
}

.message-list__content {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.message-list__date {
  color: var(--p-text-muted-color);
}
</style>
