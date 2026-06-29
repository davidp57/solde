<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('settings.title')"
      :subtitle="t('settings.subtitle')"
    />

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="organisation">{{ t('settings.tab_organisation') }}</Tab>
        <Tab value="comptabilite">{{ t('settings.tab_comptabilite') }}</Tab>
        <Tab value="communication">{{ t('settings.tab_communication') }}</Tab>
        <Tab value="danger" class="settings-tab--danger">{{ t('settings.tab_danger') }}</Tab>
      </TabList>
    </Tabs>

    <!-- ───────── Organisation ───────── -->
    <section v-show="activeTab === 'organisation'" class="settings-section">
      <AppPanel :title="t('settings.section_identity')" :subtitle="t('settings.section_asso_subtitle')">
        <AppSettingRow :label="t('settings.asso_name')" :description="t('settings.asso_name_desc')" html-for="association_name">
          <template #control>
            <InputText id="association_name" v-model="form.association_name" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.siret')" html-for="association_siret">
          <template #control>
            <InputText id="association_siret" v-model="form.association_siret" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.address')" html-for="association_address">
          <template #control>
            <Textarea id="association_address" v-model="form.association_address" rows="3" />
          </template>
        </AppSettingRow>
      </AppPanel>

      <AppPanel :title="t('settings.section_payment')" :subtitle="t('settings.section_payment_subtitle')">
        <AppSettingRow :label="t('settings.payment_iban')" html-for="payment_iban">
          <template #control>
            <InputText id="payment_iban" v-model="form.payment_iban" :placeholder="t('settings.payment_iban_placeholder')" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.payment_bic')" html-for="payment_bic">
          <template #control>
            <InputText id="payment_bic" v-model="form.payment_bic" :placeholder="t('settings.payment_bic_placeholder')" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.payment_check_payee')" :description="t('settings.payment_instructions_help')" html-for="payment_check_payee">
          <template #control>
            <InputText id="payment_check_payee" v-model="form.payment_check_payee" :placeholder="t('settings.payment_check_payee_placeholder')" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.bank_account_courant_acctid')" :description="t('settings.bank_account_courant_acctid_help')" html-for="bank_account_courant_acctid">
          <template #control>
            <InputText id="bank_account_courant_acctid" v-model="form.bank_account_courant_acctid" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.bank_account_epargne_acctid')" :description="t('settings.bank_account_epargne_acctid_help')" html-for="bank_account_epargne_acctid">
          <template #control>
            <InputText id="bank_account_epargne_acctid" v-model="form.bank_account_epargne_acctid" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.list_default_limit')" :description="t('settings.list_default_limit_help')" html-for="list_default_limit">
          <template #control>
            <InputNumber id="list_default_limit" v-model="form.list_default_limit" :min="0" :max="5000" :step="100" show-buttons />
          </template>
        </AppSettingRow>
      </AppPanel>

      <SettingsSaveBar :dirty="orgDirty" :loading="savingOrg" @save="saveOrg" @cancel="revert" />
    </section>

    <!-- ───────── Comptabilité ───────── -->
    <section v-show="activeTab === 'comptabilite'" class="settings-section">
      <AppPanel :title="t('settings.section_numbering')" :subtitle="t('settings.section_numbering_subtitle')">
        <AppSettingRow :label="t('settings.client_invoice_number_template')" :description="t('settings.client_invoice_number_template_help')">
          <template #control>
            <div class="settings-template-control">
              <InputText v-model="form.client_invoice_number_template" class="settings-mono" :placeholder="t('settings.client_invoice_number_template_placeholder')" />
              <Tag :value="`→ ${invoicePreview}`" severity="success" />
            </div>
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.client_invoice_seq_digits')" :warning="t('settings.client_invoice_seq_digits_help')" html-for="client_invoice_seq_digits">
          <template #control>
            <InputNumber id="client_invoice_seq_digits" v-model="form.client_invoice_seq_digits" :min="2" :max="6" :use-grouping="false" show-buttons />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.supplier_invoice_number_template')" :description="t('settings.supplier_invoice_number_template_help')">
          <template #control>
            <InputText v-model="form.supplier_invoice_number_template" class="settings-mono" :placeholder="t('settings.supplier_invoice_number_template_placeholder')" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.cheque_number_template')" :description="t('settings.cheque_number_template_help')">
          <template #control>
            <InputText v-model="form.cheque_number_template" class="settings-mono" :placeholder="t('settings.cheque_number_template_placeholder')" />
          </template>
        </AppSettingRow>
      </AppPanel>

      <AppPanel :title="t('settings.section_fiscal')" :subtitle="t('settings.section_fiscal_subtitle')">
        <AppSettingRow :label="t('settings.fiscal_year_start')" html-for="fiscal_year_start_month">
          <template #control>
            <Select id="fiscal_year_start_month" v-model="form.fiscal_year_start_month" :options="monthOptions" option-label="label" option-value="value" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.default_invoice_due_days')" :description="t('settings.default_invoice_due_days_help')" html-for="default_invoice_due_days">
          <template #control>
            <InputNumber id="default_invoice_due_days" v-model="form.default_invoice_due_days" :min="0" :max="365" :use-grouping="false" show-buttons />
          </template>
        </AppSettingRow>
      </AppPanel>

      <AppPanel :title="t('settings.section_default_prices')" :subtitle="t('settings.section_default_prices_subtitle')">
        <AppSettingRow :label="t('settings.default_price_cours')" :description="t('settings.default_price_help')" html-for="default_price_cours">
          <template #control>
            <InputNumber id="default_price_cours" v-model="form.default_price_cours" :min="0" :min-fraction-digits="2" :max-fraction-digits="2" suffix=" €" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.default_price_adhesion')" html-for="default_price_adhesion">
          <template #control>
            <InputNumber id="default_price_adhesion" v-model="form.default_price_adhesion" :min="0" :min-fraction-digits="2" :max-fraction-digits="2" suffix=" €" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.default_price_autres')" html-for="default_price_autres">
          <template #control>
            <InputNumber id="default_price_autres" v-model="form.default_price_autres" :min="0" :min-fraction-digits="2" :max-fraction-digits="2" suffix=" €" />
          </template>
        </AppSettingRow>
      </AppPanel>

      <SettingsSaveBar :dirty="accDirty" :loading="savingAcc" @save="saveAcc" @cancel="revert" />

      <!-- Opening balances (self-managed) -->
      <SettingsSystemOpeningPanel />
    </section>

    <!-- ───────── Communication ───────── -->
    <section v-show="activeTab === 'communication'" class="settings-section">
      <AppPanel :title="t('settings.section_smtp')" :subtitle="t('settings.section_smtp_subtitle')">
        <AppSettingRow :label="t('settings.smtp_host')" html-for="smtp_host">
          <template #control>
            <InputText id="smtp_host" v-model="form.smtp_host" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.smtp_port')" html-for="smtp_port">
          <template #control>
            <InputNumber id="smtp_port" v-model="form.smtp_port" :min="1" :max="65535" :use-grouping="false" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.smtp_username')" html-for="smtp_user">
          <template #control>
            <InputText id="smtp_user" v-model="form.smtp_user" autocomplete="username" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.smtp_password')" html-for="smtp_password">
          <template #control>
            <Password id="smtp_password" v-model="form.smtp_password" :placeholder="t('settings.smtp_password_placeholder')" :feedback="false" toggle-mask />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.smtp_from')" html-for="smtp_from_email">
          <template #control>
            <InputText id="smtp_from_email" v-model="form.smtp_from_email" type="email" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.smtp_bcc')" :description="t('settings.smtp_bcc_help')" html-for="smtp_bcc">
          <template #control>
            <InputText id="smtp_bcc" v-model="form.smtp_bcc" type="email" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.smtp_use_tls')" html-for="smtp_use_tls">
          <template #control>
            <ToggleSwitch id="smtp_use_tls" v-model="form.smtp_use_tls" />
          </template>
        </AppSettingRow>
      </AppPanel>

      <AppPanel :title="t('settings.section_email_templates')" :subtitle="t('settings.section_email_templates_subtitle')">
        <AppSettingRow :label="t('settings.email_subject_template')" :description="emailVarsHelp" html-for="email_subject_template">
          <template #control>
            <InputText id="email_subject_template" v-model="form.email_subject_template" :placeholder="t('settings.email_subject_template_placeholder')" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.email_body_template')" :description="emailVarsHelp" html-for="email_body_template">
          <template #control>
            <Textarea id="email_body_template" v-model="form.email_body_template" rows="7" auto-resize />
          </template>
        </AppSettingRow>
      </AppPanel>

      <AppPanel :title="t('settings.section_reminder_templates')" :subtitle="t('settings.section_reminder_templates_subtitle')">
        <AppSettingRow :label="t('settings.reminder_first_subject_template')" :description="reminderVarsHelp" html-for="reminder_first_subject_template">
          <template #control>
            <InputText id="reminder_first_subject_template" v-model="form.reminder_first_subject_template" :placeholder="t('settings.reminder_first_subject_template_placeholder')" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.reminder_first_body_template')" :description="reminderVarsHelp" html-for="reminder_first_body_template">
          <template #control>
            <Textarea id="reminder_first_body_template" v-model="form.reminder_first_body_template" rows="6" auto-resize />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.reminder_next_subject_template')" :description="reminderVarsHelp" html-for="reminder_next_subject_template">
          <template #control>
            <InputText id="reminder_next_subject_template" v-model="form.reminder_next_subject_template" :placeholder="t('settings.reminder_next_subject_template_placeholder')" />
          </template>
        </AppSettingRow>
        <AppSettingRow :label="t('settings.reminder_next_body_template')" :description="reminderVarsHelp" html-for="reminder_next_body_template">
          <template #control>
            <Textarea id="reminder_next_body_template" v-model="form.reminder_next_body_template" rows="6" auto-resize />
          </template>
        </AppSettingRow>
      </AppPanel>

      <SettingsSaveBar :dirty="comDirty" :loading="savingCom" @save="saveCom" @cancel="revert" />

      <!-- AI assistant (self-managed) -->
      <SettingsChatPanel />
    </section>

    <!-- ───────── Zone dangereuse ───────── -->
    <section v-show="activeTab === 'danger'" class="settings-section">
      <SettingsDangerZonePanel />
    </section>

    <Message v-if="errorMessage" severity="error" class="mt-4" :closable="true">{{ errorMessage }}</Message>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Password from 'primevue/password'
