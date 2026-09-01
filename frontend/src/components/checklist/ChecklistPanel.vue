<template>
  <Drawer
    :visible="store.panelVisible"
    :header="headerLabel"
    position="right"
    :modal="false"
    :dismissable="false"
    class="checklist-drawer"
    @update:visible="store.panelVisible = $event"
  >
    <!-- No session yet: offer to start the one today's date points at. -->
    <div v-if="!store.isOpen" class="app-dialog-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('checklist.title') }}</p>
        <p class="app-dialog-intro__text">{{ t('checklist.intro') }}</p>
      </section>
      <div class="app-field">
        <label class="app-field__label" for="checklist-period">
          {{ t('checklist.period') }}
        </label>
        <InputText id="checklist-period" v-model="periodDraft" placeholder="2026-09" />
      </div>
      <div class="app-form-actions">
        <Button
          :label="t('checklist.start', { period: formatPeriod(periodDraft) })"
          :loading="busy"
          :disabled="!isValidPeriod"
          @click="start"
        />
      </div>
    </div>

    <!-- Closing: the recap of what has not been ticked, before confirming. -->
    <div v-else-if="confirmingClose" class="app-dialog-form">
      <section class="app-dialog-intro">
        <p class="app-dialog-intro__eyebrow">{{ t('checklist.close_title') }}</p>
        <p class="app-dialog-intro__text">
          {{ t('checklist.close_intro', { period: formatPeriod(store.session?.period ?? '') }) }}
        </p>
      </section>
      <Message v-if="uncheckedSteps.length === 0" severity="success">
        {{ t('checklist.close_complete') }}
      </Message>
      <template v-else>
        <Message severity="warn">
          {{ t('checklist.close_remaining', { count: uncheckedSteps.length }) }}
        </Message>
        <ul class="checklist-recap">
          <li v-for="step in uncheckedSteps" :key="step.key">
            {{ t(`checklist.steps.${step.key}`) }}
          </li>
        </ul>
      </template>
      <div class="app-form-actions">
        <Button
          :label="t('common.cancel')"
          severity="secondary"
          text
          @click="confirmingClose = false"
        />
        <Button :label="t('checklist.close_confirm')" :loading="busy" @click="close" />
      </div>
    </div>

    <!-- The session itself. -->
    <div v-else class="app-dialog-form checklist-body">
      <Message v-if="store.lateSteps.length" severity="warn" class="checklist-late">
        {{ t('checklist.late', { count: store.lateSteps.length }) }}
      </Message>

      <p class="checklist-progress">
        {{ t('checklist.progress', { done: store.checkedCount, total: store.steps.length }) }}
      </p>

      <section v-for="block in blocks" :key="block.name" class="checklist-block">
        <h3 class="checklist-block__title">{{ t(`checklist.blocks.${block.name}`) }}</h3>
        <div v-for="step in block.steps" :key="step.key" class="checklist-step">
          <Checkbox
            :input-id="`step-${step.key}`"
            :model-value="step.checked"
            binary
            :disabled="busy"
            @update:model-value="(value: boolean) => toggle(step.key, value)"
          />
          <div class="checklist-step__body">
            <label :for="`step-${step.key}`" class="checklist-step__label">
              <span v-if="step.external" class="checklist-step__external">⇢</span>
              {{ t(`checklist.steps.${step.key}`) }}
              <Tag
                v-if="step.carried_over && !step.checked"
                :value="t('checklist.late_tag')"
                severity="warn"
              />
            </label>
            <p v-if="signalText(step)" class="checklist-step__signal">{{ signalText(step) }}</p>
            <button
              v-if="step.route && !step.external"
              type="button"
              class="checklist-step__link"
              @click="goTo(step.route)"
            >
              {{ t('checklist.go_to_screen') }}
            </button>
          </div>
        </div>
      </section>

      <div class="app-form-actions">
        <Button
          :label="t('checklist.close_action')"
          severity="secondary"
          @click="confirmingClose = true"
        />
      </div>
    </div>
  </Drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Drawer from 'primevue/drawer'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import { useToast } from 'primevue/usetoast'
