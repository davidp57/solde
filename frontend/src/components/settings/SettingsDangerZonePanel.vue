<template>
  <AppPanel
    class="danger-panel"
    :title="t('settings.danger_zone')"
    :subtitle="t('settings.reset_db_desc')"
  >
    <div class="settings-danger">
      <div>
        <Button
          :label="t('settings.bootstrap_accounting')"
          icon="pi pi-refresh"
          severity="secondary"
          outlined
          :loading="bootstrapping"
          @click="confirmBootstrap"
        />
      </div>
      <div>
        <Button
          :label="t('settings.reset_db')"
          icon="pi pi-trash"
          severity="danger"
          outlined
          :loading="resetting"
          @click="confirmReset"
        />
      </div>
      <section class="settings-selective-reset">
        <div class="settings-selective-reset__header">
          <h3 class="settings-selective-reset__title">
            {{ t('settings.selective_reset_title') }}
          </h3>
          <p class="settings-selective-reset__subtitle">
            {{ t('settings.selective_reset_subtitle') }}
          </p>
        </div>
        <p class="settings-selective-reset__hint">{{ t('settings.selective_reset_help') }}</p>

        <div class="app-form-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('settings.selective_reset_type') }}</label>
            <Select
              v-model="selectiveResetForm.importType"
              :options="selectiveResetImportTypeOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('settings.selective_reset_fiscal_year') }}</label>
            <Select
              v-model="selectiveResetForm.fiscalYearId"
              :options="selectiveResetFiscalYearOptions"
              option-label="label"
              option-value="value"
              class="w-full"
            />
          </div>
        </div>

        <div class="app-form-actions">
          <Button
            :label="t('settings.selective_reset_preview')"
            icon="pi pi-search"
            severity="secondary"
            outlined
            :loading="selectiveResetPreviewLoading"
            @click="previewSelectiveReset"
          />
          <Button
            :label="t('settings.selective_reset_apply')"
            icon="pi pi-trash"
            severity="danger"
            :disabled="!canApplySelectiveReset"
            :loading="selectiveResetApplying"
            @click="confirmSelectiveReset"
          />
        </div>

        <Message
          v-if="selectiveResetSuccessMessage"
          severity="success"
          class="mt-2"
          :closable="true"
        >
          {{ selectiveResetSuccessMessage }}
        </Message>
        <Message
          v-if="selectiveResetErrorMessage"
          severity="error"
          class="mt-2"
          :closable="true"
        >
          {{ selectiveResetErrorMessage }}
        </Message>

        <div v-if="selectiveResetPreview" class="settings-selective-reset__preview">
          <div class="settings-selective-reset__groups">
            <section>
              <h4>{{ t('settings.selective_reset_root_objects') }}</h4>
              <ul>
                <li v-for="entry in selectiveResetRootEntries" :key="`root-${entry.key}`">
                  {{ selectiveResetObjectLabel(entry.key) }} : {{ entry.count }}
                </li>
              </ul>
            </section>
            <section>
              <h4>{{ t('settings.selective_reset_derived_objects') }}</h4>
              <ul>
                <li v-for="entry in selectiveResetDerivedEntries" :key="`derived-${entry.key}`">
                  {{ selectiveResetObjectLabel(entry.key) }} : {{ entry.count }}
                </li>
              </ul>
            </section>
            <section>
              <h4>{{ t('settings.selective_reset_delete_plan') }}</h4>
              <ul>
                <li v-for="entry in selectiveResetDeleteEntries" :key="`delete-${entry.key}`">
                  {{ selectiveResetObjectLabel(entry.key) }} : {{ entry.count }}
                </li>
              </ul>
            </section>
          </div>
        </div>
      </section>
      <Message v-if="resetMessage" severity="warn" class="mt-2" :closable="true">
        {{ resetMessage }}
      </Message>
      <Message v-if="bootstrapMessage" severity="info" class="mt-2" :closable="true">
        {{ bootstrapMessage }}
      </Message>
    </div>
  </AppPanel>

  <ConfirmDialog />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import ConfirmDialog from 'primevue/confirmdialog'
