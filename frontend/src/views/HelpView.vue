<template>
  <AppPage width="wide">
    <AppPageHeader :title="t('help.title')" :subtitle="t('help.subtitle')">
      <template #actions>
        <Button
          :label="t('comments.leave_comment')"
          icon="pi pi-comment"
          severity="secondary"
          @click="commentDialogVisible = true"
        />
      </template>
    </AppPageHeader>

    <Tabs v-model:value="activeTab">
      <TabList>
        <Tab value="manual">{{ t('help.tab_manual') }}</Tab>
        <Tab value="changelog">{{ t('help.tab_changelog') }}</Tab>
      </TabList>

      <TabPanels>
        <!-- Onglet Manuel -->
        <TabPanel value="manual">
          <div v-if="loadingManual" class="help-loading">
            <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem" />
            <span>{{ t('help.loading') }}</span>
          </div>
          <Message v-else-if="errorManual" severity="error" :closable="false">
            {{ t('help.error') }}
          </Message>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div
            v-else
            class="help-content prose"
            v-html="renderedManual"
            @click="handleContentClick"
          />
        </TabPanel>

        <!-- Onglet Nouveautés -->
        <TabPanel value="changelog">
          <div v-if="loadingChangelog" class="help-loading">
            <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem" />
            <span>{{ t('help.changelog_loading') }}</span>
          </div>
          <Message v-else-if="errorChangelog" severity="error" :closable="false">
            {{ t('help.changelog_error') }}
          </Message>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div
            v-else
            class="help-content prose"
            v-html="renderedChangelog"
            @click="handleContentClick"
          />
        </TabPanel>
      </TabPanels>
    </Tabs>

    <Dialog
      v-model:visible="commentDialogVisible"
      :header="t('comments.title')"
      :modal="true"
      :closable="true"
      :draggable="false"
      style="width: 36rem"
    >
      <div class="comment-dialog__body">
        <p class="comment-dialog__subtitle">{{ t('comments.subtitle') }}</p>
        <Textarea
          v-model="newContent"
          :placeholder="t('comments.placeholder')"
          rows="5"
          class="w-full"
          :disabled="submitting"
          autofocus
        />
      </div>
      <template #footer>
        <Button
          :label="t('comments.cancel')"
          severity="secondary"
          text
          :disabled="submitting"
          @click="commentDialogVisible = false"
        />
        <Button
          :label="t('comments.submit')"
          icon="pi pi-send"
          :loading="submitting"
          :disabled="!newContent.trim()"
          @click="submitComment"
        />
      </template>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Message from 'primevue/message'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import Textarea from 'primevue/textarea'
import { useToast } from 'primevue/usetoast'
import { renderMarkdown } from '@/utils/renderMarkdown'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import { getManual, getChangelogUser } from '@/api/help'
import { createCommentApi } from '@/api/app_comment'

const { t } = useI18n()
const toast = useToast()

const activeTab = ref<string>('manual')

const manualText = ref('')
const loadingManual = ref(true)
const errorManual = ref(false)

const changelogText = ref('')
const loadingChangelog = ref(true)
const errorChangelog = ref(false)

const commentDialogVisible = ref(false)
const newContent = ref('')
const submitting = ref(false)

const renderedManual = computed(() => {
  if (!manualText.value) return ''
  return renderMarkdown(manualText.value)
})

const renderedChangelog = computed(() => {
  if (!changelogText.value) return ''
  return renderMarkdown(changelogText.value)
})

/**
 * Intercept clicks on rendered Markdown content.
 * - Anchor links (#section) → smooth-scroll within the page.
 * - External or router links → let the browser handle them normally.
 */
function handleContentClick(event: MouseEvent): void {
  const target = event.target as HTMLElement
  const anchor = target.closest('a') as HTMLAnchorElement | null
  if (!anchor) return

  const href = anchor.getAttribute('href')
  if (!href) return

  if (href.startsWith('#')) {
    event.preventDefault()
    const id = decodeURIComponent(href.slice(1))
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }
}

async function submitComment(): Promise<void> {
  if (!newContent.value.trim()) return
  submitting.value = true
  try {
    await createCommentApi(newContent.value.trim())
    newContent.value = ''
    commentDialogVisible.value = false
    toast.add({ severity: 'success', summary: t('comments.added'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 4000 })
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  const [manualResult, changelogResult] = await Promise.allSettled([
    getManual(),
    getChangelogUser(),
  ])

  if (manualResult.status === 'fulfilled') {
    manualText.value = manualResult.value
  } else {
    errorManual.value = true
  }
  loadingManual.value = false

  if (changelogResult.status === 'fulfilled') {
    changelogText.value = changelogResult.value
  } else {
    errorChangelog.value = true
  }
  loadingChangelog.value = false
})
</script>

<style scoped>
.help-loading {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
  color: var(--app-text-muted);
  padding: var(--app-space-6);
}

.help-content {
  max-width: 60rem;
}

.comment-dialog__body {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-3);
}

.comment-dialog__subtitle {
  color: var(--app-text-muted);
  font-size: 0.9375rem;
  margin: 0;
}

/* Basic prose styles for the rendered Markdown */
/* Heading hierarchy: distinct sizes and colors per level */
.prose :deep(h1),
.prose :deep(h2),
.prose :deep(h3),
.prose :deep(h4) {
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 0.5em;
  scroll-margin-top: 80px;
}

.prose :deep(h1) {
  font-size: 1.9rem;
  font-weight: 700;
  color: var(--app-text-primary);
  margin-top: 2em;
}

.prose :deep(h2) {
  font-size: 1.45rem;
  color: var(--p-primary-color);
  border-bottom: 2px solid color-mix(in srgb, var(--p-primary-color) 25%, transparent);
  padding-bottom: 0.3em;
  margin-top: 2em;
}

.prose :deep(h3) {
  font-size: 1.15rem;
  color: color-mix(in srgb, var(--p-primary-color) 75%, var(--app-text-primary));
  margin-top: 1.4em;
}

.prose :deep(h4) {
  font-size: 1rem;
  color: var(--app-text-muted);
  font-style: italic;
  margin-top: 1em;
}

.prose :deep(p) {
  margin-bottom: 0.75em;
  line-height: 1.7;
}

.prose :deep(ul),
.prose :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 0.75em;
}

.prose :deep(li) {
  margin-bottom: 0.25em;
}

.prose :deep(code) {
  background: var(--p-surface-100);
  border-radius: 3px;
  padding: 0.15em 0.4em;
  font-size: 0.875em;
  font-family: monospace;
}

.prose :deep(pre) {
  background: var(--p-surface-100);
  border-radius: var(--app-radius);
  padding: var(--app-space-4);
  overflow-x: auto;
  margin-bottom: 0.75em;
}

.prose :deep(pre code) {
  background: none;
  padding: 0;
}

.prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 0.75em;
}

.prose :deep(th),
.prose :deep(td) {
  border: 1px solid var(--p-surface-200);
  padding: var(--app-space-2) var(--app-space-3);
  text-align: left;
}

.prose :deep(th) {
  background: var(--p-surface-100);
  font-weight: 600;
}

.prose :deep(blockquote) {
  border-left: 4px solid var(--p-primary-color);
  margin: 0 0 0.75em;
  padding: var(--app-space-2) var(--app-space-4);
  color: var(--app-text-muted);
}
</style>
