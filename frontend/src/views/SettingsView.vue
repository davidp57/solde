<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('settings.title')"
      :subtitle="t('settings.subtitle')"
    />
    <SettingsAssociationPanel />
    <SettingsSmtpPanel />
    <SettingsSystemOpeningPanel />
    <SettingsChatPanel />
    <SettingsDangerZonePanel />
  </AppPage>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import SettingsAssociationPanel from '@/components/settings/SettingsAssociationPanel.vue'
import SettingsSmtpPanel from '@/components/settings/SettingsSmtpPanel.vue'
import SettingsChatPanel from '@/components/settings/SettingsChatPanel.vue'
import SettingsSystemOpeningPanel from '@/components/settings/SettingsSystemOpeningPanel.vue'
import SettingsDangerZonePanel from '@/components/settings/SettingsDangerZonePanel.vue'

const { t } = useI18n()
</script>

