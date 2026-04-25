<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="t('salary.title')">
      <template #actions>
        <Button :label="t('salary.new')" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard :label="t('salary.title')" :value="filteredSalaries.length" />
      <AppStatCard :label="t('salary.gross')" :value="formatAmount(salaryMetrics.gross)" />
      <AppStatCard
        :label="t('salary.net_pay')"
        :value="formatAmount(salaryMetrics.netPay)"
        tone="success"
      />
      <AppStatCard
        :label="t('salary.total_cost')"
        :value="formatAmount(salaryMetrics.totalCost)"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('salary.title')" dense>
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <AppListState
            :displayed-count="filteredSalaries.length"
            :total-count="salaries.length"
            :loading="loading"
            :search-text="filterText"
          />
          <Button
            :label="t('common.reset_filters')"
            icon="pi pi-filter-slash"
            severity="secondary"
            outlined
            size="small"
            :disabled="!hasAnyFilters"
            @click="resetAllFilters"
          />
        </div>
        <div class="app-filter-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('salary.filter_employee') }}</label>
            <Select
              v-model="filterEmployee"
              :options="employeeFilterOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('salary.filter_employee')"
              show-clear
              @change="loadSalaries"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('salary.filter_month') }}</label>
            <InputText
              v-model="filterMonth"
              :placeholder="t('salary.filter_month')"
              @change="loadSalaries"
            />
          </div>
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
          </div>
        </div>
      </div>

      <DataTable
        v-model:filters="salaryTableFilters"
        :value="salaryRows"
        :loading="loading"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        data-key="id"
        size="small"
        row-hover
        :global-filter-fields="[
          'employee_name',
          'month',
          'hours_value',
          'gross_value',
          'net_pay_value',
          'total_cost_value',
        ]"
        removable-sort
        @value-change="syncDisplayedSalaries"
      >
        <Column
          field="employee_name"
          :header="t('salary.employee')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="salaryEmployeeOptions"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="month"
          :header="t('salary.month')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatDisplayMonth(data.month) }}</template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="salaryMonthOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="hours_value"
          :header="t('salary.hours')"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ data.hours }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="gross_value"
          :header="t('salary.gross')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatAmount(data.gross) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="net_pay_value"
          :header="t('salary.net_pay')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatAmount(data.net_pay) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="total_cost_value"
          :header="t('salary.total_cost')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatAmount(data.total_cost) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column :header="t('common.actions')" style="width: 8rem">
          <template #body="{ data }">
            <div class="salary-actions">
              <Button
                icon="pi pi-pencil"
                size="small"
                severity="secondary"
                text
                :title="t('salary.edit')"
                :aria-label="t('salary.edit')"
                @click="openEditDialog(data)"
              />
              <Button
                icon="pi pi-trash"
                size="small"
                severity="danger"
                text
                :title="t('common.delete')"
                :aria-label="t('common.delete')"
                @click="confirmDelete(data)"
              />
            </div>
          </template>
        </Column>
        <template #empty
          ><div class="app-empty-state">{{ t('salary.empty') }}</div></template
        >
      </DataTable>
    </AppPanel>

    <AppPanel :title="t('salary.summary_title')" dense>
      <DataTable
        v-model:filters="summaryTableFilters"
        :value="summaryRows"
        :loading="summaryLoading"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        data-key="month"
        size="small"
        row-hover
        :global-filter-fields="[
          'month',
          'count',
          'total_gross_value',
          'total_employer_charges_value',
          'total_net_pay_value',
          'total_cost_value',
        ]"
        removable-sort
        @value-change="syncDisplayedSummary"
      >
        <Column
          field="month"
          :header="t('salary.month')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatDisplayMonth(data.month) }}</template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="summaryMonthOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="count"
          header="#"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="total_gross_value"
          :header="t('salary.gross')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatAmount(data.total_gross) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="total_employer_charges_value"
          :header="t('salary.employer_charges')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatAmount(data.total_employer_charges) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="total_net_pay_value"
          :header="t('salary.net_pay')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatAmount(data.total_net_pay) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="total_cost_value"
          :header="t('salary.total_cost')"
          class="app-money"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatAmount(data.total_cost) }}</template>
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <template #empty
          ><div class="app-empty-state">{{ t('salary.empty') }}</div></template
        >
      </DataTable>
    </AppPanel>

    <AppPanel :title="t('salary.workforce_title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field">
            <label class="app-field__label">{{ t('salary.filter_month_from') }}</label>
            <InputText
              v-model="workforceFromMonth"
              :placeholder="t('salary.month_placeholder')"
              @change="loadWorkforce"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('salary.filter_month_to') }}</label>
            <InputText
              v-model="workforceToMonth"
              :placeholder="t('salary.month_placeholder')"
              @change="loadWorkforce"
            />
          </div>
          <div class="app-field app-field--align-end">
            <Button
              :label="t('common.refresh')"
              icon="pi pi-refresh"
              severity="secondary"
              outlined
              size="small"
              :loading="workforceLoading"
              @click="loadWorkforce"
            />
          </div>
        </div>
      </div>
      <DataTable
        :value="workforceSummaryByMonth"
        :loading="workforceLoading"
        class="app-data-table"
        striped-rows
        size="small"
        row-hover
        removable-sort
      >
        <Column field="month" :header="t('salary.month')" sortable>
          <template #body="{ data }">{{ formatDisplayMonth(data.month) }}</template>
        </Column>
        <Column
          field="cdi"
          :header="t('salary.workforce_type_cdi')"
          class="app-money"
          data-type="numeric"
          sortable
        >
          <template #body="{ data }">{{ data.cdi > 0 ? formatAmount(data.cdi) : '—' }}</template>
        </Column>
        <Column
          field="cdd"
          :header="t('salary.workforce_type_cdd')"
          class="app-money"
          data-type="numeric"
          sortable
        >
          <template #body="{ data }">{{ data.cdd > 0 ? formatAmount(data.cdd) : '—' }}</template>
        </Column>
        <Column
          field="ae"
          :header="t('salary.workforce_type_ae')"
          class="app-money"
          data-type="numeric"
          sortable
        >
          <template #body="{ data }">{{ data.ae > 0 ? formatAmount(data.ae) : '—' }}</template>
        </Column>
        <Column
          field="total"
          :header="t('salary.workforce_col_total')"
          class="app-money"
          data-type="numeric"
          sortable
        >
          <template #body="{ data }">{{ formatAmount(data.total) }}</template>
        </Column>
        <template #empty
          ><div class="app-empty-state">{{ t('salary.workforce_empty') }}</div></template
        >
      </DataTable>
    </AppPanel>

    <Dialog
      :visible="dialogVisible"
      @update:visible="onCloseDialog"
      :header="editing ? t('salary.edit') : t('salary.new')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('salary.title') }}</p>
          <p class="app-dialog-intro__text">
            {{ t(isEditing ? 'salary.form_intro_edit' : 'salary.form_intro_create') }}
          </p>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('salary.group_identity_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('salary.group_identity_subtitle') }}</p>
          </div>
          <div class="app-form-grid">
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('salary.employee') }}</label>
              <Select
                v-model="form.employee_id"
                :options="employees"
                option-label="label"
                option-value="value"
                :placeholder="t('salary.employee_placeholder')"
              />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('salary.month') }}</label>
              <InputText v-model="form.month" :placeholder="t('salary.month_placeholder')" />
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('salary.group_brut_title') }}</h3>
            <p class="app-dialog-section__copy">
              {{ isCDD ? t('salary.group_brut_subtitle_cdd') : t('salary.group_brut_subtitle_cdi') }}
            </p>
          </div>
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('salary.hours') }}</label>
              <InputNumber v-model="form.hours" :min-fraction-digits="2" />
            </div>
            <template v-if="isCDD">
              <div class="app-field">
                <label class="app-field__label">{{ t('salary.hourly_rate') }}</label>
                <InputNumber
                  :model-value="selectedEmployee?.hourly_rate ?? 0"
                  :min-fraction-digits="2"
                  suffix=" €/h"
                  :disabled="true"
                />
              </div>
              <div class="app-field">
                <label class="app-field__label">{{ t('salary.brut_declared') }}</label>
                <InputNumber
                  :model-value="form.brut_declared ?? 0"
                  :min-fraction-digits="2"
                  suffix=" €"
                  :disabled="true"
                />
              </div>
              <div class="app-field">
                <label class="app-field__label">{{ t('salary.conges_payes') }}</label>
                <InputNumber
                  :model-value="form.conges_payes ?? 0"
                  :min-fraction-digits="2"
                  suffix=" €"
                  :disabled="true"
                />
              </div>
              <div class="app-field">
                <label class="app-field__label">{{ t('salary.precarite') }}</label>
                <InputNumber
                  :model-value="form.precarite ?? 0"
                  :min-fraction-digits="2"
                  suffix=" €"
                  :disabled="true"
                />
              </div>
              <div class="app-field app-field--full">
                <label class="app-field__label">{{ t('salary.brut_total_computed') }}</label>
                <InputNumber
                  :model-value="form.gross"
                  :min-fraction-digits="2"
                  suffix=" €"
                  :disabled="true"
                />
                <small class="app-dialog-note">{{ t('salary.brut_total_computed_help') }}</small>
              </div>
            </template>
            <template v-else>
              <div class="app-field">
                <label class="app-field__label">{{ t('salary.gross') }}</label>
                <InputNumber v-model="form.gross" :min-fraction-digits="2" suffix=" €" />
              </div>
            </template>
            <div class="app-field app-field--full">
              <Button
                :label="t('salary.copy_previous')"
                icon="pi pi-history"
                severity="secondary"
                outlined
                size="small"
                :loading="copyingPrevious"
                :disabled="!form.employee_id"
                type="button"
                @click="copyPrevious"
              />
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('salary.group_cea_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('salary.group_cea_subtitle') }}</p>
          </div>
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('salary.employee_charges') }}</label>
              <InputNumber v-model="form.employee_charges" :min-fraction-digits="2" suffix=" €" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('salary.employer_charges') }}</label>
              <InputNumber v-model="form.employer_charges" :min-fraction-digits="2" suffix=" €" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('salary.tax') }}</label>
              <InputNumber v-model="form.tax" :min-fraction-digits="2" suffix=" €" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('salary.net_pay') }}</label>
              <InputNumber v-model="form.net_pay" :min-fraction-digits="2" suffix=" €" />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('salary.net_pay_computed') }}</label>
              <InputNumber
                :model-value="netPayComputed"
                :min-fraction-digits="2"
                suffix=" €"
                :disabled="true"
              />
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('salary.notes') }}</label>
            <Textarea v-model="form.notes" rows="2" />
            <small class="app-dialog-note">{{ t('salary.notes_help') }}</small>
          </div>
        </section>
      </div>
      <template #footer>
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          text
          @click="onCloseDialog(false)"
        />
        <Button :label="t('common.save')" :loading="saving" @click="save" />
      </template>
    </Dialog>

    <ConfirmDialog />
    <Toast />
  </AppPage>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
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
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppListState from '../components/ui/AppListState.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import {
  listSalariesApi,
  getSalarySummaryApi,
  createSalaryApi,
  updateSalaryApi,
  deleteSalaryApi,
  getPreviousSalaryApi,
  getWorkforceCostApi,
  type SalaryRead,
  type SalarySummaryRow,
  type WorkforceCostRow,
} from '../api/accounting'
import { listContactsApi } from '../api/contacts'
import {
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import { useUnsavedChangesGuard } from '../composables/useUnsavedChangesGuard'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { formatDisplayMonth } from '../utils/format'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()

interface EmployeeOption {
  label: string
  value: number
  contract_type: 'cdi' | 'cdd' | null
  hourly_rate: number | null
  base_gross: number | null
  base_hours: number | null
}

const salaries = ref<SalaryRead[]>([])
const summary = ref<SalarySummaryRow[]>([])
const salaryRows = computed(() =>
  salaries.value.map((salary) => ({
    ...salary,
    hours_value: toSalaryNumber(salary.hours),
    gross_value: toSalaryNumber(salary.gross),
    net_pay_value: toSalaryNumber(salary.net_pay),
    total_cost_value: toSalaryNumber(salary.total_cost),
  })),
)
const summaryRows = computed(() =>
  summary.value.map((row) => ({
    ...row,
    total_gross_value: toSalaryNumber(row.total_gross),
    total_employer_charges_value: toSalaryNumber(row.total_employer_charges),
    total_net_pay_value: toSalaryNumber(row.total_net_pay),
    total_cost_value: toSalaryNumber(row.total_cost),
  })),
)
const {
  filters: salaryTableFilters,
  globalFilter: salaryGlobalFilter,
  displayedRows: filteredSalaries,
  syncDisplayedRows: syncDisplayedSalaries,
  resetFilters: resetSalaryFilters,
  hasActiveFilters: hasActiveSalaryFilters,
} = useDataTableFilters(salaryRows, {
  global: textFilter(''),
  employee_name: inFilter(),
  month: inFilter(),
  hours_value: numericRangeFilter(),
  gross_value: numericRangeFilter(),
  net_pay_value: numericRangeFilter(),
  total_cost_value: numericRangeFilter(),
})
const {
  filters: summaryTableFilters,
  globalFilter: summaryGlobalFilter,
  syncDisplayedRows: syncDisplayedSummary,
  resetFilters: resetSummaryFilters,
} = useDataTableFilters(summaryRows, {
  global: textFilter(''),
  month: inFilter(),
  count: numericRangeFilter(),
  total_gross_value: numericRangeFilter(),
  total_employer_charges_value: numericRangeFilter(),
  total_net_pay_value: numericRangeFilter(),
  total_cost_value: numericRangeFilter(),
})
const filterText = computed({
  get: () => salaryGlobalFilter.value,
  set: (value: string) => {
    salaryGlobalFilter.value = value
    summaryGlobalFilter.value = value
  },
})

const hasAnyFilters = computed(
  () =>
    hasActiveSalaryFilters.value ||
    Boolean(filterEmployee.value) ||
    Boolean(filterMonth.value),
)

function resetAllFilters(): void {
  resetSalaryFilters()
  resetSummaryFilters()
  filterEmployee.value = undefined
  filterMonth.value = ''
  void loadSalaries()
}
function toSalaryNumber(value: number | string | null | undefined): number {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : 0
  }
  if (typeof value === 'string') {
    const parsedValue = Number.parseFloat(value)
    return Number.isFinite(parsedValue) ? parsedValue : 0
  }
  return 0
}

