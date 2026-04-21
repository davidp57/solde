<template>
  <AppPage width="wide">
    <AppPageHeader :eyebrow="t('ui.page.collection_eyebrow')" :title="t('bank.title')">
      <template #actions>
        <Button
          :label="t('bank.import_statement')"
          icon="pi pi-upload"
          severity="secondary"
          @click="importDialogVisible = true"
        />
        <Button
          :label="t('bank.new_deposit')"
          icon="pi pi-inbox"
          severity="secondary"
          @click="openDepositDialog"
        />
        <Button
          :label="t('bank.new_transaction')"
          icon="pi pi-plus"
          @click="txDialogVisible = true"
        />
      </template>
    </AppPageHeader>

    <section class="app-stat-grid">
      <AppStatCard
        :label="t('bank.current_balance')"
        :value="displayBalanceValue"
        :caption="currentBalanceCaption"
      />
      <AppStatCard
        :label="t('bank.period_variation')"
        :value="formatSignedAmount(displayedPeriodVariation)"
        :caption="periodVariationCaption"
        :tone="displayedPeriodVariationTone"
      />
      <AppStatCard
        :label="t('bank.transactions_title')"
        :value="displayedTransactions.length"
        :caption="t('bank.metrics.transactions_total', { count: transactions.length })"
      />
      <AppStatCard
        :label="t('bank.deposits_title')"
        :value="displayedDeposits.length"
        :caption="t('bank.metrics.pending_payments', { count: undepositedPayments.length })"
        tone="warn"
      />
    </section>

    <AppPanel :title="t('bank.funds_chart_title')" dense>
      <p class="bank-chart-panel__intro">{{ t('bank.funds_chart_intro') }}</p>
      <TrendLineChart
        :data="fundsChartData"
        :series="fundsChartSeries"
        :empty-label="t('bank.funds_chart_empty')"
        :ariaLabel="t('bank.funds_chart_title')"
      />
    </AppPanel>

    <AppPanel :title="t('bank.title')" dense>
      <div class="app-toolbar">
        <div class="app-filter-grid">
          <div class="app-field app-field--span-2">
            <label class="app-field__label">{{ t('common.filter_placeholder') }}</label>
            <InputText v-model="activeGlobalFilter" :placeholder="t('common.filter_placeholder')" />
          </div>
          <div class="app-field">
            <label class="app-field__label">{{ t('common.reset_filters') }}</label>
            <Button
              icon="pi pi-filter-slash"
              severity="secondary"
              outlined
              :disabled="!activeHasFilters"
              @click="resetActiveFilters"
            />
          </div>
        </div>
      </div>

      <Tabs v-model:value="activeTab">
        <TabList>
          <Tab value="transactions">{{ t('bank.transactions_title') }}</Tab>
          <Tab value="deposits">{{ t('bank.deposits_title') }}</Tab>
        </TabList>

        <TabPanels>
          <TabPanel value="transactions">
            <div class="bank-panel-toolbar">
              <ToggleButton
                v-model="unreconciledOnly"
                :on-label="t('bank.tx_reconciled')"
                :off-label="t('bank.tx_reconciled')"
                @change="loadTransactions"
              />
            </div>
            <DataTable
              v-model:filters="transactionTableFilters"
              :value="transactionRows"
              :loading="loadingTx"
              class="app-data-table"
              filter-display="menu"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              :global-filter-fields="[
                'date',
                'amount',
                'description',
                'reference',
                'balance_after',
                'reconciled_label',
                'detected_category_label',
                'source_label',
              ]"
              data-key="id"
              size="small"
              row-hover
              removable-sort
              @value-change="syncDisplayedTransactions"
            >
              <Column
                field="date"
                :header="t('bank.tx_date')"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
                <template #filter="{ filterModel }">
                  <AppDateRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="amount_value"
                :header="t('bank.tx_amount')"
                class="app-money bank-table__amount"
                sortable
                filter-field="amount_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <span :class="parseFloat(data.amount) >= 0 ? 'bank-positive' : 'bank-negative'">
                    {{ formatAmount(data.amount) }}
                  </span>
                </template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="description"
                :header="t('bank.tx_description')"
                class="bank-table__description"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText v-model="filterModel.value" :placeholder="t('bank.tx_description')" />
                </template>
              </Column>
              <Column
                field="reference"
                :header="t('bank.tx_reference')"
                class="bank-table__reference"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText v-model="filterModel.value" :placeholder="t('bank.tx_reference')" />
                </template>
              </Column>
              <Column
                field="balance_after_value"
                :header="t('bank.tx_balance_short')"
                class="bank-table__balance"
                sortable
                filter-field="balance_after_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">{{ formatAmount(data.balance_after) }}</template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="reconciled_label"
                :header="t('bank.tx_reconciled_short')"
                class="bank-table__reconciled"
                sortable
                filter-field="reconciled"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <i
                    :class="
                      data.reconciled
                        ? 'pi pi-check-circle text-green-500'
                        : 'pi pi-circle text-surface-400'
                    "
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
                field="detected_category_label"
                :header="t('bank.tx_category_short')"
                class="bank-table__category"
                sortable
                filter-field="detected_category"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <Tag
                    class="bank-detected-category-tag"
                    :value="t(`bank.categories.${data.detected_category}`)"
                  />
                </template>
                <template #filter="{ filterModel }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="categoryOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                  />
                </template>
              </Column>
              <Column
                field="source_label"
                :header="t('bank.tx_source_short')"
                class="bank-table__source"
                sortable
                filter-field="source"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <Tag
                    :value="t(`bank.sources.${data.source}`)"
                    :severity="data.source === 'system_opening' ? 'info' : 'secondary'"
                  />
                </template>
                <template #filter="{ filterModel }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="sourceOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                  />
                </template>
              </Column>
              <Column :header="t('common.actions')" style="width: 7.25rem">
                <template #body="{ data }">
                  <Button
                    v-if="canLinkExistingSupplierPayment(data)"
                    icon="pi pi-link"
                    size="small"
                    severity="secondary"
                    text
                    :title="t('bank.link_supplier_payment')"
                    @click="openExistingSupplierPaymentDialog(data)"
                  />
                  <Button
                    v-if="canCreateSupplierPayment(data)"
                    icon="pi pi-arrow-up-right"
                    size="small"
                    severity="secondary"
                    text
                    :title="t('bank.create_supplier_payment')"
                    @click="openSupplierPaymentDialog(data)"
                  />
                  <Button
                    v-if="canLinkExistingClientPayment(data)"
                    icon="pi pi-link"
                    size="small"
                    severity="secondary"
                    text
                    :title="t('bank.link_client_payment')"
                    @click="openExistingClientPaymentDialog(data)"
                  />
                  <Button
                    v-if="canCreateClientPayment(data)"
                    icon="pi pi-wallet"
                    size="small"
                    severity="secondary"
                    text
                    :title="t('bank.create_client_payment')"
                    @click="openClientPaymentDialog(data)"
                  />
                  <Button
                    v-if="!data.reconciled"
                    icon="pi pi-check"
                    size="small"
                    severity="success"
                    text
                    :title="t('bank.reconcile')"
                    @click="reconcile(data)"
                  />
                </template>
              </Column>
              <template #empty>
                <div class="app-empty-state">{{ t('bank.transactions_empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>

          <TabPanel value="deposits">
            <DataTable
              v-model:filters="depositTableFilters"
              :value="depositRows"
              :loading="loadingDeposits"
              class="app-data-table"
              filter-display="menu"
              striped-rows
              paginator
              :rows="20"
              :rows-per-page-options="[20, 50, 100, 500]"
              :global-filter-fields="[
                'date',
                'type_label',
                'total_amount',
                'bank_reference',
                'payment_count_label',
              ]"
              data-key="id"
              size="small"
              row-hover
              removable-sort
              @value-change="syncDisplayedDeposits"
            >
              <Column
                field="date"
                :header="t('bank.deposit_date')"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">{{ formatDisplayDate(data.date) }}</template>
                <template #filter="{ filterModel }">
                  <AppDateRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="type_label"
                :header="t('bank.deposit_type')"
                sortable
                filter-field="type"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  <Tag :value="t(`bank.deposit_types.${data.type}`)" />
                </template>
                <template #filter="{ filterModel }">
                  <AppFilterMultiSelect
                    v-model="filterModel.value"
                    :options="depositTypeOptions"
                    option-label="label"
                    option-value="value"
                    :placeholder="t('common.all')"
                    display="chip"
                    show-clear
                  />
                </template>
              </Column>
              <Column
                field="total_amount_value"
                :header="t('bank.deposit_total')"
                class="app-money"
                sortable
                filter-field="total_amount_value"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">{{ formatAmount(data.total_amount) }}</template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <Column
                field="bank_reference"
                :header="t('bank.deposit_bank_ref')"
                sortable
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #filter="{ filterModel }">
                  <InputText
                    v-model="filterModel.value"
                    :placeholder="t('bank.deposit_bank_ref')"
                  />
                </template>
              </Column>
              <Column
                field="payment_count"
                :header="t('bank.deposit_payments')"
                sortable
                filter-field="payment_count"
                data-type="numeric"
                :show-filter-match-modes="false"
                :show-add-button="false"
              >
                <template #body="{ data }">
                  {{
                    t('bank.metrics.deposit_payment_count', {
                      count: data.payment_ids?.length || 0,
                    })
                  }}
                </template>
                <template #filter="{ filterModel }">
                  <AppNumberRangeFilter v-model="filterModel.value" />
                </template>
              </Column>
              <template #empty>
                <div class="app-empty-state">{{ t('bank.deposits_empty') }}</div>
              </template>
            </DataTable>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </AppPanel>

    <!-- Add transaction dialog -->
    <Dialog
      v-model:visible="txDialogVisible"
      :header="t('bank.new_transaction')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <form class="app-dialog-form bank-form" @submit.prevent="submitTransaction">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.transactions_title') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.transaction_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.tx_date') }}</label>
              <DatePicker v-model="txForm.date" date-format="yy-mm-dd" show-icon />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.tx_amount') }}</label>
              <InputNumber
                v-model="txForm.amount"
                mode="decimal"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
              />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('bank.tx_description') }}</label>
              <InputText v-model="txForm.description" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.tx_reference') }}</label>
              <InputText v-model="txForm.reference" />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.tx_balance') }}</label>
              <InputNumber
                v-model="txForm.balance_after"
                mode="decimal"
                :min-fraction-digits="2"
                :max-fraction-digits="2"
              />
            </div>
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="txDialogVisible = false"
          />
          <Button type="submit" :label="t('common.save')" :loading="saving" />
        </div>
      </form>
    </Dialog>

    <!-- Statement import dialog -->
    <Dialog
      v-model:visible="importDialogVisible"
      :header="t('bank.import_dialog_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form bank-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.import_statement') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.import_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-form-grid">
            <div class="app-field app-field--span-2">
              <label class="app-field__label">{{ t('bank.import_file_label') }}</label>
              <div class="bank-import-file-row">
                <Button
                  :label="t('bank.import_pick_file')"
                  icon="pi pi-paperclip"
                  severity="secondary"
                  outlined
                  @click="openImportFilePicker"
                />
                <span class="bank-import-file-name">
                  {{ importFileName || t('bank.import_no_file') }}
                </span>
              </div>
              <input
                ref="importFileInput"
                type="file"
                class="bank-import-file-input"
                accept=".csv,.ofx,.qfx,.qif,text/csv,text/plain,application/xml,text/xml"
                @change="onImportFileSelected"
              />
            </div>
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="importDialogVisible = false"
          />
          <Button
            :label="t('bank.import_statement')"
            icon="pi pi-upload"
            :loading="saving"
            @click="submitImport"
          />
        </div>
      </div>
    </Dialog>

    <Dialog
      v-model:visible="clientPaymentDialogVisible"
      :header="t('bank.create_client_payment_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form bank-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.create_client_payment') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.create_client_payment_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <p v-if="clientPaymentTransaction" class="app-dialog-note">
            {{
              t('bank.create_client_payment_tx_summary', {
                date: formatDisplayDate(clientPaymentTransaction.date),
                amount: formatAmount(clientPaymentTransaction.amount),
                description:
                  clientPaymentTransaction.description || clientPaymentTransaction.reference || '-',
              })
            }}
          </p>
          <div class="app-field">
            <label class="app-field__label">{{
              t('bank.create_client_payment_allocations')
            }}</label>
            <div
              v-if="!clientPaymentLoading && clientPaymentAllocations.length > 0"
              class="app-dialog-list bank-allocation-list"
            >
              <div
                v-for="allocation in clientPaymentAllocations"
                :key="allocation.invoice_id"
                class="app-dialog-list__item bank-allocation-item"
              >
                <div class="bank-allocation-item__summary">
                  <Checkbox
                    v-model="allocation.selected"
                    binary
                    @update:model-value="syncClientAllocationAmount(allocation)"
                  />
                  <span class="app-dialog-list__meta">
                    <span class="app-dialog-list__title">{{ allocation.title }}</span>
                    <span class="app-dialog-list__caption">{{ allocation.caption }}</span>
                  </span>
                </div>
                <div class="bank-allocation-item__amount">
                  <label class="app-field__label">{{
                    t('bank.create_client_payment_allocated_amount')
                  }}</label>
                  <InputNumber
                    v-model="allocation.allocated_amount"
                    mode="currency"
                    currency="EUR"
                    locale="fr-FR"
                    :min="0"
                    :max="clientAllocationMaxAmount(allocation)"
                    :disabled="!allocation.selected"
                    fluid
                    @update:model-value="syncClientAllocationAmount(allocation)"
                  />
                </div>
              </div>
            </div>
          </div>
          <Message
            v-if="!clientPaymentLoading && clientPaymentAllocations.length === 0"
            severity="warn"
          >
            {{ t('bank.create_client_payment_no_invoice') }}
          </Message>
          <Message
            v-else-if="!clientPaymentLoading"
            :severity="Math.abs(clientPaymentRemainingToAllocate) < 0.005 ? 'info' : 'warn'"
          >
            {{
              Math.abs(clientPaymentRemainingToAllocate) < 0.005
                ? t('bank.create_client_payment_ready_to_save')
                : t('bank.create_client_payment_remaining_to_allocate', {
                    amount: formatAmount(clientPaymentRemainingToAllocate),
                  })
            }}
          </Message>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="clientPaymentDialogVisible = false"
          />
          <Button
            :label="t('common.save')"
            :loading="clientPaymentSaving"
            :disabled="clientPaymentLoading || !canSubmitClientPayment"
            @click="submitClientPayment"
          />
        </div>
      </div>
    </Dialog>

    <Dialog
      v-model:visible="existingClientPaymentDialogVisible"
      :header="t('bank.link_client_payment_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form bank-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.link_client_payment') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.link_client_payment_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <p v-if="existingClientPaymentTransaction" class="app-dialog-note">
            {{
              t('bank.create_client_payment_tx_summary', {
                date: formatDisplayDate(existingClientPaymentTransaction.date),
                amount: formatAmount(existingClientPaymentTransaction.amount),
                description:
                  existingClientPaymentTransaction.description ||
                  existingClientPaymentTransaction.reference ||
                  '-',
              })
            }}
          </p>
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.link_client_payment_payments') }}</label>
            <div
              v-if="!existingClientPaymentLoading && existingClientPaymentSelections.length > 0"
              class="app-dialog-list bank-allocation-list"
            >
              <div
                v-for="selection in existingClientPaymentSelections"
                :key="selection.payment_id"
                class="app-dialog-list__item bank-allocation-item"
              >
                <div class="bank-allocation-item__summary">
                  <Checkbox v-model="selection.selected" binary />
                  <span class="app-dialog-list__meta">
                    <span class="app-dialog-list__title">{{ selection.title }}</span>
                    <span class="app-dialog-list__caption">{{ selection.caption }}</span>
                  </span>
                </div>
                <strong class="bank-allocation-item__fixed-amount">{{
                  formatAmount(selection.amount)
                }}</strong>
              </div>
            </div>
          </div>
          <Message
            v-if="!existingClientPaymentLoading && existingClientPaymentSelections.length === 0"
            severity="warn"
          >
            {{ t('bank.link_client_payment_no_payment') }}
          </Message>
          <Message
            v-else-if="!existingClientPaymentLoading"
            :severity="Math.abs(existingClientPaymentRemainingToMatch) < 0.005 ? 'info' : 'warn'"
          >
            {{
              Math.abs(existingClientPaymentRemainingToMatch) < 0.005
                ? t('bank.link_client_payment_ready_to_confirm')
                : t('bank.link_client_payment_remaining_to_match', {
                    amount: formatAmount(existingClientPaymentRemainingToMatch),
                  })
            }}
          </Message>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="existingClientPaymentDialogVisible = false"
          />
          <Button
            :label="t('common.confirm')"
            :loading="existingClientPaymentSaving"
            :disabled="existingClientPaymentLoading || !canSubmitExistingClientPayment"
            @click="submitExistingClientPayment"
          />
        </div>
      </div>
    </Dialog>

    <Dialog
      v-model:visible="supplierPaymentDialogVisible"
      :header="t('bank.create_supplier_payment_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form bank-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.create_supplier_payment') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.create_supplier_payment_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <p v-if="supplierPaymentTransaction" class="app-dialog-note">
            {{
              t('bank.create_client_payment_tx_summary', {
                date: formatDisplayDate(supplierPaymentTransaction.date),
                amount: formatAmount(supplierPaymentTransaction.amount),
                description:
                  supplierPaymentTransaction.description ||
                  supplierPaymentTransaction.reference ||
                  '-',
              })
            }}
          </p>
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.create_supplier_payment_invoice') }}</label>
            <Select
              v-model="supplierPaymentForm.invoice_id"
              :options="supplierPaymentInvoiceOptions"
              option-label="label"
              option-value="value"
              :loading="supplierPaymentLoading"
              :placeholder="
                supplierPaymentLoading
                  ? t('common.loading')
                  : t('bank.create_supplier_payment_invoice')
              "
              filter
              show-clear
            />
          </div>
          <Message
            v-if="!supplierPaymentLoading && supplierPaymentInvoiceOptions.length === 0"
            severity="warn"
          >
            {{ t('bank.create_supplier_payment_no_invoice') }}
          </Message>
          <Message
            v-else-if="!supplierPaymentLoading && supplierPaymentForm.invoice_id !== null"
            severity="info"
          >
            {{ t('bank.suggested_candidate_hint') }}
          </Message>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="supplierPaymentDialogVisible = false"
          />
          <Button
            :label="t('common.save')"
            :loading="supplierPaymentSaving"
            :disabled="supplierPaymentForm.invoice_id === null || supplierPaymentLoading"
            @click="submitSupplierPayment"
          />
        </div>
      </div>
    </Dialog>

    <Dialog
      v-model:visible="existingSupplierPaymentDialogVisible"
      :header="t('bank.link_supplier_payment_title')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form bank-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.link_supplier_payment') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.link_supplier_payment_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <p v-if="existingSupplierPaymentTransaction" class="app-dialog-note">
            {{
              t('bank.create_client_payment_tx_summary', {
                date: formatDisplayDate(existingSupplierPaymentTransaction.date),
                amount: formatAmount(existingSupplierPaymentTransaction.amount),
                description:
                  existingSupplierPaymentTransaction.description ||
                  existingSupplierPaymentTransaction.reference ||
                  '-',
              })
            }}
          </p>
          <div class="app-field">
            <label class="app-field__label">{{ t('bank.link_supplier_payment_payment') }}</label>
            <Select
              v-model="existingSupplierPaymentForm.payment_id"
              :options="existingSupplierPaymentOptions"
              option-label="label"
              option-value="value"
              :loading="existingSupplierPaymentLoading"
              :placeholder="
                existingSupplierPaymentLoading
                  ? t('common.loading')
                  : t('bank.link_supplier_payment_payment')
              "
              filter
              show-clear
            />
          </div>
          <Message
            v-if="!existingSupplierPaymentLoading && existingSupplierPaymentOptions.length === 0"
            severity="warn"
          >
            {{ t('bank.link_supplier_payment_no_payment') }}
          </Message>
          <Message
            v-else-if="
              !existingSupplierPaymentLoading && existingSupplierPaymentForm.payment_id !== null
            "
            severity="info"
          >
            {{ t('bank.suggested_candidate_hint') }}
          </Message>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="existingSupplierPaymentDialogVisible = false"
          />
          <Button
            :label="t('common.confirm')"
            :loading="existingSupplierPaymentSaving"
            :disabled="
              existingSupplierPaymentForm.payment_id === null || existingSupplierPaymentLoading
            "
            @click="submitExistingSupplierPayment"
          />
        </div>
      </div>
    </Dialog>

    <!-- Create deposit dialog -->
    <Dialog
      v-model:visible="depositDialogVisible"
      :header="t('bank.new_deposit')"
      modal
      class="app-dialog app-dialog--medium"
    >
      <div class="app-dialog-form bank-form">
        <section class="app-dialog-intro">
          <p class="app-dialog-intro__eyebrow">{{ t('bank.deposits_title') }}</p>
          <p class="app-dialog-intro__text">{{ t('bank.deposit_intro') }}</p>
        </section>
        <section class="app-dialog-section">
          <div class="app-form-grid">
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.deposit_date') }}</label>
              <DatePicker v-model="depositForm.date" date-format="yy-mm-dd" show-icon />
            </div>
            <div class="app-field">
              <label class="app-field__label">{{ t('bank.deposit_type') }}</label>
              <Select
                v-model="depositForm.type"
                :options="depositTypeOptions"
                option-label="label"
                option-value="value"
              />
            </div>
            <div class="app-field app-field--full">
              <label class="app-field__label">{{ t('bank.deposit_bank_ref') }}</label>
              <InputText v-model="depositForm.bank_reference" />
            </div>
          </div>
        </section>
        <section class="app-dialog-section">
          <div class="app-dialog-section__header">
            <h3 class="app-dialog-section__title">{{ t('bank.deposit_selection_title') }}</h3>
            <p class="app-dialog-section__copy">{{ t('bank.deposit_selection_subtitle') }}</p>
          </div>
          <Message v-if="availableDepositPayments.length === 0" severity="warn">
            {{ t('bank.deposit_empty') }}
          </Message>
          <p v-if="availableDepositPayments.length === 0" class="app-dialog-note">
            {{ t('bank.deposit_empty_hint') }}
          </p>
          <div v-else class="app-dialog-list">
            <label
              v-for="p in availableDepositPayments"
              :key="p.id"
              class="app-dialog-list__item bank-payment-option"
            >
              <Checkbox v-model="depositForm.payment_ids" :value="p.id" />
              <span class="app-dialog-list__meta">
                <span class="app-dialog-list__title"
                  >{{ formatDisplayDate(p.date) }} — {{ formatAmount(p.amount) }}</span
                >
                <span class="app-dialog-list__caption">{{
                  t(`payments.methods.${p.method}`)
                }}</span>
              </span>
            </label>
          </div>
        </section>
        <div class="app-form-actions">
          <Button
            :label="t('common.cancel')"
            severity="secondary"
            text
            @click="depositDialogVisible = false"
          />
          <Button
            :label="t('common.save')"
            :loading="saving"
            :disabled="depositForm.payment_ids.length === 0"
            @click="submitDeposit"
          />
        </div>
      </div>
    </Dialog>
  </AppPage>
