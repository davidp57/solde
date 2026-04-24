<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('contacts.title')"
      :subtitle="t('contacts.subtitle')"
    >
      <template #actions>
        <Button :label="t('contacts.import_emails')" icon="pi pi-envelope" severity="secondary" outlined @click="importDialogVisible = true" />
        <Button :label="t('contacts.new')" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('contacts.metrics.total')"
        :value="contacts.length"
        :caption="t('contacts.metrics.clients', { count: clientCount })"
      />
      <AppStatCard
        :label="t('contacts.metrics.suppliers')"
        :value="supplierCount"
        :caption="t('contacts.metrics.mixed', { count: mixedCount })"
        tone="success"
      />
      <AppStatCard
        :label="t('contacts.metrics.with_email')"
        :value="emailCount"
        :caption="t('contacts.metrics.with_phone', { count: phoneCount })"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('contacts.workspace_title')" :subtitle="t('contacts.workspace_subtitle')">
      <Tabs v-model:value="activeTab" class="contacts-tabs">
        <TabList>
          <Tab value="all">{{ t('contacts.tabs.all') }} ({{ contacts.length }})</Tab>
          <Tab value="client">{{ t('contacts.tabs.clients') }} ({{ clientCount + mixedCount }})</Tab>
          <Tab value="fournisseur">{{ t('contacts.tabs.suppliers') }} ({{ supplierCount + mixedCount }})</Tab>
        </TabList>
      </Tabs>

      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('contacts.filters_hint') }}</p>
          <AppListState
            :displayed-count="displayedContacts.length"
            :loading="loading"
            :search-text="search"
            :active-filters="activeFilterLabels"
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
            <label class="app-field__label">{{ t('contacts.search_placeholder') }}</label>
            <InputText
              v-model="search"
              :placeholder="t('contacts.search_placeholder')"
              @input="debouncedLoad"
            />
          </div>
        </div>
      </div>

      <AppTableSkeleton v-if="loading && !contacts.length" :rows="8" :cols="5" />
      <DataTable
        v-else
        v-model:filters="tableFilters"
        :value="contactRows"
        :loading="loading"
        class="app-data-table contacts-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        data-key="id"
        size="small"
        row-hover
        :global-filter-fields="['nom', 'prenom', 'type', 'email', 'telephone']"
        removable-sort
        @value-change="syncDisplayedContacts"
      >
        <Column
          field="nom"
          :header="t('contacts.nom')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('contacts.nom')" />
          </template>
        </Column>
        <Column
          field="prenom"
          :header="t('contacts.prenom')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('contacts.prenom')" />
          </template>
        </Column>
        <Column
          field="type_label"
          :header="t('contacts.type')"
          sortable
          filter-field="type"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag :value="t(`contacts.types.${data.type}`)" :severity="typeSeverity(data.type)" />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="typeOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              display="chip"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="email"
          :header="t('contacts.email')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('contacts.email')" />
          </template>
        </Column>
        <Column
          field="telephone"
          :header="t('contacts.telephone')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('contacts.telephone')" />
          </template>
        </Column>
        <Column :header="t('common.actions')" class="contacts-table__actions">
          <template #body="{ data }">
            <div class="app-inline-actions">
              <Button
                icon="pi pi-history"
                size="small"
                severity="info"
                text
                :title="t('contact_history.title')"
                @click="$router.push(`/contacts/${data.id}/history`)"
              />
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
        <template #empty>
          <div class="app-empty-state">{{ t('contacts.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <Dialog
      v-model:visible="importDialogVisible"
      :header="t('contacts.import_emails_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="contacts-import-form">
        <p class="app-field__hint">{{ t('contacts.import_emails_subtitle') }}</p>
        <div class="app-field">
          <Textarea
            v-model="importText"
            :placeholder="t('contacts.import_emails_placeholder')"
            rows="8"
            class="w-full"
            style="font-family: monospace; font-size: 0.875rem"
          />
        </div>
        <Message v-if="importResult" severity="success" :closable="false">
          {{ t('contacts.import_emails_result', { updated: importResult.updated, not_found: importResult.not_found, already: importResult.already_has_email }) }}
        </Message>
        <div class="app-form-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="closeImportDialog" />
          <Button :label="t('contacts.import_emails')" icon="pi pi-check" :loading="importLoading" @click="runImport" />
        </div>
      </div>
    </Dialog>

    <Dialog
      v-model:visible="dialogVisible"
      :header="editingContact ? t('contacts.edit') : t('contacts.new')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <ContactForm ref="contactFormRef" :contact="editingContact" @saved="onSaved" @cancel="dialogVisible = false" />
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
import InputText from 'primevue/inputtext'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppFilterMultiSelect from '@/components/ui/AppFilterMultiSelect.vue'
import AppListState from '@/components/ui/AppListState.vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import AppTableSkeleton from '@/components/ui/AppTableSkeleton.vue'
import { deleteContactApi, importContactEmailsApi, listContactsApi, type Contact } from '@/api/contacts'
import type { ContactEmailImportRow } from '@/api/contacts'
import ContactForm from '@/components/ContactForm.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import {
  collectActiveFilterLabels,
} from '../composables/activeFilterLabels'
import { inFilter, textFilter, useDataTableFilters } from '../composables/useDataTableFilters'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const contacts = ref<Contact[]>([])
const loading = ref(false)
const search = ref('')
const activeTab = ref<'all' | 'client' | 'fournisseur'>('all')
const dialogVisible = ref(false)
const contactFormRef = ref<InstanceType<typeof ContactForm> | null>(null)
const editingContact = ref<Contact | null>(null)
const importDialogVisible = ref(false)
const importText = ref('')
const importLoading = ref(false)
const importResult = ref<{ updated: number; not_found: number; already_has_email: number } | null>(null)

const tabContacts = computed(() => {
  if (activeTab.value === 'client') return contacts.value.filter((c) => c.type === 'client' || c.type === 'les_deux')
  if (activeTab.value === 'fournisseur') return contacts.value.filter((c) => c.type === 'fournisseur' || c.type === 'les_deux')
  return contacts.value
})
const contactRows = computed(() =>
  tabContacts.value.map((contact) => ({
    ...contact,
    type_label: t(`contacts.types.${contact.type}`),
  })),
)
const {
  filters: tableFilters,
  displayedRows: displayedContacts,
  syncDisplayedRows: syncDisplayedContacts,
  resetFilters,
  hasActiveFilters,
} = useDataTableFilters(contactRows, {
  global: textFilter(''),
  nom: textFilter(),
  prenom: textFilter(),
  type: inFilter(),
  email: textFilter(),
  telephone: textFilter(),
})
const clientCount = computed(
  () => contacts.value.filter((contact) => contact.type === 'client').length,
)
const supplierCount = computed(
  () => contacts.value.filter((contact) => contact.type === 'fournisseur').length,
)
const mixedCount = computed(
  () => contacts.value.filter((contact) => contact.type === 'les_deux').length,
)
const emailCount = computed(() => contacts.value.filter((contact) => Boolean(contact.email)).length)
const phoneCount = computed(
  () => contacts.value.filter((contact) => Boolean(contact.telephone)).length,
)
const activeFilterLabels = computed(() => collectActiveFilterLabels())

const typeOptions = [
  { label: t('contacts.types.client'), value: 'client' as const },
  { label: t('contacts.types.fournisseur'), value: 'fournisseur' as const },
  { label: t('contacts.types.les_deux'), value: 'les_deux' as const },
]

function typeSeverity(type: ContactType): 'info' | 'success' | 'warn' {
  if (type === 'client') return 'info'
  if (type === 'fournisseur') return 'success'
  return 'warn'
}

let _debounceTimer: ReturnType<typeof setTimeout> | undefined

function debouncedLoad(): void {
  clearTimeout(_debounceTimer)
  _debounceTimer = setTimeout(loadContacts, 300)
}

const hasAnyFilters = computed(
  () => hasActiveFilters.value || Boolean(search.value) || activeTab.value !== 'all',
)

function resetAllFilters(): void {
  resetFilters()
  search.value = ''
  activeTab.value = 'all'
  void loadContacts()
}

async function loadContacts(): Promise<void> {
  loading.value = true
  try {
    contacts.value = await listContactsApi({
      search: search.value || undefined,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loading.value = false
  }
}

function closeImportDialog(): void {
  importDialogVisible.value = false
  importText.value = ''
  importResult.value = null
}

function parseImportText(text: string): ContactEmailImportRow[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .flatMap((line) => {
      const commaIdx = line.lastIndexOf(',')
      if (commaIdx < 1) return []
      const nom = line.slice(0, commaIdx).trim()
      const email = line.slice(commaIdx + 1).trim()
      if (!nom || !email.includes('@')) return []
      return [{ nom, email }]
    })
}

async function runImport(): Promise<void> {
  const rows = parseImportText(importText.value)
  if (rows.length === 0) {
    toast.add({ severity: 'warn', summary: t('contacts.import_emails_empty'), life: 3000 })
    return
  }
  importLoading.value = true
  try {
    importResult.value = await importContactEmailsApi(rows)
    void loadContacts()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    importLoading.value = false
  }
}

function openCreateDialog(): void {
  editingContact.value = null
  dialogVisible.value = true
}

function openEditDialog(contact: Contact): void {
  editingContact.value = contact
  dialogVisible.value = true
}

function onSaved(): void {
  dialogVisible.value = false
  void loadContacts()
}

useKeyboardShortcuts({
  onNew: () => {
    if (!dialogVisible.value) openCreateDialog()
  },
  onSave: () => {
    if (dialogVisible.value) void contactFormRef.value?.submit()
  },
  onClose: () => {
    if (dialogVisible.value) dialogVisible.value = false
  },
})

function confirmDelete(contact: Contact): void {
  confirm.require({
    message: t('contacts.confirm_delete', { nom: contact.nom }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('common.delete') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: () => void doDelete(contact),
  })
}

async function doDelete(contact: Contact): Promise<void> {
  try {
    await deleteContactApi(contact.id)
    toast.add({ severity: 'success', summary: t('contacts.deleted'), life: 3000 })
    void loadContacts()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  }
}

onMounted(loadContacts)
</script>

<style scoped>
.contacts-table__actions {
  width: 8rem;
}

.contacts-tabs {
  margin-bottom: var(--app-space-4);
}

.contacts-import-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}
</style>