const salaryMetrics = computed(() =>
  filteredSalaries.value.reduce(
    (accumulator, salary) => {
      accumulator.gross += toSalaryNumber(salary.gross)
      accumulator.netPay += toSalaryNumber(salary.net_pay)
      accumulator.totalCost += toSalaryNumber(salary.total_cost)
      return accumulator
    },
    { gross: 0, netPay: 0, totalCost: 0 },
  ),
)
const employees = ref<EmployeeOption[]>([])
const loading = ref(false)
const summaryLoading = ref(false)
const filterEmployee = ref<number | undefined>(undefined)
const filterMonth = ref('')
const employeeFilterOptions = computed(() => {
  const optionsById = new Map<number, EmployeeOption>()

  for (const employee of employees.value) {
    optionsById.set(employee.value, employee)
  }

  for (const salary of salaries.value) {
    if (!optionsById.has(salary.employee_id)) {
      optionsById.set(salary.employee_id, {
        label: salary.employee_name,
        value: salary.employee_id,
      })
    }
  }

  return Array.from(optionsById.values()).sort((left, right) =>
    left.label.localeCompare(right.label),
  )
})
const salaryEmployeeOptions = computed(() =>
  Array.from(new Set(salaries.value.map((salary) => salary.employee_name))).sort(),
)
const salaryMonthOptions = computed(() =>
  Array.from(new Set(salaries.value.map((salary) => salary.month)))
    .sort()
    .map((month) => ({ label: formatDisplayMonth(month), value: month })),
)
const summaryMonthOptions = computed(() =>
  Array.from(new Set(summary.value.map((row) => row.month)))
    .sort()
    .map((month) => ({ label: formatDisplayMonth(month), value: month })),
)
const salaryMonthRange = computed(() => ({
  from_month: fiscalYearStore.selectedFiscalYear?.start_date.slice(0, 7),
  to_month: fiscalYearStore.selectedFiscalYear?.end_date.slice(0, 7),
}))

