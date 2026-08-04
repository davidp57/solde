<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="t('documents.title')">
      <template #actions>
        <div class="app-page-header__actions">
          <Button
            v-if="canWrite"
            :label="t('documents.upload')"
            icon="pi pi-upload"
            data-testid="document-upload-open"
            @click="openUploadDialog"
          />
        </div>
      </template>
    </AppPageHeader>

    <AppPanel :title="t('documents.title')" dense>
      <p class="documents-intro">{{ t('documents.intro') }}</p>

      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <AppListState
            :displayed-count="documents.length"
            :total-count="total"
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
            @click="resetFilters"
          />
        </div>
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.search') }}</label>
            <InputText
              v-model="search"
              :placeholder="t('documents.search_placeholder')"
              data-testid="document-search"
              @keyup.enter="loadDocuments"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('documents.fiscal_year') }}</label>
            <Select
              v-model="fiscalYearFilter"
              :options="fiscalYearFilterOptions"
              option-label="label"
              option-value="value"
              data-testid="document-year-filter"
              @change="loadDocuments"
            />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('documents.tag') }}</label>
            <Select
              v-model="tagFilter"
              :options="tagFilterOptions"
              option-label="label"
              option-value="value"
              show-clear
              data-testid="document-tag-filter"
              @change="loadDocuments"
            />
          </div>
        </div>
      </div>

      <AppTableSkeleton v-if="loading" :rows="6" :cols="5" />
      <DataTable
        v-else
        :value="documents"
        class="app-data-table"
        striped-rows
        data-key="id"
        size="small"
        row-hover
        removable-sort
      >
        <template #empty>{{ t('documents.empty') }}</template>
        <Column field="title" :header="t('documents.column_title')" sortable>
          <template #body="{ data }">
            <div class="document-title">{{ data.title }}</div>
            <div class="document-filename">{{ data.filename }}</div>
          </template>
        </Column>
        <Column field="fiscal_year_name" :header="t('documents.fiscal_year')" sortable>
          <template #body="{ data }">
            <span v-if="data.fiscal_year_name">{{ data.fiscal_year_name }}</span>
            <span v-else class="document-muted">{{ t('documents.no_fiscal_year') }}</span>
          </template>
        </Column>
        <Column :header="t('documents.tags')">
          <template #body="{ data }">
            <Tag v-for="tag in data.tags" :key="tag" :value="tag" class="document-tag" />
            <span v-if="!data.tags.length" class="document-muted">—</span>
          </template>
        </Column>
        <Column field="uploaded_at" :header="t('documents.uploaded_at')" sortable>
          <template #body="{ data }">{{ formatDateTime(data.uploaded_at) }}</template>
        </Column>
        <Column field="size_bytes" :header="t('documents.size')" sortable>
          <template #body="{ data }">{{ formatSize(data.size_bytes) }}</template>
        </Column>
        <Column :header="t('common.actions')" style="width: 10rem">
          <template #body="{ data }">
            <div class="document-actions">
              <Button
                icon="pi pi-download"
                severity="secondary"
                outlined
                size="small"
                :aria-label="t('documents.download')"
                :title="t('documents.download')"
                @click="download(data)"
              />
              <Button
                v-if="canWrite"
                icon="pi pi-pencil"
                severity="secondary"
                outlined
                size="small"
                :aria-label="t('common.edit')"
                :title="t('common.edit')"
                data-testid="document-edit"
                @click="openEditDialog(data)"
              />
              <Button
                v-if="canWrite"
                icon="pi pi-trash"
                severity="danger"
                outlined
                size="small"
                :aria-label="t('common.delete')"
                :title="t('common.delete')"
                data-testid="document-delete"
                @click="confirmDelete(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </AppPanel>

    <Dialog
      v-model:visible="uploadDialogVisible"
      :header="t('documents.upload')"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="app-dialog-form">
        <div class="app-field">
          <label class="app-field__label">{{ t('documents.file') }} *</label>
          <input
            type="file"
            data-testid="document-file"
            @change="onFileSelected"
          />
          <small class="app-field__hint">{{ t('documents.file_hint') }}</small>
        </div>
        <div class="app-field">
          <label class="app-field__label">{{ t('documents.column_title') }} *</label>
          <InputText v-model="form.title" data-testid="document-title" />
        </div>
        <div class="app-field">
          <label class="app-field__label">{{ t('documents.fiscal_year') }}</label>
          <Select
            v-model="form.fiscal_year_id"
            :options="fiscalYearOptions"
            option-label="label"
            option-value="value"
            show-clear
            :placeholder="t('documents.no_fiscal_year')"
          />
        </div>
        <div class="app-field">
          <label class="app-field__label">{{ t('documents.tags') }}</label>
          <InputText v-model="form.tags" :placeholder="t('documents.tags_placeholder')" />
          <small v-if="knownTags.length" class="app-field__hint">
            {{ t('documents.tags_known') }} {{ knownTags.map((entry) => entry.tag).join(', ') }}
          </small>
        </div>
        <div class="app-field">
          <label class="app-field__label">{{ t('documents.notes') }}</label>
          <Textarea v-model="form.notes" rows="3" auto-resize />
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="uploadDialogVisible = false" />
        <Button
          :label="editingId ? t('common.save') : t('documents.upload')"
          :loading="saving"
          data-testid="document-submit"
          @click="submit"
        />
      </template>
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
import Textarea from 'primevue/textarea'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import {
  deleteDocumentApi,
  getDocumentDownloadUrl,
  listDocumentTagsApi,
  listDocumentsApi,
  updateDocumentApi,
  uploadDocumentApi,
  type AppDocument,
  type DocumentTag,
} from '../api/document'
import AppListState from '../components/ui/AppListState.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppTableSkeleton from '../components/ui/AppTableSkeleton.vue'
import { useAuthStore } from '../stores/auth'
import { useFiscalYearStore } from '../stores/fiscalYear'
import { downloadAuthenticatedFile } from '../utils/downloadFile'
import { getErrorDetail } from '../utils/errorUtils'

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const auth = useAuthStore()
const fiscalYearStore = useFiscalYearStore()

