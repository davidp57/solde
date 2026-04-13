<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('users.title')"
      :subtitle="t('users.subtitle')"
    >
      <template #actions>
        <Button :label="t('users.new')" icon="pi pi-plus" @click="openCreateDialog" />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard :label="t('users.stats.total')" :value="users.length" :caption="t('users.results_label', { count: users.length })" />
      <AppStatCard :label="t('users.stats.active')" :value="activeCount" :caption="t('users.status_values.active')" tone="success" />
      <AppStatCard :label="t('users.stats.admins')" :value="adminCount" :caption="t('users.role_cards.admin.title')" tone="warn" />
    </section>

    <AppPanel :title="t('users.matrix_title')" :subtitle="t('users.matrix_subtitle')">
      <div class="users-role-grid">
        <article v-for="role in roleCards" :key="role.value" class="users-role-card">
          <header class="users-role-card__header">
            <strong>{{ role.title }}</strong>
            <span>{{ role.subtitle }}</span>
          </header>
          <p>{{ role.description }}</p>
        </article>
      </div>
    </AppPanel>

    <AppPanel :title="t('users.workspace_title')" :subtitle="t('users.workspace_subtitle')">
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <span class="app-chip">{{ t('users.results_label', { count: users.length }) }}</span>
        </div>
      </div>

      <DataTable
        :value="users"
        :loading="loading"
        class="app-data-table"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[10, 20, 50]"
        data-key="id"
        size="small"
        row-hover
      >
        <Column field="username" :header="t('users.username')" sortable />
        <Column field="email" :header="t('users.email')" sortable />
        <Column field="role" :header="t('users.role')">
          <template #body="{ data }">
            <Tag :value="roleLabel(data.role)" :severity="roleSeverity(data.role)" />
          </template>
        </Column>
        <Column field="is_active" :header="t('users.status')">
          <template #body="{ data }">
            <Tag
              :value="data.is_active ? t('users.status_values.active') : t('users.status_values.inactive')"
              :severity="data.is_active ? 'success' : 'contrast'"
            />
          </template>
        </Column>
        <Column field="created_at" :header="t('users.created_at')" sortable>
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>
        <Column :header="t('common.actions')" class="users-actions">
          <template #body="{ data }">
            <div class="app-inline-actions">
              <Button
                icon="pi pi-pencil"
                size="small"
                severity="secondary"
                text
                @click="openEditDialog(data)"
              />
            </div>
          </template>
        </Column>
        <template #empty>
          <div class="app-empty-state">{{ t('users.empty') }}</div>
        </template>
      </DataTable>
    </AppPanel>

    <Dialog
      v-model:visible="createDialogVisible"
      :header="t('users.new')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <form class="app-form-stack" @submit.prevent="submitCreate">
        <div class="app-field">
          <label class="app-field__label" for="user-create-username">{{ t('users.username') }}</label>
          <InputText id="user-create-username" v-model="createForm.username" class="w-full" />
        </div>
        <div class="app-field">
          <label class="app-field__label" for="user-create-email">{{ t('users.email') }}</label>
          <InputText id="user-create-email" v-model="createForm.email" type="email" class="w-full" />
        </div>
        <div class="app-field">
          <label class="app-field__label" for="user-create-password">{{ t('users.password') }}</label>
          <Password
            id="user-create-password"
            v-model="createForm.password"
            :feedback="false"
            toggle-mask
            class="w-full"
            input-class="w-full"
          />
          <small class="app-field__help">{{ t('users.password_help') }}</small>
        </div>
        <div class="app-field">
          <label class="app-field__label" for="user-create-role">{{ t('users.role') }}</label>
          <Select
            id="user-create-role"
            v-model="createForm.role"
            :options="roleOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>
        <div class="app-form-actions">
          <Button type="button" :label="t('common.cancel')" severity="secondary" @click="closeCreateDialog" />
          <Button type="submit" :label="t('users.save')" :disabled="!canCreate" :loading="savingCreate" />
        </div>
      </form>
    </Dialog>

    <Dialog
      v-model:visible="editDialogVisible"
      :header="t('users.edit')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <form class="app-form-stack" @submit.prevent="submitEdit">
        <div class="app-field">
          <label class="app-field__label">{{ t('users.username') }}</label>
          <InputText :model-value="editingUser?.username ?? ''" disabled class="w-full" />
        </div>
        <div class="app-field">
          <label class="app-field__label">{{ t('users.email') }}</label>
          <InputText :model-value="editingUser?.email ?? ''" disabled class="w-full" />
        </div>
        <div class="app-field">
          <label class="app-field__label" for="user-edit-role">{{ t('users.role') }}</label>
          <Select
            id="user-edit-role"
            v-model="editForm.role"
            :options="roleOptions"
            option-label="label"
            option-value="value"
            class="w-full"
            :disabled="isEditingSelf"
          />
        </div>
        <div class="users-switch-row">
          <ToggleSwitch id="user-edit-active" v-model="editForm.is_active" :disabled="isEditingSelf" />
          <label for="user-edit-active" class="app-field__label">{{ t('users.active') }}</label>
        </div>
        <Message v-if="isEditingSelf" severity="warn" :closable="false">{{ t('users.self_guard') }}</Message>
        <div class="app-form-actions">
          <Button type="button" :label="t('common.cancel')" severity="secondary" @click="closeEditDialog" />
          <Button type="submit" :label="t('users.update')" :disabled="!canEdit" :loading="savingEdit" />
        </div>
      </form>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import { useToast } from 'primevue/usetoast'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import { createUserApi, listUsersApi, updateUserApi } from '@/api/users'