const dialogVisible = ref(false)
const editing = ref<SalaryRead | null>(null)
const saving = ref(false)
const isEditing = computed(() => editing.value !== null)
const copyingPrevious = ref(false)
const formInitialSnapshot = ref('')
const isFormDirty = computed(() => JSON.stringify(form.value) !== formInitialSnapshot.value)

function captureFormSnapshot(): void {
  formInitialSnapshot.value = JSON.stringify(form.value)
}

const onCloseDialog = useUnsavedChangesGuard(dialogVisible, () => isFormDirty.value, { withRouteLeaveGuard: true })

// Workforce cost panel
const workforceCost = ref<WorkforceCostRow[]>([])
const workforceLoading = ref(false)
const workforceFromMonth = ref('')
const workforceToMonth = ref('')

interface WorkforceMonthRow {
  month: string
  cdi: number
  cdd: number
  ae: number
  total: number
}

const workforceSummaryByMonth = computed<WorkforceMonthRow[]>(() => {
  const map = new Map<string, WorkforceMonthRow>()
  for (const row of workforceCost.value) {
    if (!map.has(row.month)) {
      map.set(row.month, { month: row.month, cdi: 0, cdd: 0, ae: 0, total: 0 })
    }
    const entry = map.get(row.month)!
    const cost = Number(row.total_cost)
    const type = row.person_type.toUpperCase()
    if (type === 'CDI') entry.cdi += cost
    else if (type === 'CDD') entry.cdd += cost
    else if (type === 'AE') entry.ae += cost
    entry.total += cost
  }
  return Array.from(map.values()).sort((a, b) => a.month.localeCompare(b.month))
})

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
  brut_declared: number | null
  conges_payes: number | null
  precarite: number | null
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
    brut_declared: null,
    conges_payes: null,
    precarite: null,
  }
}

