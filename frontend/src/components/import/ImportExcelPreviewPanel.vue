<template>
  <AppPanel :title="t('import.preview_title')" dense>
    <div class="import-preview-overview" data-testid="preview-quick-summary">
      <article class="import-preview-overview-card">
        <span class="import-preview-overview-card__label">{{ t('import.estimated_contacts') }}</span>
        <strong class="import-preview-overview-card__value">{{ preview.estimated_contacts }}</strong>
      </article>
      <article class="import-preview-overview-card">
        <span class="import-preview-overview-card__label">{{ t('import.estimated_invoices') }}</span>
        <strong class="import-preview-overview-card__value">{{ preview.estimated_invoices }}</strong>
      </article>
      <article class="import-preview-overview-card">
        <span class="import-preview-overview-card__label">{{ t('import.estimated_payments') }}</span>
        <strong class="import-preview-overview-card__value">{{ preview.estimated_payments }}</strong>
      </article>
      <article class="import-preview-overview-card">
        <span class="import-preview-overview-card__label">{{ t('import.estimated_entries') }}</span>
        <strong class="import-preview-overview-card__value">{{ preview.estimated_entries }}</strong>
      </article>
      <article class="import-preview-overview-card">
        <span class="import-preview-overview-card__label">{{ t('import.operations_title') }}</span>
        <strong class="import-preview-overview-card__value">{{ operationDecisionStats.total }}</strong>
      </article>
    </div>

    <div class="import-preview-overview-meta">
      <p class="import-preview-state" :class="previewStateClass">{{ previewStateMessage }}</p>
      <div class="import-operation-metrics import-operation-metrics--inline">
        <span class="import-operation-metric import-operation-metric--success">
          {{ t('import.operation_decision.apply') }}: {{ operationDecisionStats.apply }}
        </span>
        <span class="import-operation-metric import-operation-metric--muted">
          {{ t('import.operation_decision.ignore') }}: {{ operationDecisionStats.ignore }}
        </span>
        <span class="import-operation-metric import-operation-metric--danger">
          {{ t('import.operation_decision.block') }}: {{ operationDecisionStats.block }}
        </span>
        <span class="import-operation-metric import-operation-metric--danger">
          {{ t('import.operation_status.failed') }}: {{ operationDecisionStats.failed }}
        </span>
      </div>
    </div>

    <div
      v-if="hasBlockingOperations"
      class="import-preview-inline-alert"
      data-testid="preview-blocked-guidance"
    >
      <div>
        <strong>{{ t('import.blocked_heading') }}</strong>
        <p class="import-action-hint">{{ t('import.blocked_subtitle_short') }}</p>
      </div>
      <Button
        data-testid="show-blocked-operations"
        :label="t('import.blocked_cta_show')"
        severity="secondary"
        outlined
        @click="showBlockedOperations()"
      />
    </div>

    <!-- Tab navigation -->
    <div class="import-preview-tabs" role="tablist" :aria-label="t('import.preview_tabs_aria_label')">
      <button
        id="preview-tab-details"
        type="button"
        role="tab"
        data-testid="preview-tab-details"
        class="import-preview-tab"
        :class="{ 'import-preview-tab--active': activePreviewTab === 'details' }"
        aria-controls="preview-tabpanel-details"
        :aria-selected="activePreviewTab === 'details'"
        :tabindex="activePreviewTab === 'details' ? 0 : -1"
        @click="activePreviewTab = 'details'"
      >
        {{ t('import.preview_tab_details') }}
        <span v-if="operationDecisionStats.total" class="import-preview-tab__count">
          {{ operationDecisionStats.total }}
        </span>
      </button>
      <button
        id="preview-tab-full-summary"
        type="button"
        role="tab"
        data-testid="preview-tab-full-summary"
        class="import-preview-tab"
        :class="{ 'import-preview-tab--active': activePreviewTab === 'full-summary' }"
        aria-controls="preview-tabpanel-full-summary"
        :aria-selected="activePreviewTab === 'full-summary'"
        :tabindex="activePreviewTab === 'full-summary' ? 0 : -1"
        @click="activePreviewTab = 'full-summary'"
      >
        {{ t('import.preview_tab_full_summary') }}
      </button>
      <button
        id="preview-tab-warnings"
        type="button"
        role="tab"
        data-testid="preview-tab-warnings"
        class="import-preview-tab"
        :class="{ 'import-preview-tab--active': activePreviewTab === 'warnings' }"
        aria-controls="preview-tabpanel-warnings"
        :aria-selected="activePreviewTab === 'warnings'"
        :tabindex="activePreviewTab === 'warnings' ? 0 : -1"
        @click="activePreviewTab = 'warnings'"
      >
        {{ t('import.preview_tab_warnings') }}
        <span v-if="previewIssueCount" class="import-preview-tab__count">{{ previewIssueCount }}</span>
      </button>
    </div>

    <!-- Full summary tab -->
    <div
      v-if="activePreviewTab === 'full-summary'"
      id="preview-tabpanel-full-summary"
      role="tabpanel"
      aria-labelledby="preview-tab-full-summary"
      data-testid="preview-full-summary-tab"
    >
      <div class="import-summary-grid">
        <div class="import-summary-row">
          <span>{{ t('import.estimated_contacts') }}</span>
          <span class="font-medium">{{ preview.estimated_contacts }}</span>
        </div>
        <div class="import-summary-row">
          <span>{{ t('import.estimated_invoices') }}</span>
          <span class="font-medium">{{ preview.estimated_invoices }}</span>
        </div>
        <div class="import-summary-row">
          <span>{{ t('import.estimated_payments') }}</span>
          <span class="font-medium">{{ preview.estimated_payments }}</span>
        </div>
        <div class="import-summary-row">
          <span>{{ t('import.estimated_salaries') }}</span>
          <span class="font-medium">{{ preview.estimated_salaries }}</span>
        </div>
        <div class="import-summary-row">
          <span>{{ t('import.estimated_entries') }}</span>
          <span class="font-medium">{{ preview.estimated_entries }}</span>
        </div>
      </div>

      <div v-if="previewComparison" class="import-comparison-block">
        <div class="import-comparison-block__header">
          <div>
            <p class="import-section-eyebrow">{{ t('import.preview_comparison_section_title') }}</p>
            <h3 class="import-sheet-list__title">{{ comparisonTitle }}</h3>
            <p class="import-action-hint">{{ comparisonSubtitle }}</p>
          </div>
          <div class="import-sheet-card__stats">
            <strong class="import-sheet-card__rows">
              {{ t('import.comparison_file_rows', { count: previewComparison.totals.file_rows }) }}
            </strong>
            <span class="import-sheet-card__stat import-sheet-card__stat--success">
              {{ t('import.comparison_already_in_solde', { count: previewComparison.totals.already_in_solde }) }}
            </span>
            <span class="import-sheet-card__stat">
              {{ t('import.comparison_missing_in_solde', { count: previewComparison.totals.missing_in_solde }) }}
            </span>
            <span class="import-sheet-card__stat import-sheet-card__stat--warning">
              {{ t('import.comparison_extra_in_solde', { count: previewComparison.totals.extra_in_solde }) }}
            </span>
          </div>
        </div>

        <div class="import-comparison-grid">
          <article
            v-for="domain in previewComparison.domains"
            :key="`comparison-${domain.kind}`"
            class="import-comparison-card"
          >
            <h4 class="import-sheet-card__title">{{ previewSheetKindLabel(domain.kind) }}</h4>
            <div class="import-summary-grid import-summary-grid--compact">
              <div class="import-summary-row">
                <span>{{ t('import.comparison_file_rows', { count: domain.file_rows }) }}</span>
                <strong>{{ domain.file_rows }}</strong>
              </div>
              <div class="import-summary-row">
                <span>{{ t('import.comparison_already_in_solde', { count: domain.already_in_solde }) }}</span>
                <strong>{{ domain.already_in_solde }}</strong>
              </div>
              <div class="import-summary-row">
                <span>{{ t('import.comparison_missing_in_solde', { count: domain.missing_in_solde }) }}</span>
                <strong>{{ domain.missing_in_solde }}</strong>
              </div>
              <div class="import-summary-row">
                <span>{{ t('import.comparison_extra_in_solde', { count: domain.extra_in_solde }) }}</span>
                <strong>{{ domain.extra_in_solde }}</strong>
              </div>
              <div class="import-summary-row">
                <span>{{ t('import.comparison_ignored_by_policy', { count: domain.ignored_by_policy }) }}</span>
                <strong>{{ domain.ignored_by_policy }}</strong>
              </div>
              <div class="import-summary-row">
                <span>{{ t('import.comparison_blocked', { count: domain.blocked }) }}</span>
                <strong>{{ domain.blocked }}</strong>
              </div>
            </div>
            <div v-if="domain.extra_in_solde_details?.length" class="import-comparison-detail-block">
              <span class="app-field__label">
                {{ t('import.comparison_extra_details_title', { count: domain.extra_in_solde_details.length }) }}
              </span>
              <ul class="import-comparison-detail-list">
                <li
                  v-for="(detail, detailIndex) in domain.extra_in_solde_details"
                  :key="`comparison-${domain.kind}-detail-${detailIndex}`"
                  class="import-comparison-detail-item"
                >
                  <strong>{{ detail.summary }}</strong>
                  <div
                    v-if="previewComparisonExtraDetailFields(detail).length"
                    class="import-comparison-detail-fields"
                  >
                    <span
                      v-for="field in previewComparisonExtraDetailFields(detail)"
                      :key="`${detail.summary}-${field.key}`"
                      class="import-comparison-detail-field"
                    >
                      {{ t(`import.comparison_detail_fields.${field.key}`) }}: {{ field.value }}
                    </span>
                  </div>
                </li>
              </ul>
            </div>
          </article>
        </div>
      </div>

      <div v-if="preview.sheets.length" class="import-diagnostic-block">
        <div class="import-diagnostic-block__header">
          <div>
            <p class="import-section-eyebrow">{{ t('import.preview_diagnostic_section_title') }}</p>
            <h3 class="import-sheet-list__title">{{ t('import.preview_diagnostic_title') }}</h3>
            <p class="import-action-hint">{{ t('import.preview_diagnostic_subtitle') }}</p>
          </div>
        </div>
      </div>

      <div v-if="preview.sheets.length" class="import-sheet-list">
        <h3 class="import-sheet-list__title">{{ t('import.sheets_title') }}</h3>
        <article v-for="sheet in preview.sheets" :key="sheet.name" class="import-sheet-card">
          <div class="import-sheet-card__header">
            <div>
              <h4 class="import-sheet-card__title">{{ sheet.name }}</h4>
              <p class="import-sheet-card__meta">
                {{ previewSheetKindLabel(sheet.kind) }} · {{ previewSheetStatusLabel(sheet.status) }}
              </p>
            </div>
            <div class="import-sheet-card__stats">
              <strong class="import-sheet-card__rows">{{
                t('import.sheet_rows', { count: sheet.rows })
              }}</strong>
              <span v-if="sheet.ignored_rows" class="import-sheet-card__stat import-sheet-card__stat--warning">
                {{ t('import.sheet_ignored_rows', { count: sheet.ignored_rows }) }}
              </span>
              <span v-if="sheet.blocked_rows" class="import-sheet-card__stat import-sheet-card__stat--danger">
                {{ t('import.sheet_blocked_rows', { count: sheet.blocked_rows }) }}
              </span>
            </div>
          </div>
          <div v-if="sheet.detected_columns.length" class="import-sheet-card__section">
            <span class="app-field__label">{{ t('import.detected_columns') }}</span>
            <div class="import-chip-row">
              <span v-for="column in sheet.detected_columns" :key="column" class="import-chip">{{ column }}</span>
            </div>
          </div>
          <div v-if="sheet.missing_columns.length" class="import-sheet-card__section">
            <span class="app-field__label">{{ t('import.missing_columns') }}</span>
            <div class="import-chip-row">
              <span v-for="column in sheet.missing_columns" :key="column" class="import-chip import-chip--danger">{{ column }}</span>
            </div>
          </div>
          <ul v-if="sheet.warnings.length" class="import-warnings">
            <li
              v-for="(warning, idx) in previewIssueMessages(sheet.warnings, sheet.warning_details)"
              :key="`${sheet.name}-warning-${idx}`"
            >{{ warning }}</li>
          </ul>
          <ul v-if="sheet.errors.length" class="import-errors">
            <li
              v-for="(error, idx) in previewIssueMessages(sheet.errors, sheet.error_details)"
              :key="`${sheet.name}-error-${idx}`"
            >{{ error }}</li>
          </ul>
        </article>
      </div>
    </div>

    <!-- Details tab (operation table) -->
    <div
      v-else-if="activePreviewTab === 'details'"
      id="preview-tabpanel-details"
      role="tabpanel"
      aria-labelledby="preview-tab-details"
      data-testid="preview-details-tab"
    >
      <div v-if="activeRun?.operations.length" class="import-operation-block">
        <div class="import-diagnostic-block__header">
          <div>
            <p class="import-section-eyebrow">{{ t('import.operations_title') }}</p>
            <h3 class="import-sheet-list__title">{{ t('import.operations_table_title') }}</h3>
            <p class="import-action-hint">{{ t('import.operations_table_subtitle') }}</p>
          </div>
          <div class="import-operation-metrics">
            <span class="import-operation-metric">
              <strong>{{ operationDecisionStats.total }}</strong>
              {{ t('import.operations_count', { count: operationDecisionStats.total }) }}
            </span>
            <span class="import-operation-metric import-operation-metric--success">
              {{ t('import.operation_decision.apply') }}: {{ operationDecisionStats.apply }}
            </span>
            <span class="import-operation-metric import-operation-metric--muted">
              {{ t('import.operation_decision.ignore') }}: {{ operationDecisionStats.ignore }}
            </span>
            <span class="import-operation-metric import-operation-metric--danger">
              {{ t('import.operation_decision.block') }}: {{ operationDecisionStats.block }}
            </span>
            <span class="import-operation-metric import-operation-metric--danger">
              {{ t('import.operation_status.failed') }}: {{ operationDecisionStats.failed }}
            </span>
          </div>
        </div>

        <div class="import-operation-toolbar">
          <div class="app-field import-operation-toolbar__search">
            <label for="operations-search" class="app-field__label">{{ t('import.operations_filter_label') }}</label>
            <input
              id="operations-search"
              v-model.trim="operationSearch"
              data-testid="operations-search"
              type="search"
              class="app-input"
              :placeholder="t('import.operations_filter_placeholder')"
            />
          </div>
          <div class="app-field">
            <label for="operations-type-filter" class="app-field__label">{{ t('import.operations_filter_type') }}</label>
            <select
              id="operations-type-filter"
              v-model="operationTypeFilter"
              data-testid="operations-type-filter"
              class="app-input"
            >
              <option value="all">{{ t('import.operations_filter_all_types') }}</option>
              <option
                v-for="option in operationTypeOptions"
                :key="`operation-type-${option.value}`"
                :value="option.value"
              >{{ option.label }}</option>
            </select>
          </div>
          <div class="app-field">
            <label for="operations-status-filter" class="app-field__label">{{ t('import.operations_filter_status') }}</label>
            <select
              id="operations-status-filter"
              v-model="operationStatusFilter"
              data-testid="operations-status-filter"
              class="app-input"
            >
              <option value="all">{{ t('import.operations_filter_all_statuses') }}</option>
              <option
                v-for="option in operationStatusOptions"
                :key="`operation-status-${option.value}`"
                :value="option.value"
              >{{ option.label }}</option>
            </select>
          </div>
        </div>

        <div v-if="filteredOperationGroups.length === 0" class="app-empty-state import-empty-inline">
          {{ t('import.operations_no_match') }}
        </div>

        <div v-else data-testid="operations-table" class="import-operation-table-wrap">
          <table class="import-operation-table">
            <thead>
              <tr>
                <th class="import-operation-table__expander-column"></th>
                <th>
                  <button type="button" class="import-operation-sort" @click="setOperationSort('summary')">
                    <span>{{ t('import.operations_column_summary') }}</span>
                    <span class="import-operation-sort__indicator">{{ operationSortIndicator('summary') }}</span>
                  </button>
                </th>
                <th>
                  <button type="button" class="import-operation-sort" @click="setOperationSort('sourceSheet')">
                    <span>{{ t('import.operations_column_sheet') }}</span>
                    <span class="import-operation-sort__indicator">{{ operationSortIndicator('sourceSheet') }}</span>
                  </button>
                </th>
                <th>
                  <button type="button" class="import-operation-sort" @click="setOperationSort('sourceRowCount')">
                    <span>{{ t('import.operations_column_rows') }}</span>
                    <span class="import-operation-sort__indicator">{{ operationSortIndicator('sourceRowCount') }}</span>
                  </button>
                </th>
                <th>
                  <button type="button" class="import-operation-sort" @click="setOperationSort('status')">
                    <span>{{ t('import.operations_column_status') }}</span>
                    <span class="import-operation-sort__indicator">{{ operationSortIndicator('status') }}</span>
                  </button>
                </th>
              </tr>
            </thead>

            <tbody v-for="group in filteredOperationGroups" :key="`operation-group-${group.key}`">
              <tr class="import-operation-group-row">
                <th colspan="5">
                  <div class="import-operation-group-row__content">
                    <span>{{ group.label }}</span>
                    <span class="import-operation-group-row__count">
                      {{ t('import.operations_group_count', { count: group.rows.length }) }}
                    </span>
                  </div>
                </th>
              </tr>

              <template v-for="row in group.rows" :key="`operation-row-${row.id}`">
                <tr :data-testid="`operation-row-${row.id}`" class="import-operation-row">
                  <td class="import-operation-table__expander-column">
                    <button
                      type="button"
                      class="import-operation-toggle"
                      :data-testid="`toggle-operation-${row.id}`"
                      :aria-expanded="isOperationExpanded(row.id)"
                      @click="toggleOperationExpanded(row.id)"
                    >
                      {{ isOperationExpanded(row.id) ? t('import.operation_detail_hide') : t('import.operation_detail_show') }}
                    </button>
                  </td>
                  <td class="import-operation-table__summary-cell">
                    <div class="import-operation-summary-cell">
                      <strong>{{ row.summary }}</strong>
                      <span class="import-operation-summary-cell__meta">#{{ row.operation.position }}</span>
                    </div>
                  </td>
                  <td>{{ row.sourceSheetLabel }}</td>
                  <td :title="row.sourceRowsLabel">{{ row.sourceRowCount }}</td>
                  <td>
                    <div class="import-operation-status-stack">
                      <span
                        class="import-operation-badge"
                        :class="operationStatusBadgeClass(row.operation.status)"
                      >{{ row.statusLabel }}</span>
                      <span class="import-operation-status-stack__meta">{{ row.decisionLabel }}</span>
                    </div>
                  </td>
                </tr>

                <tr
                  v-if="isOperationExpanded(row.id)"
                  :data-testid="`operation-detail-${row.id}`"
                  class="import-operation-detail-row"
                >
                  <td colspan="5">
                    <div class="import-operation-detail-card">
                      <div>
                        <span class="app-field__label">{{ t('import.operation_detail_summary_label') }}</span>
                        <h4 class="import-operation-detail-card__title">{{ row.summary }}</h4>
                      </div>
                      <div class="import-operation-detail-grid">
                        <div>
                          <span class="app-field__label">{{ t('import.operation_source_rows_label') }}</span>
                          <p class="import-action-hint">{{ row.sourceRowsLabel }}</p>
                        </div>
                        <div v-if="row.operation.description">
                          <span class="app-field__label">{{ t('import.operation_description_label') }}</span>
                          <p class="import-action-hint">{{ row.operation.description }}</p>
                        </div>
                        <div v-if="row.operation.error_message">
                          <span class="app-field__label">{{ t('import.errors') }}</span>
                          <p class="import-action-hint import-operation-detail-card__error">
                            {{ row.operation.error_message }}
                          </p>
                        </div>
                      </div>

                      <div v-if="operationSourceRows(row.operation).length" class="import-sheet-card__section">
                        <span class="app-field__label">{{ t('import.operation_source_data_label') }}</span>
                        <ul class="import-comparison-detail-list">
                          <li
                            v-for="(sourceRow, index) in operationSourceRows(row.operation)"
                            :key="`${row.id}-source-row-${index}`"
                            class="import-comparison-detail-item"
                          >
                            <strong>{{ operationSourceRowLabel(sourceRow, index) }}</strong>
                            <div v-if="operationSourceFields(sourceRow).length" class="import-comparison-detail-fields">
                              <span
                                v-for="field in operationSourceFields(sourceRow)"
                                :key="`${row.id}-source-row-${index}-${field.key}`"
                                class="import-comparison-detail-field"
                              >{{ operationSourceFieldLabel(field.key) }}: {{ field.value }}</span>
                            </div>
                          </li>
                        </ul>
                      </div>

                      <ul v-if="row.operation.diagnostics.length" class="import-warnings">
                        <li
                          v-for="(diagnostic, index) in row.operation.diagnostics"
                          :key="`${row.id}-diagnostic-${index}`"
                        >{{ diagnostic }}</li>
                      </ul>

                      <div class="import-sheet-card__section">
                        <span class="app-field__label">{{ t('import.operation_business_effects') }}</span>
                        <ul v-if="operationBusinessEffects(row.operation).length" class="import-comparison-detail-list">
                          <li
                            v-for="(effect, index) in operationBusinessEffects(row.operation)"
                            :key="`${row.id}-business-effect-${effect.id ?? `planned-${index}`}`"
                            class="import-comparison-detail-item"
                          >
                            <strong>{{ operationEffectLabel(effect) }}</strong>
                            <span v-if="effect.entity_reference" class="import-comparison-detail-field">
                              {{ effect.entity_reference }}
                            </span>
                            <div v-if="operationEffectDetailFields(effect).length" class="import-comparison-detail-fields">
                              <span
                                v-for="field in operationEffectDetailFields(effect)"
                                :key="`${row.id}-business-effect-${effect.id ?? `planned-${index}`}-${field.key}`"
                                class="import-comparison-detail-field"
                              >{{ operationEffectFieldLabel(field.key) }}: {{ field.value }}</span>
                            </div>
                          </li>
                        </ul>
                        <p v-else class="import-action-hint">{{ t('import.operation_business_effects_empty') }}</p>
                      </div>

                      <div class="import-sheet-card__section">
                        <span class="app-field__label">{{ t('import.operation_accounting_effects') }}</span>
                        <ul v-if="operationAccountingEffects(row.operation).length" class="import-comparison-detail-list">
                          <li
                            v-for="(effect, index) in operationAccountingEffects(row.operation)"
                            :key="`${row.id}-accounting-effect-${effect.id ?? `planned-${index}`}`"
                            class="import-comparison-detail-item"
                          >
                            <strong>{{ operationEffectLabel(effect) }}</strong>
                            <span v-if="effect.entity_reference" class="import-comparison-detail-field">
                              {{ effect.entity_reference }}
                            </span>
                            <div v-if="operationEffectDetailFields(effect).length" class="import-comparison-detail-fields">
                              <span
                                v-for="field in operationEffectDetailFields(effect)"
                                :key="`${row.id}-accounting-effect-${effect.id ?? `planned-${index}`}-${field.key}`"
                                class="import-comparison-detail-field"
                              >{{ operationEffectFieldLabel(field.key) }}: {{ field.value }}</span>
                            </div>
                          </li>
                        </ul>
                        <p v-else class="import-action-hint">{{ t('import.operation_accounting_effects_empty') }}</p>
                      </div>

                      <div v-if="row.operation.effects.length" class="import-sheet-card__section">
                        <span class="app-field__label">{{ t('import.operation_effects') }}</span>
                        <ul class="import-comparison-detail-list">
                          <li
                            v-for="(effect, index) in row.operation.effects"
                            :key="`${row.id}-effect-${effect.id ?? `planned-${index}`}`"
                            class="import-comparison-detail-item"
                          >
                            <strong>{{ operationEffectLabel(effect) }}</strong>
                            <span v-if="effect.entity_reference" class="import-comparison-detail-field">
                              {{ effect.entity_reference }}
                            </span>
                          </li>
                        </ul>
                      </div>

                      <div
                        v-if="row.operation.can_undo || row.operation.can_redo"
                        class="app-form-actions import-inline-actions"
                      >
                        <Button
                          v-if="row.operation.can_undo"
                          :label="t('import.undo_operation')"
                          severity="secondary"
                          outlined
                          :loading="busyOperationId === row.operation.id"
                          @click="emit('undo-operation', row.operation.id)"
                        />
                        <Button
                          v-if="row.operation.can_redo"
                          :label="t('import.redo_operation')"
                          severity="secondary"
                          outlined
                          :loading="busyOperationId === row.operation.id"
                          @click="emit('redo-operation', row.operation.id)"
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Warnings tab -->
    <div
      v-else
      id="preview-tabpanel-warnings"
      role="tabpanel"
      aria-labelledby="preview-tab-warnings"
      data-testid="preview-warnings-tab"
    >
      <div v-if="hasBlockingOperations" class="import-blocked-guidance">
        <div>
          <p class="import-section-eyebrow">{{ t('import.blocked_title') }}</p>
          <h3 class="import-sheet-list__title">{{ t('import.blocked_heading') }}</h3>
          <p class="import-action-hint">{{ t('import.blocked_subtitle') }}</p>
        </div>
        <ul class="import-blocked-guidance__steps">
          <li>{{ t('import.blocked_step_open') }}</li>
          <li>{{ t('import.blocked_step_fix') }}</li>
          <li>{{ t('import.blocked_step_retry') }}</li>
        </ul>
      </div>

      <div v-if="preview.warnings.length" class="import-warnings-block">
        <span class="app-field__label">{{ t('import.warnings') }}</span>
        <ul class="import-warnings">
          <li
            v-for="(warning, idx) in previewIssueMessages(preview.warnings, preview.warning_details)"
            :key="`warning-${idx}`"
          >{{ warning }}</li>
        </ul>
      </div>

      <div v-if="preview.errors.length" class="import-errors">
        <span class="app-field__label">{{ t('import.errors') }}</span>
        <ul>
          <li
            v-for="(err, idx) in previewIssueMessages(preview.errors, preview.error_details)"
            :key="idx"
          >{{ err }}</li>
        </ul>
      </div>

      <div
        v-if="previewIssueCount === 0 && !hasBlockingOperations"
        class="app-empty-state import-empty-inline"
      >
        {{ t('import.no_preview_alerts') }}
      </div>
    </div>

    <!-- Confirm actions -->
    <div class="app-form-actions import-confirm">
      <Button
        data-testid="confirm-import-button"
        :label="t('import.confirm_import')"
        icon="pi pi-check"
        :loading="importing"
        :disabled="!canConfirmImport || !activeRun?.can_execute"
        @click="emit('do-import')"
      />
      <Button
        v-if="activeRun?.can_undo"
        :label="t('import.undo_run')"
        icon="pi pi-undo"
        severity="secondary"
        outlined
        :loading="importing"
        @click="emit('undo-run', activeRun.id)"
      />
      <Button
        v-if="activeRun?.can_redo"
        :label="t('import.redo_run')"
        icon="pi pi-refresh"
        severity="secondary"
        outlined
        :loading="importing"
        @click="emit('redo-run', activeRun.id)"
      />
    </div>
    <p
      v-if="hasPreviewWarnings && preview.can_import"
      data-testid="confirm-import-warning"
      class="import-action-hint import-action-hint--warning"
    >
      {{ t('import.warning_review_hint') }}
    </p>
  </AppPanel>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import AppPanel from '../ui/AppPanel.vue'
