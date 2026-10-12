"""Local JSON invoice storage. Decimal values survive a round trip."""

import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4


DEFAULT_DIRECTORY = Path(__file__).parent / "invoices"


def _encode(value):
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Amounts must be finite.")
        return {"__decimal__": str(value)}
    if isinstance(value, float):
        raise TypeError("Store money as Decimal, never float.")
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    return value


def _decode(value):
    if set(value) == {"__decimal__"}:
        amount = Decimal(value["__decimal__"])
        if not amount.is_finite():
            raise ValueError("Amounts must be finite.")
        return amount
    return value


def _invoice_path(invoice_id: str, directory: Path) -> Path:
    if len(invoice_id) != 32 or any(character not in "0123456789abcdef" for character in invoice_id):
        raise ValueError("Invalid saved invoice identifier.")
    return directory / f"{invoice_id}.json"


def save_invoice(invoice: dict, directory: Path = DEFAULT_DIRECTORY) -> str:
    """Save a new snapshot and return its unique storage identifier."""
    payload = json.dumps(_encode(invoice), indent=2, ensure_ascii=False, allow_nan=False)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    invoice_id = uuid4().hex
    path = _invoice_path(invoice_id, directory)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.replace(path)
    return invoice_id


def load_invoice(invoice_id: str, directory: Path = DEFAULT_DIRECTORY) -> dict:
    path = _invoice_path(invoice_id, Path(directory))
    invoice = json.loads(path.read_text(encoding="utf-8"), object_hook=_decode)
    if not isinstance(invoice, dict):
        raise ValueError("Saved invoice must be an object.")
    return invoice


def list_invoices(directory: Path = DEFAULT_DIRECTORY) -> list[dict]:
    """Return saved invoice identifiers and labels for the interface."""
    directory = Path(directory)
    if not directory.exists():
        return []
    result = []
    for path in sorted(directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        invoice = load_invoice(path.stem, directory)
        result.append({
            "id": path.stem,
            "label": f"{invoice.get('invoice_number', 'Invoice')} | {invoice.get('client_name', '')} | {invoice.get('date', '')}",
        })
    return result