</template>

<script setup lang="ts">
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import DatePicker from 'primevue/datepicker'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Select from 'primevue/select'
import Tab from 'primevue/tab'
import TabList from 'primevue/tablist'
import TabPanel from 'primevue/tabpanel'
import TabPanels from 'primevue/tabpanels'
import Tabs from 'primevue/tabs'
import Tag from 'primevue/tag'
import ToggleButton from 'primevue/togglebutton'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { listContactsApi, type Contact } from '@/api/contacts'
import TrendLineChart, {
  type TrendLineChartSeries,
} from '../components/charts/TrendLineChart.vue'
import AppPage from '../components/ui/AppPage.vue'
import AppDateRangeFilter from '../components/ui/AppDateRangeFilter.vue'
import AppFilterMultiSelect from '../components/ui/AppFilterMultiSelect.vue'
import AppNumberRangeFilter from '../components/ui/AppNumberRangeFilter.vue'
import AppPageHeader from '../components/ui/AppPageHeader.vue'
import AppPanel from '../components/ui/AppPanel.vue'
import AppStatCard from '../components/ui/AppStatCard.vue'
import {
  addTransaction,
  createClientPaymentsFromTransaction,
  createDeposit,
  createSupplierPaymentFromTransaction,
  getBankBalance,
  getBankFundsChart,
  importBankStatement,
  linkClientPaymentToTransaction,
  linkClientPaymentsToTransaction,
  linkSupplierPaymentToTransaction,
  listDeposits,
  listTransactions,
  updateTransaction,
  type BankImportFormat,
  type BankTransactionClientPaymentAllocation,
  type BankTransaction,
  type Deposit,
  type FundsChartRow as BankFundsChartRow,
} from '@/api/bank'
import { listInvoicesApi, type Invoice } from '@/api/invoices'
import { listPayments, type Payment } from '@/api/payments'
import { useFiscalYearStore } from '@/stores/fiscalYear'
import { scoreInvoiceSuggestion, scorePaymentSuggestion } from '@/utils/bankReconciliation'
import { formatContactDisplayName } from '@/utils/contact'
import { formatDisplayDate } from '@/utils/format'
import {
  dateRangeFilter,
  inFilter,
  numericRangeFilter,
  textFilter,
  useDataTableFilters,
} from '../composables/useDataTableFilters'