import ToggleSwitch from 'primevue/toggleswitch'
import Tag from 'primevue/tag'
import Message from 'primevue/message'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppSettingRow from '@/components/ui/AppSettingRow.vue'
import SettingsSaveBar from '@/components/settings/SettingsSaveBar.vue'
import SettingsSystemOpeningPanel from '@/components/settings/SettingsSystemOpeningPanel.vue'
import SettingsChatPanel from '@/components/settings/SettingsChatPanel.vue'
import SettingsDangerZonePanel from '@/components/settings/SettingsDangerZonePanel.vue'
import { getSettingsApi, updateSettingsApi } from '@/api/settings'

const { t } = useI18n()
const toast = useToast()

const activeTab = ref<'organisation' | 'comptabilite' | 'communication' | 'danger'>('organisation')

interface SettingsForm {
  association_name: string
  association_siret: string
  association_address: string
  payment_iban: string
  payment_bic: string
  payment_check_payee: string
  bank_account_courant_acctid: string
  bank_account_epargne_acctid: string
  list_default_limit: number
  fiscal_year_start_month: number
  default_invoice_due_days: number | null
  client_invoice_seq_digits: number
  client_invoice_number_template: string
  supplier_invoice_number_template: string
  cheque_number_template: string
  default_price_cours: number | null
  default_price_adhesion: number | null
  default_price_autres: number | null
  smtp_host: string | null
  smtp_port: number
  smtp_user: string | null
  smtp_password: string | null
  smtp_from_email: string | null
  smtp_use_tls: boolean
  smtp_bcc: string | null
  email_subject_template: string | null
  email_body_template: string | null
  reminder_first_subject_template: string | null
  reminder_first_body_template: string | null
  reminder_next_subject_template: string | null
  reminder_next_body_template: string | null
}