import type {
  ImportEffectRead,
  ImportOperationRead,
  ImportRunRead,
  PreviewComparisonExtraDetail,
  PreviewResult,
  PreviewSheetResult,
} from '@/api/accounting'

interface Props {
  preview: PreviewResult
  activeRun: ImportRunRead | null
  importing: boolean
  busyRunId: number | null
  busyOperationId: number | null
  canConfirmImport: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'undo-operation': [operationId: number]
  'redo-operation': [operationId: number]
  'undo-run': [runId: number]
  'redo-run': [runId: number]
  'do-import': []
}>()

const { t } = useI18n()

// Tab and table state
const activePreviewTab = ref<'details' | 'full-summary' | 'warnings'>('details')
const operationSearch = ref('')
const operationTypeFilter = ref('all')
const operationStatusFilter = ref<'all' | ImportOperationRead['status']>('all')
const operationSortField = ref<'position' | 'summary' | 'sourceSheet' | 'sourceRowCount' | 'status'>('position')
const operationSortDirection = ref<'asc' | 'desc'>('asc')
const expandedOperationIds = ref<number[]>([])

watch(() => props.activeRun?.id, () => {
  activePreviewTab.value = 'details'
  operationSearch.value = ''
  operationTypeFilter.value = 'all'
  operationStatusFilter.value = 'all'
  operationSortField.value = 'position'
  operationSortDirection.value = 'asc'
  expandedOperationIds.value = []
})

