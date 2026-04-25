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
                :aria-label="t('contact_history.title')"
                @click="$router.push(`/contacts/${data.id}/history`)"
              />
              <Button
                icon="pi pi-pencil"
                size="small"
                severity="secondary"
                text
                :title="t('contacts.edit')"
                :aria-label="t('contacts.edit')"
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
      @hide="closeImportDialog"
    >
      <div class="contacts-import-form">
        <p v-if="!importText.trim()" class="contacts-import-preview__summary">{{ t('contacts.import_emails_subtitle') }}</p>
        <div v-if="importText.trim()" class="contacts-import-preview">
          <p class="contacts-import-preview__summary" :class="{ 'contacts-import-preview__summary--none': !importResult && parsedPreview.rows.length === 0 }">
            <template v-if="importResult">{{ t('contacts.import_emails_result', { updated: importResult.updated, not_found: importResult.not_found, already: importResult.already_has_email }) }}</template>
            <template v-else-if="parsedPreview.rows.length > 0">{{ t('contacts.import_emails_preview_valid', { count: parsedPreview.rows.length }) }}</template>
            <template v-else>{{ t('contacts.import_emails_preview_none') }}</template>
          </p>
          <div v-if="parsedPreview.ignoredLines.length > 0" class="contacts-import-issues">
            <p class="contacts-import-issues__label">{{ t('contacts.import_emails_lines_ignored_label') }}</p>
            <ul class="contacts-import-issues__list">
              <li v-for="line in parsedPreview.ignoredLines" :key="line.lineNumber" class="contacts-import-issues__item contacts-import-issues__item--warn">
                <span class="contacts-import-issues__num">{{ line.lineNumber }}</span>
                <code class="contacts-import-issues__text">{{ line.raw.length > 70 ? line.raw.slice(0, 67) + '\u2026' : line.raw }}</code>
              </li>
            </ul>
          </div>
          <div v-if="serverErrorLines.length > 0" class="contacts-import-issues">
            <p class="contacts-import-issues__label">{{ t('contacts.import_emails_lines_error_label') }}</p>
            <ul class="contacts-import-issues__list">
              <li v-for="line in serverErrorLines" :key="line.lineNumber" class="contacts-import-issues__item contacts-import-issues__item--error">
                <span class="contacts-import-issues__num">{{ line.lineNumber }}</span>
                <code class="contacts-import-issues__text">{{ line.raw.length > 70 ? line.raw.slice(0, 67) + '\u2026' : line.raw }}</code>
              </li>
            </ul>
          </div>
          <template v-if="importResult">
            <div v-if="updatedResultLines.length > 0" class="contacts-import-issues">
              <p class="contacts-import-issues__label">{{ t('contacts.import_emails_lines_updated_label') }}</p>
              <ul class="contacts-import-issues__list">
                <li v-for="line in updatedResultLines" :key="line.lineNumber" class="contacts-import-issues__item contacts-import-issues__item--success">
                  <span class="contacts-import-issues__num">{{ line.lineNumber }}</span>
                  <code class="contacts-import-issues__text">{{ line.raw.length > 70 ? line.raw.slice(0, 67) + '\u2026' : line.raw }}</code>
                </li>
              </ul>
            </div>
            <div v-if="notFoundResultLines.length > 0" class="contacts-import-issues">
              <p class="contacts-import-issues__label">{{ t('contacts.import_emails_lines_not_found_label') }}</p>
              <ul class="contacts-import-issues__list">
                <li v-for="line in notFoundResultLines" :key="line.lineNumber" class="contacts-import-issues__item contacts-import-issues__item--not-found">
                  <span class="contacts-import-issues__num">{{ line.lineNumber }}</span>
                  <code class="contacts-import-issues__text">{{ line.raw.length > 70 ? line.raw.slice(0, 67) + '\u2026' : line.raw }}</code>
                </li>
              </ul>
            </div>
            <div v-if="alreadyHasEmailResultLines.length > 0" class="contacts-import-issues">
              <p class="contacts-import-issues__label">{{ t('contacts.import_emails_lines_already_label') }}</p>
              <ul class="contacts-import-issues__list">
                <li v-for="line in alreadyHasEmailResultLines" :key="line.lineNumber" class="contacts-import-issues__item contacts-import-issues__item--already">
                  <span class="contacts-import-issues__num">{{ line.lineNumber }}</span>
                  <code class="contacts-import-issues__text">{{ line.raw.length > 70 ? line.raw.slice(0, 67) + '\u2026' : line.raw }}</code>
                </li>
              </ul>
            </div>
          </template>
        </div>
        <div class="contacts-import-editor">
          <div ref="backdropRef" class="contacts-import-editor__backdrop" aria-hidden="true">
            <div
              v-for="(_, i) in importLinesList"
              :key="i"
              class="contacts-import-editor__line"
              :class="{
                'contacts-import-editor__line--warn': warnLineSet.has(i + 1),
                'contacts-import-editor__line--error': errorLineSet.has(i + 1),
                'contacts-import-editor__line--result-updated': updatedLineSet.has(i + 1),
                'contacts-import-editor__line--result-not-found': notFoundLineSet.has(i + 1),
                'contacts-import-editor__line--result-already': alreadyLineSet.has(i + 1),
              }"
            />
          </div>
          <textarea
            ref="textareaRef"
            v-model="importText"
            :placeholder="t('contacts.import_emails_placeholder')"
            rows="8"
            wrap="off"
            class="contacts-import-editor__textarea"
            @scroll="syncBackdropScroll"
          />
        </div>
        <Message v-if="importError" severity="error" :closable="false">
          {{ importError }}
        </Message>
        <div class="app-form-actions">
          <Button :label="t('common.cancel')" severity="secondary" text :disabled="importLoading" @click="closeImportDialog" />
          <Button
            :label="t('contacts.import_emails')"
            icon="pi pi-check"
            :loading="importLoading"
            :disabled="!importText.trim() || parsedPreview.rows.length === 0"
            @click="runImport"
          />
        </div>
      </div>
    </Dialog>

    <Dialog
      :visible="dialogVisible"
      @update:visible="onCloseDialog"
      @show="focusFormInput"
      :header="editingContact ? t('contacts.edit') : t('contacts.new')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div ref="formWrapperEl">
        <ContactForm ref="contactFormRef" :contact="editingContact" @saved="onSaved" @cancel="onCloseDialog(false)" />
      </div>
    </Dialog>

    <ConfirmDialog />
  </AppPage>