const { t } = useI18n()
const toast = useToast()
const fiscalYearStore = useFiscalYearStore()

const balance = ref('0')
const fundsChartData = ref<BankFundsChartRow[]>([])
const transactions = ref<BankTransaction[]>([])
const deposits = ref<Deposit[]>([])
const undepositedPayments = ref<Payment[]>([])
const loadingTx = ref(false)
const loadingDeposits = ref(false)
const activeTab = ref('transactions')
const unreconciledOnly = ref(false)
const txDialogVisible = ref(false)
const importDialogVisible = ref(false)
const depositDialogVisible = ref(false)
const saving = ref(false)
const clientPaymentDialogVisible = ref(false)
const clientPaymentSaving = ref(false)
const clientPaymentLoading = ref(false)
const existingClientPaymentDialogVisible = ref(false)
const existingClientPaymentSaving = ref(false)
const existingClientPaymentLoading = ref(false)
const supplierPaymentDialogVisible = ref(false)
const supplierPaymentSaving = ref(false)
const supplierPaymentLoading = ref(false)
const existingSupplierPaymentDialogVisible = ref(false)
const existingSupplierPaymentSaving = ref(false)
const existingSupplierPaymentLoading = ref(false)
const importContent = ref('')
const importFileName = ref('')
const importFileInput = ref<HTMLInputElement | null>(null)
const clientPaymentTransaction = ref<BankTransaction | null>(null)
const existingClientPaymentTransaction = ref<BankTransaction | null>(null)
const supplierPaymentTransaction = ref<BankTransaction | null>(null)
const existingSupplierPaymentTransaction = ref<BankTransaction | null>(null)
const clientInvoices = ref<Invoice[]>([])
const supplierInvoices = ref<Invoice[]>([])
const clientContacts = ref<Contact[]>([])
const existingClientPayments = ref<Payment[]>([])
const existingSupplierPayments = ref<Payment[]>([])

