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
        <div class="app-toolbar__meta">
          <AppListState
            :displayed-count="displayedFiscalYears.length"
            :total-count="fiscalYears.length"
            :loading="loading"
            :search-text="filterText"
          />
          <Button
            :label="t('common.reset_filters')"
            icon="pi pi-filter-slash"
            severity="secondary"
            outlined
            size="small"
            :disabled="!hasActiveFilters"
            @click="resetFilters"
          />
          <Button
            :label="t('common.export_excel')"
            icon="pi pi-file-excel"
            severity="secondary"
            outlined
            size="small"
            @click="doExportExcel"
          />
        </div>

        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
          </div>
        </div>
      </div>

      <template v-if="isMobile">
        <AppMobileCardList :items="fiscalYearRows" :empty-message="t('accounting.fiscalYear.empty')">
          <template #card="{ item: data }">
            <div class="app-mobile-card-row app-mobile-card-row--between">
              <span class="app-mobile-card-value" style="font-weight:700">{{ data.name }}</span>
              <Tag
                :value="t(`accounting.fiscalYear.statuses.${data.status}`)"
                :severity="statusSeverity(data.status)"
              />
            </div>
            <div class="app-mobile-card-row">
              <span class="app-mobile-card-label">{{ t('accounting.fiscalYear.start_date') }}</span>
              <span class="app-mobile-card-value">{{ formatDisplayDate(data.start_date) }}</span>
            </div>
            <div class="app-mobile-card-row">
              <span class="app-mobile-card-label">{{ t('accounting.fiscalYear.end_date') }}</span>
              <span class="app-mobile-card-value">{{ formatDisplayDate(data.end_date) }}</span>
            </div>
            <div v-if="data.status === 'open' || canOpenNext(data)" class="app-mobile-card-actions">
              <Button
                v-if="data.status === 'open'"
                :label="t('accounting.fiscalYear.close_administrative')"
                icon="pi pi-box"
                severity="warn"
                text
                size="small"
                @click="confirmAdministrativeClose(data)"
              />
              <Button
                v-if="data.status === 'open'"
                :label="t('accounting.fiscalYear.close')"
                icon="pi pi-lock"
                severity="danger"
                text
                size="small"
                @click="openCloseDialog(data)"
              />
              <Button
                v-if="canOpenNext(data)"
                :label="t('accounting.fiscalYear.open_next')"
                icon="pi pi-forward"
                text
                size="small"
                @click="openNextDialog(data)"
              />
            </div>
          </template>
        </AppMobileCardList>
      </template>
      <DataTable
        v-else
        v-model:filters="tableFilters"
        :value="fiscalYearRows"
        :loading="loading"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="50"
        :rows-per-page-options="[20, 50, 100, 500]"
        size="small"
        row-hover
        :global-filter-fields="['name', 'start_date', 'end_date', 'status']"
        removable-sort
        @value-change="syncDisplayedFiscalYears"
      >
        <Column
          field="name"
          :header="t('accounting.fiscalYear.name')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('accounting.fiscalYear.name')" />
          </template>
        </Column>
        <Column
          field="start_date"
          :header="t('accounting.fiscalYear.start_date')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatDisplayDate(data.start_date) }}</template>
          <template #filter="{ filterModel }">
            <AppDateRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="end_date"
          :header="t('accounting.fiscalYear.end_date')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">{{ formatDisplayDate(data.end_date) }}</template>
          <template #filter="{ filterModel }">
            <AppDateRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
        <Column
          field="status_label"
          :header="t('accounting.fiscalYear.status')"
          sortable
          filter-field="status"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag
              :value="t(`accounting.fiscalYear.statuses.${data.status}`)"
              :severity="statusSeverity(data.status)"
            />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="statusOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              display="chip"
              show-clear
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
              @click="openCloseDialog(data)"
            />
            <Button
              v-if="canOpenNext(data)"
              data-testid="fy-open-next"
              :label="t('accounting.fiscalYear.open_next')"
              icon="pi pi-forward"
              text
              @click="openNextDialog(data)"
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

    <!-- Close dialog — shows the pre-close checks before the irreversible step -->
    <Dialog
      v-model:visible="closeDialogVisible"
      :header="t('accounting.fiscalYear.close')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form" data-testid="fy-close-body">
        <p v-if="checksLoading">{{ t('accounting.fiscalYear.checks_loading') }}</p>
        <template v-else>
          <Message v-if="preCloseWarnings.length" severity="warn">
            <p>{{ t('accounting.fiscalYear.checks_warning_intro') }}</p>
            <ul class="fy-checks">
              <li v-for="warning in preCloseWarnings" :key="warning">{{ warning }}</li>
            </ul>
          </Message>
          <Message v-else severity="success">
            {{ t('accounting.fiscalYear.pre_close_ok') }}
          </Message>
          <p>{{ t('accounting.fiscalYear.close_confirm', { name: closeTarget?.name ?? '' }) }}</p>
          <p class="app-dialog-hint">{{ t('accounting.fiscalYear.close_then_open_next') }}</p>
        </template>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="closeDialogVisible = false" />
        <Button
          data-testid="fy-close-confirm"
          :label="t('accounting.fiscalYear.close')"
          icon="pi pi-lock"
          severity="danger"
          :loading="closing"
          :disabled="checksLoading"
          @click="doClose"
        />
      </template>
    </Dialog>

    <!-- Open next fiscal year — carries balances forward (report à nouveau) -->
    <Dialog
      v-model:visible="nextDialogVisible"
      :header="t('accounting.fiscalYear.open_next')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__text">
            {{ t('accounting.fiscalYear.open_next_intro', { name: nextTarget?.name ?? '' }) }}
          </p>
        </section>
        <div class="app-form-grid">
          <div class="app-field app-field--full">
            <label class="app-field__label">{{ t('accounting.fiscalYear.name') }}</label>
            <InputText v-model="nextForm.name" data-testid="fy-next-name" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.fiscalYear.start_date') }}</label>
            <InputText v-model="nextForm.start_date" type="date" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('accounting.fiscalYear.end_date') }}</label>
            <InputText v-model="nextForm.end_date" type="date" />
          </div>
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="nextDialogVisible = false" />
        <Button
          data-testid="fy-next-confirm"
          :label="t('accounting.fiscalYear.open_next_confirm')"
          icon="pi pi-check"
          :loading="openingNext"
          @click="doOpenNext"
        />
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
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import AppListState from '../components/ui/AppListState.vue'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppMobileCardList from '../components/ui/AppMobileCardList.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import {
  listFiscalYearsApi,
  createFiscalYearApi,
  closeFiscalYearApi,
  closeFiscalYearAdministrativeApi,
  getFiscalYearPreCloseChecksApi,
  openNextFiscalYearApi,
  type FiscalYearRead,
  type FiscalYearStatus,
} from '../api/accounting'
import {
  dateRangeFilter,
  inFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'
import { useBreakpoints } from '../composables/useBreakpoints'
import { useTableExport, type ExportColumn } from '@/composables/useTableExport'
import { formatDisplayDate } from '@/utils/format'

const { t } = useI18n()
const { isMobile } = useBreakpoints()
const toast = useToast()
const confirm = useConfirm()
const { exportToExcel } = useTableExport()
const exportColumns: ExportColumn[] = [
  { field: 'name', header: t('accounting.fiscalYear.name') },
  { field: 'start_date', header: t('accounting.fiscalYear.start_date') },
  { field: 'end_date', header: t('accounting.fiscalYear.end_date') },
  { field: 'status_label', header: t('accounting.fiscalYear.status') },
]
function doExportExcel(): void {
  exportToExcel(displayedFiscalYears.value, exportColumns, 'fiscal-years-export')
}

const fiscalYears = ref<FiscalYearRead[]>([])
const loading = ref(false)
const saving = ref(false)
const showDialog = ref(false)
const fiscalYearRows = ref<Array<FiscalYearRead & { status_label: string }>>([])
const statusOptions = [
  { label: t('accounting.fiscalYear.statuses.open'), value: 'open' as FiscalYearStatus },
  { label: t('accounting.fiscalYear.statuses.closing'), value: 'closing' as FiscalYearStatus },
  { label: t('accounting.fiscalYear.statuses.closed'), value: 'closed' as FiscalYearStatus },
]
const {
  filters: tableFilters,
  globalFilter: filterText,
  displayedRows: displayedFiscalYears,
  syncDisplayedRows: syncDisplayedFiscalYears,
  resetFilters,
  hasActiveFilters,
} = useDataTableFilters(fiscalYearRows, {
  global: textFilter(''),
  name: textFilter(),
  start_date: dateRangeFilter(),
  end_date: dateRangeFilter(),
  status: inFilter(),
})

const form = ref({ name: '', start_date: '', end_date: '' })

const closeDialogVisible = ref(false)
const closeTarget = ref<FiscalYearRead | null>(null)
const preCloseWarnings = ref<string[]>([])
const checksLoading = ref(false)
const closing = ref(false)

const nextDialogVisible = ref(false)
const nextTarget = ref<FiscalYearRead | null>(null)
const nextForm = ref({ name: '', start_date: '', end_date: '' })
const openingNext = ref(false)

function statusSeverity(status: FiscalYearStatus) {
  if (status === 'open') return 'success'
  if (status === 'closing') return 'warn'
  return 'secondary'
}

async function load() {
  loading.value = true
  try {
    fiscalYears.value = await listFiscalYearsApi()
    fiscalYearRows.value = fiscalYears.value.map((fiscalYear) => ({
      ...fiscalYear,
      status_label: t(`accounting.fiscalYear.statuses.${fiscalYear.status}`),
    }))
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

async function openCloseDialog(fy: FiscalYearRead) {
  closeTarget.value = fy
  preCloseWarnings.value = []
  closeDialogVisible.value = true
  checksLoading.value = true
  try {
    preCloseWarnings.value = await getFiscalYearPreCloseChecksApi(fy.id)
  } catch {
    closeDialogVisible.value = false
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    checksLoading.value = false
  }
}

async function doClose() {
  const fy = closeTarget.value
  if (!fy) return
  closing.value = true
  try {
    await closeFiscalYearApi(fy.id)
    closeDialogVisible.value = false
    toast.add({
      severity: 'success',
      summary: t('accounting.fiscalYear.closed_ok', { name: fy.name }),
      life: 3000,
    })
    await load()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    closing.value = false
  }
}

/** A closed year can be rolled over as long as no later year exists yet. */
function canOpenNext(fy: FiscalYearRead): boolean {
  if (fy.status !== 'closed') return false
  return !fiscalYears.value.some((other) => other.start_date > fy.end_date)
}

function openNextDialog(fy: FiscalYearRead) {
  nextTarget.value = fy
  nextForm.value = suggestNextFiscalYear(fy)
  nextDialogVisible.value = true
}

/** Suggest the year that starts the day after *fy* ends and spans the same length. */
function suggestNextFiscalYear(fy: FiscalYearRead): {
  name: string
  start_date: string
  end_date: string
} {
  const start = new Date(`${fy.end_date}T00:00:00`)
  start.setDate(start.getDate() + 1)
  const end = new Date(start)
  end.setFullYear(end.getFullYear() + 1)
  end.setDate(end.getDate() - 1)
  // Format from local parts: toISOString() shifts to UTC and would move the
  // fiscal year boundary by one day east of Greenwich.
  const iso = (value: Date) =>
    `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
  const startYear = start.getFullYear()
  const endYear = end.getFullYear()
  return {
    name: startYear === endYear ? String(startYear) : `${startYear}-${endYear}`,
    start_date: iso(start),
    end_date: iso(end),
  }
}

async function doOpenNext() {
  const fy = nextTarget.value
  if (!fy) return
  openingNext.value = true
  try {
    await openNextFiscalYearApi(fy.id, nextForm.value)
    nextDialogVisible.value = false
    toast.add({
      severity: 'success',
      summary: t('accounting.fiscalYear.open_next_ok', { name: nextForm.value.name }),
      life: 4000,
    })
    await load()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    openingNext.value = false
  }
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