</template>

<script setup lang="ts">
import axios from 'axios'
import Button from 'primevue/button'
import Column from 'primevue/column'
import ConfirmDialog from 'primevue/confirmdialog'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppFilterMultiSelect from '@/components/ui/AppFilterMultiSelect.vue'
import AppListState from '@/components/ui/AppListState.vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import AppTableSkeleton from '@/components/ui/AppTableSkeleton.vue'
import { deleteContactApi, importContactEmailsApi, listContactsApi, type Contact } from '@/api/contacts'
import type { ContactEmailImportResult, ContactEmailImportRow } from '@/api/contacts'
import type { ContactType } from '@/api/types'
import ContactForm from '@/components/ContactForm.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { useUnsavedChangesGuard } from '@/composables/useUnsavedChangesGuard'
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
const formWrapperEl = ref<HTMLElement | null>(null)

function focusFormInput(): void {
  nextTick(() => {
    formWrapperEl.value?.querySelector<HTMLElement>('input:not([type="hidden"]):not([disabled])')?.focus()
  })
}

const onCloseDialog = useUnsavedChangesGuard(dialogVisible, () => Boolean(contactFormRef.value?.isDirty))
const importDialogVisible = ref(false)
const importText = ref('')
const importLoading = ref(false)
const importResult = ref<ContactEmailImportResult | null>(null)
const importError = ref<string | null>(null)
const serverErrorLines = ref<Array<{ lineNumber: number; raw: string }>>([])
const parsedPreview = computed(() => parseImportText(importText.value))
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const backdropRef = ref<HTMLDivElement | null>(null)
const importLinesList = computed(() => importText.value.split('\n'))
const warnLineSet = computed(() => new Set(parsedPreview.value.ignoredLines.map((l) => l.lineNumber)))
const errorLineSet = computed(() => new Set(serverErrorLines.value.map((l) => l.lineNumber)))
const updatedResultLines = computed(() => {
  if (!importResult.value) return []
  const { rowLineNumbers, rowRaws } = parsedPreview.value
  return importResult.value.updated_indices
    .filter((i) => i < rowLineNumbers.length)
    .map((i) => ({ lineNumber: rowLineNumbers[i], raw: rowRaws[i] }))
})
const notFoundResultLines = computed(() => {
  if (!importResult.value) return []
  const { rowLineNumbers, rowRaws } = parsedPreview.value
  return importResult.value.not_found_indices
    .filter((i) => i < rowLineNumbers.length)
    .map((i) => ({ lineNumber: rowLineNumbers[i], raw: rowRaws[i] }))
})
const alreadyHasEmailResultLines = computed(() => {
  if (!importResult.value) return []
  const { rowLineNumbers, rowRaws } = parsedPreview.value
  return importResult.value.already_has_email_indices
    .filter((i) => i < rowLineNumbers.length)
    .map((i) => ({ lineNumber: rowLineNumbers[i], raw: rowRaws[i] }))
})
const updatedLineSet = computed(() => new Set(updatedResultLines.value.map((l) => l.lineNumber)))
const notFoundLineSet = computed(() => new Set(notFoundResultLines.value.map((l) => l.lineNumber)))
const alreadyLineSet = computed(() => new Set(alreadyHasEmailResultLines.value.map((l) => l.lineNumber)))
watch(importText, () => {
  importError.value = null
  serverErrorLines.value = []
})

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