import type { UserRead, UserRole } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

interface CreateUserForm {
  username: string
  email: string
  password: string
  role: UserRole
}

interface EditUserForm {
  role: UserRole
  is_active: boolean
}

const { t } = useI18n()
const toast = useToast()
const auth = useAuthStore()

const users = ref<UserRead[]>([])
const loading = ref(false)
const savingCreate = ref(false)
const savingEdit = ref(false)
const createDialogVisible = ref(false)
const editDialogVisible = ref(false)
const editingUser = ref<UserRead | null>(null)
const createForm = ref<CreateUserForm>(defaultCreateForm())
const editForm = ref<EditUserForm>(defaultEditForm())

const userApiErrorMessages: Record<string, string> = {
  'You cannot deactivate your own account': 'users.api_errors.self_deactivate',
  'You cannot remove your own admin role': 'users.api_errors.self_demote',
  'At least one active admin must remain': 'users.api_errors.last_admin',
  'No changes requested': 'users.api_errors.no_changes',
  'User not found': 'users.api_errors.user_not_found',
}

function defaultCreateForm(): CreateUserForm {
  return {
    username: '',
    email: '',
    password: '',
    role: 'readonly',
  }
}

function defaultEditForm(): EditUserForm {
  return {
    role: 'readonly',
    is_active: true,
  }
}

const roleOptions = computed(() => [
  { value: 'readonly' as const, label: t('users.role_cards.readonly.title') },
  { value: 'secretaire' as const, label: t('users.role_cards.secretaire.title') },
  { value: 'tresorier' as const, label: t('users.role_cards.tresorier.title') },
  { value: 'admin' as const, label: t('users.role_cards.admin.title') },
])

const roleCards = computed(() => [
  {
    value: 'readonly',
    title: t('users.role_cards.readonly.title'),
    subtitle: t('users.role_cards.readonly.subtitle'),
    description: t('users.role_cards.readonly.description'),
  },
  {
    value: 'secretaire',
    title: t('users.role_cards.secretaire.title'),
    subtitle: t('users.role_cards.secretaire.subtitle'),
    description: t('users.role_cards.secretaire.description'),
  },
  {
    value: 'tresorier',
    title: t('users.role_cards.tresorier.title'),
    subtitle: t('users.role_cards.tresorier.subtitle'),
    description: t('users.role_cards.tresorier.description'),
  },
  {
    value: 'admin',
    title: t('users.role_cards.admin.title'),
    subtitle: t('users.role_cards.admin.subtitle'),
    description: t('users.role_cards.admin.description'),
  },
])