import Message from 'primevue/message'
import Select from 'primevue/select'
import { useConfirm } from 'primevue/useconfirm'
import {
  applySelectiveResetApi,
  bootstrapAccountingApi,
  previewSelectiveResetApi,
  resetDbApi,
  type SelectiveResetImportType,
  type SelectiveResetPreview,
} from '@/api/settings'
import AppPanel from '@/components/ui/AppPanel.vue'
import { useFiscalYearStore } from '@/stores/fiscalYear'
import { useDarkMode } from '@/composables/useDarkMode'

const { t } = useI18n()
const { isDark } = useDarkMode()
const fiscalYearStore = useFiscalYearStore()
const confirm = useConfirm()

const dangerHeaderBg = computed(() => (isDark.value ? 'rgba(239,68,68,0.08)' : 'var(--p-red-50)'))
const dangerBorderColor = computed(() =>
  isDark.value ? 'rgba(239,68,68,0.25)' : 'var(--p-red-200)',
)
const dangerTitleColor = computed(() => (isDark.value ? 'var(--p-red-400)' : 'var(--p-red-600)'))

interface SelectiveResetForm {
  importType: SelectiveResetImportType
  fiscalYearId: number | null
}

const resetting = ref(false)
const bootstrapping = ref(false)
const resetMessage = ref('')
const bootstrapMessage = ref('')
const selectiveResetForm = ref<SelectiveResetForm>({ importType: 'gestion', fiscalYearId: null })
const selectiveResetPreview = ref<SelectiveResetPreview | null>(null)
const selectiveResetPreviewLoading = ref(false)
const selectiveResetApplying = ref(false)
const selectiveResetSuccessMessage = ref('')
const selectiveResetErrorMessage = ref('')

const selectiveResetImportTypeOptions = computed(() => [
  { label: t('settings.selective_reset_import_type_gestion'), value: 'gestion' },
  { label: t('settings.selective_reset_import_type_comptabilite'), value: 'comptabilite' },
])
const selectiveResetFiscalYearOptions = computed(() =>
  fiscalYearStore.fiscalYears.map((fy) => ({ label: fy.name, value: fy.id })),
)
const selectiveResetRootEntries = computed(() =>
  Object.entries(selectiveResetPreview.value?.root_objects ?? {}).map(([key, count]) => ({ key, count })),
)
const selectiveResetDerivedEntries = computed(() =>
  Object.entries(selectiveResetPreview.value?.derived_objects ?? {}).map(([key, count]) => ({ key, count })),
)
const selectiveResetDeleteEntries = computed(() =>
  Object.entries(selectiveResetPreview.value?.delete_plan ?? {}).map(([key, count]) => ({ key, count })),
)
const canApplySelectiveReset = computed(
  () =>
    selectiveResetPreview.value !== null &&
    !selectiveResetPreviewLoading.value &&
    selectiveResetDeleteEntries.value.length > 0,
)

function selectiveResetObjectLabel(key: string): string {
  return t(`settings.selective_reset_object_${key}`)
}

function buildSelectiveResetPayload(): { import_type: SelectiveResetImportType; fiscal_year_id: number } | null {
  if (selectiveResetForm.value.fiscalYearId === null) {
    selectiveResetErrorMessage.value = t('settings.selective_reset_missing_fiscal_year')
    return null
  }
  return {
    import_type: selectiveResetForm.value.importType,
    fiscal_year_id: selectiveResetForm.value.fiscalYearId,
  }
}