type OperationTableRow = {
  id: number
  groupKey: string
  groupLabel: string
  summary: string
  sourceSheetLabel: string
  sourceRowCount: number
  sourceRowsLabel: string
  statusLabel: string
  decisionLabel: string
  searchText: string
  operation: ImportOperationRead
}

// Computed values
const previewState = computed<'ready' | 'noop' | 'blocked'>(() => {
  if (props.preview.can_import) return 'ready'
  if (props.preview.errors.length === 0) return 'noop'
  return 'blocked'
})

const previewStateClass = computed(() => {
  if (previewState.value === 'ready') return 'import-preview-state--ready'
  if (previewState.value === 'noop') return 'import-preview-state--noop'
  return 'import-preview-state--blocked'
})

const previewStateMessage = computed(() => {
  if (previewState.value === 'ready') return t('import.preview_ready')
  if (previewState.value === 'noop') return t('import.preview_noop')
  return t('import.preview_blocked')
})

const hasPreviewWarnings = computed(() =>
  Boolean(
    props.preview.warnings.length > 0 ||
    props.preview.warning_details.length > 0 ||
    props.preview.sheets.some(
      (sheet) => sheet.warnings.length > 0 || sheet.warning_details.length > 0,
    ),
  ),
)

const previewIssueCount = computed(() =>
  props.preview.warnings.length + props.preview.errors.length,
)

