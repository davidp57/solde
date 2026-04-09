<template>
  <div class="contacts-view p-4">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-2xl font-semibold">{{ t('contacts.title') }}</h2>
      <Button
        :label="t('contacts.new')"
        icon="pi pi-plus"
        @click="openCreateDialog"
      />
    </div>

    <!-- Filters -->
    <div class="flex gap-3 mb-4 flex-wrap">
      <InputText
        v-model="search"
        :placeholder="t('contacts.search_placeholder')"
        class="w-64"
        @input="debouncedLoad"
      />
      <Select
        v-model="typeFilter"
        :options="typeOptions"
        option-label="label"
        option-value="value"
        :placeholder="t('contacts.filter_type')"
        show-clear
        class="w-48"
        @change="loadContacts"
      />
    </div>

    <!-- Table -->
    <DataTable
      :value="contacts"
      :loading="loading"
      striped-rows
      paginator
      :rows="20"
      :rows-per-page-options="[10, 20, 50]"
      data-key="id"
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
      <Column :header="t('common.actions')" style="width: 10rem">
        <template #body="{ data }">
          <div class="flex gap-1">
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
    </DataTable>

    <!-- Create / Edit Dialog -->
    <Dialog
      v-model:visible="dialogVisible"
      :header="editingContact ? t('contacts.edit') : t('contacts.new')"
      modal
      :style="{ width: '480px' }"
    >
      <ContactForm
        :contact="editingContact"
        @saved="onSaved"
        @cancel="dialogVisible = false"
      />
    </Dialog>

    <!-- Confirm delete -->
    <ConfirmDialog />
  </div>
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
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
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
    acceptSeverity: 'danger',
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