interface ClientPaymentAllocationDraft {
  invoice_id: number
  title: string
  caption: string
  remaining_amount: number
  allocated_amount: number
  selected: boolean
}

interface ExistingClientPaymentSelectionDraft {
  payment_id: number
  title: string
  caption: string
  amount: number
  selected: boolean
}

const depositTypeOptions = [
  { label: t('bank.deposit_types.cheques'), value: 'cheques' },
  { label: t('bank.deposit_types.especes'), value: 'especes' },
]

const sourceOptions = [
  { label: t('bank.sources.manual'), value: 'manual' },
  { label: t('bank.sources.import'), value: 'import' },
  { label: t('bank.sources.system_opening'), value: 'system_opening' },
]

const categoryOptions = [
  { label: t('bank.categories.customer_payment'), value: 'customer_payment' },
  { label: t('bank.categories.cheque_deposit'), value: 'cheque_deposit' },
  { label: t('bank.categories.cash_deposit'), value: 'cash_deposit' },
  { label: t('bank.categories.supplier_payment'), value: 'supplier_payment' },
  { label: t('bank.categories.salary'), value: 'salary' },
  { label: t('bank.categories.social_charge'), value: 'social_charge' },
  { label: t('bank.categories.bank_fee'), value: 'bank_fee' },
  { label: t('bank.categories.internal_transfer'), value: 'internal_transfer' },
  { label: t('bank.categories.grant'), value: 'grant' },
  { label: t('bank.categories.sepa_debit'), value: 'sepa_debit' },
  { label: t('bank.categories.other_credit'), value: 'other_credit' },
  { label: t('bank.categories.other_debit'), value: 'other_debit' },
  { label: t('bank.categories.uncategorized'), value: 'uncategorized' },
]

const yesNoOptions = [
  { label: t('common.yes'), value: true },
  { label: t('common.no'), value: false },
]

const transactionRows = computed(() =>
  transactions.value.map((transaction) => ({
    ...transaction,
    amount_value: parseFloat(transaction.amount),
    balance_after_value: parseFloat(transaction.balance_after),
    reconciled_label: transaction.reconciled ? t('common.yes') : t('common.no'),
    detected_category_label: t(`bank.categories.${transaction.detected_category}`),
    source_label: t(`bank.sources.${transaction.source}`),
  })),
)

const depositRows = computed(() =>
  deposits.value.map((deposit) => ({
    ...deposit,
    type_label: t(`bank.deposit_types.${deposit.type}`),
    total_amount_value: parseFloat(deposit.total_amount),
    payment_count: deposit.payment_ids?.length || 0,
    payment_count_label: `${deposit.payment_ids?.length || 0}`,
  })),
)

const availableDepositPayments = computed(() => {
  const expectedMethod = depositForm.value.type === 'cheques' ? 'cheque' : 'especes'
  return undepositedPayments.value.filter((payment) => payment.method === expectedMethod)
})

const displayedPeriodVariation = computed(() =>
  displayedTransactions.value.reduce(
    (total, transaction) => total + parseFloat(transaction.amount),
    0,
  ),
)

const selectedPeriodLabel = computed(
  () => fiscalYearStore.selectedFiscalYear?.name ?? t('app.all_fiscal_years'),
)

