<template>
  <Dialog
    :visible="visible"
    :header="rule ? t('accounting.rules.edit') : t('accounting.rules.new')"
    modal
    class="app-dialog app-dialog--large"
    @update:visible="$emit('update:visible', $event)"
  >
    <form class="app-dialog-form" @submit.prevent="submit">
      <!-- intro -->
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('accounting.rules.title') }}</p>
        <p class="app-dialog-intro__text">
          {{ rule ? t('accounting.rules.form_intro_edit') : t('accounting.rules.form_intro_create') }}
        </p>
      </section>

      <!-- identity -->
      <section class="app-dialog-section">
        <div class="app-dialog-section__header">
          <p class="app-dialog-section__title">{{ t('accounting.rules.identity_title') }}</p>
          <p class="app-dialog-section__subtitle">{{ t('accounting.rules.identity_subtitle') }}</p>
        </div>
        <div class="app-form-grid">
          <!-- trigger type -->
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('accounting.rules.trigger_type') }}</label>
            <Select
              v-if="!rule"
              v-model="form.trigger_type"
              :options="triggerOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('accounting.rules.trigger_type_placeholder')"
              class="w-full"
            />
            <div v-else class="app-field__read-value">
              <Tag :value="triggerLabel(rule.trigger_type)" severity="secondary" />
              <span class="app-field__help">{{ t('accounting.rules.trigger_type_locked') }}</span>
            </div>
          </div>
          <!-- name -->
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('accounting.rules.name') }}</label>
            <InputText v-model="form.name" class="w-full" />
          </div>
          <!-- description -->
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('accounting.rules.description') }}</label>
            <Textarea v-model="form.description" rows="2" auto-resize class="w-full" />
          </div>
          <!-- priority + is_active -->
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.rules.priority') }}</label>
            <InputNumber v-model="form.priority" :min="0" :max="999" class="w-full" />
          </div>
          <div class="app-field app-field--inline-toggle">
            <label class="app-field__label">{{ t('accounting.rules.active') }}</label>
            <ToggleSwitch v-model="form.is_active" />
          </div>
        </div>
      </section>

      <!-- entries -->
      <section class="app-dialog-section">
        <div class="app-dialog-section__header">
          <p class="app-dialog-section__title">{{ t('accounting.rules.entries_title') }}</p>
          <p class="app-dialog-section__subtitle">{{ t('accounting.rules.entries_subtitle') }}</p>
        </div>
        <DataTable :value="form.entries" size="small" class="app-data-table rule-entries-table">
          <Column :header="t('accounting.rules.entry_account')" style="width: 9rem">
            <template #body="{ index }">
              <InputText v-model="form.entries[index].account_number" size="small" class="w-full" />
            </template>
          </Column>
          <Column :header="t('accounting.rules.entry_side')" style="width: 8rem">
            <template #body="{ index }">
              <Select
                v-model="form.entries[index].side"
                :options="sideOptions"
                option-label="label"
                option-value="value"
                size="small"
                class="w-full"
              />
            </template>
          </Column>
          <Column :header="t('accounting.rules.entry_template')">
            <template #body="{ index }">
              <InputText v-model="form.entries[index].description_template" size="small" class="w-full" />
            </template>
          </Column>
          <Column style="width: 3rem">
            <template #body="{ index }">
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                size="small"
                :title="t('accounting.rules.remove_entry')"
                @click="removeEntry(index)"
              />
            </template>
          </Column>
          <template #empty>
            <div class="app-empty-state">{{ t('accounting.rules.entries') }} — aucune ligne</div>
          </template>
        </DataTable>
        <div class="rule-entries-actions">
          <Button
            :label="t('accounting.rules.add_entry')"
            icon="pi pi-plus"
            severity="secondary"
            size="small"
            outlined
            @click="addEntry"
          />
        </div>
      </section>

      <div class="app-form-actions">
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          text
          @click="$emit('update:visible', false)"
        />
        <Button type="submit" :label="t('common.save')" :loading="saving" />
      </div>
    </form>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { useToast } from 'primevue/usetoast'
import { createRuleApi, updateRuleApi, type AccountingRuleRead } from '@/api/accounting'