function defaultForm(): SettingsForm {
  return {
    association_name: '',
    association_siret: '',
    association_address: '',
    payment_iban: '',
    payment_bic: '',
    payment_check_payee: '',
    bank_account_courant_acctid: '',
    bank_account_epargne_acctid: '',
    list_default_limit: 500,
    fiscal_year_start_month: 8,
    default_invoice_due_days: null,
    client_invoice_seq_digits: 3,
    client_invoice_number_template: '{year}-{seq}',
    supplier_invoice_number_template: 'FF-%Y%m%d%H.%M.%S',
    cheque_number_template: '{date}.{seq}',
    default_price_cours: null,
    default_price_adhesion: null,
    default_price_autres: null,
    smtp_host: null,
    smtp_port: 587,
    smtp_user: null,
    smtp_password: null,
    smtp_from_email: null,
    smtp_use_tls: true,
    smtp_bcc: null,
    email_subject_template: null,
    email_body_template: null,
    reminder_first_subject_template: null,
    reminder_first_body_template: null,
    reminder_next_subject_template: null,
    reminder_next_body_template: null,
  }
}

const form = reactive<SettingsForm>(defaultForm())
// Baseline snapshot (excludes the write-only smtp_password) for dirty tracking.
let baseline: Omit<SettingsForm, 'smtp_password'> = snapshot()
const savingOrg = ref(false)
const savingAcc = ref(false)
const savingCom = ref(false)
const errorMessage = ref('')