const isAlreadyImportedPreview = computed(() =>
  Boolean(
    props.preview.error_details.some((detail) => detail.category === 'already-imported') ||
    props.preview.errors.some((message) => message.startsWith('Fichier deja importe')),
  ),
)

const showPreviewComparison = computed(
  () => Boolean(props.preview.comparison?.domains.length) && isAlreadyImportedPreview.value,
)

const previewComparison = computed(() =>
  showPreviewComparison.value ? (props.preview.comparison ?? null) : null,
)

const comparisonTitle = computed(() => {
  if (props.preview.comparison?.mode === 'global-convergence') return t('import.comparison_title_global')
  return t('import.comparison_title')
})

const comparisonSubtitle = computed(() => {
  if (props.preview.comparison?.mode === 'global-convergence') return t('import.comparison_subtitle_global')
  return t('import.comparison_subtitle')
})

const operationTableRows = computed<OperationTableRow[]>(() =>
  (props.activeRun?.operations ?? []).map((operation) => {
    const groupLabel = operationGroupLabel(operation.operation_type)
    const summary = operationSummaryLabel(operation)
    const sourceSheetLabel = operation.source_sheet?.trim() || t('import.operation_no_sheet')
    const sourceRowsLabel = operation.source_row_numbers.length
      ? operation.source_row_numbers.join(', ')
      : t('import.operation_no_sheet')
    const statusLabel = t(`import.operation_status.${operation.status}`)
    const decisionLabel = t(`import.operation_decision.${operation.decision}`)
    const effectTerms = operation.effects
      .map((effect) => [effect.entity_reference, effect.entity_type, effect.action].join(' '))
      .join(' ')
    const sourceDataTerms = (operation.source_data ?? [])
      .flatMap((sourceRow) => Object.values(sourceRow))
      .filter((value) => value !== null && value !== undefined && value !== '')
      .map((value) => String(value))

    return {
      id: operation.id,
      groupKey: operation.operation_type,
      groupLabel,
      summary,
      sourceSheetLabel,
      sourceRowCount: operation.source_row_numbers.length,
      sourceRowsLabel,
      statusLabel,
      decisionLabel,
      searchText: [
        groupLabel, summary, sourceSheetLabel, sourceRowsLabel, statusLabel, decisionLabel,
        operation.description ?? '', operation.error_message ?? '',
        ...operation.diagnostics, effectTerms, ...sourceDataTerms,
      ].join(' ').toLocaleLowerCase('fr-FR'),
      operation,
    }
  }),
)