const props = defineProps<{
  visible: boolean
  /** Pass a rule to edit; omit to create a new one. */
  rule?: AccountingRuleRead | null
}>()

const emit = defineEmits<{
  'update:visible': [val: boolean]
  saved: [rule: AccountingRuleRead]
}>()

const { t } = useI18n()
const toast = useToast()
const saving = ref(false)

// All trigger type values from the backend model
const ALL_TRIGGER_TYPES = [
  'invoice_client_cs',
  'invoice_client_a',
  'invoice_client_cs_a',
  'invoice_client_general',
  'invoice_fournisseur_subcontracting',
  'invoice_fournisseur_general',
  'payment_received_especes',
  'payment_received_cheque',
  'payment_received_virement',
  'payment_sent_especes',
  'payment_sent_virement',
  'deposit_especes',
  'deposit_cheques',
  'bank_fees',
  'bank_insurance',
  'bank_savings_interest',
  'bank_internal_transfer_from_savings',
  'bank_internal_transfer_to_savings',
  'bank_social_charges',
  'subsidy_received',
  'salary_gross',
  'salary_employee_charges',
  'salary_employer_charges',
  'salary_withholding_tax',
  'salary_payment',
  'manual',
] as const

const triggerOptions = ALL_TRIGGER_TYPES.map((v) => ({
  label: t(`accounting.rules.trigger_types.${v}`),
  value: v,
}))

const sideOptions = [
  { label: t('accounting.rules.entry_side_debit'), value: 'debit' },
  { label: t('accounting.rules.entry_side_credit'), value: 'credit' },
]

function triggerLabel(value: string): string {
  const key = `accounting.rules.trigger_types.${value}`
  const translated = t(key)
  return translated === key ? value : translated
}

interface EntryForm {
  account_number: string
  side: 'debit' | 'credit'
  description_template: string
}

interface FormState {
  trigger_type: string
  name: string
  description: string
  priority: number
  is_active: boolean
  entries: EntryForm[]
}

function emptyForm(): FormState {
  return {
    trigger_type: '',
    name: '',
    description: '',
    priority: 10,
    is_active: true,
    entries: [],
  }
}

function ruleToForm(r: AccountingRuleRead): FormState {
  return {
    trigger_type: r.trigger_type,
    name: r.name,
    description: r.description ?? '',
    priority: r.priority,
    is_active: r.is_active,
    entries: r.entries.map((e) => ({
      account_number: e.account_number,
      side: e.side,
      description_template: e.description_template,
    })),
  }
}

const form = ref<FormState>(emptyForm())

watch(
  () => props.visible,
  (v) => {
    if (v) form.value = props.rule ? ruleToForm(props.rule) : emptyForm()
  },
)

function addEntry(): void {
  form.value.entries.push({ account_number: '', side: 'debit', description_template: '{{label}}' })
}

function removeEntry(index: number): void {
  form.value.entries.splice(index, 1)
}

async function submit(): Promise<void> {
  saving.value = true
  try {
    let saved: AccountingRuleRead
    if (props.rule) {
      saved = await updateRuleApi(props.rule.id, {
        name: form.value.name,
        description: form.value.description || null,
        priority: form.value.priority,
        is_active: form.value.is_active,
        entries: form.value.entries,
      })
      toast.add({ severity: 'success', summary: t('accounting.rules.saved'), life: 3000 })
    } else {
      saved = await createRuleApi({
        trigger_type: form.value.trigger_type,
        name: form.value.name,
        description: form.value.description || null,
        priority: form.value.priority,
        is_active: form.value.is_active,
        entries: form.value.entries,
      })
      toast.add({ severity: 'success', summary: t('accounting.rules.created'), life: 3000 })
    }
    emit('update:visible', false)
    emit('saved', saved)
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 409) {
      toast.add({ severity: 'error', summary: t('accounting.rules.duplicate_trigger'), life: 4000 })
    } else {
      toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
    }
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.rule-entries-table {
  margin-top: 0.5rem;
}

.rule-entries-actions {
  margin-top: 0.5rem;
}

.app-field__read-value {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.app-field__help {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color, #6c757d);
}

.app-field--inline-toggle {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
</style>
