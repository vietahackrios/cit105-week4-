"""Streamlit invoice interface."""

from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import uuid4

import streamlit as st

from calculations import invoice_totals
from storage import save_invoice, load_invoice, list_invoices
from pdf_export import export_invoice_pdf


st.set_page_config(page_title="Invoice Studio", layout="wide")


def add_item():
    st.session_state.item_ids.append(uuid4().hex)


def remove_item(item_id):
    st.session_state.item_ids.remove(item_id)
    for field in ("description", "quantity", "price"):
        st.session_state.pop(f"{field}_{item_id}", None)


def restore(invoice):
    for item_id in st.session_state.item_ids:
        for field in ("description", "quantity", "price"):
            st.session_state.pop(f"{field}_{item_id}", None)
    for key in ("client_name", "client_address", "invoice_number"):
        st.session_state[key] = invoice.get(key, "")
    st.session_state.invoice_date = date.fromisoformat(invoice["date"])
    for key in ("discount_percent", "tax_percent"):
        st.session_state[key] = str(invoice[key])
    st.session_state.item_ids = []
    for item in invoice["items"]:
        item_id = uuid4().hex
        st.session_state.item_ids.append(item_id)
        st.session_state[f"description_{item_id}"] = item["description"]
        st.session_state[f"quantity_{item_id}"] = str(item["quantity"])
        st.session_state[f"price_{item_id}"] = str(item["unit_price"])


defaults = {"item_ids": [], "client_name": "", "client_address": "", "invoice_number": "INV-001", "invoice_date": date.today(), "discount_percent": "0", "tax_percent": "0"}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.title("Invoice Studio")
st.caption("Exact Decimal calculations · JSON storage · Printable PDF")
with st.sidebar:
    st.header("Saved invoices")
    try:
        saved = list_invoices()
        if saved:
            labels = {entry["id"]: entry["label"] for entry in saved}
            selected = st.selectbox("Choose an invoice", list(labels), format_func=labels.get)
            if st.button("Load invoice"):
                restore(load_invoice(selected))
                st.success("Invoice loaded")
        else:
            st.info("No saved invoices yet.")
    except (OSError, ValueError, KeyError) as error:
        st.error(f"Could not load saved invoices: {error}")
    st.caption("JSON files live on this server. Download a JSON backup for your records.")

left, right = st.columns(2)
with left:
    st.text_input("Client name", key="client_name")
    st.text_area("Client address", key="client_address")
with right:
    st.text_input("Invoice number", key="invoice_number")
    st.date_input("Invoice date", key="invoice_date")

st.subheader("Line items")
st.button("Add line item", on_click=add_item)
items = []
invalid = False
for item_id in st.session_state.item_ids:
    description_column, quantity_column, price_column, remove_column = st.columns([5, 2, 2, 1])
    description = description_column.text_input("Description", key=f"description_{item_id}")
    quantity_text = quantity_column.text_input("Quantity", value="1", key=f"quantity_{item_id}")
    price_text = price_column.text_input("Unit price (USD)", value="0.00", key=f"price_{item_id}")
    remove_column.button("Remove", key=f"remove_{item_id}", on_click=remove_item, args=(item_id,))
    try:
        items.append({"description": description, "quantity": Decimal(quantity_text), "unit_price": Decimal(price_text)})
    except InvalidOperation:
        invalid = True

discount_column, tax_column = st.columns(2)
discount_text = discount_column.text_input("Discount (%)", key="discount_percent")
tax_text = tax_column.text_input("Tax (%)", key="tax_percent")
st.caption("Values update when you press Enter or leave a field. Discount is applied before tax.")
try:
    if invalid:
        raise ValueError("Enter valid quantities and prices.")
    discount, tax = Decimal(discount_text), Decimal(tax_text)
    totals = invoice_totals([(item["quantity"], item["unit_price"]) for item in items], discount, tax)
except (InvalidOperation, ValueError, TypeError) as error:
    st.error(f"Check your amounts: {error}")
    st.stop()

for column, (label, key) in zip(st.columns(4), [("Subtotal", "subtotal"), ("Discount", "discount"), ("Tax", "tax"), ("Grand total", "total")]):
    column.metric(label, f"${totals[key]:,.2f}")

invoice = {"client_name": st.session_state.client_name, "client_address": st.session_state.client_address, "invoice_number": st.session_state.invoice_number, "date": st.session_state.invoice_date.isoformat(), "items": items, "discount_percent": discount, "tax_percent": tax}
if st.button("Save invoice to JSON"):
    try:
        save_invoice(invoice)
        st.session_state.saved_notice = True
        st.rerun()
    except (OSError, ValueError, TypeError) as error:
        st.error(f"Could not save invoice: {error}")
if st.session_state.pop("saved_notice", False):
    st.success("Invoice saved. Find it in the sidebar.")
st.download_button("Download PDF", data=export_invoice_pdf(invoice), file_name="invoice.pdf", mime="application/pdf")
