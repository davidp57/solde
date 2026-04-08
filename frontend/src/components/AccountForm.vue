<template>
  <form @submit.prevent="submit">
    <div class="flex flex-col gap-4">
      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label for="af-number" class="font-medium text-sm">
            {{ t('accounting.accounts.number') }} *
          </label>
          <InputText
            id="af-number"
            v-model="form.number"
            :placeholder="t('accounting.accounts.number_placeholder')"
            :disabled="!!account"
            required
            class="w-full"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label for="af-type" class="font-medium text-sm">
            {{ t('accounting.accounts.type') }} *
          </label>
          <Select
            id="af-type"
            v-model="form.type"
            :options="typeOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
      </div>

      <div class="flex flex-col gap-1">
        <label for="af-label" class="font-medium text-sm">
          {{ t('accounting.accounts.label') }} *
        </label>
        <InputText
          id="af-label"
          v-model="form.label"
          :placeholder="t('accounting.accounts.label')"
          required
          class="w-full"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label for="af-parent" class="font-medium text-sm">
          {{ t('accounting.accounts.parent_number') }}
        </label>
        <InputText
          id="af-parent"
          v-model="form.parent_number"
          :placeholder="t('accounting.accounts.parent_number_placeholder')"
          class="w-full"
        />
      </div>

      <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

      <div class="flex justify-end gap-2 pt-2">
        <Button
          type="button"
          :label="t('common.cancel')"
          severity="secondary"
          :disabled="saving"
          @click="$emit('cancel')"
        />
        <Button
          type="submit"
          :label="t('common.save')"
          :loading="saving"
          icon="pi pi-check"
        />
      </div>
    </div>
  </form>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { ref, watch } from 'vue'
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