import type { ChecklistBlock, ChecklistStep } from '@/api/checklist'
import { useChecklistStore } from '@/stores/checklist'
import { formatCurrency, formatDisplayDate, formatDisplayMonth } from '@/utils/format'
import { getErrorDetail } from '@/utils/errorUtils'

const { t } = useI18n()
const router = useRouter()
const toast = useToast()
const store = useChecklistStore()

const busy = ref(false)
const confirmingClose = ref(false)
const periodDraft = ref('')

const isValidPeriod = computed(() => /^\d{4}-(0[1-9]|1[0-2])$/.test(periodDraft.value))

const headerLabel = computed(() =>
  store.isOpen
    ? t('checklist.header', { period: formatPeriod(store.session?.period ?? '') })
    : t('checklist.title'),
)

const uncheckedSteps = computed(() => store.steps.filter((s) => !s.checked))

/** Blocks in the order the steps declare them, empty ones left out. */
const blocks = computed(() => {
  const grouped: { name: ChecklistBlock; steps: ChecklistStep[] }[] = []
  for (const step of store.steps) {
    const last = grouped[grouped.length - 1]
    if (last && last.name === step.block) last.steps.push(step)
    else grouped.push({ name: step.block, steps: [step] })
  }
  return grouped
})

function formatPeriod(period: string): string {
  const label = formatDisplayMonth(period)
  return label ? label.charAt(0).toUpperCase() + label.slice(1) : period
}

/** The observed fact for a step, worded here — the API only returns the numbers. */
function signalText(step: ChecklistStep): string | null {
  if (!step.signal) return null
  const payload = store.signals[step.signal]
  if (!payload) return null
  const params: Record<string, string> = {}
  for (const [key, value] of Object.entries(payload)) {
    if (key === 'at' || key === 'date') params[key] = formatDisplayDate(String(value))
    else if (key === 'amount') params[key] = formatCurrency(String(value))
    else params[key] = String(value)
  }
  return t(`checklist.signals.${step.signal}`, params)
}

async function run(action: () => Promise<void>): Promise<void> {
  busy.value = true
  try {
    await action()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: getErrorDetail(error, t('common.error.unknown')),
      life: 4000,
    })
  } finally {
    busy.value = false
  }
}

async function start(): Promise<void> {
  await run(() => store.start(periodDraft.value))
}

async function toggle(stepKey: string, checked: boolean): Promise<void> {
  await run(() => store.toggle(stepKey, checked))
}

async function close(): Promise<void> {
  await run(async () => {
    await store.close()
    confirmingClose.value = false
    toast.add({ severity: 'success', summary: t('checklist.closed'), life: 3000 })
  })
}

function goTo(route: string): void {
  void router.push({ name: route })
  store.panelVisible = false
}

watch(
  () => store.panelVisible,
  (visible) => {
    if (!visible) {
      confirmingClose.value = false
      return
    }
    // The period is filled in *after* reloading: the suggestion depends on which
    // months have already been held, and a stale one offers an action that fails.
    void run(async () => {
      await store.load()
      periodDraft.value = store.suggestedPeriod
    })
  },
)
</script>

<style scoped>
.checklist-body {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.checklist-progress {
  margin: 0;
  font-weight: 600;
}

.checklist-block__title {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.75;
}

.checklist-step {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.35rem 0;
}

.checklist-step__body {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.checklist-step__label {
  cursor: pointer;
  line-height: 1.35;
}

.checklist-step__external {
  opacity: 0.7;
  margin-right: 0.25rem;
}

.checklist-step__signal {
  margin: 0;
  font-size: 0.82rem;
  opacity: 0.7;
}

.checklist-step__link {
  align-self: flex-start;
  padding: 0;
  border: none;
  background: none;
  color: var(--p-primary-color);
  font-size: 0.82rem;
  cursor: pointer;
}

.checklist-recap {
  margin: 0;
  padding-left: 1.2rem;
}
</style>
