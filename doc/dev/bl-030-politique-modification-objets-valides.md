# BL-030 — Policy for Editing Validated Business Objects

## Purpose

Formalize the editing safeguards that apply once a business object has already produced downstream effects.

The general rule retained is the following:

- free editing while an object is still in a preparatory state;
- constrained editing with controlled regeneration when the object has already triggered effects but can still be modified without creating business inconsistency;
- no direct editing once the object has already been consumed by other business or accounting effects.

## Rules currently implemented

### Invoices

- a `draft` invoice remains freely editable;
- a `sent` but unpaid invoice remains editable;
- when a `sent` unpaid invoice is modified, accounting entries auto-generated from that invoice are deleted and regenerated inside the same transactional flow;
- an invoice outside that perimeter (`paid`, `partial`, `overdue`, `disputed`) is no longer directly editable.

## Payments

- a payment becomes almost immutable after creation;
- structural fields (`amount`, `date`, `method`, deposit state) are no longer editable;
- standard deletion of a payment is forbidden until a dedicated business cancellation flow correctly handles treasury and accounting side effects;
- only minor non-structural corrections remain allowed: `reference`, `notes`, and `cheque_number` when the payment method is cheque.

## Reversible imports

- `undo/redo` for reversible imports remains strict;
- as soon as an object created from an import manually diverges from the expected state, including through the object's standard API, strict replay must be blocked;
- strict verification explicitly reloads the ORM instance before computing the current fingerprint, to avoid false behavior caused by expired attributes.

## Out of scope for this delivery

- dedicated business cancellation mechanisms such as credit notes, accounting reversals, or payment reversal flows;
- a complete status matrix for every business object;
- an explicit business audit log of modifications.
