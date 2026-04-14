<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('ui.page.accounting_eyebrow')"
      :title="t('accounting.fiscalYear.title')"
    >
      <template #actions>
        <Button
          :label="t('accounting.fiscalYear.new')"
          icon="pi pi-plus"
          @click="showDialog = true"
        />
      </template>
    </AppPageHeader>

    <AppPanel :title="t('accounting.fiscalYear.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
          </div>
        </div>
      </div>

      <DataTable
        :value="filtered"
        :loading="loading"
        class="app-data-table"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        size="small"
        row-hover
      >
        <Column field="name" :header="t('accounting.fiscalYear.name')" />
        <Column field="start_date" :header="t('accounting.fiscalYear.start_date')">
          <template #body="{ data }">{{ formatDisplayDate(data.start_date) }}</template>
        </Column>
        <Column field="end_date" :header="t('accounting.fiscalYear.end_date')">
          <template #body="{ data }">{{ formatDisplayDate(data.end_date) }}</template>
        </Column>
        <Column field="status" :header="t('accounting.fiscalYear.status')">
          <template #body="{ data }">
            <Tag
              :value="t(`accounting.fiscalYear.statuses.${data.status}`)"
              :severity="statusSeverity(data.status)"
            />
          </template>
        </Column>
        <Column :header="t('common.actions')">
          <template #body="{ data }">
            <Button
              v-if="data.status === 'open'"
              :label="t('accounting.fiscalYear.close_administrative')"
              icon="pi pi-box"
              severity="warn"
              text
              @click="confirmAdministrativeClose(data)"
            />
            <Button
              v-if="data.status === 'open'"
              :label="t('accounting.fiscalYear.close')"
              icon="pi pi-lock"
              severity="danger"
              text
              @click="confirmClose(data)"
            />
          </template>
        </Column>
        <template #empty
          ><div class="app-empty-state">{{ t('accounting.balance.empty') }}</div></template
        >
      </DataTable>
    </AppPanel>

    <!-- Create dialog -->
    <Dialog
      v-model:visible="showDialog"
      :header="t('accounting.fiscalYear.new')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('accounting.fiscalYear.title') }}</p>
          <p class="app-dialog-intro__text">{{ t('accounting.fiscalYear.form_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">
              {{ t('accounting.fiscalYear.calendar_title') }}
            </h3>
            <p class="app-dialog-section__copy">
              {{ t('accounting.fiscalYear.calendar_subtitle') }}
            </p>
          </div>
          <div class="app-form-grid">
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('accounting.fiscalYear.name') }}</label>
              <InputText
                v-model="form.name"
                :placeholder="t('accounting.fiscalYear.name_placeholder')"
              />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('accounting.fiscalYear.start_date') }}</label>
              <InputText v-model="form.start_date" type="date" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('accounting.fiscalYear.end_date') }}</label>
              <InputText v-model="form.end_date" type="date" />
            </div>
          </div>
        </section>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="showDialog = false" />
        <Button :label="t('common.save')" icon="pi pi-check" :loading="saving" @click="createFY" />
      </template>
    </Dialog>

    <!-- Confirm close dialog -->
    <ConfirmDialog />
  </AppPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import {
  listFiscalYearsApi,
  createFiscalYearApi,
  closeFiscalYearApi,
  closeFiscalYearAdministrativeApi,
  type FiscalYearRead,
  type FiscalYearStatus,
} from '../api/accounting'
import { useTableFilter } from '../composables/useTableFilter'
import { formatDisplayDate } from '@/utils/format'

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

const fiscalYears = ref<FiscalYearRead[]>([])
const { filterText, filtered } = useTableFilter(fiscalYears)
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)

const form = ref({ name: '', start_date: '', end_date: '' })

function statusSeverity(status: FiscalYearStatus) {
  if (status === 'open') return 'success'
  if (status === 'closing') return 'warn'
  return 'secondary'
}

async function load() {
  loading.value = true
  try {
    fiscalYears.value = await listFiscalYearsApi()
  } finally {
    loading.value = false
  }
}

async function createFY() {
  saving.value = true
  try {
    await createFiscalYearApi(form.value)
    showDialog.value = false
    form.value = { name: '', start_date: '', end_date: '' }
    await load()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

function confirmClose(fy: FiscalYearRead) {
  confirm.require({
    message: t('accounting.fiscalYear.close_confirm', { name: fy.name }),
    header: t('accounting.fiscalYear.close'),
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: t('common.cancel'), severity: 'secondary', text: true },
    acceptProps: { label: t('common.confirm'), severity: 'danger' },
    accept: async () => {
      try {
        await closeFiscalYearApi(fy.id)
        toast.add({
          severity: 'success',
          summary: t('accounting.fiscalYear.closed_ok', { name: fy.name }),
          life: 3000,
        })
        await load()
      } catch {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
      }
    },
  })
}

function confirmAdministrativeClose(fy: FiscalYearRead) {
  confirm.require({
    message: t('accounting.fiscalYear.close_administrative_confirm', { name: fy.name }),
    header: t('accounting.fiscalYear.close_administrative'),
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: t('common.cancel'), severity: 'secondary', text: true },
    acceptProps: { label: t('common.confirm'), severity: 'warn' },
    accept: async () => {
      try {
        await closeFiscalYearAdministrativeApi(fy.id)
        toast.add({
          severity: 'success',
          summary: t('accounting.fiscalYear.closed_administrative_ok', { name: fy.name }),
          life: 3000,
        })
        await load()
      } catch {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
      }
    },
  })
}

onMounted(load)
</script>
