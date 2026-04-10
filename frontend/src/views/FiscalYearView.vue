<template>
  <div class="view-container">
    <div class="view-header">
      <h1>{{ t('accounting.fiscalYear.title') }}</h1>
      <Button
        :label="t('accounting.fiscalYear.new')"
        icon="pi pi-plus"
        @click="showDialog = true"
      />
    </div>

    <div class="mb-4">
      <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" class="w-64" />
    </div>

    <DataTable :value="filtered" :loading="loading" striped-rows>
      <Column field="name" :header="t('accounting.fiscalYear.name')" />
      <Column field="start_date" :header="t('accounting.fiscalYear.start_date')" />
      <Column field="end_date" :header="t('accounting.fiscalYear.end_date')" />
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
            :label="t('accounting.fiscalYear.close')"
            icon="pi pi-lock"
            severity="danger"
            text
            @click="confirmClose(data)"
          />
        </template>
      </Column>
      <template #empty>{{ t('accounting.balance.empty') }}</template>
    </DataTable>

    <!-- Create dialog -->
    <Dialog
      v-model:visible="showDialog"
      :header="t('accounting.fiscalYear.new')"
      modal
      style="width: 420px"
    >
      <div class="form-fields">
        <div class="field">
          <label>{{ t('accounting.fiscalYear.name') }}</label>
          <InputText v-model="form.name" :placeholder="t('accounting.fiscalYear.name_placeholder')" />
        </div>
        <div class="field">
          <label>{{ t('accounting.fiscalYear.start_date') }}</label>
          <InputText v-model="form.start_date" type="date" />
        </div>
        <div class="field">
          <label>{{ t('accounting.fiscalYear.end_date') }}</label>
          <InputText v-model="form.end_date" type="date" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="showDialog = false" />
        <Button :label="t('common.save')" icon="pi pi-check" :loading="saving" @click="createFY" />
      </template>
    </Dialog>

    <!-- Confirm close dialog -->
    <ConfirmDialog />
  </div>
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
import {
  listFiscalYearsApi,
  createFiscalYearApi,
  closeFiscalYearApi,
  type FiscalYearRead,
  type FiscalYearStatus,
} from '../api/accounting'
import { useTableFilter } from '../composables/useTableFilter'

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
        toast.add({ severity: 'success', summary: t('accounting.fiscalYear.closed_ok', { name: fy.name }), life: 3000 })
        await load()
      } catch {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
      }
    },
  })
}

onMounted(load)
</script>
