<template>
  <Dialog
    v-model:visible="visible"
    :header="contactName || '…'"
    modal
    class="app-dialog app-dialog--xlarge"
    :style="{ width: 'min(90vw, 1100px)' }"
  >
    <ContactHistoryContent
      v-if="visible && props.contactId !== null"
      :contact-id="props.contactId!"
      @contact-loaded="contactName = $event"
    />
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import ContactHistoryContent from './ContactHistoryContent.vue'

const visible = defineModel<boolean>({ required: true })
const props = defineProps<{ contactId: number | null }>()

const contactName = ref('')

watch(visible, (v) => {
  if (!v) contactName.value = ''
})
</script>
