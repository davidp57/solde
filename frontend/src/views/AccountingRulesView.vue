<template>
  <div class="view-container">
    <div class="view-header">
      <h1>{{ t('accounting.rules.title') }}</h1>
      <Button
        :label="t('accounting.rules.seed')"
        icon="pi pi-download"
        :loading="seeding"
        @click="seedRules"
      />
    </div>

    <div class="mb-4">
      <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" class="w-64" />
    </div>

    <DataTable :value="filtered" :loading="loading" striped-rows>
      <Column field="trigger_type" :header="t('accounting.rules.trigger_type')" />
      <Column field="name" :header="t('accounting.rules.name')" />
      <Column field="is_active" :header="t('accounting.rules.active')">
        <template #body="{ data }">
          <Tag
            :value="data.is_active ? t('accounting.rules.active') : t('accounting.rules.inactive')"
            :severity="data.is_active ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column field="priority" :header="t('accounting.rules.priority')" />
      <Column :header="t('common.actions')">
        <template #body="{ data }">
          <Button
            :icon="data.is_active ? 'pi pi-eye-slash' : 'pi pi-eye'"
            :severity="data.is_active ? 'secondary' : 'success'"
            text
            rounded
            :title="data.is_active ? t('accounting.rules.deactivate') : t('accounting.rules.activate')"
            @click="toggleRule(data)"
          />
        </template>
      </Column>
      <template #empty>{{ t('accounting.balance.empty') }}</template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import {
  listRulesApi,
  updateRuleApi,
  seedRulesApi,
  type AccountingRuleRead,
} from '../api/accounting'
import { useTableFilter } from '../composables/useTableFilter'

const { t } = useI18n()
const toast = useToast()

const rules = ref<AccountingRuleRead[]>([])
const { filterText, filtered } = useTableFilter(rules)
const loading = ref(false)
const seeding = ref(false)

async function load() {
  loading.value = true
  try {
    rules.value = await listRulesApi()
  } finally {
    loading.value = false
  }
}

async function toggleRule(rule: AccountingRuleRead) {
  try {
    const updated = await updateRuleApi(rule.id, { is_active: !rule.is_active })
    const idx = rules.value.findIndex((r) => r.id === rule.id)
    if (idx !== -1) rules.value[idx] = updated
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  }
}

async function seedRules() {
  seeding.value = true
  try {
    const result = await seedRulesApi()
    if (result.inserted > 0) {
      toast.add({ severity: 'success', summary: t('accounting.rules.seed_ok', { n: result.inserted }), life: 3000 })
    } else {
      toast.add({ severity: 'info', summary: t('accounting.rules.seed_already_done'), life: 3000 })
    }
    await load()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    seeding.value = false
  }
}

onMounted(load)
</script>