const ORG_FIELDS = [
  'association_name',
  'association_siret',
  'association_address',
  'payment_iban',
  'payment_bic',
  'payment_check_payee',
  'bank_account_courant_acctid',
  'bank_account_epargne_acctid',
  'list_default_limit',
] as const
const ACC_FIELDS = [
  'fiscal_year_start_month',
  'default_invoice_due_days',
  'client_invoice_seq_digits',
  'client_invoice_number_template',
  'supplier_invoice_number_template',
  'cheque_number_template',
  'default_price_cours',
  'default_price_adhesion',
  'default_price_autres',
] as const
const COM_FIELDS = [
  'smtp_host',
  'smtp_port',
  'smtp_user',
  'smtp_from_email',
  'smtp_use_tls',
  'smtp_bcc',
  'email_subject_template',
  'email_body_template',
  'reminder_first_subject_template',
  'reminder_first_body_template',
  'reminder_next_subject_template',
  'reminder_next_body_template',
] as const

function snapshot(): Omit<SettingsForm, 'smtp_password'> {
  const rest = { ...form } as Partial<SettingsForm>
  delete rest.smtp_password
  return structuredClone(rest) as Omit<SettingsForm, 'smtp_password'>
}

function fieldsDirty(keys: readonly (keyof SettingsForm)[]): boolean {
  return keys.some(
    (k) => JSON.stringify(form[k]) !== JSON.stringify((baseline as Record<string, unknown>)[k]),
  )
}

const orgDirty = computed(() => fieldsDirty(ORG_FIELDS))
const accDirty = computed(() => fieldsDirty(ACC_FIELDS))
const comDirty = computed(() => fieldsDirty(COM_FIELDS) || Boolean(form.smtp_password))

const emailVarsHelp = computed(() =>
  t('settings.email_template_vars_help', {
    v1: '{invoice_number}',
    v2: '{description}',
    v3: '{association_name}',
    v4: '{invoice_ref}',
  }),
)

const reminderVarsHelp = computed(() =>
  t('settings.reminder_template_vars_help', {
    v1: '{invoice_ref}',
    v2: '{montant_du}',
    v3: '{echeance}',
    v4: '{derniere_relance}',
    v5: '{nombre_de_relances}',
    v6: '{association_name}',
  }),
)

const monthFormatter = new Intl.DateTimeFormat('fr-FR', { month: 'long' })
const monthOptions = Array.from({ length: 12 }, (_, i) => {
  const label = monthFormatter.format(new Date(2000, i, 1))
  return { label: label.charAt(0).toUpperCase() + label.slice(1), value: i + 1 }
})

const invoicePreview = computed(() => {
  const tpl = form.client_invoice_number_template || '{year}-{seq}'
  const year = new Date().getFullYear()
  const seq = String(13).padStart(form.client_invoice_seq_digits || 3, '0')
  return tpl.replace('{year}', String(year)).replace('{seq}', seq)
})

