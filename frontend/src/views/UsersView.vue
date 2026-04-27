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
      <AppStatCard
        :label="t('users.stats.total')"
        :value="users.length"
        :caption="t('users.results_label', { count: users.length })"
      />
      <AppStatCard
        :label="t('users.stats.active')"
        :value="activeCount"
        :caption="t('users.status_values.active')"
        tone="success"
      />
      <AppStatCard
        :label="t('users.stats.admins')"
        :value="adminCount"
        :caption="t('users.role_cards.admin.title')"
        tone="warn"
      />
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
          <AppListState
            :displayed-count="displayedUsers.length"
            :total-count="users.length"
            :loading="loading"
            :search-text="globalFilter"
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
        </div>

        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="globalFilter" :placeholder="t('common.filter_placeholder')" />
          </div>
        </div>
      </div>

      <DataTable
        v-model:filters="tableFilters"
        :value="userRows"
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
        :global-filter-fields="['username', 'email', 'role', 'is_active', 'created_date']"
        removable-sort
        @value-change="syncDisplayedUsers"
      >
        <Column
          field="username"
          :header="t('users.username')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('users.username')" />
          </template>
        </Column>
        <Column
          field="email"
          :header="t('users.email')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('users.email')" />
          </template>
        </Column>
        <Column
          field="role_label"
          :header="t('users.role')"
          sortable
          filter-field="role"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag :value="roleLabel(data.role)" :severity="roleSeverity(data.role)" />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="allRoleOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="status_label"
          :header="t('users.status')"
          sortable
          filter-field="is_active"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag
              :value="
                data.is_active ? t('users.status_values.active') : t('users.status_values.inactive')
              "
              :severity="data.is_active ? 'success' : 'contrast'"
            />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="yesNoOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="created_date"
          :header="t('users.created_at')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
          <template #filter="{ filterModel }">
            <AppDateRangeFilter v-model="filterModel.value" />
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
              <Button
                icon="pi pi-key"
                size="small"
                severity="secondary"
                text
                :disabled="data.id === auth.user?.id"
                @click="openResetDialog(data)"
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
          <label class="app-field__label" for="user-create-username">{{
            t('users.username')
          }}</label>
          <InputText id="user-create-username" v-model="createForm.username" class="w-full" />
        </div>
        <div class="app-field">
          <label class="app-field__label" for="user-create-email">{{ t('users.email') }}</label>
          <InputText
            id="user-create-email"
            v-model="createForm.email"
            type="email"
            class="w-full"
          />
        </div>
        <div class="app-field">
          <label class="app-field__label" for="user-create-password">{{
            t('users.password')
          }}</label>
          <Password
            id="user-create-password"
            v-model="createForm.password"
            :feedback="false"
            toggle-mask
            class="w-full"
            input-class="w-full"
          />
          <small class="app-field__help">{{ t('users.password_help') }}</small>
          <Message v-if="createPasswordComplexityError" severity="warn" :closable="false">
            {{ createPasswordComplexityError }}
          </Message>
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
          <Button
            type="button"
            :label="t('common.cancel')"
            severity="secondary"
            @click="closeCreateDialog"
          />
          <Button
            type="submit"
            :label="t('users.save')"
            :disabled="!canCreate"
            :loading="savingCreate"
          />
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
          <InputText v-model="editForm.email" type="email" class="w-full" /></div>
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
          <ToggleSwitch
            id="user-edit-active"
            v-model="editForm.is_active"
            :disabled="isEditingSelf"
          />
          <label for="user-edit-active" class="app-field__label">{{ t('users.active') }}</label>
        </div>
        <Message v-if="isEditingSelf" severity="warn" :closable="false">{{
          t('users.self_guard')
        }}</Message>
        <div class="app-form-actions">
          <Button
            type="button"
            :label="t('common.cancel')"
            severity="secondary"
            @click="closeEditDialog"
          />
          <Button
            type="submit"
            :label="t('users.update')"
            :disabled="!canEdit"
            :loading="savingEdit"
          />
        </div>
      </form>
    </Dialog>

    <Dialog
      v-model:visible="resetDialogVisible"
      :header="t('users.reset_dialog_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <form class="app-form-stack" @submit.prevent="submitResetPassword">
        <Message severity="info" :closable="false">{{ t('users.reset_password_help') }}</Message>
        <div class="app-field">
          <label class="app-field__label">{{ t('users.username') }}</label>
          <InputText :model-value="resetPasswordUser?.username ?? ''" disabled class="w-full" />
        </div>
        <div class="app-field">
          <label class="app-field__label" for="user-reset-password">{{
            t('users.reset_password')
          }}</label>
          <Password
            id="user-reset-password"
            v-model="resetPasswordForm.new_password"
            :feedback="false"
            toggle-mask
            class="w-full"
            input-class="w-full"
          />
          <Message v-if="resetPasswordComplexityError" severity="warn" :closable="false">
            {{ resetPasswordComplexityError }}
          </Message>
        </div>
        <div class="app-form-actions">
          <Button
            type="button"
            :label="t('common.cancel')"
            severity="secondary"
            @click="closeResetDialog"
          />
          <Button
            type="submit"
            :label="t('users.reset_password_action')"
            :disabled="!canResetPassword"
            :loading="savingResetPassword"
          />
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
import AppDateRangeFilter from '@/components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '@/components/ui/AppFilterMultiSelect.vue'
import AppListState from '@/components/ui/AppListState.vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppStatCard from '@/components/ui/AppStatCard.vue'
import { createUserApi, listUsersApi, resetUserPasswordApi, updateUserApi } from '@/api/users'
import type { UserPasswordResetRequest, UserRead, UserRole } from '@/api/types'
import { PASSWORD_MIN_LENGTH } from '@/constants/auth'
import { useAuthStore } from '@/stores/auth'
import {
  dateRangeFilter,
  inFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'

interface CreateUserForm {
  username: string
  email: string
  password: string
  role: UserRole
}

interface EditUserForm {
  role: UserRole
  is_active: boolean
  email: string
}

type ResetPasswordForm = UserPasswordResetRequest

interface RoleDefinition {
  value: UserRole
  title: string
  subtitle: string
  description: string
}

interface ApiErrorDetail {
  code?: string
  message?: string
}

const { t } = useI18n()
const toast = useToast()
const auth = useAuthStore()

const users = ref<UserRead[]>([])
const userRows = ref<
  Array<UserRead & { role_label: string; status_label: string; created_date: string }>
>([])
const loading = ref(false)
const savingCreate = ref(false)
const savingEdit = ref(false)
const savingResetPassword = ref(false)
const createDialogVisible = ref(false)
const editDialogVisible = ref(false)
const resetDialogVisible = ref(false)
const editingUser = ref<UserRead | null>(null)
const resetPasswordUser = ref<UserRead | null>(null)
const createForm = ref<CreateUserForm>(defaultCreateForm())
const editForm = ref<EditUserForm>(defaultEditForm())
const resetPasswordForm = ref<ResetPasswordForm>(defaultResetPasswordForm())
const yesNoOptions = [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
]
const {
  filters: tableFilters,
  globalFilter,
  displayedRows: displayedUsers,
  syncDisplayedRows: syncDisplayedUsers,
  resetFilters,
  hasActiveFilters,
} = useDataTableFilters(userRows, {
  global: textFilter(''),
  username: textFilter(),
  email: textFilter(),
  role: inFilter(),
  is_active: inFilter(),
  created_date: dateRangeFilter(),
})

const userApiErrorMessages: Record<string, string> = {
  self_deactivate: 'users.api_errors.self_deactivate',
  self_demote: 'users.api_errors.self_demote',
  last_admin: 'users.api_errors.last_admin',
  no_changes: 'users.api_errors.no_changes',
  user_not_found: 'users.api_errors.user_not_found',
  email_exists: 'users.api_errors.email_exists',
  email_required: 'users.api_errors.email_required',
}

const legacyUserApiErrorMessages: Record<string, string> = {
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
    role: 'secretaire',
  }
}