const displayedPeriodVariationTone = computed(() => {
  if (displayedPeriodVariation.value > 0) return 'success'
  if (displayedPeriodVariation.value < 0) return 'danger'
  return 'warn'
})

const {
  filters: transactionTableFilters,
  globalFilter: transactionGlobalFilter,
  displayedRows: displayedTransactions,
  hasActiveFilters: transactionHasActiveFilters,
  resetFilters: resetTransactionFilters,
  syncDisplayedRows: syncDisplayedTransactions,
} = useDataTableFilters(transactionRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  amount_value: numericRangeFilter(),
  description: textFilter(),
  reference: textFilter(),
  balance_after_value: numericRangeFilter(),
  reconciled: inFilter(),
  detected_category: inFilter(),
  source: inFilter(),
})

const {
  filters: depositTableFilters,
  globalFilter: depositGlobalFilter,
  displayedRows: displayedDeposits,
  hasActiveFilters: depositHasActiveFilters,
  resetFilters: resetDepositFilters,
  syncDisplayedRows: syncDisplayedDeposits,
} = useDataTableFilters(depositRows, {
  global: textFilter(''),
  date: dateRangeFilter(),
  type: inFilter(),
  total_amount_value: numericRangeFilter(),
  bank_reference: textFilter(),
  payment_count: numericRangeFilter(),
})

const activeGlobalFilter = computed({
  get: () =>
    activeTab.value === 'transactions' ? transactionGlobalFilter.value : depositGlobalFilter.value,
  set: (value: string) => {
    if (activeTab.value === 'transactions') {
      transactionGlobalFilter.value = value
    } else {
      depositGlobalFilter.value = value
    }
  },
})

const activeHasFilters = computed(() =>
  activeTab.value === 'transactions'
    ? transactionHasActiveFilters.value
    : depositHasActiveFilters.value,
)

function pickLatestVisibleBalanceAfter(
  rows: Array<{ id: number; date: string; balance_after: string }>,
): string | null {
  if (rows.length === 0) {
    return null
  }

  const latestRow = rows.reduce((latest, current) => {
    if (current.date > latest.date) {
      return current
    }
    if (current.date === latest.date && current.id > latest.id) {
      return current
    }
    return latest
  })

  return latestRow.balance_after
}

const scopedBalance = computed(() => pickLatestVisibleBalanceAfter(displayedTransactions.value))

const displayBalanceValue = computed(() => formatAmount(scopedBalance.value ?? balance.value))

const currentBalanceCaption = computed(() =>
  transactionHasActiveFilters.value || fiscalYearStore.selectedFiscalYear
    ? t('bank.metrics.visible_scope_caption')
    : t('bank.metrics.current_balance_caption'),
)

const fundsChartSeries = computed<TrendLineChartSeries[]>(() => [
  {
    key: 'total',
    label: t('bank.funds_chart_total'),
    color: '#0f766e',
    fill: true,
  },
  {
    key: 'current_account',
    label: t('bank.funds_chart_current_account'),
    color: '#2563eb',
  },
  {
    key: 'savings_account',
    label: t('bank.funds_chart_savings_account'),
    color: '#ea580c',
    dashed: true,
  },
])

const periodVariationCaption = computed(() =>
  transactionHasActiveFilters.value
    ? t('bank.metrics.visible_scope_caption')
    : t('bank.metrics.period_variation_caption', { period: selectedPeriodLabel.value }),
)

function resetActiveFilters() {
  if (activeTab.value === 'transactions') {
    resetTransactionFilters()
    return
  }

  resetDepositFilters()
}

const txForm = ref({
  date: new Date(),
  amount: 0,
  description: '',
  reference: '',
  balance_after: 0,
})
const depositForm = ref({
  date: new Date(),
  type: 'cheques' as 'cheques' | 'especes',
  bank_reference: '',
  payment_ids: [] as number[],
})
const clientPaymentForm = ref({
  allocations: [] as ClientPaymentAllocationDraft[],
})
const existingClientPaymentForm = ref({
  selections: [] as ExistingClientPaymentSelectionDraft[],
})
const supplierPaymentForm = ref({
  invoice_id: null as number | null,
})
const existingSupplierPaymentForm = ref({
  payment_id: null as number | null,
})

function formatAmount(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

function formatSignedAmount(value: number): string {
  if (value > 0) {
    return `+${formatAmount(value)}`
  }
  return formatAmount(value)
}

function contactName(contactId: number): string {
  const contact = clientContacts.value.find((candidate) => candidate.id === contactId)
  if (!contact) {
    return `#${contactId}`
  }
  return formatContactDisplayName(contact)
}

function invoiceRemainingAmount(invoice: Invoice): number {
  return Math.max(0, parseFloat(invoice.total_amount) - parseFloat(invoice.paid_amount))
}

function resolveApiErrorMessage(error: unknown): string {
  const detail = (
    error as {
      response?: {
        data?: {
          detail?: unknown
        }
      }
    }
  )?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail
  }
  return t('common.error.unknown')
}

const sortedClientPaymentInvoices = computed(() => {
  const transactionAmount = clientPaymentTransaction.value
    ? parseFloat(clientPaymentTransaction.value.amount)
    : 0

  return clientInvoices.value
    .filter(
      (invoice) =>
        ['sent', 'partial', 'overdue'].includes(invoice.status) &&
        invoiceRemainingAmount(invoice) > 0,
    )
    .sort((left, right) => {
      const leftScore = scoreInvoiceSuggestion({
        transactionAmount,
        transactionDate: clientPaymentTransaction.value?.date ?? '',
        transactionDescription: clientPaymentTransaction.value?.description ?? '',
        transactionReference: clientPaymentTransaction.value?.reference,
        candidateNumber: left.number,
        candidateReference: left.reference,
        candidateContactName: contactName(left.contact_id),
        candidateDate: left.date,
        candidateRemainingAmount: invoiceRemainingAmount(left),
      })
      const rightScore = scoreInvoiceSuggestion({
        transactionAmount,
        transactionDate: clientPaymentTransaction.value?.date ?? '',
        transactionDescription: clientPaymentTransaction.value?.description ?? '',
        transactionReference: clientPaymentTransaction.value?.reference,
        candidateNumber: right.number,
        candidateReference: right.reference,
        candidateContactName: contactName(right.contact_id),
        candidateDate: right.date,
        candidateRemainingAmount: invoiceRemainingAmount(right),
      })
      if (leftScore !== rightScore) {
        return rightScore - leftScore
      }
      return right.date.localeCompare(left.date)
    })
})

const clientPaymentAllocations = computed(() => clientPaymentForm.value.allocations)

const clientPaymentTransactionAmount = computed(() =>
  clientPaymentTransaction.value ? parseFloat(clientPaymentTransaction.value.amount) : 0,
)

const clientPaymentSelectedTotal = computed(() =>
  clientPaymentForm.value.allocations.reduce(
    (sum, allocation) => sum + (allocation.selected ? Number(allocation.allocated_amount || 0) : 0),
    0,
  ),
)

const clientPaymentRemainingToAllocate = computed(() =>
  Number((clientPaymentTransactionAmount.value - clientPaymentSelectedTotal.value).toFixed(2)),
)

const canSubmitClientPayment = computed(
  () =>
    clientPaymentAllocations.value.some(
      (allocation) => allocation.selected && allocation.allocated_amount > 0,
    ) && Math.abs(clientPaymentRemainingToAllocate.value) < 0.005,
)