const form = ref<SalaryForm>(blankForm())

const selectedEmployee = computed<EmployeeOption | null>(
  () => employees.value.find((e) => e.value === form.value.employee_id) ?? null,
)

const isCDD = computed(() => selectedEmployee.value?.contract_type === 'cdd')
const isCDI = computed(() => selectedEmployee.value?.contract_type === 'cdi')

const netPayComputed = computed(() => {
  return form.value.gross - form.value.employee_charges - form.value.tax
})

// Auto-calc CDD brut fields when hours changes
watch(
  () => [form.value.hours, form.value.employee_id] as const,
  () => {
    if (!isCDD.value) return
    const round2 = (n: number) => Math.round(n * 100) / 100
    const rate = selectedEmployee.value?.hourly_rate ?? 0
    const brutD = round2(form.value.hours * rate)
    const cp = round2(brutD * 0.1)
    const prec = round2((brutD + cp) * 0.1)
    form.value.brut_declared = brutD
    form.value.conges_payes = cp
    form.value.precarite = prec
    form.value.gross = round2(brutD + cp + prec)
  },
)

// Pre-fill CDI from employee base data when employee changes in create mode
watch(
  () => form.value.employee_id,
  () => {
    if (editing.value !== null) return
    if (isCDI.value && selectedEmployee.value) {
      form.value.hours = selectedEmployee.value.base_hours ?? 0
      form.value.gross = selectedEmployee.value.base_gross ?? 0
    }
  },
)

