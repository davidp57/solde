<template>
  <Dialog
    :visible="visible"
    :header="t('contacts.merge_title')"
    modal
    class="app-dialog app-dialog--medium"
    @update:visible="onClose"
  >
    <div class="contact-merge">
      <Message severity="warn" :closable="false" class="contact-merge__warning">
        {{ t('contacts.merge_warning') }}
      </Message>

      <div class="app-field">
        <label class="app-field__label">{{ t('contacts.merge_source_label') }}</label>
        <div class="contact-merge__source-name">
          <strong>{{ sourceContact?.nom }}<template v-if="sourceContact?.prenom"> {{ sourceContact.prenom }}</template></strong>
          <Tag
            v-if="sourceContact"
            :value="t(`contacts.types.${sourceContact.type}`)"
            :severity="typeSeverity(sourceContact.type)"
            class="contact-merge__type-tag"
          />
        </div>
      </div>

      <div class="app-field">
        <label class="app-field__label">{{ t('contacts.merge_target_label') }}</label>
        <Select
          v-model="selectedTarget"
          :options="targetOptions"
          option-label="label"
          option-value="value"
          :placeholder="t('contacts.merge_select_placeholder')"
          filter
          :filter-placeholder="t('contacts.merge_select_placeholder')"
          class="contact-merge__select"
        />
      </div>

      <Message v-if="sameContactError" severity="error" :closable="false">
        {{ t('contacts.merge_same_contact_error') }}
      </Message>
      <Message v-if="errorMessage" severity="error" :closable="false">
        {{ errorMessage }}
      </Message>

      <div class="app-form-actions">
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          text
          :disabled="loading"
          @click="onClose(false)"
        />
        <Button
          :label="t('contacts.merge_confirm')"
          icon="pi pi-arrow-right-arrow-left"
          severity="danger"
          :loading="loading"
          :disabled="!selectedTarget || sameContactError"
          @click="doMerge"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { mergeContactApi, type Contact } from '@/api/contacts'
import { getApiErrorMessage } from '@/composables/useApiError'
import type { ContactType } from '@/api/types'

const props = defineProps<{
  visible: boolean
  sourceContact: Contact | null
  contacts: Contact[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'merged', sourceId: number): void
}>()

const { t } = useI18n()
const toast = useToast()

const selectedTarget = ref<number | null>(null)
const loading = ref(false)
const errorMessage = ref<string | null>(null)

const sameContactError = computed(
  () => selectedTarget.value !== null && selectedTarget.value === props.sourceContact?.id,
)

const targetOptions = computed(() => {
  if (!props.sourceContact) return []
  return props.contacts
    .filter((c) => c.id !== props.sourceContact!.id && c.is_active)
    .map((c) => ({
      value: c.id,
      label: c.prenom ? `${c.nom} ${c.prenom}` : c.nom,
    }))
    .sort((a, b) => a.label.localeCompare(b.label, 'fr', { sensitivity: 'base' }))
})

watch(
  () => props.visible,
  (v) => {
    if (!v) {
      selectedTarget.value = null
      errorMessage.value = null
    }
  },
)

function typeSeverity(type: ContactType): 'info' | 'success' | 'warn' {
  if (type === 'client') return 'info'
  if (type === 'fournisseur') return 'success'
  return 'warn'
}

function onClose(value: boolean): void {
  emit('update:visible', value)
}

async function doMerge(): Promise<void> {
  if (!props.sourceContact || !selectedTarget.value) return
  loading.value = true
  errorMessage.value = null
  try {
    const result = await mergeContactApi(props.sourceContact.id, selectedTarget.value)
    toast.add({
      severity: 'success',
      summary: t('contacts.merge_title'),
      detail: t('contacts.merge_success', {
        invoices: result.invoices_reassigned,
        payments: result.payments_reassigned,
      }),
      life: 5000,
    })
    emit('merged', props.sourceContact.id)
    onClose(false)
  } catch (err: unknown) {
    errorMessage.value = getApiErrorMessage(err) ?? t('common.error.unknown')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.contact-merge {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.contact-merge__warning {
  margin-bottom: 0.25rem;
}

.contact-merge__source-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--p-inputtext-background);
  border: 1px solid var(--p-inputtext-border-color);
  border-radius: var(--p-border-radius-sm, 4px);
  font-size: 0.95rem;
  color: var(--p-inputtext-color);
}

.contact-merge__type-tag {
  font-size: 0.75rem;
}

.contact-merge__select {
  width: 100%;
}
</style>