const supplierPaymentInvoiceOptions = computed(() => {
  const transactionAmount = supplierPaymentTransaction.value
    ? Math.abs(parseFloat(supplierPaymentTransaction.value.amount))
    : 0

  return supplierInvoices.value
    .filter(
      (invoice) =>
        ['sent', 'partial', 'overdue'].includes(invoice.status) &&
        invoiceRemainingAmount(invoice) > 0,
    )
    .sort((left, right) => {
      const leftScore = scoreInvoiceSuggestion({
        transactionAmount,
        transactionDate: supplierPaymentTransaction.value?.date ?? '',
        transactionDescription: supplierPaymentTransaction.value?.description ?? '',
        transactionReference: supplierPaymentTransaction.value?.reference,
        candidateNumber: left.number,
        candidateReference: left.reference,
        candidateContactName: contactName(left.contact_id),
        candidateDate: left.date,
        candidateRemainingAmount: invoiceRemainingAmount(left),
      })
      const rightScore = scoreInvoiceSuggestion({
        transactionAmount,
        transactionDate: supplierPaymentTransaction.value?.date ?? '',
        transactionDescription: supplierPaymentTransaction.value?.description ?? '',
        transactionReference: supplierPaymentTransaction.value?.reference,
        candidateNumber: right.number,
        candidateReference: right.reference,
        candidateContactName: contactName(right.contact_id),
        candidateDate: right.date,
        candidateRemainingAmount: invoiceRemainingAmount(right),
      })
      if (leftScore !== rightScore) {
        return rightScore - leftScore
      }
      return right.date.localeCompare(left.date)
    })
    .map((invoice) => ({
      label: `${invoice.number} · ${contactName(invoice.contact_id)} · ${t(
        'bank.remaining_amount',
        {
          amount: formatAmount(invoiceRemainingAmount(invoice)),
        },
      )}`,
      value: invoice.id,
    }))
})

const sortedExistingClientPayments = computed(() => {
  const transactionAmount = existingClientPaymentTransaction.value
    ? parseFloat(existingClientPaymentTransaction.value.amount)
    : 0

  return existingClientPayments.value
    .filter(
      (payment) =>
        payment.method === 'virement' && parseFloat(payment.amount) <= transactionAmount + 0.0001,
    )
    .sort((left, right) => {
      const leftScore = scorePaymentSuggestion({
        transactionAmount,
        transactionDate: existingClientPaymentTransaction.value?.date ?? '',
        transactionDescription: existingClientPaymentTransaction.value?.description ?? '',
        transactionReference: existingClientPaymentTransaction.value?.reference,
        candidateInvoiceNumber: left.invoice_number,
        candidateReference: left.reference,
        candidateContactName: contactName(left.contact_id),
        candidateDate: left.date,
        candidateAmount: parseFloat(left.amount),
      })
      const rightScore = scorePaymentSuggestion({
        transactionAmount,
        transactionDate: existingClientPaymentTransaction.value?.date ?? '',
        transactionDescription: existingClientPaymentTransaction.value?.description ?? '',
        transactionReference: existingClientPaymentTransaction.value?.reference,
        candidateInvoiceNumber: right.invoice_number,
        candidateReference: right.reference,
        candidateContactName: contactName(right.contact_id),
        candidateDate: right.date,
        candidateAmount: parseFloat(right.amount),
      })
      if (leftScore !== rightScore) {
        return rightScore - leftScore
      }
      return right.date.localeCompare(left.date)
    })
})

const existingClientPaymentSelections = computed(() => existingClientPaymentForm.value.selections)

const existingClientPaymentTransactionAmount = computed(() =>
  existingClientPaymentTransaction.value
    ? parseFloat(existingClientPaymentTransaction.value.amount)
    : 0,
)

const existingClientPaymentSelectedTotal = computed(() =>
  existingClientPaymentForm.value.selections.reduce(
    (sum, selection) => sum + (selection.selected ? selection.amount : 0),
    0,
  ),
)

const existingClientPaymentRemainingToMatch = computed(() =>
  Number(
    (
      existingClientPaymentTransactionAmount.value - existingClientPaymentSelectedTotal.value
    ).toFixed(2),
  ),
)

const canSubmitExistingClientPayment = computed(
  () =>
    existingClientPaymentSelections.value.some((selection) => selection.selected) &&
    Math.abs(existingClientPaymentRemainingToMatch.value) < 0.005,
)

