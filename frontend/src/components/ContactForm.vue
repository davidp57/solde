<template>
  <form class="app-dialog-form" @submit.prevent="submit">
    <section class="app-dialog-intro">
      <p class="app-dialog-intro__eyebrow">{{ t('contacts.title') }}</p>
      <p class="app-dialog-intro__text">
        {{ t(isEditing ? 'contacts.form_intro_edit' : 'contacts.form_intro_create') }}
      </p>
    </section>

    <section class="app-dialog-section">
      <div class="app-dialog-section__header">
        <h3 class="app-dialog-section__title">{{ t('contacts.identity_title') }}</h3>
        <p class="app-dialog-section__copy">{{ t('contacts.identity_subtitle') }}</p>
      </div>
      <div class="contact-form">
        <div class="app-field">
          <label for="cf-type" class="app-field__label">{{ t('contacts.type') }} *</label>
          <Select
            id="cf-type"
            v-model="form.type"
            :options="typeOptions"
            option-label="label"
            option-value="value"
            class="w-full"
          />
        </div>

        <div class="app-form-grid">
          <div class="app-field">
            <label for="cf-nom" class="app-field__label">{{ t('contacts.nom') }} *</label>
            <InputText
              id="cf-nom"
              v-model="form.nom"
              :placeholder="t('contacts.nom')"
              required
              class="w-full"
            />
            <small v-if="fieldErrors['nom']" class="p-error">{{ fieldErrors['nom'] }}</small>
          </div>
          <div class="app-field">
            <label for="cf-prenom" class="app-field__label">{{ t('contacts.prenom') }}</label>
            <InputText
              id="cf-prenom"
              v-model="form.prenom"
              :placeholder="t('contacts.prenom')"
              class="w-full"
            />
          </div>
        </div>
      </div>
    </section>

    <section class="app-dialog-section">
      <div class="app-dialog-section__header">
        <h3 class="app-dialog-section__title">{{ t('contacts.contact_title') }}</h3>
        <p class="app-dialog-section__copy">{{ t('contacts.contact_subtitle') }}</p>
      </div>
      <div class="contact-form">
        <div class="app-field">
          <label for="cf-email" class="app-field__label">{{ t('contacts.email') }}</label>
          <InputText
            id="cf-email"
            v-model="form.email"
            type="email"
            :placeholder="t('contacts.email')"
            class="w-full"
          />
          <small v-if="fieldErrors['email']" class="p-error">{{ fieldErrors['email'] }}</small>
        </div>

        <div class="app-field">
          <label for="cf-tel" class="app-field__label">{{ t('contacts.telephone') }}</label>
          <InputText
            id="cf-tel"
            v-model="form.telephone"
            :placeholder="t('contacts.telephone')"
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="cf-adresse" class="app-field__label">{{ t('contacts.adresse') }}</label>
          <Textarea
            id="cf-adresse"
            v-model="form.adresse"
            :placeholder="t('contacts.adresse')"
            rows="2"
            class="w-full"
          />
        </div>

        <div class="app-field">
          <label for="cf-notes" class="app-field__label">{{ t('contacts.notes') }}</label>
          <Textarea
            id="cf-notes"
            v-model="form.notes"
            :placeholder="t('contacts.notes')"
            rows="2"
            class="w-full"
          />
          <small class="app-dialog-note">{{ t('contacts.notes_help') }}</small>
        </div>

        <div class="app-field">
          <label class="app-field__label">{{ t('employees.is_contractor') }}</label>
          <ToggleSwitch v-model="form.is_contractor" />
          <small class="app-dialog-note">{{ t('employees.is_contractor_help') }}</small>
        </div>
      </div>
    </section>

    <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

    <div class="app-form-actions">
      <Button
        type="button"
        :label="t('common.cancel')"
        severity="secondary"
        :disabled="saving"
        @click="$emit('cancel')"
      />
      <Button type="submit" :label="t('common.save')" :loading="saving" icon="pi pi-check" />
    </div>
  </form>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { createContactApi, updateContactApi, type Contact } from '@/api/contacts'
import type { ContactType } from '@/api/types'

const props = defineProps<{ contact: Contact | null }>()
const emit = defineEmits<{ saved: []; cancel: [] }>()

const { t } = useI18n()

const typeOptions = [
  { label: t('contacts.types.client'), value: 'client' as ContactType },
  { label: t('contacts.types.fournisseur'), value: 'fournisseur' as ContactType },
  { label: t('contacts.types.les_deux'), value: 'les_deux' as ContactType },
]

interface FormState {
  type: ContactType
  nom: string
  prenom: string
  email: string
  telephone: string
  adresse: string
  notes: string
  is_contractor: boolean
}

function fromContact(c: Contact | null): FormState {
  return {
    type: c?.type ?? 'client',
    nom: c?.nom ?? '',
    prenom: c?.prenom ?? '',
    email: c?.email ?? '',
    telephone: c?.telephone ?? '',
    adresse: c?.adresse ?? '',
    notes: c?.notes ?? '',
    is_contractor: c?.is_contractor ?? false,
  }
}

const form = ref<FormState>(fromContact(props.contact))
const saving = ref(false)
const errorMessage = ref('')
const fieldErrors = ref<Record<string, string>>({})
const initialSnapshot = ref(JSON.stringify(fromContact(props.contact)))
const isDirty = computed(() => JSON.stringify(form.value) !== initialSnapshot.value)
const isEditing = computed(() => props.contact !== null)

watch(
  () => props.contact,
  (c) => {
    form.value = fromContact(c)
    errorMessage.value = ''
    fieldErrors.value = {}
    initialSnapshot.value = JSON.stringify(fromContact(c))
  },
)

async function submit(): Promise<void> {
  saving.value = true
  errorMessage.value = ''
  fieldErrors.value = {}
  try {
    const payload = {
      type: form.value.type,
      nom: form.value.nom,
      prenom: form.value.prenom || null,
      email: form.value.email || null,
      telephone: form.value.telephone || null,
      adresse: form.value.adresse || null,
      notes: form.value.notes || null,
      is_contractor: form.value.is_contractor,
    }
    if (props.contact) {
      await updateContactApi(props.contact.id, payload)
    } else {
      await createContactApi(payload)
    }
    emit('saved')
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 422) {
      const detail = error.response.data?.detail
      if (Array.isArray(detail)) {
        const errors: Record<string, string> = {}
        for (const item of detail) {
          if (Array.isArray(item.loc) && item.loc.length > 0) {
            errors[String(item.loc[item.loc.length - 1])] = item.msg
          }
        }
        fieldErrors.value = errors
      } else {
        errorMessage.value = t('common.error.unknown')
      }
    } else {
      errorMessage.value = t('common.error.unknown')
    }
  } finally {
    saving.value = false
  }
}

defineExpose({ submit, isDirty })
</script>

<style scoped>
.contact-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-5);
}
</style>