function syncBackdropScroll(): void {
  if (textareaRef.value && backdropRef.value) {
    backdropRef.value.scrollTop = textareaRef.value.scrollTop
  }
}

function closeImportDialog(): void {
  importDialogVisible.value = false
  importText.value = ''
  importResult.value = null
  importError.value = null
  serverErrorLines.value = []
}

interface ParsedLine { lineNumber: number; raw: string }

function parseImportText(text: string): { rows: ContactEmailImportRow[]; rowLineNumbers: number[]; rowRaws: string[]; ignoredLines: ParsedLine[] } {
  const rows: ContactEmailImportRow[] = []
  const rowLineNumbers: number[] = []
  const rowRaws: string[] = []
  const ignoredLines: ParsedLine[] = []
  text.split('\n').forEach((raw, idx) => {
    const line = raw.trim()
    if (!line) return
    const lineNumber = idx + 1
    const commaIdx = line.lastIndexOf(',')
    if (commaIdx < 1) {
      ignoredLines.push({ lineNumber, raw: line })
      return
    }
    const nom = line.slice(0, commaIdx).trim()
    const email = line.slice(commaIdx + 1).trim()
    if (!nom || !email.includes('@')) {
      ignoredLines.push({ lineNumber, raw: line })
      return
    }
    rows.push({ nom, email })
    rowLineNumbers.push(lineNumber)
    rowRaws.push(line)
  })
  return { rows, rowLineNumbers, rowRaws, ignoredLines }
}