async function load(): Promise<void> {
  try {
    const data = await getSettingsApi()
    Object.assign(form, {
      association_name: data.association_name,
      association_siret: data.association_siret,
      association_address: data.association_address,
      payment_iban: data.payment_iban ?? '',
      payment_bic: data.payment_bic ?? '',
      payment_check_payee: data.payment_check_payee ?? '',
      bank_account_courant_acctid: data.bank_account_courant_acctid ?? '',
      bank_account_epargne_acctid: data.bank_account_epargne_acctid ?? '',
      list_default_limit: data.list_default_limit ?? 500,
      fiscal_year_start_month: data.fiscal_year_start_month,
      default_invoice_due_days: data.default_invoice_due_days,
      client_invoice_seq_digits: data.client_invoice_seq_digits,
      client_invoice_number_template: data.client_invoice_number_template,
      supplier_invoice_number_template: data.supplier_invoice_number_template,
      cheque_number_template: data.cheque_number_template ?? '{date}.{seq}',
      default_price_cours: data.default_price_cours,
      default_price_adhesion: data.default_price_adhesion,
      default_price_autres: data.default_price_autres,
      smtp_host: data.smtp_host,
      smtp_port: data.smtp_port,
      smtp_user: data.smtp_user,
      smtp_password: null,
      smtp_from_email: data.smtp_from_email,
      smtp_use_tls: data.smtp_use_tls,
      smtp_bcc: data.smtp_bcc,
      email_subject_template: data.email_subject_template,
      email_body_template: data.email_body_template,
      reminder_first_subject_template: data.reminder_first_subject_template,
      reminder_first_body_template: data.reminder_first_body_template,
      reminder_next_subject_template: data.reminder_next_subject_template,
      reminder_next_body_template: data.reminder_next_body_template,
    })
    baseline = snapshot()
  } catch {
    errorMessage.value = t('common.error.unknown')
  }
}

function revert(): void {
  Object.assign(form, baseline, { smtp_password: null })
}

async function runSave(
  saving: { value: boolean },
  payload: Parameters<typeof updateSettingsApi>[0],
): Promise<void> {
  saving.value = true
  errorMessage.value = ''
  try {
    await updateSettingsApi(payload)
    baseline = snapshot()
    toast.add({ severity: 'success', summary: t('settings.saved'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('settings.save_error'), life: 4000 })
  } finally {
    saving.value = false
  }
}

function saveOrg(): Promise<void> {
  return runSave(savingOrg, {
    association_name: form.association_name,
    association_siret: form.association_siret,
    association_address: form.association_address,
    payment_iban: form.payment_iban || null,
    payment_bic: form.payment_bic || null,
    payment_check_payee: form.payment_check_payee || null,
    bank_account_courant_acctid: form.bank_account_courant_acctid || null,
    bank_account_epargne_acctid: form.bank_account_epargne_acctid || null,
    list_default_limit: form.list_default_limit,
  })
}

function saveAcc(): Promise<void> {
  return runSave(savingAcc, {
    fiscal_year_start_month: form.fiscal_year_start_month,
    default_invoice_due_days: form.default_invoice_due_days,
    client_invoice_seq_digits: form.client_invoice_seq_digits,
    client_invoice_number_template: form.client_invoice_number_template,
    supplier_invoice_number_template: form.supplier_invoice_number_template,
    cheque_number_template: form.cheque_number_template || '{date}.{seq}',
    default_price_cours: form.default_price_cours,
    default_price_adhesion: form.default_price_adhesion,
    default_price_autres: form.default_price_autres,
  })
}

async function saveCom(): Promise<void> {
  const payload: Parameters<typeof updateSettingsApi>[0] = {
    smtp_host: form.smtp_host,
    smtp_port: form.smtp_port,
    smtp_user: form.smtp_user,
    smtp_from_email: form.smtp_from_email,
    smtp_use_tls: form.smtp_use_tls,
    smtp_bcc: form.smtp_bcc,
    email_subject_template: form.email_subject_template?.trim() || null,
    email_body_template: form.email_body_template?.trim() || null,
    reminder_first_subject_template: form.reminder_first_subject_template?.trim() || null,
    reminder_first_body_template: form.reminder_first_body_template?.trim() || null,
    reminder_next_subject_template: form.reminder_next_subject_template?.trim() || null,
    reminder_next_body_template: form.reminder_next_body_template?.trim() || null,
  }
  if (form.smtp_password) {
    payload.smtp_password = form.smtp_password
  }
  await runSave(savingCom, payload)
  form.smtp_password = null
}

onMounted(() => {
  void load()
})
</script>

<style scoped>
.settings-section {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-5);
}

.settings-tab--danger {
  color: var(--p-red-500, #dc2626);
}

.settings-template-control {
  display: flex;
  align-items: center;
  gap: var(--app-space-2);
}

.settings-mono :deep(input),
.settings-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
</style>
