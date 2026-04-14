<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.accounting_eyebrow')" :title="t('accounting.rules.title')">
      <template #actions>
        <Button
          :label="t('accounting.rules.seed')"
          icon="pi pi-download"
          :loading="seeding"
          @click="seedRules"
        />
      </template>
    </AppPageHeader>

    <AppPanel :title="t('accounting.rules.title')" dense>
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <AppListState
            :displayed-count="filtered.length"
            :total-count="rules.length"
            :loading="loading"
            :search-text="filterText"
          />
        </div>

        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="filterText" :placeholder="t('common.filter_placeholder')" />
          </div>
        </div>
      </div>

      <DataTable
        :value="filtered"
        :loading="loading"
        class="app-data-table"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        size="small"
        row-hover
      >
        <Column field="trigger_type" :header="t('accounting.rules.trigger_type')" sortable />
        <Column field="name" :header="t('accounting.rules.name')" sortable />
        <Column field="is_active" :header="t('accounting.rules.active')" sortable>
          <template #body="{ data }">
            <Tag
              :value="
                data.is_active ? t('accounting.rules.active') : t('accounting.rules.inactive')
              "
              :severity="data.is_active ? 'success' : 'secondary'"
            />
          </template>
        </Column>
        <Column field="priority" :header="t('accounting.rules.priority')" sortable />
        <Column :header="t('common.actions')">
          <template #body="{ data }">
            <Button
              :icon="data.is_active ? 'pi pi-eye-slash' : 'pi pi-eye'"
              :severity="data.is_active ? 'secondary' : 'success'"
              text
              rounded
              :title="
                data.is_active ? t('accounting.rules.deactivate') : t('accounting.rules.activate')
              "
              @click="toggleRule(data)"
            />
          </template>
        </Column>
        <template #empty
          ><div class="app-empty-state">{{ t('accounting.balance.empty') }}</div></template
        >
      </DataTable>
    </AppPanel>
  </AppPage>
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
import AppListState from '../components/ui/AppListState.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
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
      toast.add({
        severity: 'success',
        summary: t('accounting.rules.seed_ok', { n: result.inserted }),
        life: 3000,
      })
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
