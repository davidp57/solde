<template>
  <AppPage>
    <AppPageHeader
      :eyebrow="t('ui.page.collection_eyebrow')"
      :title="t('settings.title')"
      :subtitle="t('settings.subtitle')"
    />
    <SettingsAssociationSmtpPanel />
    <SettingsSystemOpeningPanel />
    <SettingsBackupPanel />
    <SettingsDangerZonePanel />
  </AppPage>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import SettingsAssociationSmtpPanel from '@/components/settings/SettingsAssociationSmtpPanel.vue'
import SettingsSystemOpeningPanel from '@/components/settings/SettingsSystemOpeningPanel.vue'
import SettingsBackupPanel from '@/components/settings/SettingsBackupPanel.vue'
import SettingsDangerZonePanel from '@/components/settings/SettingsDangerZonePanel.vue'

const { t } = useI18n()
</script>