const activeCount = computed(() => users.value.filter((user) => user.is_active).length)
const adminCount = computed(() => users.value.filter((user) => user.role === 'admin').length)
const isEditingSelf = computed(() => editingUser.value?.id === auth.user?.id)
const canCreate = computed(() => {
  return (
    createForm.value.username.trim().length > 0
    && createForm.value.email.trim().length > 0
    && createForm.value.password.length >= 8
  )
})
const canEdit = computed(() => {
  if (!editingUser.value || isEditingSelf.value) {
    return false
  }
  return (
    editForm.value.role !== editingUser.value.role
    || editForm.value.is_active !== editingUser.value.is_active
  )
})

function roleLabel(role: UserRole): string {
  return t(`users.role_cards.${role}.title`)
}

function roleSeverity(role: UserRole): 'info' | 'success' | 'warn' | 'contrast' {
  if (role === 'admin') return 'warn'
  if (role === 'tresorier') return 'success'
  if (role === 'secretaire') return 'info'
  return 'contrast'
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function getApiErrorSummary(error: unknown): string {
  const status = (error as { response?: { status?: number } }).response?.status
  const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail

  if (status === 403) {
    return t('common.error.forbidden')
  }
  if (status === 404) {
    return t('common.error.notFound')
  }
  if (typeof detail === 'string') {
    const translationKey = userApiErrorMessages[detail]
    if (translationKey !== undefined) {
      return t(translationKey)
    }
  }

  return t('common.error.unknown')
}

async function loadUsers(): Promise<void> {
  loading.value = true
  try {
    users.value = await listUsersApi()
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getApiErrorSummary(error), life: 3000 })
  } finally {
    loading.value = false
  }
}

function openCreateDialog(): void {
  createForm.value = defaultCreateForm()
  createDialogVisible.value = true
}

function closeCreateDialog(): void {
  createDialogVisible.value = false
  createForm.value = defaultCreateForm()
}

function openEditDialog(user: UserRead): void {
  editingUser.value = user
  editForm.value = {
    role: user.role,
    is_active: user.is_active,
  }
  editDialogVisible.value = true
}

function closeEditDialog(): void {
  editDialogVisible.value = false
  editingUser.value = null
  editForm.value = defaultEditForm()
}

async function submitCreate(): Promise<void> {
  if (!canCreate.value) return

  savingCreate.value = true
  try {
    await createUserApi({ ...createForm.value, username: createForm.value.username.trim(), email: createForm.value.email.trim() })
    toast.add({ severity: 'success', summary: t('users.created'), life: 3000 })
    closeCreateDialog()
    await loadUsers()
  } catch (error: unknown) {
    const status = (error as { response?: { status?: number } }).response?.status
    toast.add({
      severity: 'error',
      summary: status === 409 ? t('users.duplicate_error') : getApiErrorSummary(error),
      life: 3500,
    })
  } finally {
    savingCreate.value = false
  }
}

async function submitEdit(): Promise<void> {
  if (!editingUser.value || !canEdit.value) return

  savingEdit.value = true
  try {
    await updateUserApi(editingUser.value.id, {
      role: editForm.value.role,
      is_active: editForm.value.is_active,
    })
    toast.add({ severity: 'success', summary: t('users.updated'), life: 3000 })
    closeEditDialog()
    await loadUsers()
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getApiErrorSummary(error), life: 3500 })
  } finally {
    savingEdit.value = false
  }
}

onMounted(loadUsers)
</script>

<style scoped>
.users-role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
  gap: 1rem;
}

.users-role-card {
  padding: 1rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 1rem;
  background: var(--p-content-background);
}

.users-role-card__header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}

.users-role-card__header span {
  color: var(--p-text-muted-color);
  font-size: 0.85rem;
}

.users-actions {
  width: 6rem;
}

.users-switch-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
</style>