const operationTypeOptions = computed(() => {
  const labels = new Map<string, string>()
  for (const row of operationTableRows.value) {
    if (!labels.has(row.groupKey)) labels.set(row.groupKey, row.groupLabel)
  }
  return Array.from(labels.entries())
    .map(([value, label]) => ({ value, label }))
    .sort((left, right) => left.label.localeCompare(right.label, 'fr', { sensitivity: 'base' }))
})

const operationStatusOptions = computed(() => {
  const labels = new Map<ImportOperationRead['status'], string>()
  for (const row of operationTableRows.value) {
    if (!labels.has(row.operation.status)) labels.set(row.operation.status, row.statusLabel)
  }
  return Array.from(labels.entries()).map(([value, label]) => ({ value, label }))
})

const filteredOperationRows = computed(() => {
  const searchTerm = operationSearch.value.trim().toLocaleLowerCase('fr-FR')
  return operationTableRows.value.filter((row) => {
    if (operationTypeFilter.value !== 'all' && row.groupKey !== operationTypeFilter.value) return false
    if (operationStatusFilter.value !== 'all' && row.operation.status !== operationStatusFilter.value) return false
    if (searchTerm && !row.searchText.includes(searchTerm)) return false
    return true
  })
})

const sortedOperationRows = computed(() => {
  const rows = [...filteredOperationRows.value]
  rows.sort((left, right) => {
    let comparison = 0
    switch (operationSortField.value) {
      case 'summary': comparison = left.summary.localeCompare(right.summary, 'fr', { sensitivity: 'base', numeric: true }); break
      case 'sourceSheet': comparison = left.sourceSheetLabel.localeCompare(right.sourceSheetLabel, 'fr', { sensitivity: 'base', numeric: true }); break
      case 'sourceRowCount': comparison = left.sourceRowCount - right.sourceRowCount; break
      case 'status': comparison = left.statusLabel.localeCompare(right.statusLabel, 'fr', { sensitivity: 'base', numeric: true }); break
      default: comparison = left.operation.position - right.operation.position; break
    }
    if (comparison === 0) comparison = left.operation.position - right.operation.position
    return operationSortDirection.value === 'asc' ? comparison : -comparison
  })
  return rows
})