function confirmBootstrap(): void {
  confirm.require({
    message: t('settings.bootstrap_accounting_confirm'),
    header: t('settings.bootstrap_accounting'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'warn', label: t('common.confirm') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: bootstrapAccounting,
  })
}

function confirmReset(): void {
  confirm.require({
    message: t('settings.reset_db_confirm'),
    header: t('settings.reset_db'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('settings.reset_db_yes') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: doReset,
  })
}

async function doReset(): Promise<void> {
  resetting.value = true
  resetMessage.value = ''
  try {
    const deleted = await resetDbApi()
    const total = Object.values(deleted).reduce((s, n) => s + n, 0)
    resetMessage.value = t('settings.reset_db_done', { count: total })
  } catch {
    resetMessage.value = t('settings.reset_db_error')
  } finally {
    resetting.value = false
  }
}

async function bootstrapAccounting(): Promise<void> {
  bootstrapping.value = true
  bootstrapMessage.value = ''
  try {
    const result = await bootstrapAccountingApi()
    await fiscalYearStore.refresh()
    bootstrapMessage.value = t('settings.bootstrap_accounting_done', {
      accounts: result.accounts_inserted,
      rules: result.rules_inserted,
      fiscalYears: result.fiscal_years_created,
    })
  } catch {
    bootstrapMessage.value = t('settings.bootstrap_accounting_error')
  } finally {
    bootstrapping.value = false
  }
}

async function previewSelectiveReset(): Promise<void> {
  selectiveResetPreviewLoading.value = true
  selectiveResetSuccessMessage.value = ''
  selectiveResetErrorMessage.value = ''
  const payload = buildSelectiveResetPayload()
  if (!payload) {
    selectiveResetPreviewLoading.value = false
    return
  }
  try {
    const preview = await previewSelectiveResetApi(payload)
    selectiveResetPreview.value = preview
    selectiveResetSuccessMessage.value =
      Object.keys(preview.delete_plan).length > 0
        ? t('settings.selective_reset_preview_ready', {
            type: t(`settings.selective_reset_import_type_${preview.import_type}`),
            year: preview.fiscal_year_name,
          })
        : t('settings.selective_reset_preview_empty')
  } catch {
    selectiveResetErrorMessage.value = t('settings.selective_reset_error')
  } finally {
    selectiveResetPreviewLoading.value = false
  }
}

function confirmSelectiveReset(): void {
  confirm.require({
    message: t('settings.selective_reset_confirm'),
    header: t('settings.selective_reset_confirm_header'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('settings.selective_reset_apply_yes') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: applySelectiveReset,
  })
}

async function applySelectiveReset(): Promise<void> {
  selectiveResetApplying.value = true
  selectiveResetSuccessMessage.value = ''
  selectiveResetErrorMessage.value = ''
  const payload = buildSelectiveResetPayload()
  if (!payload) {
    selectiveResetApplying.value = false
    return
  }
  try {
    const result = await applySelectiveResetApi(payload)
    selectiveResetPreview.value = result
    const deletedCount = Object.values(result.delete_plan).reduce((sum, v) => sum + v, 0)
    selectiveResetSuccessMessage.value = t('settings.selective_reset_done', {
      count: deletedCount,
      type: t(`settings.selective_reset_import_type_${result.import_type}`),
      year: result.fiscal_year_name,
    })
  } catch {
    selectiveResetErrorMessage.value = t('settings.selective_reset_error')
  } finally {
    selectiveResetApplying.value = false
  }
}

watch(
  () => [selectiveResetForm.value.importType, selectiveResetForm.value.fiscalYearId],
  () => {
    selectiveResetPreview.value = null
    selectiveResetSuccessMessage.value = ''
    selectiveResetErrorMessage.value = ''
  },
)

onMounted(() => {
  void fiscalYearStore.initialize().then(() => {
    selectiveResetForm.value.fiscalYearId =
      fiscalYearStore.selectedFiscalYearId ?? fiscalYearStore.fiscalYears[0]?.id ?? null
  })
})
</script>

<style scoped>
.settings-danger {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.settings-selective-reset {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
  padding: var(--app-space-4);
  border: 1px solid var(--app-border-subtle);
  border-radius: var(--app-radius-lg);
  background: var(--app-surface-subtle);
}

.settings-selective-reset__header,
.settings-selective-reset__title,
.settings-selective-reset__subtitle {
  margin: 0;
}

.settings-selective-reset__subtitle,
.settings-selective-reset__hint {
  color: var(--app-text-muted);
}

.settings-selective-reset__preview {
  border-top: 1px solid var(--app-border-subtle);
  padding-top: var(--app-space-3);
}

.settings-selective-reset__groups {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--app-space-4);
}

.settings-selective-reset__groups h4,
.settings-selective-reset__groups ul {
  margin: 0;
}

.settings-selective-reset__groups ul {
  padding-left: 1rem;
}

.danger-panel :deep(.app-panel__header) {
  background-color: v-bind(dangerHeaderBg);
  border-bottom: 1px solid v-bind(dangerBorderColor);
}

.danger-panel :deep(.app-panel__title) {
  color: v-bind(dangerTitleColor);
  font-weight: 600;
}

@media (max-width: 767px) {
  .settings-selective-reset__groups {
    grid-template-columns: 1fr;
  }
}
</style>