async function runImport(): Promise<void> {
  const { rows, rowLineNumbers, rowRaws } = parsedPreview.value
  if (rows.length === 0) {
    toast.add({ severity: 'warn', summary: t('contacts.import_emails_empty'), life: 3000 })
    return
  }
  importLoading.value = true
  importError.value = null
  serverErrorLines.value = []
  try {
    importResult.value = await importContactEmailsApi(rows)
    void loadContacts()
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 422) {
      const detail = err.response.data?.detail
      if (Array.isArray(detail) && detail.length > 0) {
        const badIndices = new Set<number>()
        for (const e of detail as Array<{ loc?: unknown[] }>) {
          if (Array.isArray(e.loc) && typeof e.loc[1] === 'number') {
            badIndices.add(e.loc[1] as number)
          }
        }
        if (badIndices.size > 0) {
          serverErrorLines.value = [...badIndices]
            .filter(i => i < rowLineNumbers.length)
            .map(i => ({ lineNumber: rowLineNumbers[i], raw: rowRaws[i] }))
            .sort((a, b) => a.lineNumber - b.lineNumber)
        } else {
          importError.value = t('contacts.import_emails_error_format')
        }
      } else {
        importError.value = t('contacts.import_emails_error_format')
      }
    } else {
      toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
    }
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

.contacts-import-preview {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-1);
}

.contacts-import-preview__summary {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  margin: 0;
}

.contacts-import-preview__summary--none {
  color: var(--p-yellow-500);
}

.contacts-import-issues {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-1);
}

.contacts-import-issues__label {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  margin: 0;
}

.contacts-import-issues__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.contacts-import-issues__item {
  display: flex;
  align-items: baseline;
  gap: var(--app-space-2);
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
}

.contacts-import-issues__item--warn {
  background-color: color-mix(in srgb, var(--p-yellow-500) 12%, transparent);
}

.contacts-import-issues__item--error {
  background-color: color-mix(in srgb, var(--p-red-500) 12%, transparent);
}

.contacts-import-issues__num {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 700;
  font-family: monospace;
  min-width: 2ch;
  color: var(--p-text-muted-color);
}

.contacts-import-issues__text {
  font-family: monospace;
  font-size: 0.8125rem;
  word-break: break-all;
}

.contacts-import-editor {
  position: relative;
  border: 1px solid var(--p-inputtext-border-color);
  border-radius: 6px;
  background: var(--p-inputtext-background);
}

.contacts-import-editor:focus-within {
  border-color: var(--p-primary-color);
  box-shadow: 0 0 0 1px var(--p-primary-color);
}

.contacts-import-editor__backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: inherit;
  pointer-events: none;
  padding: 0.5rem 0.75rem;
  font-family: monospace;
  font-size: 0.875rem;
  line-height: 1.5;
}

.contacts-import-editor__line {
  height: calc(0.875rem * 1.5);
}

.contacts-import-editor__line--warn {
  background-color: color-mix(in srgb, var(--p-yellow-500) 22%, transparent);
}

.contacts-import-editor__line--error {
  background-color: color-mix(in srgb, var(--p-red-500) 22%, transparent);
}

.contacts-import-editor__textarea {
  display: block;
  position: relative;
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  resize: vertical;
  padding: 0.5rem 0.75rem;
  font-family: monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--p-inputtext-color);
  overflow-x: auto;
  box-sizing: border-box;
}

.contacts-import-editor__line--result-updated {
  background-color: color-mix(in srgb, var(--p-green-500) 22%, transparent);
}

.contacts-import-editor__line--result-not-found {
  background-color: color-mix(in srgb, var(--p-orange-500) 22%, transparent);
}

.contacts-import-editor__line--result-already {
  background-color: color-mix(in srgb, var(--p-blue-400) 18%, transparent);
}

.contacts-import-issues__item--success {
  background-color: color-mix(in srgb, var(--p-green-500) 12%, transparent);
}

.contacts-import-issues__item--not-found {
  background-color: color-mix(in srgb, var(--p-orange-500) 12%, transparent);
}

.contacts-import-issues__item--already {
  background-color: color-mix(in srgb, var(--p-blue-400) 10%, transparent);
}


.contacts-import-editor__textarea::placeholder {
  color: var(--p-inputtext-placeholder-color);
}
</style>
