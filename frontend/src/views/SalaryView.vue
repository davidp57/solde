<template>
  <div class="salary-view p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">{{ t('salary.title') }}</h2>
      <Button :label="t('salary.new')" icon="pi pi-plus" @click="openCreateDialog" />
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4 flex-wrap">
      <Select
        v-model="filterEmployee"
        :options="employees"
        option-label="label"
        option-value="value"
        :placeholder="t('salary.filter_employee')"
        show-clear
        class="w-56"
        @change="loadSalaries"
      />
      <InputText
        v-model="filterMonth"
        :placeholder="t('salary.filter_month')"
        class="w-36"
        @change="loadSalaries"
      />
      <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" class="w-64" />
    </div>

    <!-- Table -->
    <DataTable
      :value="filteredSalaries"
      :loading="loading"
      striped-rows
      paginator
      :rows="20"
      data-key="id"
    >
      <Column field="employee_name" :header="t('salary.employee')" sortable />
      <Column field="month" :header="t('salary.month')" sortable />
      <Column :header="t('salary.hours')">
        <template #body="{ data }">{{ data.hours }}</template>
      </Column>
      <Column :header="t('salary.gross')">
        <template #body="{ data }">{{ formatAmount(data.gross) }}</template>
      </Column>
      <Column :header="t('salary.net_pay')">
        <template #body="{ data }">{{ formatAmount(data.net_pay) }}</template>
      </Column>
      <Column :header="t('salary.total_cost')">
        <template #body="{ data }">{{ formatAmount(data.total_cost) }}</template>
      </Column>
      <Column :header="t('common.actions')" style="width: 8rem">
        <template #body="{ data }">
          <div class="flex gap-1">
            <Button
              icon="pi pi-pencil"
              size="small"
              severity="secondary"
              text
              @click="openEditDialog(data)"
            />
            <Button
              icon="pi pi-trash"
              size="small"
              severity="danger"
              text
              @click="confirmDelete(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Monthly summary -->
    <div class="mt-8">
      <h3 class="text-lg font-medium mb-3">{{ t('salary.summary_title') }}</h3>
      <DataTable :value="filteredSummary" :loading="summaryLoading" striped-rows data-key="month">
        <Column field="month" :header="t('salary.month')" sortable />
        <Column field="count" header="#" />
        <Column :header="t('salary.gross')">
          <template #body="{ data }">{{ formatAmount(data.total_gross) }}</template>
        </Column>
        <Column :header="t('salary.employer_charges')">
          <template #body="{ data }">{{ formatAmount(data.total_employer_charges) }}</template>
        </Column>
        <Column :header="t('salary.net_pay')">
          <template #body="{ data }">{{ formatAmount(data.total_net_pay) }}</template>
        </Column>
        <Column :header="t('salary.total_cost')">
          <template #body="{ data }">{{ formatAmount(data.total_cost) }}</template>
        </Column>
      </DataTable>
    </div>

    <!-- Create / Edit dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editing ? t('salary.edit') : t('salary.new')"
      modal
      :style="{ width: '520px' }"
    >
      <div class="flex flex-col gap-4 pt-2">
        <div class="flex flex-col gap-1">
          <label class="font-medium text-sm">{{ t('salary.employee') }}</label>
          <Select
            v-model="form.employee_id"
            :options="employees"
            option-label="label"
            option-value="value"
            :placeholder="t('salary.employee_placeholder')"
            class="w-full"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="font-medium text-sm">{{ t('salary.month') }}</label>
          <InputText v-model="form.month" :placeholder="t('salary.month_placeholder')" class="w-full" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">{{ t('salary.hours') }}</label>
            <InputNumber v-model="form.hours" :min-fraction-digits="2" class="w-full" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">{{ t('salary.gross') }}</label>
            <InputNumber v-model="form.gross" :min-fraction-digits="2" suffix=" €" class="w-full" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">{{ t('salary.employee_charges') }}</label>
            <InputNumber v-model="form.employee_charges" :min-fraction-digits="2" suffix=" €" class="w-full" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">{{ t('salary.employer_charges') }}</label>
            <InputNumber v-model="form.employer_charges" :min-fraction-digits="2" suffix=" €" class="w-full" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">{{ t('salary.tax') }}</label>
            <InputNumber v-model="form.tax" :min-fraction-digits="2" suffix=" €" class="w-full" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="font-medium text-sm">{{ t('salary.net_pay') }}</label>
            <InputNumber v-model="form.net_pay" :min-fraction-digits="2" suffix=" €" class="w-full" />
          </div>
        </div>
        <div class="flex flex-col gap-1">
          <label class="font-medium text-sm">{{ t('salary.notes') }}</label>
          <Textarea v-model="form.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" severity="secondary" text @click="dialogVisible = false" />
        <Button :label="t('common.save')" :loading="saving" @click="save" />
      </template>
    </Dialog>

    <!-- Confirm delete -->
    <ConfirmDialog />
    <Toast />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import Toast from 'primevue/toast'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import {
  listSalariesApi,
  getSalarySummaryApi,
  createSalaryApi,
  updateSalaryApi,
  deleteSalaryApi,
  type SalaryRead,
  type SalarySummaryRow,
} from '../api/accounting'
import apiClient from '../api/client'
import { useTableFilter, applyFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

interface EmployeeOption { label: string; value: number }

const salaries = ref<SalaryRead[]>([])
const summary = ref<SalarySummaryRow[]>([])
const { filterText, filtered: filteredSalaries } = useTableFilter(salaries)
const filteredSummary = computed(() => applyFilter(summary.value, filterText.value))
const employees = ref<EmployeeOption[]>([])
const loading = ref(false)
const summaryLoading = ref(false)
const filterEmployee = ref<number | undefined>(undefined)
const filterMonth = ref('')

const dialogVisible = ref(false)
const editing = ref<SalaryRead | null>(null)
const saving = ref(false)

interface SalaryForm {
  employee_id: number | null
  month: string
  hours: number
  gross: number
  employee_charges: number
  employer_charges: number
  tax: number
  net_pay: number
  notes: string
}

function blankForm(): SalaryForm {
  return {
    employee_id: null,
    month: '',
    hours: 0,
    gross: 0,
    employee_charges: 0,
    employer_charges: 0,
    tax: 0,
    net_pay: 0,
    notes: '',
  }
}

const form = ref<SalaryForm>(blankForm())

function formatAmount(v: number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(v)
}

async function loadEmployees() {
  try {
    const res = await apiClient.get<{ id: number; nom: string; prenom: string | null }[]>('/contacts/')
    employees.value = res.data.map((c) => ({
      label: [c.prenom, c.nom].filter(Boolean).join(' '),
      value: c.id,
    }))
  } catch { /* ignore */ }
}

async function loadSalaries() {
  loading.value = true
  try {
    salaries.value = await listSalariesApi({
      employee_id: filterEmployee.value,
      month: filterMonth.value || undefined,
    })
  } finally {
    loading.value = false
  }
}

async function loadSummary() {
  summaryLoading.value = true
  try {
    summary.value = await getSalarySummaryApi()
  } finally {
    summaryLoading.value = false
  }
}

function openCreateDialog() {
  editing.value = null
  form.value = blankForm()
  dialogVisible.value = true
}

function openEditDialog(salary: SalaryRead) {
  editing.value = salary
  form.value = {
    employee_id: salary.employee_id,
    month: salary.month,
    hours: salary.hours,
    gross: salary.gross,
    employee_charges: salary.employee_charges,
    employer_charges: salary.employer_charges,
    tax: salary.tax,
    net_pay: salary.net_pay,
    notes: salary.notes ?? '',
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.value.employee_id || !form.value.month) return
  saving.value = true
  try {
    const payload = {
      employee_id: form.value.employee_id,
      month: form.value.month,
      hours: form.value.hours,
      gross: form.value.gross,
      employee_charges: form.value.employee_charges,
      employer_charges: form.value.employer_charges,
      tax: form.value.tax,
      net_pay: form.value.net_pay,
      notes: form.value.notes || null,
    }
    if (editing.value) {
      await updateSalaryApi(editing.value.id, payload)
    } else {
      await createSalaryApi(payload)
    }
    dialogVisible.value = false
    await loadSalaries()
    await loadSummary()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

function confirmDelete(salary: SalaryRead) {
  confirm.require({
    message: t('salary.confirm_delete', { employee: salary.employee_name, month: salary.month }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptSeverity: 'danger',
    accept: async () => {
      await deleteSalaryApi(salary.id)
      toast.add({ severity: 'success', summary: t('salary.deleted'), life: 2000 })
      await loadSalaries()
      await loadSummary()
    },
  })
}

onMounted(async () => {
  await Promise.all([loadEmployees(), loadSalaries(), loadSummary()])
})
</script>
