# CIT 105 - Module 4: Invoice Studio

Application 2 of 4: a Streamlit invoicing application with exact Decimal arithmetic, local JSON storage, and printable PDF export.

## Setup

Use Python 3.14 (the local development version). Clone this repository, open a terminal in its root, and run:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS/Linux, create the environment with `python3 -m venv .venv` and replace `.\.venv\Scripts\python.exe` with `.venv/bin/python`.

## Use

Enter the client name, address, invoice number, and date. Click **Add line item**, then enter a description, quantity, and unit price. Values recalculate when Enter is pressed or a field loses focus. Remove a line with **Remove**. Text fields are converted directly to Decimal; no float is used for invoice arithmetic.

Set the discount and tax percentages. Click **Save invoice to JSON**, then select a saved invoice in the sidebar and click **Load invoice**. Click **Download PDF** to export the current invoice.

Example: quantity 1 at USD 50.00, discount 10%, tax 8% gives subtotal 50.00, discount 5.00, taxable amount 45.00, tax 3.60, and total **48.60**.

## Module separation

| File | Responsibility |
| --- | --- |
| calculations.py | Decimal arithmetic and validation; no Streamlit imports or calls |
| storage.py | Save, list, and load JSON invoices |
| pdf_export.py | ReportLab PDF layout; calls the calculation module |
| app.py | Streamlit widgets and session state |
| test_calculations.py | Calculation test suite (pending completion) |

## Arithmetic decisions

Each line is rounded to cents using ROUND_HALF_UP after multiplying quantity by unit price. Rounded lines are summed. The percentage discount is rounded to cents and subtracted from the subtotal. Tax is calculated on that discounted amount and rounded to cents. The grand total is the discounted amount plus tax.

The discount comes before tax because this assignment taxes the amount payable after the discount. This is the application's calculation rule, not a claim about all jurisdictions.

All calculation inputs must be finite Decimal values. Negative quantities and prices are rejected; zero quantities are allowed. The discount must be between 0 and 100 percent. JSON stores each Decimal as an explicitly tagged string and reconstructs it as Decimal when loaded.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

**Formal suite status:** not yet completed or run. The initial suite must be generated with Claude Code in the AI Lab as required by the assignment. A passing pytest result will be recorded here after execution.

Manual checks performed with the student: add a line, remove it, and add another; save and reload an invoice; download and open a PDF; confirm the 48.60 example above. Separate development checks confirmed a 97.20 total for quantity 2 and exact Decimal preservation through JSON.

### Four student-authored additional cases

Pending: the student must choose and write four additional cases, then describe each case and what it protects against here. AI-generated cases will not be presented as student-authored work.

## Screenshot and sample PDF

The repository includes `sample_invoice.pdf`, using the 48.60 example. A screenshot of the running application still needs to be added before submission.

## Deployment

Push this project to a GitHub repository named **cit105-week4**. In Streamlit Community Cloud, create an app from that repository and select **app.py** as the entry point. Select a compatible Python version and install dependencies from requirements.txt.

Saved invoices are local server files. Community Cloud server storage is not guaranteed to survive restarts or redeployment. This assignment version is intended for demonstration with sample data and a single user, not production billing.

Repository URL and deployed application URL: pending publication.

## AI assistance disclosure

OpenAI Codex/ChatGPT assisted with setup, wrote the initial application modules, performed development checks, and prepared documentation. The student manually tested the running application. Claude Code has not yet generated the required initial test suite. The four additional student-authored cases remain pending. This disclosure will be updated to reflect the final work accurately.