const existingSupplierPaymentOptions = computed(() => {
  const transactionAmount = existingSupplierPaymentTransaction.value
    ? Math.abs(parseFloat(existingSupplierPaymentTransaction.value.amount))
    : 0

  return existingSupplierPayments.value
    .filter(
      (payment) =>
        payment.method === 'virement' &&
        Math.abs(parseFloat(payment.amount) - transactionAmount) < 0.0001,
    )
    .sort((left, right) => {
      const leftScore = scorePaymentSuggestion({
        transactionAmount,
        transactionDate: existingSupplierPaymentTransaction.value?.date ?? '',
        transactionDescription: existingSupplierPaymentTransaction.value?.description ?? '',
        transactionReference: existingSupplierPaymentTransaction.value?.reference,
        candidateInvoiceNumber: left.invoice_number,
        candidateReference: left.reference,
        candidateContactName: contactName(left.contact_id),
        candidateDate: left.date,
        candidateAmount: parseFloat(left.amount),
      })
      const rightScore = scorePaymentSuggestion({
        transactionAmount,
        transactionDate: existingSupplierPaymentTransaction.value?.date ?? '',
        transactionDescription: existingSupplierPaymentTransaction.value?.description ?? '',
        transactionReference: existingSupplierPaymentTransaction.value?.reference,
        candidateInvoiceNumber: right.invoice_number,
        candidateReference: right.reference,
        candidateContactName: contactName(right.contact_id),
        candidateDate: right.date,
        candidateAmount: parseFloat(right.amount),
      })
      if (leftScore !== rightScore) {
        return rightScore - leftScore
      }
      return right.date.localeCompare(left.date)
    })
    .map((payment) => {
      const reference = payment.reference ? ` · ${payment.reference}` : ''
      return {
        label: `${payment.invoice_number || `#${payment.invoice_id}`} · ${contactName(
          payment.contact_id,
        )} · ${formatAmount(payment.amount)} · ${formatDisplayDate(payment.date)}${reference}`,
        value: payment.id,
      }
    })
})

function toIsoDate(d: Date | string): string {
  if (typeof d === 'string') return d
  return d.toISOString().slice(0, 10)
}

function detectImportFormatFromFileName(fileName: string): BankImportFormat {
  const lowerName = fileName.toLowerCase()
  if (lowerName.endsWith('.ofx') || lowerName.endsWith('.qfx')) {
    return 'ofx'
  }
  if (lowerName.endsWith('.qif')) {
    return 'qif'
  }
  return 'csv'
}

function buildClientPaymentAllocationDrafts(): ClientPaymentAllocationDraft[] {
  let remainingToAllocate = clientPaymentTransactionAmount.value

  return sortedClientPaymentInvoices.value.map((invoice) => {
    const remainingAmount = invoiceRemainingAmount(invoice)
    const suggestedAmount = Math.min(remainingAmount, Math.max(remainingToAllocate, 0))
    remainingToAllocate = Number((remainingToAllocate - suggestedAmount).toFixed(2))

    return {
      invoice_id: invoice.id,
      title: `${invoice.number} · ${contactName(invoice.contact_id)}`,
      caption: `${formatDisplayDate(invoice.date)} · ${t('bank.remaining_amount', {
        amount: formatAmount(remainingAmount),
      })}`,
      remaining_amount: remainingAmount,
      allocated_amount: suggestedAmount,
      selected: suggestedAmount > 0,
    }
  })
}

function buildExistingClientPaymentSelectionDrafts(): ExistingClientPaymentSelectionDraft[] {
  let remainingToMatch = existingClientPaymentTransactionAmount.value

  return sortedExistingClientPayments.value.map((payment) => {
    const amount = parseFloat(payment.amount)
    const reference = payment.reference ? ` · ${payment.reference}` : ''
    const selected = amount <= remainingToMatch + 0.0001
    if (selected) {
      remainingToMatch = Number((remainingToMatch - amount).toFixed(2))
    }

    return {
      payment_id: payment.id,
      title: `${payment.invoice_number || `#${payment.invoice_id}`} · ${contactName(
        payment.contact_id,
      )}`,
      caption: `${formatDisplayDate(payment.date)}${reference}`,
      amount,
      selected,
    }
  })
}

function clientAllocationSelectedSumExcluding(invoiceId: number): number {
  return clientPaymentForm.value.allocations.reduce((sum, allocation) => {
    if (!allocation.selected || allocation.invoice_id === invoiceId) {
      return sum
    }
    return sum + Number(allocation.allocated_amount || 0)
  }, 0)
}

function clientAllocationMaxAmount(allocation: ClientPaymentAllocationDraft): number {
  const remainingTxAmount =
    clientPaymentTransactionAmount.value -
    clientAllocationSelectedSumExcluding(allocation.invoice_id)
  return Math.max(0, Math.min(allocation.remaining_amount, remainingTxAmount))
}

function syncClientAllocationAmount(allocation: ClientPaymentAllocationDraft): void {
  if (!allocation.selected) {
    allocation.allocated_amount = 0
    return
  }

  const maxAmount = clientAllocationMaxAmount(allocation)
  const currentAmount = Number(allocation.allocated_amount || 0)

  if (currentAmount <= 0) {
    allocation.allocated_amount = maxAmount
    return
  }

  allocation.allocated_amount = Math.min(currentAmount, maxAmount)
}

function openImportFilePicker() {
  importFileInput.value?.click()
}

async function onImportFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) {
    return
  }

  importFileName.value = file.name
  importContent.value = await file.text()
  input.value = ''
}

async function loadTransactions() {
  loadingTx.value = true
  try {
    transactions.value = await listTransactions({
      from_date: fiscalYearStore.selectedFiscalYear?.start_date,
      to_date: fiscalYearStore.selectedFiscalYear?.end_date,
      unreconciled_only: unreconciledOnly.value,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loadingTx.value = false
  }
}

async function loadDeposits() {
  loadingDeposits.value = true
  try {
    deposits.value = await listDeposits({
      from_date: fiscalYearStore.selectedFiscalYear?.start_date,
      to_date: fiscalYearStore.selectedFiscalYear?.end_date,
    })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    loadingDeposits.value = false
  }
}

async function loadFundsChart() {
  try {
    fundsChartData.value = await getBankFundsChart(6)
  } catch {
    fundsChartData.value = []
  }
}

async function loadAll() {
  const [b] = await Promise.all([
    getBankBalance(),
    loadTransactions(),
    loadDeposits(),
    loadFundsChart(),
  ])
  balance.value = b.balance
}

async function reconcile(tx: BankTransaction) {
  await updateTransaction(tx.id, { reconciled: true })
  await loadTransactions()
}

function canCreateClientPayment(tx: BankTransaction): boolean {
  return (
    !tx.reconciled &&
    parseFloat(tx.amount) > 0 &&
    ['customer_payment', 'other_credit'].includes(tx.detected_category)
  )
}

function canLinkExistingClientPayment(tx: BankTransaction): boolean {
  return canCreateClientPayment(tx)
}

function canCreateSupplierPayment(tx: BankTransaction): boolean {
  return (
    !tx.reconciled &&
    parseFloat(tx.amount) < 0 &&
    ['supplier_payment', 'other_debit'].includes(tx.detected_category)
  )
}

function canLinkExistingSupplierPayment(tx: BankTransaction): boolean {
  return canCreateSupplierPayment(tx)
}

async function openClientPaymentDialog(tx: BankTransaction) {
  clientPaymentTransaction.value = tx
  clientPaymentForm.value.allocations = []
  clientPaymentDialogVisible.value = true
  clientPaymentLoading.value = true
  try {
    const [invoices, contacts] = await Promise.all([
      listInvoicesApi({ invoice_type: 'client' }),
      listContactsApi({ active_only: true }),
    ])
    clientInvoices.value = invoices
    clientContacts.value = contacts
    clientPaymentForm.value.allocations = buildClientPaymentAllocationDrafts()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    clientPaymentLoading.value = false
  }
}

async function openExistingClientPaymentDialog(tx: BankTransaction) {
  existingClientPaymentTransaction.value = tx
  existingClientPaymentForm.value.selections = []
  existingClientPaymentDialogVisible.value = true
  existingClientPaymentLoading.value = true
  try {
    const [payments, contacts] = await Promise.all([
      listPayments({ invoice_type: 'client' }),
      listContactsApi({ active_only: true }),
    ])
    existingClientPayments.value = payments
    clientContacts.value = contacts
    existingClientPaymentForm.value.selections = buildExistingClientPaymentSelectionDrafts()
  } catch (error) {
    toast.add({ severity: 'error', summary: resolveApiErrorMessage(error), life: 3000 })
  } finally {
    existingClientPaymentLoading.value = false
  }
}

async function openSupplierPaymentDialog(tx: BankTransaction) {
  supplierPaymentTransaction.value = tx
  supplierPaymentForm.value.invoice_id = null
  supplierPaymentDialogVisible.value = true
  supplierPaymentLoading.value = true
  try {
    const [invoices, contacts] = await Promise.all([
      listInvoicesApi({ invoice_type: 'fournisseur' }),
      listContactsApi({ active_only: true }),
    ])
    supplierInvoices.value = invoices
    clientContacts.value = contacts
    supplierPaymentForm.value.invoice_id = supplierPaymentInvoiceOptions.value[0]?.value ?? null
  } catch (error) {
    toast.add({ severity: 'error', summary: resolveApiErrorMessage(error), life: 3000 })
  } finally {
    supplierPaymentLoading.value = false
  }
}

async function openExistingSupplierPaymentDialog(tx: BankTransaction) {
  existingSupplierPaymentTransaction.value = tx
  existingSupplierPaymentForm.value.payment_id = null
  existingSupplierPaymentDialogVisible.value = true
  existingSupplierPaymentLoading.value = true
  try {
    const [payments, contacts] = await Promise.all([
      listPayments({ invoice_type: 'fournisseur' }),
      listContactsApi({ active_only: true }),
    ])
    existingSupplierPayments.value = payments
    clientContacts.value = contacts
    existingSupplierPaymentForm.value.payment_id =
      existingSupplierPaymentOptions.value[0]?.value ?? null
  } catch (error) {
    toast.add({ severity: 'error', summary: resolveApiErrorMessage(error), life: 3000 })
  } finally {
    existingSupplierPaymentLoading.value = false
  }
}

async function submitClientPayment() {
  if (!clientPaymentTransaction.value || !canSubmitClientPayment.value) {
    return
  }

  clientPaymentSaving.value = true
  try {
    const allocations: BankTransactionClientPaymentAllocation[] =
      clientPaymentForm.value.allocations
        .filter((allocation) => allocation.selected && allocation.allocated_amount > 0)
        .map((allocation) => ({
          invoice_id: allocation.invoice_id,
          amount: allocation.allocated_amount.toFixed(2),
        }))

    await createClientPaymentsFromTransaction(clientPaymentTransaction.value.id, allocations)
    clientPaymentDialogVisible.value = false
    clientPaymentTransaction.value = null
    const allocationCount = allocations.length
    clientPaymentForm.value.allocations = []
    toast.add({
      severity: 'success',
      summary: t('bank.create_client_payment_success', { count: allocationCount }),
      life: 3000,
    })
    await loadTransactions()
  } catch (error) {
    toast.add({ severity: 'error', summary: resolveApiErrorMessage(error), life: 3000 })
  } finally {
    clientPaymentSaving.value = false
  }
}

async function submitExistingClientPayment() {
  if (!existingClientPaymentTransaction.value || !canSubmitExistingClientPayment.value) {
    return
  }

  existingClientPaymentSaving.value = true
  try {
    const paymentIds = existingClientPaymentForm.value.selections
      .filter((selection) => selection.selected)
      .map((selection) => selection.payment_id)

    const [singlePaymentId] = paymentIds
    if (paymentIds.length === 1 && singlePaymentId !== undefined) {
      await linkClientPaymentToTransaction(
        existingClientPaymentTransaction.value.id,
        singlePaymentId,
      )
    } else {
      await linkClientPaymentsToTransaction(existingClientPaymentTransaction.value.id, paymentIds)
    }

    existingClientPaymentDialogVisible.value = false
    existingClientPaymentTransaction.value = null
    existingClientPaymentForm.value.selections = []
    toast.add({
      severity: 'success',
      summary: t('bank.link_client_payment_success', { count: paymentIds.length }),
      life: 3000,
    })
    await loadTransactions()
  } catch (error) {
    toast.add({ severity: 'error', summary: resolveApiErrorMessage(error), life: 3000 })
  } finally {
    existingClientPaymentSaving.value = false
  }
}

async function submitSupplierPayment() {
  if (!supplierPaymentTransaction.value || supplierPaymentForm.value.invoice_id === null) {
    return
  }

  supplierPaymentSaving.value = true
  try {
    await createSupplierPaymentFromTransaction(
      supplierPaymentTransaction.value.id,
      supplierPaymentForm.value.invoice_id,
    )
    supplierPaymentDialogVisible.value = false
    supplierPaymentTransaction.value = null
    supplierPaymentForm.value.invoice_id = null
    toast.add({
      severity: 'success',
      summary: t('bank.create_supplier_payment_success'),
      life: 3000,
    })
    await loadTransactions()
  } catch (error) {
    toast.add({ severity: 'error', summary: resolveApiErrorMessage(error), life: 3000 })
  } finally {
    supplierPaymentSaving.value = false
  }
}

async function submitExistingSupplierPayment() {
  if (
    !existingSupplierPaymentTransaction.value ||
    existingSupplierPaymentForm.value.payment_id === null
  ) {
    return
  }

  existingSupplierPaymentSaving.value = true
  try {
    await linkSupplierPaymentToTransaction(
      existingSupplierPaymentTransaction.value.id,
      existingSupplierPaymentForm.value.payment_id,
    )
    existingSupplierPaymentDialogVisible.value = false
    existingSupplierPaymentTransaction.value = null
    existingSupplierPaymentForm.value.payment_id = null
    toast.add({
      severity: 'success',
      summary: t('bank.link_supplier_payment_success'),
      life: 3000,
    })
    await loadTransactions()
  } catch (error) {
    toast.add({ severity: 'error', summary: resolveApiErrorMessage(error), life: 3000 })
  } finally {
    existingSupplierPaymentSaving.value = false
  }
}

async function submitTransaction() {
  saving.value = true
  try {
    await addTransaction({
      date: toIsoDate(txForm.value.date),
      amount: String(txForm.value.amount),
      description: txForm.value.description,
      reference: txForm.value.reference || null,
      balance_after: String(txForm.value.balance_after),
    })
    txDialogVisible.value = false
    await loadAll()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

async function submitImport() {
  if (!importFileName.value || !importContent.value.trim()) {
    toast.add({ severity: 'warn', summary: t('bank.import_file_required'), life: 3000 })
    return
  }

  saving.value = true
  try {
    const imported = await importBankStatement(
      detectImportFormatFromFileName(importFileName.value),
      importContent.value,
    )
    importDialogVisible.value = false
    importContent.value = ''
    importFileName.value = ''
    toast.add({
      severity: 'success',
      summary: t('bank.import_success', { n: imported.length }),
      life: 3000,
    })
    await loadAll()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

async function openDepositDialog() {
  undepositedPayments.value = await listPayments({
    invoice_type: 'client',
    undeposited_only: true,
    from_date: fiscalYearStore.selectedFiscalYear?.start_date,
    to_date: fiscalYearStore.selectedFiscalYear?.end_date,
  })
  depositForm.value.payment_ids = []
  depositForm.value.type = 'cheques'
  depositDialogVisible.value = true
}

async function submitDeposit() {
  saving.value = true
  try {
    await createDeposit({
      date: toIsoDate(depositForm.value.date),
      type: depositForm.value.type,
      payment_ids: depositForm.value.payment_ids,
      bank_reference: depositForm.value.bank_reference || null,
    })
    depositDialogVisible.value = false
    await loadAll()
  } catch {
    toast.add({ severity: 'error', summary: t('common.error.unknown'), life: 3000 })
  } finally {
    saving.value = false
  }
}

watch(
  () => depositForm.value.type,
  () => {
    depositForm.value.payment_ids = []
  },
)

watch(
  () => fiscalYearStore.selectedFiscalYearId,
  (newId, oldId) => {
    if (!fiscalYearStore.initialized || newId === oldId) return
    void loadAll()
  },
)

onMounted(async () => {
  await fiscalYearStore.initialize()
  await loadAll()
})
</script>

<style scoped>
.bank-chart-panel__intro {
  margin: 0 0 var(--app-space-4);
  color: var(--p-text-muted-color);
}

.bank-panel-toolbar {
  margin-bottom: var(--app-space-4);
}

:deep(.bank-table__description) {
  min-width: 20rem;
}

:deep(.bank-table__reference) {
  min-width: 12rem;
}

:deep(.bank-table__amount) {
  width: 8rem;
}

:deep(.bank-table__balance) {
  width: 6.5rem;
}

:deep(.bank-table__reconciled) {
  width: 5.5rem;
}

:deep(.bank-table__category) {
  width: 7.5rem;
}

:deep(.bank-table__source) {
  width: 5.25rem;
}

:deep(.bank-detected-category-tag) {
  border: 1px solid color-mix(in srgb, var(--app-surface-border) 82%, transparent 18%);
  background: color-mix(in srgb, var(--app-surface-muted) 84%, var(--app-surface-bg) 16%);
  color: color-mix(in srgb, var(--p-text-muted-color) 78%, var(--p-text-color) 22%);
}

:deep(.bank-detected-category-tag .p-tag-label) {
  white-space: nowrap;
  font-size: 0.78rem;
  line-height: 1;
}

:global(html.dark-mode) .bank-detected-category-tag {
  color: color-mix(in srgb, var(--p-surface-100) 82%, var(--p-text-color) 18%);
  border-color: color-mix(in srgb, var(--app-surface-border) 70%, transparent 30%);
  background: color-mix(in srgb, var(--app-surface-muted) 70%, var(--app-surface-bg) 30%);
}

.bank-import-file-row {
  display: flex;
  align-items: center;
  gap: var(--app-space-3);
}

.bank-import-file-name {
  color: var(--app-text-muted);
  font-size: 0.95rem;
}

.bank-import-file-input {
  display: none;
}

.bank-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}

.bank-positive {
  color: var(--p-green-600);
}

.bank-negative {
  color: var(--p-red-500);
}

.bank-payment-option {
  cursor: pointer;
}

.bank-allocation-list {
  gap: var(--app-space-3);
}

.bank-allocation-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--app-space-4);
}

.bank-allocation-item__summary {
  display: flex;
  align-items: flex-start;
  gap: var(--app-space-3);
  min-width: 0;
}

.bank-allocation-item__amount {
  min-width: 12rem;
}

.bank-allocation-item__fixed-amount {
  white-space: nowrap;
}

@media (max-width: 768px) {
  .bank-allocation-item {
    flex-direction: column;
  }

  .bank-allocation-item__amount {
    width: 100%;
    min-width: 0;
  }
}

.bank-payment-option :deep(.p-checkbox) {
  margin-top: 0.15rem;
}

:deep(.p-tabpanels) {
  padding-inline: 0;
  padding-bottom: 0;
}
</style>
