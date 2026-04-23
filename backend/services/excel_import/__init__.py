"""Excel import service -- package re-exports."""

from __future__ import annotations

from backend.services.excel_import._comparison import (  # noqa: F401
    _build_extra_in_solde_summary as _build_extra_in_solde_summary,
)
from backend.services.excel_import._comparison import (
    _build_salary_row_months as _build_salary_row_months,
)
from backend.services.excel_import._comparison import (
    _build_sheet_row_dates as _build_sheet_row_dates,
)
from backend.services.excel_import._comparison import (
    _comparison_years_within_bounds as _comparison_years_within_bounds,
)
from backend.services.excel_import._comparison import (
    _expand_date_bounds as _expand_date_bounds,
)
from backend.services.excel_import._comparison import (
    _filter_date_issues_in_window as _filter_date_issues_in_window,
)
from backend.services.excel_import._comparison import (
    _filter_salary_issues_in_window as _filter_salary_issues_in_window,
)
from backend.services.excel_import._comparison import (
    _find_date_column_index as _find_date_column_index,
)
from backend.services.excel_import._comparison import (
    _gestion_bank_comparison_signature as _gestion_bank_comparison_signature,
)
from backend.services.excel_import._comparison import (
    _gestion_cash_comparison_signature as _gestion_cash_comparison_signature,
)
from backend.services.excel_import._comparison import (
    _gestion_file_fiscal_year_bounds as _gestion_file_fiscal_year_bounds,
)
from backend.services.excel_import._comparison import (
    _gestion_payment_comparison_signature as _gestion_payment_comparison_signature,
)
from backend.services.excel_import._comparison import (
    _gestion_salary_comparison_signature as _gestion_salary_comparison_signature,
)
from backend.services.excel_import._comparison import (
    _is_salary_month_within_comparison_window as _is_salary_month_within_comparison_window,
)
from backend.services.excel_import._comparison import (
    _is_within_comparison_window as _is_within_comparison_window,
)
from backend.services.excel_import._comparison import (
    _is_within_date_bounds as _is_within_date_bounds,
)
from backend.services.excel_import._comparison import (
    _make_gestion_bank_extra_detail as _make_gestion_bank_extra_detail,
)
from backend.services.excel_import._comparison import (
    _make_gestion_cash_extra_detail as _make_gestion_cash_extra_detail,
)
from backend.services.excel_import._comparison import (
    _make_gestion_invoice_extra_detail as _make_gestion_invoice_extra_detail,
)
from backend.services.excel_import._comparison import (
    _make_gestion_payment_extra_detail as _make_gestion_payment_extra_detail,
)
from backend.services.excel_import._comparison import (
    _make_gestion_salary_extra_detail as _make_gestion_salary_extra_detail,
)
from backend.services.excel_import._comparison import (
    _preview_file_fiscal_year_bounds as _preview_file_fiscal_year_bounds,
)
from backend.services.excel_import._comparison import (
    _PreviewFilterWindow as _PreviewFilterWindow,
)
from backend.services.excel_import._comparison import (
    _resolve_comparison_window as _resolve_comparison_window,
)
from backend.services.excel_import._comparison import (
    _salary_month_to_date as _salary_month_to_date,
)
from backend.services.excel_import._comparison_domains import (  # noqa: F401
    _build_comptabilite_preview_comparison_domains as _build_comptabilite_preview_comparison_domains,
)
from backend.services.excel_import._comparison_domains import (
    _build_gestion_preview_comparison_domains as _build_gestion_preview_comparison_domains,
)
from backend.services.excel_import._comparison_domains import (
    _collect_comptabilite_extra_in_solde_by_kind as _collect_comptabilite_extra_in_solde_by_kind,
)
from backend.services.excel_import._comparison_domains import (
    _collect_gestion_extra_in_solde_by_kind as _collect_gestion_extra_in_solde_by_kind,
)
from backend.services.excel_import._comparison_domains import (
    _load_existing_accounting_entry_comparison_signatures as _load_existing_accounting_entry_comparison_signatures,
)
from backend.services.excel_import._comparison_domains import (
    _make_preview_comparison_domain as _make_preview_comparison_domain,
)
from backend.services.excel_import._comparison_loaders import (  # noqa: F401
    _load_existing_bank_comparison_items as _load_existing_bank_comparison_items,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_bank_comparison_signatures as _load_existing_bank_comparison_signatures,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_cash_comparison_items as _load_existing_cash_comparison_items,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_cash_comparison_signatures as _load_existing_cash_comparison_signatures,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_client_invoice_comparison_items as _load_existing_client_invoice_comparison_items,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_client_invoice_comparison_signatures as _load_existing_client_invoice_comparison_signatures,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_client_payment_comparison_items as _load_existing_client_payment_comparison_items,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_client_payment_comparison_signatures as _load_existing_client_payment_comparison_signatures,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_salary_comparison_items as _load_existing_salary_comparison_items,
)
from backend.services.excel_import._comparison_loaders import (
    _load_existing_salary_comparison_signatures as _load_existing_salary_comparison_signatures,
)
from backend.services.excel_import._constants import (  # noqa: F401
    _CLIENT_INVOICE_CLARIFIED_MESSAGE as _CLIENT_INVOICE_CLARIFIED_MESSAGE,
)
from backend.services.excel_import._constants import (
    _CLIENT_INVOICE_REFERENCE_RE as _CLIENT_INVOICE_REFERENCE_RE,
)
from backend.services.excel_import._constants import (
    _COMPTABILITE_FILE_YEAR_RE as _COMPTABILITE_FILE_YEAR_RE,
)
from backend.services.excel_import._constants import (
    _GESTION_FILE_YEAR_RE as _GESTION_FILE_YEAR_RE,
)
from backend.services.excel_import._constants import (
    _GESTION_IMPORT_ORDER as _GESTION_IMPORT_ORDER,
)
from backend.services.excel_import._constants import (
    _SALARY_ACCRUAL_ACCOUNT_PREFIXES as _SALARY_ACCRUAL_ACCOUNT_PREFIXES,
)
from backend.services.excel_import._constants import (
    _SALARY_MONTH_RE as _SALARY_MONTH_RE,
)
from backend.services.excel_import._constants import (
    _SALARY_PAYMENT_ACCOUNT_PREFIXES as _SALARY_PAYMENT_ACCOUNT_PREFIXES,
)
from backend.services.excel_import._constants import (
    _SALARY_TRAILING_INITIAL_RE as _SALARY_TRAILING_INITIAL_RE,
)
from backend.services.excel_import._constants import (
    _ImportSheetFailure as _ImportSheetFailure,
)
from backend.services.excel_import._constants import (
    _IssueT as _IssueT,
)
from backend.services.excel_import._constants import (
    _load_existing_generated_accounting_group_signatures as _load_existing_generated_accounting_group_signatures,
)
from backend.services.excel_import._constants import (
    _SupplierInvoiceCandidate as _SupplierInvoiceCandidate,
)
from backend.services.excel_import._constants import (
    logger as logger,
)
from backend.services.excel_import._entry_groups import (  # noqa: F401
    _build_entry_row_groups as _build_entry_row_groups,
)
from backend.services.excel_import._entry_groups import (
    _ensure_supplier_invoice_payment as _ensure_supplier_invoice_payment,
)
from backend.services.excel_import._entry_groups import (
    _invoice_row_from_supplier_candidate as _invoice_row_from_supplier_candidate,
)
from backend.services.excel_import._entry_groups import (
    _matching_existing_salary_entry_group as _matching_existing_salary_entry_group,
)
from backend.services.excel_import._entry_groups import (
    _normalized_entry_group_signature as _normalized_entry_group_signature,
)
from backend.services.excel_import._entry_groups import (
    _queue_client_payment_from_bank_row as _queue_client_payment_from_bank_row,
)
from backend.services.excel_import._entry_groups import (
    _supplier_invoice_candidate_from_bank_row as _supplier_invoice_candidate_from_bank_row,
)
from backend.services.excel_import._entry_groups import (
    _supplier_invoice_candidate_from_cash_row as _supplier_invoice_candidate_from_cash_row,
)
from backend.services.excel_import._import_cash_bank import (  # noqa: F401
    _import_bank_sheet as _import_bank_sheet,
)
from backend.services.excel_import._import_cash_bank import (
    _import_cash_sheet as _import_cash_sheet,
)
from backend.services.excel_import._import_contacts_invoices import (  # noqa: F401
    _import_contacts_sheet as _import_contacts_sheet,
)
from backend.services.excel_import._import_contacts_invoices import (
    _import_invoices_sheet as _import_invoices_sheet,
)
from backend.services.excel_import._import_entries import (  # noqa: F401
    _import_entries_sheet as _import_entries_sheet,
)
from backend.services.excel_import._import_payments_salaries import (  # noqa: F401
    _import_payments_sheet as _import_payments_sheet,
)
from backend.services.excel_import._import_payments_salaries import (
    _import_salaries_sheet as _import_salaries_sheet,
)
from backend.services.excel_import._invoices import (  # noqa: F401
    _build_client_invoice_lines_from_import_row as _build_client_invoice_lines_from_import_row,
)
from backend.services.excel_import._invoices import (
    _can_clarify_existing_client_invoice as _can_clarify_existing_client_invoice,
)
from backend.services.excel_import._invoices import (
    _clarify_existing_client_invoice_from_entries as _clarify_existing_client_invoice_from_entries,
)
from backend.services.excel_import._invoices import (
    _client_invoice_breakdown_from_entry_group as _client_invoice_breakdown_from_entry_group,
)
from backend.services.excel_import._invoices import (
    _client_invoice_line_type_from_account_number as _client_invoice_line_type_from_account_number,
)
from backend.services.excel_import._invoices import (
    _client_settlement_account_from_method as _client_settlement_account_from_method,
)
from backend.services.excel_import._invoices import (
    _current_client_invoice_breakdown as _current_client_invoice_breakdown,
)
from backend.services.excel_import._invoices import (
    _extract_client_invoice_references as _extract_client_invoice_references,
)
from backend.services.excel_import._invoices import (
    _find_clarifiable_existing_client_invoice as _find_clarifiable_existing_client_invoice,
)
from backend.services.excel_import._invoices import (
    _is_client_invoice_entry_group as _is_client_invoice_entry_group,
)
from backend.services.excel_import._invoices import (
    _is_client_payment_entry_group as _is_client_payment_entry_group,
)
from backend.services.excel_import._invoices import (
    _is_supplier_direct_settlement_entry_group as _is_supplier_direct_settlement_entry_group,
)
from backend.services.excel_import._invoices import (
    _load_existing_client_invoices_by_number as _load_existing_client_invoices_by_number,
)
from backend.services.excel_import._invoices import (
    _load_existing_client_payment_reference_signatures as _load_existing_client_payment_reference_signatures,
)
from backend.services.excel_import._invoices import (
    _load_existing_supplier_payment_reference_signatures as _load_existing_supplier_payment_reference_signatures,
)
from backend.services.excel_import._invoices import (
    _matching_existing_client_invoice_reference as _matching_existing_client_invoice_reference,
)
from backend.services.excel_import._invoices import (
    _matching_existing_client_payment_reference as _matching_existing_client_payment_reference,
)
from backend.services.excel_import._invoices import (
    _matching_existing_supplier_invoice_payment_reference as _matching_existing_supplier_invoice_payment_reference,
)
from backend.services.excel_import._invoices import (
    _merge_existing_client_invoice_entry_groups as _merge_existing_client_invoice_entry_groups,
)
from backend.services.excel_import._invoices import (
    _normalize_decimal_text as _normalize_decimal_text,
)
from backend.services.excel_import._invoices import (
    _single_client_invoice_reference as _single_client_invoice_reference,
)
from backend.services.excel_import._invoices import (
    _supplier_settlement_account_from_method as _supplier_settlement_account_from_method,
)
from backend.services.excel_import._loaders import (  # noqa: F401
    _direct_bank_trigger_from_row as _direct_bank_trigger_from_row,
)
from backend.services.excel_import._loaders import (
    _generate_direct_bank_entries as _generate_direct_bank_entries,
)
from backend.services.excel_import._loaders import (
    _load_existing_contacts_by_salary_key as _load_existing_contacts_by_salary_key,
)
from backend.services.excel_import._loaders import (
    _load_existing_payment_signatures as _load_existing_payment_signatures,
)
from backend.services.excel_import._loaders import (
    _load_existing_salary_group_signatures as _load_existing_salary_group_signatures,
)
from backend.services.excel_import._loaders import (
    _load_existing_salary_keys as _load_existing_salary_keys,
)
from backend.services.excel_import._loaders import (
    _payment_row_from_bank_row as _payment_row_from_bank_row,
)
from backend.services.excel_import._loaders import (
    _payment_signature as _payment_signature,
)
from backend.services.excel_import._orchestrator import (  # noqa: F401
    import_comptabilite_file,
    import_gestion_file,
)
from backend.services.excel_import._preview_existing import (  # noqa: F401
    _add_comptabilite_existing_rows_preview as _add_comptabilite_existing_rows_preview,
)
from backend.services.excel_import._preview_existing import (
    _add_gestion_existing_rows_preview as _add_gestion_existing_rows_preview,
)
from backend.services.excel_import._preview_existing import (
    _add_gestion_payment_validation as _add_gestion_payment_validation,
)
from backend.services.excel_import._preview_sheets import (  # noqa: F401
    _collect_sample_rows as _collect_sample_rows,
)
from backend.services.excel_import._preview_sheets import (
    _preview_gestion_file as _preview_gestion_file,
)
from backend.services.excel_import._preview_sheets import (
    _preview_sheet_comptabilite as _preview_sheet_comptabilite,
)
from backend.services.excel_import._preview_sheets import (
    _preview_sheet_gestion as _preview_sheet_gestion,
)
from backend.services.excel_import._preview_sheets import (
    preview_comptabilite_file,
    preview_gestion_file,
)
from backend.services.excel_import._salary import (  # noqa: F401
    _accounting_amount_signature as _accounting_amount_signature,
)
from backend.services.excel_import._salary import (
    _entry_group_amount_signature as _entry_group_amount_signature,
)
from backend.services.excel_import._salary import (
    _extract_salary_month as _extract_salary_month,
)
from backend.services.excel_import._salary import (
    _is_salary_accrual_like_entry_group as _is_salary_accrual_like_entry_group,
)
from backend.services.excel_import._salary import (
    _is_salary_payment_like_entry_group as _is_salary_payment_like_entry_group,
)
from backend.services.excel_import._salary import (
    _is_salary_related_label as _is_salary_related_label,
)
from backend.services.excel_import._salary import (
    _salary_employee_key as _salary_employee_key,
)
from backend.services.excel_import._salary import (
    _salary_entry_date as _salary_entry_date,
)
from backend.services.excel_import._salary import (
    _salary_group_amount_signature as _salary_group_amount_signature,
)
from backend.services.excel_import._salary import (
    _salary_month_group_lines as _salary_month_group_lines,
)
from backend.services.excel_import._salary import (
    _salary_month_group_signatures as _salary_month_group_signatures,
)
from backend.services.excel_import._salary import (
    _salary_month_label as _salary_month_label,
)
from backend.services.excel_import._salary import (
    _salary_month_standalone_tax_signatures as _salary_month_standalone_tax_signatures,
)
from backend.services.excel_import._sheet_wrappers import (  # noqa: F401
    _is_cash_pending_deposit_forecast as _is_cash_pending_deposit_forecast,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_bank_sheet as _parse_bank_sheet,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_cash_sheet as _parse_cash_sheet,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_contact_sheet as _parse_contact_sheet,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_entries_sheet as _parse_entries_sheet,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_invoice_sheet as _parse_invoice_sheet,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_payment_sheet as _parse_payment_sheet,
)
from backend.services.excel_import._sheet_wrappers import (
    _parse_salary_sheet as _parse_salary_sheet,
)
from backend.services.excel_import_results import ImportResult, PreviewResult

__all__ = [
    "import_gestion_file",
    "import_comptabilite_file",
    "preview_gestion_file",
    "preview_comptabilite_file",
    "ImportResult",
    "PreviewResult",
]
