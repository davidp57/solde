<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('employees.title')"
      :subtitle="t('employees.subtitle')"
    >
      <template #actions>
        <Button :label="t('employees.new')" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard :label="t('employees.metrics.total')" :value="activeCount" />
    </section>

    <AppPanel :title="t('employees.workspace_title')" :subtitle="t('employees.workspace_subtitle')">
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <AppListState
            :displayed-count="displayedEmployees.length"
            :total-count="employees.length"
            :loading="loading"
            :search-text="search"
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
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('employees.search_placeholder') }}</label>
            <InputText
              v-model="search"
              :placeholder="t('employees.search_placeholder')"
              @input="debouncedLoad"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('employees.show_inactive') }}</label>
            <ToggleSwitch v-model="showInactive" @change="loadEmployees" />
          </div>
        </div>
      </div>

      <AppTableSkeleton v-if="loading && !employees.length" :rows="6" :cols="4" />
      <DataTable
        v-else
        v-model:filters="tableFilters"
        :value="employeeRows"
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
        :global-filter-fields="['nom', 'prenom', 'email', 'telephone']"
        removable-sort
        @value-change="syncDisplayedEmployees"
      >
        <Column
          field="nom"
          :header="t('employees.nom')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('employees.nom')" />
          </template>
        </Column>
        <Column
          field="prenom"
          :header="t('employees.prenom')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('employees.prenom')" />
          </template>
        </Column>
        <Column
          field="email"
          :header="t('employees.email')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('employees.email')" />
          </template>
        </Column>
        <Column
          field="telephone"
          :header="t('employees.telephone')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('employees.telephone')" />
          </template>
        </Column>
        <Column field="is_active" :header="t('employees.is_active')" sortable>
          <template #body="{ data }">
            <Tag
              :value="data.is_active ? t('common.active') : t('common.inactive')"
              :severity="data.is_active ? 'success' : 'secondary'"
            />
          </template>
        </Column>
        <Column :header="t('common.actions')" class="contacts-table__actions">
          <template #body="{ data }">
            <div class="app-inline-actions">
              <Button
                icon="pi pi-pencil"
                size="small"
                severity="secondary"
                text
                @click="openEditDialog(data)"
              />
              <Button
                v-if="data.is_active"
                icon="pi pi-ban"
                size="small"
                severity="warn"
                text
                :title="t('employees.confirm_deactivate', { nom: data.nom })"
                @click="confirmToggleActive(data)"
              />
              <Button
                v-else
                icon="pi pi-check-circle"
                size="small"
                severity="success"
                text
                :title="t('employees.confirm_reactivate', { nom: data.nom })"
                @click="confirmToggleActive(data)"
              />
            </div>
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('employees.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <!-- Create / Edit dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editing ? t('employees.edit') : t('employees.new')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <form class="app-dialog-form" @submit.prevent="submit">
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('employees.identity_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('employees.identity_subtitle') }}</p>
          </div>
          <div class="app-form-grid">
            <div class="app-field">
              <label for="ef-nom" class="app-field__label">{{ t('employees.nom') }} *</label>
              <InputText
                id="ef-nom"
                v-model="form.nom"
                :placeholder="t('employees.nom')"
                required
                class="w-full"
              />
            </div>
            <div class="app-field">
              <label for="ef-prenom" class="app-field__label">{{ t('employees.prenom') }}</label>
              <InputText
                id="ef-prenom"
                v-model="form.prenom"
                :placeholder="t('employees.prenom')"
                class="w-full"
              />
            </div>
          </div>
        </section>

        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('employees.contact_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('employees.contact_subtitle') }}</p>
          </div>
          <div class="contact-form">
            <div class="app-field">
              <label for="ef-email" class="app-field__label">{{ t('employees.email') }}</label>
              <InputText
                id="ef-email"
                v-model="form.email"
                type="email"
                :placeholder="t('employees.email')"
                class="w-full"
              />
            </div>
            <div class="app-field">
              <label for="ef-tel" class="app-field__label">{{ t('employees.telephone') }}</label>
              <InputText
                id="ef-tel"
                v-model="form.telephone"
                :placeholder="t('employees.telephone')"
                class="w-full"
              />
            </div>
            <div class="app-field">
              <label for="ef-adresse" class="app-field__label">{{ t('employees.adresse') }}</label>
              <Textarea
                id="ef-adresse"
                v-model="form.adresse"
                :placeholder="t('employees.adresse')"
                rows="2"
                class="w-full"
              />
            </div>
            <div class="app-field">
              <label for="ef-notes" class="app-field__label">{{ t('employees.notes') }}</label>
              <Textarea
                id="ef-notes"
                v-model="form.notes"
                :placeholder="t('employees.notes')"
                rows="2"
                class="w-full"
              />
              <small class="app-dialog-note">{{ t('employees.notes_help') }}</small>
            </div>
          </div>
        </section>

        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('employees.contract_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('employees.contract_subtitle') }}</p>
          </div>
          <div class="app-form-grid">
            <div class="app-field">
              <label for="ef-contract-type" class="app-field__label">{{ t('employees.contract_type') }}</label>
              <Select
                id="ef-contract-type"
                v-model="form.contract_type"
                :options="contractTypeOptions"
                option-label="label"
                option-value="value"
                :placeholder="t('employees.contract_type_placeholder')"
                show-clear
                class="w-full"
              />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('employees.is_contractor') }}</label>
              <ToggleSwitch v-model="form.is_contractor" />
              <small class="app-dialog-note">{{ t('employees.is_contractor_help') }}</small>
            </div>
            <template v-if="form.contract_type === 'cdi'">
              <div class="app-field">
                <label for="ef-base-gross" class="app-field__label">{{ t('employees.base_gross') }}</label>
                <InputNumber
                  id="ef-base-gross"
                  v-model="form.base_gross"
                  :min-fraction-digits="2"
                  suffix=" €"
                  class="w-full"
                />
                <small class="app-dialog-note">{{ t('employees.base_gross_help') }}</small>
              </div>
              <div class="app-field">
                <label for="ef-base-hours" class="app-field__label">{{ t('employees.base_hours') }}</label>
                <InputNumber
                  id="ef-base-hours"
                  v-model="form.base_hours"
                  :min-fraction-digits="2"
                  class="w-full"
                />
                <small class="app-dialog-note">{{ t('employees.base_hours_help') }}</small>
              </div>
            </template>
            <template v-if="form.contract_type === 'cdd'">
              <div class="app-field">
                <label for="ef-hourly-rate" class="app-field__label">{{ t('employees.hourly_rate') }}</label>
                <InputNumber
                  id="ef-hourly-rate"
                  v-model="form.hourly_rate"
                  :min-fraction-digits="2"
                  suffix=" €/h"
                  class="w-full"
                />
                <small class="app-dialog-note">{{ t('employees.hourly_rate_help') }}</small>
              </div>
            </template>
          </div>
        </section>

        <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

        <div class="app-form-actions">
          <Button
            type="button"
            :label="t('common.cancel')"
            severity="secondary"
            :disabled="saving"
            @click="dialogVisible = false"
          />
          <Button type="submit" :label="t('common.save')" :loading="saving" icon="pi pi-check" />
        </div>
      </form>
    </Dialog>

    <ConfirmDialog />
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { createContactApi, listContactsApi, updateContactApi, type Contact } from '@/api/contacts'
import AppListState from '@/components/ui/AppListState.vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import AppTableSkeleton from '@/components/ui/AppTableSkeleton.vue'
import { textFilter, useDataTableFilters } from '../composables/useDataTableFilters'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const contractTypeOptions = computed(() => [
  { label: t('employees.contract_type_cdi'), value: 'cdi' },
  { label: t('employees.contract_type_cdd'), value: 'cdd' },
])

const employees = ref<Contact[]>([])
const loading = ref(false)
const search = ref('')
const showInactive = ref(false)

const activeCount = computed(() => employees.value.filter((e) => e.is_active).length)

const employeeRows = computed(() => employees.value)
const {
  filters: tableFilters,
  displayedRows: displayedEmployees,
  syncDisplayedRows: syncDisplayedEmployees,
  resetFilters,
  hasActiveFilters,
} = useDataTableFilters(employeeRows, {
  global: textFilter(''),
  nom: textFilter(),
  prenom: textFilter(),
  email: textFilter(),
  telephone: textFilter(),
})

const hasAnyFilters = computed(() => hasActiveFilters.value || Boolean(search.value))

function resetAllFilters(): void {
  resetFilters()
  search.value = ''
  void loadEmployees()
}

let _debounceTimer: ReturnType<typeof setTimeout> | undefined

function debouncedLoad(): void {
  clearTimeout(_debounceTimer)
  _debounceTimer = setTimeout(loadEmployees, 300)
}

async function loadEmployees(): Promise<void> {
  loading.value = true
  try {
    employees.value = await listContactsApi({
      type: 'employe',
      search: search.value || undefined,
      active_only: !showInactive.value,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loading.value = false
  }
}

// --- Dialog ---

const dialogVisible = ref(false)
const editing = ref<Contact | null>(null)
const saving = ref(false)
const errorMessage = ref('')

interface EmployeeForm {
  nom: string
  prenom: string
  email: string
  telephone: string
  adresse: string
  notes: string
  contract_type: 'cdi' | 'cdd' | null
  base_gross: number | null
  base_hours: number | null
  hourly_rate: number | null
  is_contractor: boolean
}

function blankForm(): EmployeeForm {
  return {
    nom: '',
    prenom: '',
    email: '',
    telephone: '',
    adresse: '',
    notes: '',
    contract_type: null,
    base_gross: null,
    base_hours: null,
    hourly_rate: null,
    is_contractor: false,
  }
}

function fromContact(c: Contact): EmployeeForm {
  return {
    nom: c.nom,
    prenom: c.prenom ?? '',
    email: c.email ?? '',
    telephone: c.telephone ?? '',
    adresse: c.adresse ?? '',
    notes: c.notes ?? '',
    contract_type: c.contract_type ?? null,
    base_gross: c.base_gross ?? null,
    base_hours: c.base_hours ?? null,
    hourly_rate: c.hourly_rate ?? null,
    is_contractor: c.is_contractor,
  }
}

const form = ref<EmployeeForm>(blankForm())

function openCreateDialog(): void {
  editing.value = null
  form.value = blankForm()
  errorMessage.value = ''
  dialogVisible.value = true
}

function openEditDialog(employee: Contact): void {
  editing.value = employee
  form.value = fromContact(employee)
  errorMessage.value = ''
  dialogVisible.value = true
}

async function submit(): Promise<void> {
  saving.value = true
  errorMessage.value = ''
  try {
    const payload = {
      nom: form.value.nom,
      prenom: form.value.prenom || null,
      email: form.value.email || null,
      telephone: form.value.telephone || null,
      adresse: form.value.adresse || null,
      notes: form.value.notes || null,
      contract_type: form.value.contract_type,
      base_gross: form.value.base_gross,
      base_hours: form.value.base_hours,
      hourly_rate: form.value.hourly_rate,
      is_contractor: form.value.is_contractor,
    }
    if (editing.value) {
      await updateContactApi(editing.value.id, payload)
    } else {
      await createContactApi({ ...payload, type: 'employe' })
    }
    dialogVisible.value = false
    toast.add({ severity: 'success', summary: t('employees.saved'), life: 2000 })
    await loadEmployees()
  } catch {
    errorMessage.value = t('common.error.unknown')
  } finally {
    saving.value = false
  }
}

function confirmToggleActive(employee: Contact): void {
  const isActive = employee.is_active
  confirm.require({
    message: t(
      isActive
        ? 'employees.confirm_deactivate'
        : 'employees.confirm_reactivate',
      { nom: [employee.prenom, employee.nom].filter(Boolean).join(' ') },
    ),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await updateContactApi(employee.id, { is_active: !isActive })
        toast.add({
          severity: 'success',
          summary: t(isActive ? 'employees.deactivated' : 'employees.reactivated'),
          life: 2000,
        })
        await loadEmployees()
      } catch {
        toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
      }
    },
  })
}

onMounted(() => {
  void loadEmployees()
})
</script>
