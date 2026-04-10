<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('contacts.title')"
      :subtitle="t('contacts.subtitle')"
    >
      <template #actions>
        <Button :label="t('contacts.new')" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard :label="t('contacts.metrics.total')" :value="contacts.length" :caption="t('contacts.metrics.clients', { count: clientCount })" />
      <AppStatCard :label="t('contacts.metrics.suppliers')" :value="supplierCount" :caption="t('contacts.metrics.mixed', { count: mixedCount })" tone="success" />
      <AppStatCard :label="t('contacts.metrics.with_email')" :value="emailCount" :caption="t('contacts.metrics.with_phone', { count: phoneCount })" tone="warn" />
    </section>

    <AppPanel :title="t('contacts.workspace_title')" :subtitle="t('contacts.workspace_subtitle')">
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <p class="app-toolbar__hint">{{ t('contacts.filters_hint') }}</p>
          <span class="app-chip">{{ t('contacts.results_label', { count: contacts.length }) }}</span>
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
          <div class="app-field">
            <label class="app-field__label">{{ t('contacts.filter_type') }}</label>
            <Select
              v-model="typeFilter"
              :options="typeOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
              @change="loadContacts"
            />
          </div>
        </div>
      </div>

      <DataTable
        :value="contacts"
        :loading="loading"
        class="app-data-table contacts-table"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[10, 20, 50]"
        data-key="id"
        size="small"
        row-hover
      >
      <Column field="nom" :header="t('contacts.nom')" sortable />
      <Column field="prenom" :header="t('contacts.prenom')" sortable />
      <Column field="type" :header="t('contacts.type')">
        <template #body="{ data }">
          <Tag :value="t(`contacts.types.${data.type}`)" :severity="typeSeverity(data.type)" />
        </template>
      </Column>
      <Column field="email" :header="t('contacts.email')" />
      <Column field="telephone" :header="t('contacts.telephone')" />
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
      v-model:visible="dialogVisible"
      :header="editingContact ? t('contacts.edit') : t('contacts.new')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <ContactForm
        :contact="editingContact"
        @saved="onSaved"
        @cancel="dialogVisible = false"
      />
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
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import {
  deleteContactApi,
  listContactsApi,
  type Contact,
} from '@/api/contacts'
import type { ContactType } from '@/api/types'
import ContactForm from '@/components/ContactForm.vue'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const contacts = ref<Contact[]>([])
const loading = ref(false)
const search = ref('')
const typeFilter = ref<ContactType | undefined>(undefined)
const dialogVisible = ref(false)
const editingContact = ref<Contact | null>(null)
const clientCount = computed(() => contacts.value.filter((contact) => contact.type === 'client').length)
const supplierCount = computed(() => contacts.value.filter((contact) => contact.type === 'fournisseur').length)
const mixedCount = computed(() => contacts.value.filter((contact) => contact.type === 'les_deux').length)
const emailCount = computed(() => contacts.value.filter((contact) => Boolean(contact.email)).length)
const phoneCount = computed(() => contacts.value.filter((contact) => Boolean(contact.telephone)).length)

const typeOptions = [
  { label: t('contacts.types.client'), value: 'client' as ContactType },
  { label: t('contacts.types.fournisseur'), value: 'fournisseur' as ContactType },
  { label: t('contacts.types.les_deux'), value: 'les_deux' as ContactType },
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

async function loadContacts(): Promise<void> {
  loading.value = true
  try {
    contacts.value = await listContactsApi({
      type: typeFilter.value,
      search: search.value || undefined,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loading.value = false
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
</style>
