<template>
  <AppPage width="wide">
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="contactName || t('contact_history.title')"
    >
      <template #actions>
        <Button icon="pi pi-arrow-left" severity="secondary" text @click="$router.back()" />
      </template>
    </AppPageHeader>

    <ContactHistoryContent
      :contact-id="Number(route.params.id)"
      @contact-loaded="contactName = $event"
    />
  </AppPage>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import ContactHistoryContent from '../components/ContactHistoryContent.vue'

const { t } = useI18n()
const route = useRoute()
const contactName = ref('')
</script>