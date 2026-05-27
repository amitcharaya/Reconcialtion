# Reconciliation Project Documentation

## 1. Project Overview

This Django project is a banking reconciliation platform for three transaction streams:

- **ATM**
- **RGCS**
- **IMPS**

For each stream, the system allows datewise upload of three source files:

- **CBS file** — transactions posted in the Core Banking System.
- **Switch file** — transactions captured by the switch/channel system.
- **NDPG file** — settlement/clearing records.

After all required source files for a selected transaction date are uploaded, reconciliation can be run for that specific date. The related dashboard then displays reconciliation status, unmatched exposure, disputes, and reports.

## 2. Main Applications

### `cbs`
Handles CBS-side uploads and parsing for ATM, RGCS, and IMPS. CBS files represent transactions that have financially hit the bank ledger.

### `switchlog`
Handles switch-side uploads for ATM, RGCS, and IMPS. Switch records are used to validate channel activity and link CBS transactions with settlement records.

### `ndpg`
Handles NDPG raw file uploads and parsing. For RGCS reconciliation, the system uses the `actual_txn_amount` field from the RGCS NDPG model.

### `reconciliation`
Contains ATM reconciliation models, reports, and reconciliation engine logic.

### `rgcs_reconciliation`
Contains RGCS reconciliation form, model, service, report view, and Excel download support.

### `imps_reconciliation`
Contains IMPS reconciliation form, model, and reconciliation service.

### `disputes`
Creates and stores dispute cases for unmatched transactions that represent financial exposure. ATM, RGCS, and IMPS dispute flows are kept here.

### `mis_dashboard`
Provides home workflow, dashboards, reports, filter screens, and Excel export views.

## 3. Datewise Home Workflow

The home page is designed as an operational control panel. The user selects a transaction date, and the page shows separate cards for ATM, RGCS, and IMPS.

For each stream, the page shows whether the following files have been uploaded:

1. CBS
2. Switch
3. NDPG

The system then guides the user to the next pending upload. Once all three sources are uploaded for the selected date, the reconciliation button becomes the next logical action.

This avoids running reconciliation before the required data is available.

## 4. Upload Rules

- Uploads are handled datewise.
- ATM, RGCS, and IMPS upload status is maintained separately.
- Duplicate upload prevention should be enforced at the batch level wherever implemented.
- Upload forms should validate input before inserting records into the database.
- Upload completion status is shown on the home page.

## 5. Reconciliation Flow

The general reconciliation flow is:

1. Select transaction type: ATM, RGCS, or IMPS.
2. Upload CBS file for the date.
3. Upload Switch file for the date.
4. Upload NDPG file for the date.
5. Run reconciliation for the same date.
6. Redirect to the relevant dashboard after reconciliation.

After reconciliation is complete, the system redirects as follows:

- ATM reconciliation → ATM dashboard
- RGCS reconciliation → RGCS dashboard
- IMPS reconciliation → IMPS dashboard

## 6. RGCS Reconciliation Amount Rule

For RGCS reconciliation, the NDPG amount used for comparison is:

```text
actual_txn_amount
```

This is important because NDPG raw files may contain multiple amount fields. The actual transaction amount is the correct field for reconciliation comparison.

## 7. Zero Amount Rule

A dispute should not be created when all three source amounts are zero:

```text
CBS amount = 0
Switch amount = 0
NDPG amount = 0
```

Such cases do not represent financial exposure and should therefore be excluded from dispute creation.

## 8. Dispute Creation

Disputes are created for unmatched transactions that represent financial exposure.

The dispute flow now covers:

- ATM unmatched exposure
- RGCS unmatched exposure
- IMPS unmatched exposure

Dispute creation is handled in the `disputes` application so that all transaction types follow a consistent approach.

## 9. Dashboards

Each dashboard should show the selected date range and related reconciliation/dispute information.

Dashboards include:

- ATM dashboard
- RGCS dashboard
- IMPS dashboard

The dashboard date filters are also used to display disputes created within the selected range. This helps users identify unresolved financial exposure for the period under review.

## 10. Reports and Excel Export

ATM and RGCS reconciliation reports support Excel download.

The RGCS Excel download uses the same selected filters from the report page. This means that when the user filters the report by date, status, STAN, RRN, or other available parameters, the downloaded Excel file reflects the same filtered result.

## 11. Recommended Setup Steps

From the project root, run:

```bash
python -m venv env
env\Scripts\activate
pip install django openpyxl
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Then open the browser and use the home page workflow to upload files and run reconciliation.

## 12. Coding Standards Used

The project has been commented using the following professional conventions:

- Module-level docstrings explain the purpose of each Python file.
- Service files contain comments explaining business rules.
- Views explain request flow and redirects.
- Templates contain comments explaining forms, filters, and report tables.
- Business rules are kept in services instead of templates wherever possible.

## 13. Maintenance Notes

When adding a new transaction stream in future, follow the same structure:

1. Create upload batch models.
2. Create transaction models for CBS, Switch, and NDPG.
3. Create parser and validator services.
4. Add datewise upload forms.
5. Add reconciliation result model.
6. Add dashboard and reports.
7. Add dispute creation logic for unmatched financial exposure.
8. Add Excel download option for operational reporting.

## 14. Operational Use

Recommended daily process:

1. Select transaction date on home page.
2. Upload CBS, Switch, and NDPG files for ATM.
3. Run ATM reconciliation and review ATM dashboard.
4. Repeat the same flow for RGCS.
5. Repeat the same flow for IMPS.
6. Review dispute reports for the selected date range.
7. Download Excel reports wherever required for operational review or audit.