const documents = ref<AppDocument[]>([])
const knownTags = ref<DocumentTag[]>([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)

const search = ref('')
const fiscalYearFilter = ref<number | 'all' | 'none'>('all')
const tagFilter = ref<string | null>(null)

const uploadDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const selectedFile = ref<File | null>(null)
const form = ref({
  title: '',
  fiscal_year_id: null as number | null,
  tags: '',
  notes: '',
})

const canWrite = computed(() => auth.canAccessManagement)

const fiscalYearOptions = computed(() =>
  fiscalYearStore.fiscalYears.map((fy) => ({ label: fy.name, value: fy.id })),
)

const fiscalYearFilterOptions = computed(() => [
  { label: t('documents.all_years'), value: 'all' as const },
  { label: t('documents.no_fiscal_year'), value: 'none' as const },
  ...fiscalYearOptions.value,
])

const tagFilterOptions = computed(() =>
  knownTags.value.map((entry) => ({ label: `${entry.tag} (${entry.count})`, value: entry.tag })),
)

const hasAnyFilters = computed(
  () => search.value !== '' || fiscalYearFilter.value !== 'all' || tagFilter.value !== null,
)

const activeFilterLabels = computed(() => {
  const labels: string[] = []
  if (fiscalYearFilter.value === 'none') labels.push(t('documents.no_fiscal_year'))
  else if (fiscalYearFilter.value !== 'all') {
    const found = fiscalYearOptions.value.find((o) => o.value === fiscalYearFilter.value)
    if (found) labels.push(found.label)
  }
  if (tagFilter.value) labels.push(tagFilter.value)
  return labels
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`
}

function formatDateTime(value: string): string {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadDocuments(): Promise<void> {
  loading.value = true
  try {
    const { items, total: count } = await listDocumentsApi({
      search: search.value || null,
      tag: tagFilter.value,
      fiscal_year_id: typeof fiscalYearFilter.value === 'number' ? fiscalYearFilter.value : null,
      without_fiscal_year: fiscalYearFilter.value === 'none',
    })
    documents.value = items
    total.value = count
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loading.value = false
  }
}

async function loadTags(): Promise<void> {
  try {
    knownTags.value = await listDocumentTagsApi()
  } catch {
    knownTags.value = []
  }
}

async function refresh(): Promise<void> {
  await Promise.all([loadDocuments(), loadTags()])
}

function resetFilters(): void {
  search.value = ''
  fiscalYearFilter.value = 'all'
  tagFilter.value = null
  void loadDocuments()
}

function openUploadDialog(): void {
  editingId.value = null
  selectedFile.value = null
  form.value = { title: '', fiscal_year_id: null, tags: '', notes: '' }
  uploadDialogVisible.value = true
}

function openEditDialog(document: AppDocument): void {
  editingId.value = document.id
  selectedFile.value = null
  form.value = {
    title: document.title,
    fiscal_year_id: document.fiscal_year_id,
    tags: document.tags.join(', '),
    notes: document.notes ?? '',
  }
  uploadDialogVisible.value = true
}

function onFileSelected(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  selectedFile.value = file
  // Offer the filename as a starting title rather than leaving the field empty.
  if (file && !form.value.title) {
    form.value.title = file.name.replace(/\.[^.]+$/, '')
  }
}

function splitTags(raw: string): string[] {
  return raw
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

async function submit(): Promise<void> {
  if (!form.value.title.trim()) {
    toast.add({ severity: 'warn', summary: t('documents.title_required'), life: 3000 })
    return
  }
  if (editingId.value === null && !selectedFile.value) {
    toast.add({ severity: 'warn', summary: t('documents.file_required'), life: 3000 })
    return
  }

  saving.value = true
  try {
    if (editingId.value !== null) {
      await updateDocumentApi(editingId.value, {
        title: form.value.title.trim(),
        fiscal_year_id: form.value.fiscal_year_id,
        tags: splitTags(form.value.tags),
        notes: form.value.notes || null,
      })
      toast.add({ severity: 'success', summary: t('documents.updated'), life: 3000 })
    } else {
      await uploadDocumentApi({
        file: selectedFile.value as File,
        title: form.value.title.trim(),
        fiscal_year_id: form.value.fiscal_year_id,
        tags: splitTags(form.value.tags),
        notes: form.value.notes || null,
      })
      toast.add({ severity: 'success', summary: t('documents.uploaded'), life: 3000 })
    }
    uploadDialogVisible.value = false
    await refresh()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: getErrorDetail(error, t('common.error.unknown')),
      life: 6000,
    })
  } finally {
    saving.value = false
  }
}

async function download(item: AppDocument): Promise<void> {
  try {
    await downloadAuthenticatedFile(getDocumentDownloadUrl(item.id), item.filename)
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: getErrorDetail(error, t('common.error.unknown')),
      life: 5000,
    })
  }
}

function confirmDelete(document: AppDocument): void {
  confirm.require({
    message: t('documents.confirm_delete', { title: document.title }),
    header: t('common.confirm'),
    icon: 'pi pi-exclamation-triangle',
    acceptProps: { severity: 'danger', label: t('common.delete') },
    rejectProps: { severity: 'secondary', outlined: true, label: t('common.cancel') },
    accept: async () => {
      try {
        await deleteDocumentApi(document.id)
        toast.add({ severity: 'success', summary: t('documents.deleted'), life: 3000 })
        await refresh()
      } catch (error) {
        toast.add({
          severity: 'error',
          summary: getErrorDetail(error, t('common.error.unknown')),
          life: 5000,
        })
      }
    },
  })
}

onMounted(async () => {
  await fiscalYearStore.initialize()
  await refresh()
})
</script>

<style scoped>
.documents-intro {
  margin: 0 0 1rem;
  color: var(--p-text-muted-color);
  font-size: 0.9rem;
}

.document-title {
  font-weight: 600;
}

.document-filename {
  font-size: 0.8rem;
  color: var(--p-text-muted-color);
}

.document-muted {
  color: var(--p-text-muted-color);
}

.document-tag {
  margin-right: 0.25rem;
}

.document-actions {
  display: flex;
  gap: 0.25rem;
}
</style>
