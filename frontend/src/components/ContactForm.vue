<template>
  <form @submit.prevent="submit">
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-1">
        <label for="cf-type" class="font-medium text-sm">{{ t('contacts.type') }} *</label>
        <Select
          id="cf-type"
          v-model="form.type"
          :options="typeOptions"
          option-label="label"
          option-value="value"
          class="w-full"
        />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1">
          <label for="cf-nom" class="font-medium text-sm">{{ t('contacts.nom') }} *</label>
          <InputText
            id="cf-nom"
            v-model="form.nom"
            :placeholder="t('contacts.nom')"
            required
            class="w-full"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label for="cf-prenom" class="font-medium text-sm">{{ t('contacts.prenom') }}</label>
          <InputText
            id="cf-prenom"
            v-model="form.prenom"
            :placeholder="t('contacts.prenom')"
            class="w-full"
          />
        </div>
      </div>

      <div class="flex flex-col gap-1">
        <label for="cf-email" class="font-medium text-sm">{{ t('contacts.email') }}</label>
        <InputText
          id="cf-email"
          v-model="form.email"
          type="email"
          :placeholder="t('contacts.email')"
          class="w-full"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label for="cf-tel" class="font-medium text-sm">{{ t('contacts.telephone') }}</label>
        <InputText
          id="cf-tel"
          v-model="form.telephone"
          :placeholder="t('contacts.telephone')"
          class="w-full"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label for="cf-adresse" class="font-medium text-sm">{{ t('contacts.adresse') }}</label>
        <Textarea
          id="cf-adresse"
          v-model="form.adresse"
          :placeholder="t('contacts.adresse')"
          rows="2"
          class="w-full"
        />
      </div>

      <div class="flex flex-col gap-1">
        <label for="cf-notes" class="font-medium text-sm">{{ t('contacts.notes') }}</label>
        <Textarea
          id="cf-notes"
          v-model="form.notes"
          :placeholder="t('contacts.notes')"
          rows="2"
          class="w-full"
        />
      </div>

      <Message v-if="errorMessage" severity="error">{{ errorMessage }}</Message>

      <div class="flex justify-end gap-2 pt-2">
        <Button
          type="button"
          :label="t('common.cancel')"
          severity="secondary"
          :disabled="saving"
          @click="$emit('cancel')"
        />
        <Button
          type="submit"
          :label="t('common.save')"
          :loading="saving"
          icon="pi pi-check"
        />
      </div>
    </div>
  </form>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
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
  }
}

const form = ref<FormState>(fromContact(props.contact))
const saving = ref(false)
const errorMessage = ref('')

watch(
  () => props.contact,
  (c) => {
    form.value = fromContact(c)
    errorMessage.value = ''
  },
)

async function submit(): Promise<void> {
  saving.value = true
  errorMessage.value = ''
  try {
    const payload = {
      type: form.value.type,
      nom: form.value.nom,
      prenom: form.value.prenom || null,
      email: form.value.email || null,
      telephone: form.value.telephone || null,
      adresse: form.value.adresse || null,
      notes: form.value.notes || null,
    }
    if (props.contact) {
      await updateContactApi(props.contact.id, payload)
    } else {
      await createContactApi(payload)
    }
    emit('saved')
  } catch {
    errorMessage.value = t('common.error.unknown')
  } finally {
    saving.value = false
  }
}
</script>