const filteredOperationGroups = computed(() => {
  const groups = new Map<string, { key: string; label: string; rows: OperationTableRow[] }>()
  for (const row of sortedOperationRows.value) {
    const existing = groups.get(row.groupKey)
    if (existing) { existing.rows.push(row); continue }
    groups.set(row.groupKey, { key: row.groupKey, label: row.groupLabel, rows: [row] })
  }
  return Array.from(groups.values())
})

const operationDecisionStats = computed(() => {
  const operations = props.activeRun?.operations ?? []
  return {
    total: operations.length,
    apply: operations.filter((op) => op.decision === 'apply').length,
    ignore: operations.filter((op) => op.decision === 'ignore').length,
    block: operations.filter((op) => op.decision === 'block').length,
    failed: operations.filter((op) => op.status === 'failed').length,
  }
})

const blockedOperationRows = computed(() =>
  operationTableRows.value.filter(
    (row) => row.operation.decision === 'block' || row.operation.status === 'blocked',
  ),
)

const hasBlockingOperations = computed(
  () => blockedOperationRows.value.length > 0 || !props.preview.can_import,
)

// Helper functions
function previewSheetKindLabel(kind: PreviewSheetResult['kind']) {
  return t(`import.sheet_kind.${kind}`)
}

function previewSheetStatusLabel(status: PreviewSheetResult['status']) {
  return t(`import.sheet_status.${status}`)
}