function defaultEditForm(): EditUserForm {
  return {
    role: 'secretaire',
    is_active: true,
    email: '',
  }
}

function defaultResetPasswordForm(): ResetPasswordForm {
  return {
    new_password: '',
  }
}

const allRoleDefinitions = computed<RoleDefinition[]>(() => [
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

const roleDefinitions = computed(() =>
  allRoleDefinitions.value.filter((role) => role.value !== 'readonly'),
)

const roleOptions = computed(() => {
  const options = roleDefinitions.value.map((role) => ({ value: role.value, label: role.title }))

  if (editingUser.value?.role === 'readonly') {
    return [
      {
        value: 'readonly' satisfies UserRole,
        label: t('users.role_cards.readonly.title'),
      },
      ...options,
    ]
  }

  return options
})
const allRoleOptions = computed(() => [
  { value: 'readonly' as UserRole, label: t('users.role_cards.readonly.title') },
  ...roleDefinitions.value.map((role) => ({ value: role.value, label: role.title })),
])

const roleCards = computed(() => roleDefinitions.value)

function checkPasswordComplexity(p: string): string | null {
  if (p.length === 0) return null
  if (p.length < PASSWORD_MIN_LENGTH) return t('users.password_too_short', { min: PASSWORD_MIN_LENGTH })
  if (!/[A-Z]/.test(p)) return t('users.password_no_uppercase')
  if (!/[0-9]/.test(p)) return t('users.password_no_digit')
  return null
}
const createPasswordComplexityError = computed(() => checkPasswordComplexity(createForm.value.password))
const resetPasswordComplexityError = computed(() => checkPasswordComplexity(resetPasswordForm.value.new_password))

const activeCount = computed(() => users.value.filter((user) => user.is_active).length)
const adminCount = computed(() => users.value.filter((user) => user.role === 'admin').length)
const isEditingSelf = computed(() => editingUser.value?.id === auth.user?.id)
const canCreate = computed(() => {
  return (
    createForm.value.username.trim().length > 0 &&
    createForm.value.email.trim().length > 0 &&
    createPasswordComplexityError.value === null &&
    createForm.value.password.length > 0
  )
})
const canEdit = computed(() => {
  if (!editingUser.value) {
    return false
  }
  const roleOrStatusChanged =
    editForm.value.role !== editingUser.value.role ||
    editForm.value.is_active !== editingUser.value.is_active
  const emailChanged =
    editForm.value.email.trim() !== editingUser.value.email &&
    editForm.value.email.trim().length > 0
  if (isEditingSelf.value) {
    // Admin can only update their own email; role/active changes are blocked
    return emailChanged
  }
  return roleOrStatusChanged || emailChanged
})
const canResetPassword = computed(() => {
  return (
    resetPasswordComplexityError.value === null &&
    resetPasswordForm.value.new_password.length > 0 &&
    resetPasswordUser.value !== null
  )
})

function roleLabel(role: UserRole): string {
  return allRoleDefinitions.value.find((item) => item.value === role)?.title ?? role
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
  const detail = (error as { response?: { data?: { detail?: string | ApiErrorDetail } } }).response
    ?.data?.detail

  if (typeof detail === 'object' && detail !== null && typeof detail.code === 'string') {
    const translationKey = userApiErrorMessages[detail.code]
    if (translationKey !== undefined) {
      return t(translationKey)
    }
  }

  if (typeof detail === 'string') {
    const legacyTranslationKey = legacyUserApiErrorMessages[detail]
    if (legacyTranslationKey !== undefined) {
      return t(legacyTranslationKey)
    }
  }

  if (status === 403) {
    return t('common.error.forbidden')
  }
  if (status === 404) {
    return t('common.error.notFound')
  }

  return t('common.error.unknown')
}

async function loadUsers(): Promise<void> {
  loading.value = true
  try {
    users.value = await listUsersApi()
    userRows.value = users.value.map((user) => ({
      ...user,
      role_label: roleLabel(user.role),
      status_label: user.is_active ? t('common.yes') : t('common.no'),
      created_date: user.created_at.slice(0, 10),
    }))
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
    email: user.email,
  }
  editDialogVisible.value = true
}

function closeEditDialog(): void {
  editDialogVisible.value = false
  editingUser.value = null
  editForm.value = defaultEditForm()
}

function openResetDialog(user: UserRead): void {
  resetPasswordUser.value = user
  resetPasswordForm.value = defaultResetPasswordForm()
  resetDialogVisible.value = true
}

function closeResetDialog(): void {
  resetDialogVisible.value = false
  resetPasswordUser.value = null
  resetPasswordForm.value = defaultResetPasswordForm()
}

async function submitCreate(): Promise<void> {
  if (!canCreate.value) return

  savingCreate.value = true
  try {
    await createUserApi({
      ...createForm.value,
      username: createForm.value.username.trim(),
      email: createForm.value.email.trim(),
    })
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
    const payload: Parameters<typeof updateUserApi>[1] = {}
    if (editForm.value.role !== editingUser.value.role) payload.role = editForm.value.role
    if (editForm.value.is_active !== editingUser.value.is_active)
      payload.is_active = editForm.value.is_active
    if (
      editForm.value.email.trim() !== editingUser.value.email &&
      editForm.value.email.trim().length > 0
    )
      payload.email = editForm.value.email.trim()
    await updateUserApi(editingUser.value.id, payload)
    toast.add({ severity: 'success', summary: t('users.updated'), life: 3000 })
    closeEditDialog()
    await loadUsers()
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getApiErrorSummary(error), life: 3500 })
  } finally {
    savingEdit.value = false
  }
}

async function submitResetPassword(): Promise<void> {
  if (!resetPasswordUser.value || !canResetPassword.value) return

  savingResetPassword.value = true
  try {
    await resetUserPasswordApi(resetPasswordUser.value.id, {
      new_password: resetPasswordForm.value.new_password,
    })
    toast.add({ severity: 'success', summary: t('users.password_reset'), life: 3000 })
    closeResetDialog()
  } catch (error: unknown) {
    toast.add({ severity: 'error', summary: getApiErrorSummary(error), life: 3500 })
  } finally {
    savingResetPassword.value = false
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
  width: 8rem;
}

.users-switch-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
</style>
