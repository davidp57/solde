<template>
  <form class="account-form" @submit.prevent="submit">
    <section class="account-form__intro">
      <p class="account-form__eyebrow">{{ t('accounting.accounts.title') }}</p>
      <p class="account-form__intro-copy">
        {{
          t(
            isEditing
              ? 'accounting.accounts.form_intro_edit'
              : 'accounting.accounts.form_intro_create',
          )
        }}
      </p>
    </section>

    <div class="app-form-grid">
      <div class="app-field">
        <label for="af-number" class="app-field__label">
          {{ t('accounting.accounts.number') }} *
        </label>
        <InputText
          id="af-number"
          v-model="form.number"
          :placeholder="t('accounting.accounts.number_placeholder')"
          :disabled="isEditing"
          required
        />
        <small v-if="isEditing" class="account-form__hint">
          {{ t('accounting.accounts.number_locked') }}
        </small>
      </div>

      <div class="app-field">
        <label for="af-type" class="app-field__label">
          {{ t('accounting.accounts.type') }} *
        </label>
        <Select
          id="af-type"
          v-model="form.type"
          :options="typeOptions"
          option-label="label"
          option-value="value"
        />
      </div>

      <div class="app-field app-field--full">
        <label for="af-label" class="app-field__label">
          {{ t('accounting.accounts.label') }} *
        </label>
        <InputText
          id="af-label"
          v-model="form.label"
          :placeholder="t('accounting.accounts.label_placeholder')"
          required
        />
      </div>
    </div>

    <section class="account-form__group">
      <div class="account-form__group-header">
        <h3 class="account-form__group-title">{{ t('accounting.accounts.parenting_title') }}</h3>
        <p class="account-form__group-copy">{{ t('accounting.accounts.parenting_subtitle') }}</p>
      </div>

      <div class="app-field">
        <label for="af-parent" class="app-field__label">
          {{ t('accounting.accounts.parent_number') }}
        </label>
        <InputText
          id="af-parent"
          v-model="form.parent_number"
          :placeholder="t('accounting.accounts.parent_number_placeholder')"
        />
        <small class="account-form__hint">
          {{ t('accounting.accounts.parent_number_help') }}
        </small>
      </div>
    </section>

    <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

    <div class="app-form-actions">
      <Button
        type="button"
        :label="t('common.cancel')"
        severity="secondary"
        outlined
        :disabled="saving"
        @click="$emit('cancel')"
      />
      <Button type="submit" :label="t('common.save')" :loading="saving" icon="pi pi-check" />
    </div>
  </form>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  createAccountApi,
  updateAccountApi,
  type AccountingAccount,
  type AccountType,
} from '@/api/accounting'

const props = defineProps<{ account: AccountingAccount | null }>()
const emit = defineEmits<{ saved: []; cancel: [] }>()

const { t } = useI18n()

const typeOptions = [
  { label: t('accounting.account_types.actif'), value: 'actif' as AccountType },
  { label: t('accounting.account_types.passif'), value: 'passif' as AccountType },
  { label: t('accounting.account_types.charge'), value: 'charge' as AccountType },
  { label: t('accounting.account_types.produit'), value: 'produit' as AccountType },
]

interface FormState {
  number: string
  label: string
  type: AccountType
  parent_number: string
}

function fromAccount(a: AccountingAccount | null): FormState {
  return {
    number: a?.number ?? '',
    label: a?.label ?? '',
    type: a?.type ?? 'actif',
    parent_number: a?.parent_number ?? '',
  }
}

const form = ref<FormState>(fromAccount(props.account))
const saving = ref(false)
const errorMessage = ref('')
const isEditing = computed(() => props.account !== null)

watch(
  () => props.account,
  (a) => {
    form.value = fromAccount(a)
    errorMessage.value = ''
  },
)

async function submit(): Promise<void> {
  saving.value = true
  errorMessage.value = ''
  try {
    if (props.account) {
      await updateAccountApi(props.account.id, {
        label: form.value.label,
        type: form.value.type,
        parent_number: form.value.parent_number || null,
      })
    } else {
      await createAccountApi({
        number: form.value.number,
        label: form.value.label,
        type: form.value.type,
        parent_number: form.value.parent_number || null,
      })
    }
    emit('saved')
  } catch {
    errorMessage.value = t('common.error.unknown')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.account-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-5);
}

.account-form__intro {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-2);
  padding: var(--app-space-4);
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--app-surface-bg) 88%, transparent 12%);
  border: 1px solid var(--app-surface-border);
}

.account-form__eyebrow {
  margin: 0;
  color: var(--p-primary-500);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.account-form__intro-copy,
.account-form__group-copy {
  margin: 0;
  color: var(--p-text-muted-color);
  line-height: 1.55;
}

.account-form__group {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
  padding: var(--app-space-4);
  border-radius: var(--app-surface-radius-sm);
  background: color-mix(in srgb, var(--app-surface-muted) 82%, transparent 18%);
  border: 1px solid var(--app-surface-border);
}

.account-form__group-header {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-1);
}

.account-form__group-title {
  margin: 0;
  font-size: 0.98rem;
  font-weight: 700;
}

.account-form__hint {
  color: var(--p-text-muted-color);
  line-height: 1.4;
}

.account-form :deep(.p-inputtext),
.account-form :deep(.p-select) {
  width: 100%;
}
</style>