function previewComparisonExtraDetailFields(detail: PreviewComparisonExtraDetail) {
  return Object.entries(detail)
    .filter(([key, value]) => key !== 'summary' && typeof value === 'string' && value.trim())
    .map(([key, value]) => ({ key, value: value as string }))
}

function previewIssueMessages(messages: string[], details: Array<{ display_message: string }>) {
  if (details.length > 0) return details.map((detail) => detail.display_message)
  return messages
}

function operationGroupLabel(operationType: string) {
  const translated = t(`import.operation_group.${operationType}`)
  return translated === `import.operation_group.${operationType}` ? operationType : translated
}

function operationActionLabel(operationType: string) {
  const translated = t(`import.operation_action.${operationType}`)
  return translated === `import.operation_action.${operationType}`
    ? t('import.operations_column_summary')
    : translated
}

function operationSummaryLabel(operation: ImportOperationRead) {
  const title = operation.title.trim()
  const actionLabel = operationActionLabel(operation.operation_type)
  return title ? `${actionLabel} ${title}` : actionLabel
}

function operationEffectLabel(effect: ImportEffectRead) {
  const entityKey = `import.effect_entity.${effect.entity_type}`
  const entityLabel = t(entityKey)
  return `${t(`import.effect_action.${effect.action}`)} ${entityLabel === entityKey ? effect.entity_type : entityLabel}`
}

