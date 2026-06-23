<template>
  <Dialog
    :visible="visible"
    modal
    :header="t('contacts.mailing.title')"
    class="app-dialog app-dialog--large"
    @update:visible="(v: boolean) => emit('update:visible', v)"
    @show="reset"
  >
    <!-- Step 1 — period -->
    <div v-if="step === 1" class="member-mailing">
      <p class="member-mailing__intro">{{ t('contacts.mailing.step1_intro') }}</p>
      <div class="app-field">
        <label class="app-field__label">{{ t('contacts.mailing.months_label') }}</label>
        <InputNumber v-model="months" :min="1" :max="120" show-buttons data-testid="mm-months" />
      </div>
      <div class="app-form-actions">
        <Button :label="t('common.cancel')" severity="secondary" text @click="close" />
        <Button
          :label="t('contacts.mailing.load_recipients')"
          icon="pi pi-search"
          :loading="loading"
          data-testid="mm-load"
          @click="loadRecipients"
        />
      </div>
    </div>

    <!-- Step 2 — recipient selection (all preselected) -->
    <div v-else-if="step === 2" class="member-mailing">
      <p class="member-mailing__intro">
        {{ t('contacts.mailing.step2_intro', { count: clients.length }) }}
      </p>
      <DataTable
        v-model:selection="selected"
        :value="clients"
        data-key="id"
        class="app-data-table"
        paginator
        :rows="50"
        scrollable
        scroll-height="45vh"
        size="small"
      >
        <Column selection-mode="multiple" header-style="width:3rem" />
        <Column field="nom" :header="t('contacts.nom')">
          <template #body="{ data }">
            {{ data.nom }}<template v-if="data.prenom"> {{ data.prenom }}</template>
          </template>
        </Column>
        <Column field="email" :header="t('contacts.email')" />
        <template #empty>
          <div class="app-empty-state">{{ t('contacts.mailing.no_recipients') }}</div>
        </template>
      </DataTable>
      <div class="app-form-actions">
        <Button
          :label="t('common.previous')"
          icon="pi pi-arrow-left"
          severity="secondary"
          text
          @click="step = 1"
        />
        <span class="member-mailing__count">
          {{ t('contacts.mailing.selected_count', { count: selected.length }) }}
        </span>
        <Button
          :label="t('common.next')"
          icon="pi pi-arrow-right"
          :disabled="selected.length === 0"
          data-testid="mm-to-compose"
          @click="step = 3"
        />
      </div>
    </div>

    <!-- Step 3 — compose & send -->
    <div v-else class="member-mailing">
      <p class="member-mailing__intro">
        {{ t('contacts.mailing.step3_intro', { count: selected.length }) }}
      </p>
      <div class="app-field">
        <label class="app-field__label">{{ t('contacts.mailing.subject') }}</label>
        <InputText v-model="subject" data-testid="mm-subject" />
      </div>
      <div class="app-field">
        <label class="app-field__label">{{ t('contacts.mailing.body') }}</label>
        <Textarea v-model="body" rows="8" data-testid="mm-body" />
        <small class="app-dialog-note">{{ t('contacts.mailing.placeholders_help') }}</small>
      </div>
      <div class="app-form-actions">
        <Button
          :label="t('common.previous')"
          icon="pi pi-arrow-left"
          severity="secondary"
          text
          @click="step = 2"
        />
        <Button
          :label="t('contacts.mailing.send')"
          icon="pi pi-send"
          :loading="sending"
          :disabled="!subject.trim() || !body.trim()"
          data-testid="mm-send"
          @click="send"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import { listActiveClientsApi, sendMemberMailingApi, type ActiveClient } from '@/api/contacts'

defineProps<{ visible: boolean }>()
const emit = defineEmits<{ 'update:visible': [value: boolean]; sent: [] }>()

const { t } = useI18n()
const toast = useToast()

const step = ref<1 | 2 | 3>(1)
const months = ref(6)
const clients = ref<ActiveClient[]>([])
const selected = ref<ActiveClient[]>([])
const subject = ref('')
const body = ref('')
const loading = ref(false)
const sending = ref(false)

function reset(): void {
  step.value = 1
  months.value = 6
  clients.value = []
  selected.value = []
  subject.value = ''
  body.value = ''
}

function close(): void {
  emit('update:visible', false)
}

async function loadRecipients(): Promise<void> {
  loading.value = true
  try {
    clients.value = await listActiveClientsApi(months.value)
    selected.value = [...clients.value] // all preselected by default
    step.value = 2
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loading.value = false
  }
}

async function send(): Promise<void> {
  sending.value = true
  try {
    const result = await sendMemberMailingApi({
      contact_ids: selected.value.map((c) => c.id),
      subject: subject.value,
      body: body.value,
    })
    toast.add({
      severity: result.failed.length ? 'warn' : 'success',
      summary: t('contacts.mailing.sent_summary', {
        sent: result.sent,
        failed: result.failed.length,
      }),
      life: 5000,
    })
    emit('sent')
    close()
  } catch {
    toast.add({ severity: 'error', summary: t('contacts.mailing.send_error'), life: 4000 })
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.member-mailing {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.member-mailing__intro {
  margin: 0;
  color: var(--p-text-muted-color);
}

.member-mailing__count {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  margin-inline: auto;
}
</style>
