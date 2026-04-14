<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('ui.page.accounting_eyebrow')"
      :title="t('accounting.accounts.title')"
    >
      <template #actions>
        <div class="app-page-header__actions">
          <Button
            :label="t('accounting.accounts.seed')"
            icon="pi pi-database"
            severity="secondary"
            :loading="seeding"
            @click="runSeed"
          />
          <Button
            :label="t('accounting.accounts.new')"
            icon="pi pi-plus"
            @click="openCreateDialog"
          />
        </div>
      </template>
    </AppPageHeader>

    <AppPanel :title="t('accounting.accounts.title')" dense>
      <div class="account-type-toolbar">
        <Button
          v-for="opt in typeOptions"
          :key="opt.value ?? 'all'"
          :label="opt.label"
          :severity="typeFilter === opt.value ? 'primary' : 'secondary'"
          size="small"
          @click="applyTypeFilter(opt.value)"
        />
      </div>
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <AppListState
            :displayed-count="displayedAccounts.length"
            :total-count="accounts.length"
            :loading="loading"
            :search-text="filterText"
            :active-filters="activeFilterLabels"
          />
        </div>
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
          </div>
        </div>
      </div>
      <DataTable
        v-model:filters="tableFilters"
        :value="accountRows"
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
        :global-filter-fields="['number', 'label', 'type', 'is_default']"
        removable-sort
        @value-change="syncDisplayedAccounts"
      >
        <Column
          field="number"
          :header="t('accounting.accounts.number')"
          sortable
          style="width: 8rem"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('accounting.accounts.number')" />
          </template>
        </Column>
        <Column
          field="label"
          :header="t('accounting.accounts.label')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('accounting.accounts.label')" />
          </template>
        </Column>
        <Column
          field="type_label"
          :header="t('accounting.accounts.type')"
          style="width: 7rem"
          sortable
          filter-field="type"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag
              :value="t(`accounting.account_types.${data.type}`)"
              :severity="typeSeverity(data.type)"
            />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="tableTypeOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              display="chip"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="is_default_label"
          :header="t('accounting.accounts.default')"
          style="width: 6rem"
          sortable
          filter-field="is_default"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <i v-if="data.is_default" class="pi pi-check text-green-500" />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="yesNoOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              display="chip"
              show-clear
            />
          </template>
        </Column>
        <Column :header="t('common.actions')" style="width: 6rem">
          <template #body="{ data }">
            <Button
              icon="pi pi-pencil"
              size="small"
              severity="secondary"
              text
              @click="openEditDialog(data)"
            />
          </template>
        </Column>
        <template #empty
          ><div class="app-empty-state">{{ t('accounting.balance.empty') }}</div></template
        >
      </DataTable>
    </AppPanel>

    <!-- Create / Edit Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingAccount ? t('accounting.accounts.edit') : t('accounting.accounts.new')"
      modal
      class="app-dialog app-dialog--medium account-dialog"
    >
      <AccountForm :account="editingAccount" @saved="onSaved" @cancel="dialogVisible = false" />
    </Dialog>

    <Toast />
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppFilterMultiSelect from '@/components/ui/AppFilterMultiSelect.vue'
import AppListState from '@/components/ui/AppListState.vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import {
  listAccountsApi,
  seedAccountsApi,
  type AccountingAccount,
  type AccountType,
} from '@/api/accounting'
import AccountForm from '@/components/AccountForm.vue'
import { inFilter, textFilter, useDataTableFilters } from '../composables/useDataTableFilters'

const { t } = useI18n()
const toast = useToast()

const accounts = ref<AccountingAccount[]>([])
const loading = ref(false)
const seeding = ref(false)
const typeFilter = ref<AccountType | undefined>(undefined)
const dialogVisible = ref(false)
const editingAccount = ref<AccountingAccount | null>(null)
const accountRows = ref<
  Array<AccountingAccount & { type_label: string; is_default_label: string }>
>([])

const typeOptions: Array<{ label: string; value: AccountType | undefined }> = [
  { label: t('common.all'), value: undefined },
  { label: t('accounting.account_types.actif'), value: 'actif' },
  { label: t('accounting.account_types.passif'), value: 'passif' },
  { label: t('accounting.account_types.charge'), value: 'charge' },
  { label: t('accounting.account_types.produit'), value: 'produit' },
]

const activeFilterLabels = computed(() => {
  if (!typeFilter.value) return []

  const selectedOption = typeOptions.find((option) => option.value === typeFilter.value)
  return selectedOption ? [selectedOption.label] : [String(typeFilter.value)]
})
const tableTypeOptions = typeOptions.filter(
  (option): option is { label: string; value: AccountType } => option.value !== undefined,
)
const yesNoOptions = [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
]
const {
  filters: tableFilters,
  globalFilter: filterText,
  displayedRows: displayedAccounts,
  syncDisplayedRows: syncDisplayedAccounts,
} = useDataTableFilters(accountRows, {
  global: textFilter(''),
  number: textFilter(),
  label: textFilter(),
  type: inFilter(),
  is_default: inFilter(),
})

function applyTypeFilter(nextType: AccountType | undefined): void {
  typeFilter.value = nextType
  void loadAccounts()
}

function typeSeverity(type: AccountType): 'info' | 'success' | 'warn' | 'danger' {
  const map: Record<AccountType, 'info' | 'success' | 'warn' | 'danger'> = {
    actif: 'info',
    passif: 'warn',
    charge: 'danger',
    produit: 'success',
  }
  return map[type]
}

async function loadAccounts(): Promise<void> {
  loading.value = true
  try {
    accounts.value = await listAccountsApi(typeFilter.value)
    accountRows.value = accounts.value.map((account) => ({
      ...account,
      type_label: t(`accounting.account_types.${account.type}`),
      is_default_label: account.is_default ? t('common.yes') : t('common.no'),
    }))
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loading.value = false
  }
}

async function runSeed(): Promise<void> {
  seeding.value = true
  try {
    const result = await seedAccountsApi()
    if (result.inserted > 0) {
      toast.add({
        severity: 'success',
        summary: t('accounting.accounts.seed_ok', { n: result.inserted }),
        life: 4000,
      })
      void loadAccounts()
    } else {
      toast.add({
        severity: 'info',
        summary: t('accounting.accounts.seed_already_done'),
        life: 3000,
      })
    }
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    seeding.value = false
  }
}

function openCreateDialog(): void {
  editingAccount.value = null
  dialogVisible.value = true
}

function openEditDialog(account: AccountingAccount): void {
  editingAccount.value = account
  dialogVisible.value = true
}

function onSaved(): void {
  dialogVisible.value = false
  void loadAccounts()
}

onMounted(loadAccounts)
</script>

<style scoped>
.account-type-toolbar {
  display: flex;
  gap: var(--app-space-2);
  flex-wrap: wrap;
  margin-bottom: var(--app-space-4);
}

.account-dialog :deep(.p-dialog-header) {
  padding-bottom: var(--app-space-3);
}

.account-dialog :deep(.p-dialog-content) {
  padding-top: 0;
}
</style>