function operationDisplayEffects(operation: ImportOperationRead) {
  return operation.effects.length ? operation.effects : (operation.planned_effects ?? [])
}

function operationBusinessEffects(operation: ImportOperationRead) {
  return operationDisplayEffects(operation).filter((effect) => effect.entity_type !== 'accounting_entry')
}

function operationAccountingEffects(operation: ImportOperationRead) {
  return operationDisplayEffects(operation).filter((effect) => effect.entity_type === 'accounting_entry')
}

function operationEffectDetailFields(effect: ImportEffectRead) {
  return Object.entries(effect.details ?? {})
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => ({ key, value: formatEffectFieldValue(value) }))
}

function operationEffectFieldLabel(key: string) {
  const translationKey = `import.effect_detail_fields.${key}`
  const translated = t(translationKey)
  return translated === translationKey ? key : translated
}

function operationSourceRows(operation: ImportOperationRead) {
  return operation.source_data ?? []
}

function operationSourceRowLabel(sourceRow: Record<string, unknown>, index: number) {
  const sourceRowNumber = sourceRow.source_row_number
  if (typeof sourceRowNumber === 'number' || (typeof sourceRowNumber === 'string' && String(sourceRowNumber).trim())) {
    return t('import.operation_source_data_row', { row: sourceRowNumber })
  }
  return t('import.operation_source_data_row', { row: index + 1 })
}

function operationSourceFields(sourceRow: Record<string, unknown>) {
  return Object.entries(sourceRow)
    .filter(([key, value]) => key !== 'source_row_number' && value !== null && value !== undefined && value !== '')
    .map(([key, value]) => ({ key, value: formatSourceFieldValue(value) }))
}

function operationSourceFieldLabel(key: string) {
  const translationKey = `import.source_detail_fields.${key}`
  const translated = t(translationKey)
  if (translated !== translationKey) return translated
  const normalized = key.replace(/_/g, ' ').trim()
  return normalized.charAt(0).toUpperCase() + normalized.slice(1)
}

function formatEffectFieldValue(value: unknown) {
  if (typeof value === 'boolean') return value ? t('common.yes') : t('common.no')
  return String(value)
}

function formatSourceFieldValue(value: unknown) {
  if (typeof value === 'boolean') return value ? t('common.yes') : t('common.no')
  if (Array.isArray(value)) return value.map((item) => String(item)).join(', ')
  return String(value)
}

function operationStatusBadgeClass(status: ImportOperationRead['status']) {
  switch (status) {
    case 'applied': return 'import-operation-badge--success'
    case 'blocked':
    case 'failed': return 'import-operation-badge--danger'
    case 'ignored': return 'import-operation-badge--muted'
    case 'undone': return 'import-operation-badge--warning'
    default: return 'import-operation-badge--default'
  }
}

function setOperationSort(field: 'position' | 'summary' | 'sourceSheet' | 'sourceRowCount' | 'status') {
  if (operationSortField.value === field) {
    operationSortDirection.value = operationSortDirection.value === 'asc' ? 'desc' : 'asc'
    return
  }
  operationSortField.value = field
  operationSortDirection.value = 'asc'
}

function operationSortIndicator(field: 'position' | 'summary' | 'sourceSheet' | 'sourceRowCount' | 'status') {
  if (operationSortField.value !== field) return ''
  return operationSortDirection.value === 'asc' ? '↑' : '↓'
}

function isOperationExpanded(operationId: number) {
  return expandedOperationIds.value.includes(operationId)
}

function toggleOperationExpanded(operationId: number) {
  if (isOperationExpanded(operationId)) {
    expandedOperationIds.value = expandedOperationIds.value.filter((id) => id !== operationId)
    return
  }
  expandedOperationIds.value = [...expandedOperationIds.value, operationId]
}

function showBlockedOperations() {
  activePreviewTab.value = 'details'
  operationSearch.value = ''
  operationTypeFilter.value = 'all'
  operationStatusFilter.value = 'blocked'
  expandedOperationIds.value = blockedOperationRows.value.slice(0, 3).map((row) => row.id)
}
</script>