function formatAmount(v: number | string | null | undefined): string {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
    toSalaryNumber(v),
  )
}

async function loadEmployees() {
  try {
    const contacts = await listContactsApi({ type: 'employe', active_only: false })
    employees.value = contacts.map((c) => ({
      label: [c.prenom, c.nom].filter(Boolean).join(' '),
      value: c.id,
      contract_type: c.contract_type ?? null,
      hourly_rate: c.hourly_rate ?? null,
      base_gross: c.base_gross ?? null,
      base_hours: c.base_hours ?? null,
    }))
  } catch {
    /* ignore */
  }
}

async function loadSalaries() {
  loading.value = true
  try {
    salaries.value = await listSalariesApi({
      employee_id: filterEmployee.value,
      month: filterMonth.value || undefined,
      from_month: salaryMonthRange.value.from_month,
      to_month: salaryMonthRange.value.to_month,
    })
  } finally {
    loading.value = false
  }
}

async function loadSummary() {
  summaryLoading.value = true
  try {
    summary.value = await getSalarySummaryApi({
      from_month: salaryMonthRange.value.from_month,
      to_month: salaryMonthRange.value.to_month,
    })
  } finally {
    summaryLoading.value = false
  }
}

function openCreateDialog() {
  editing.value = null
  form.value = blankForm()
  dialogVisible.value = true
  void nextTick(captureFormSnapshot)
}

