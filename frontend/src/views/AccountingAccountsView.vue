<template>
  <div class="accounting-accounts-view p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">{{ t('accounting.accounts.title') }}</h2>
      <div class="flex gap-2">
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
    </div>

    <!-- Type filter tabs -->
    <div class="flex gap-2 mb-4 flex-wrap">
      <Button
        v-for="opt in typeOptions"
        :key="opt.value ?? 'all'"
        :label="opt.label"
        :severity="typeFilter === opt.value ? 'primary' : 'secondary'"
        size="small"
        @click="typeFilter = opt.value; void loadAccounts()"
      />
      <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" class="w-64" />
    </div>

    <DataTable :value="filtered" :loading="loading" striped-rows data-key="id">
      <Column field="number" :header="t('accounting.accounts.number')" sortable style="width:8rem" />
      <Column field="label" :header="t('accounting.accounts.label')" sortable />
      <Column field="type" :header="t('accounting.accounts.type')" style="width:7rem">
        <template #body="{ data }">
          <Tag :value="t(`accounting.account_types.${data.type}`)" :severity="typeSeverity(data.type)" />
        </template>
      </Column>
      <Column field="is_default" :header="t('accounting.accounts.default')" style="width:6rem">
        <template #body="{ data }">
          <i v-if="data.is_default" class="pi pi-check text-green-500" />
        </template>
      </Column>
      <Column :header="t('common.actions')" style="width:6rem">
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
    </DataTable>

    <!-- Create / Edit Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingAccount ? t('accounting.accounts.edit') : t('accounting.accounts.new')"
      modal
      :style="{ width: '440px' }"
    >
      <AccountForm
        :account="editingAccount"
        @saved="onSaved"
        @cancel="dialogVisible = false"
      />
    </Dialog>

    <Toast />
  </div>
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
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  listAccountsApi,
  seedAccountsApi,
  type AccountingAccount,
  type AccountType,
} from '@/api/accounting'
import AccountForm from '@/components/AccountForm.vue'
import { useTableFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const toast = useToast()

const accounts = ref<AccountingAccount[]>([])
const { filterText, filtered } = useTableFilter(accounts)
const loading = ref(false)
const seeding = ref(false)
const typeFilter = ref<AccountType | undefined>(undefined)
const dialogVisible = ref(false)
const editingAccount = ref<AccountingAccount | null>(null)

const typeOptions: Array<{ label: string; value: AccountType | undefined }> = [
  { label: t('common.all'), value: undefined },
  { label: t('accounting.account_types.actif'), value: 'actif' },
  { label: t('accounting.account_types.passif'), value: 'passif' },
  { label: t('accounting.account_types.charge'), value: 'charge' },
  { label: t('accounting.account_types.produit'), value: 'produit' },
]

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
