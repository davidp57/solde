<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.accounting_eyebrow')" :title="t('accounting.rules.title')">
      <template #actions>
        <Button
          :label="t('accounting.rules.seed')"
          icon="pi pi-download"
          severity="secondary"
          :loading="seeding"
          @click="seedRules"
        />
      </template>
    </AppPageHeader>

    <AppPanel :title="t('accounting.rules.title')" dense>
      <div class="app-toolbar">
        <div class="app-toolbar__meta">
          <AppListState
            :displayed-count="displayedRules.length"
            :total-count="rules.length"
            :loading="loading"
            :search-text="filterText"
          />
          <Button
            :label="t('common.reset_filters')"
            icon="pi pi-filter-slash"
            severity="secondary"
            outlined
            size="small"
            :disabled="!hasActiveFilters"
            @click="resetFilters"
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
        v-model:filters="tableFilters"
        :value="ruleRows"
        :loading="loading"
        class="app-data-table"
        filter-display="menu"
        striped-rows
        paginator
        :rows="20"
        :rows-per-page-options="[20, 50, 100, 500]"
        size="small"
        row-hover
        :global-filter-fields="['trigger_type', 'name', 'is_active', 'priority']"
        removable-sort
        @value-change="syncDisplayedRules"
      >
        <Column
          field="trigger_type"
          :header="t('accounting.rules.trigger_type')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="triggerTypeOptions"
              :placeholder="t('common.all')"
              display="chip"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="name"
          :header="t('accounting.rules.name')"
          sortable
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" :placeholder="t('accounting.rules.name')" />
          </template>
        </Column>
        <Column
          field="is_active_label"
          :header="t('accounting.rules.active')"
          sortable
          filter-field="is_active"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #body="{ data }">
            <Tag
              :value="
                data.is_active ? t('accounting.rules.active') : t('accounting.rules.inactive')
              "
              :severity="data.is_active ? 'success' : 'secondary'"
            />
          </template>
          <template #filter="{ filterModel }">
            <AppFilterMultiSelect
              v-model="filterModel.value"
              :options="yesNoOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.all')"
              display="chip"
              show-clear
            />
          </template>
        </Column>
        <Column
          field="priority"
          :header="t('accounting.rules.priority')"
          sortable
          data-type="numeric"
          :show-filter-match-modes="false"
          :show-add-button="false"
        >
          <template #filter="{ filterModel }">
            <AppNumberRangeFilter v-model="filterModel.value" />
          </template>
        </Column>
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
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppListState from '../components/ui/AppListState.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import {
  listRulesApi,
  updateRuleApi,
  seedRulesApi,
  type AccountingRuleRead,
} from '../api/accounting'
import {
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'

const { t } = useI18n()
const toast = useToast()

const rules = ref<AccountingRuleRead[]>([])
const loading = ref(false)
const seeding = ref(false)
const ruleRows = ref<Array<AccountingRuleRead & { is_active_label: string }>>([])
const triggerTypeOptions = ref<Array<{ label: string; value: string }>>([])
const yesNoOptions = [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
]
const {
  filters: tableFilters,
  globalFilter: filterText,
  displayedRows: displayedRules,
  syncDisplayedRows: syncDisplayedRules,
  resetFilters,
  hasActiveFilters,
} = useDataTableFilters(ruleRows, {
  global: textFilter(''),
  trigger_type: inFilter(),
  name: textFilter(),
  is_active: inFilter(),
  priority: numericRangeFilter(),
})

async function load() {
  loading.value = true
  try {
    rules.value = await listRulesApi()
    ruleRows.value = rules.value.map((rule) => ({
      ...rule,
      is_active_label: rule.is_active ? t('common.yes') : t('common.no'),
    }))
    triggerTypeOptions.value = Array.from(
      new Set(rules.value.map((rule) => rule.trigger_type)),
    ).map((value) => ({ label: value, value }))
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