function openEditDialog(salary: SalaryRead) {
  editing.value = salary
  form.value = {
    employee_id: salary.employee_id,
    month: salary.month,
    hours: toSalaryNumber(salary.hours),
    gross: toSalaryNumber(salary.gross),
    employee_charges: toSalaryNumber(salary.employee_charges),
    employer_charges: toSalaryNumber(salary.employer_charges),
    tax: toSalaryNumber(salary.tax),
    net_pay: toSalaryNumber(salary.net_pay),
    notes: salary.notes ?? '',
    brut_declared: salary.brut_declared ?? null,
    conges_payes: salary.conges_payes ?? null,
    precarite: salary.precarite ?? null,
  }
  dialogVisible.value = true
  void nextTick(captureFormSnapshot)
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
      brut_declared: form.value.brut_declared,
      conges_payes: form.value.conges_payes,
      precarite: form.value.precarite,
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

async function copyPrevious(): Promise<void> {
  if (!form.value.employee_id) return
  copyingPrevious.value = true
  try {
    const prev = await getPreviousSalaryApi(form.value.employee_id)
    form.value.hours = prev.hours
    form.value.gross = prev.gross
    form.value.brut_declared = prev.brut_declared
    form.value.conges_payes = prev.conges_payes
    form.value.precarite = prev.precarite
    toast.add({ severity: 'info', summary: t('salary.copy_previous_applied'), life: 3000 })
  } catch {
    toast.add({ severity: 'warn', summary: t('salary.copy_previous_not_found'), life: 3000 })
  } finally {
    copyingPrevious.value = false
  }
}

async function loadWorkforce(): Promise<void> {
  workforceLoading.value = true
  try {
    workforceCost.value = await getWorkforceCostApi({
      from_month: workforceFromMonth.value || salaryMonthRange.value.from_month,
      to_month: workforceToMonth.value || salaryMonthRange.value.to_month,
    })
  } finally {
    workforceLoading.value = false
  }
}

function confirmDelete(salary: SalaryRead) {
  confirm.require({
    message: t('salary.confirm_delete', {
      employee: salary.employee_name,
      month: formatDisplayMonth(salary.month),
    }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('common.delete') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: async () => {
      await deleteSalaryApi(salary.id)
      toast.add({ severity: 'success', summary: t('salary.deleted'), life: 2000 })
      await loadSalaries()
      await loadSummary()
    },
  })
}

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    workforceFromMonth.value = salaryMonthRange.value.from_month ?? ''
    workforceToMonth.value = salaryMonthRange.value.to_month ?? ''
    void Promise.all([loadSalaries(), loadSummary(), loadWorkforce()])
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  workforceFromMonth.value = salaryMonthRange.value.from_month ?? ''
  workforceToMonth.value = salaryMonthRange.value.to_month ?? ''
  await Promise.all([loadEmployees(), loadSalaries(), loadSummary(), loadWorkforce()])
})
</script>

<style scoped>
.salary-actions {
  display: flex;
  gap: var(--app-space-1);
}

.salary-actions :deep(.p-button) {
  flex: 0 0 auto;
}
</style>
