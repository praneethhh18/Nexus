"""GST (India) + UPI helpers for the invoicing flow.

Everything that's specific to Indian tax + payment lives here so the
rest of the invoice code stays generic:

  * validate_gstin(s)              -> bool
  * state_code_from_gstin(s)       -> '29' (Karnataka), '27' (Maharashtra), ...
  * STATE_CODES                    -> {'29': 'Karnataka', ...}
  * compute_gst(items, supplier, customer)
                                   -> {subtotal, igst, cgst, sgst,
                                       total, items_with_tax}
  * build_upi_link(vpa, name, amount_inr, ref)
                                   -> 'upi://pay?pa=...&pn=...&am=...&tn=...'
  * build_upi_qr_png(link)         -> bytes (PNG)

GST split rules (current, 2024):
    same state          -> CGST + SGST (each half of the rate)
    inter-state         -> IGST (full rate)
    UT without legislature (UTGST) is not handled separately, the
    backend treats it as CGST+SGST. Fine for SMB invoicing; if/when
    we sell to large enterprises in UTs we'll widen this.

GSTIN format (15 chars):
    [2-digit state][10-char PAN][1-digit entity][Z][1-char checksum]

  Example: 29ABCDE1234F1Z5   ← Karnataka business
"""
from __future__ import annotations

import io
import re
import urllib.parse
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple


# ── State codes (GSTIN first 2 digits → state name) ─────────────────────────
# Used for the dropdown + to infer state from GSTIN when the user
# hasn't picked one explicitly.
STATE_CODES: Dict[str, str] = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman & Diu",
    "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra",
    "28": "Andhra Pradesh (Old)",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
    "97": "Other Territory",
}


_GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


def validate_gstin(gstin: str) -> bool:
    """Structural check. We do NOT validate the checksum (rarely worth
    the dependency) — the format gate catches every typo we've seen in
    the wild. False on empty so callers can pass an unset value freely."""
    if not gstin:
        return False
    return bool(_GSTIN_RE.match(gstin.strip().upper()))


def state_code_from_gstin(gstin: str) -> str:
    """First 2 chars of a GSTIN are the state code. Returns '' if the
    GSTIN doesn't look valid; callers should then fall back to a
    user-picked state."""
    if not validate_gstin(gstin):
        return ""
    return gstin.strip()[:2]


def state_name(code: str) -> str:
    """Pretty name for a state code, or the code itself if unknown."""
    return STATE_CODES.get((code or "").strip(), code or "")


# Standard GST rates SMBs encounter. We accept 0/0.25/3/5/12/18/28
# — anything else gets rejected at invoice validation.
SUPPORTED_GST_RATES = (0.0, 0.25, 3.0, 5.0, 12.0, 18.0, 28.0)


# ── Tax computation ─────────────────────────────────────────────────────────
def _q(x) -> Decimal:
    """Decimal helper that snaps to 2dp half-up (the way India's tax
    rules read money). Avoids the classic 0.1 + 0.2 = 0.300000000004
    drift on big invoices."""
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_gst(
    line_items: List[Dict],
    supplier_state_code: str,
    customer_state_code: str,
) -> Dict:
    """Compute the full tax breakdown for an invoice.

    Each line item must carry:
        amount (qty * unit_price, before tax)
        gst_rate (0 / 0.25 / 3 / 5 / 12 / 18 / 28)

    Output:
        {
          'subtotal':  Decimal,             # sum of pre-tax amounts
          'igst':      Decimal,             # 0 if intra-state
          'cgst':      Decimal,             # 0 if inter-state
          'sgst':      Decimal,
          'tax_total': Decimal,             # igst + cgst + sgst
          'total':     Decimal,             # subtotal + tax_total
          'is_inter_state': bool,
          'items_with_tax': [
              {
                  ...original item fields...,
                  'gst_rate':  float,
                  'tax_amount': Decimal,
                  'amount_with_tax': Decimal,
              },
              ...
          ],
        }
    """
    inter_state = bool(
        supplier_state_code and customer_state_code
        and supplier_state_code != customer_state_code
    )

    subtotal = Decimal("0")
    igst_total = Decimal("0")
    cgst_total = Decimal("0")
    sgst_total = Decimal("0")
    items_out: List[Dict] = []

    for it in line_items:
        amount = _q(it.get("amount", 0))
        try:
            rate = float(it.get("gst_rate", 0) or 0)
        except (TypeError, ValueError):
            rate = 0.0
        if rate not in SUPPORTED_GST_RATES:
            # Quietly snap unsupported rates to 0; the validation layer
            # ahead of this should have rejected them. Defensive.
            rate = 0.0

        tax = _q(amount * Decimal(str(rate)) / Decimal("100"))
        subtotal += amount

        if inter_state:
            igst_total += tax
        else:
            # CGST + SGST split half each. We round each half so the
            # printed numbers reconcile against the line tax_amount.
            half = _q(tax / 2)
            other = _q(tax - half)
            cgst_total += half
            sgst_total += other

        item_out = dict(it)
        item_out["gst_rate"] = rate
        item_out["tax_amount"] = float(tax)
        item_out["amount_with_tax"] = float(_q(amount + tax))
        items_out.append(item_out)

    tax_total = igst_total + cgst_total + sgst_total

    return {
        "subtotal":   float(subtotal),
        "igst":       float(igst_total),
        "cgst":       float(cgst_total),
        "sgst":       float(sgst_total),
        "tax_total":  float(tax_total),
        "total":      float(subtotal + tax_total),
        "is_inter_state": inter_state,
        "items_with_tax": items_out,
    }


# ── UPI link + QR ──────────────────────────────────────────────────────────
_UPI_VPA_RE = re.compile(r"^[A-Za-z0-9.\-_]{2,50}@[A-Za-z0-9]{2,50}$")


def validate_upi_vpa(vpa: str) -> bool:
    """Check the UPI handle format. Anything like 'name@bank' is fine.
    We don't ping the UPI network to verify the VPA resolves; that
    would slow every invoice save by 1-2s and add a flaky dependency.
    The first failed payment will tell us if the VPA is wrong."""
    if not vpa:
        return False
    return bool(_UPI_VPA_RE.match(vpa.strip()))


def build_upi_link(
    vpa: str,
    payee_name: str,
    amount_inr: float,
    invoice_ref: str = "",
) -> str:
    """Build a `upi://pay?...` deep-link the customer can tap to open
    any UPI app pre-filled with the amount + ref. Works without a
    payment-provider account; the customer pays directly to the VPA.

    Spec reference:
        NPCI UPI Linking Specification v1.6
        pa = payee VPA (required)
        pn = payee name (recommended)
        am = amount (decimal, INR)
        cu = currency (INR)
        tn = transaction note (used to carry our invoice ref)
    """
    vpa = (vpa or "").strip()
    if not validate_upi_vpa(vpa):
        raise ValueError(f"Invalid UPI VPA: {vpa!r}")
    name = (payee_name or "Payee").strip()[:80]
    note = (invoice_ref or "Invoice").strip()[:50]

    params = {
        "pa": vpa,
        "pn": name,
        "am": f"{float(amount_inr):.2f}",
        "cu": "INR",
        "tn": note,
    }
    return "upi://pay?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


def build_upi_qr_png(link: str, *, size_px: int = 320) -> bytes:
    """Render the UPI deep-link as a PNG QR code suitable for stamping
    on the invoice PDF. Returns raw PNG bytes. ~3-5 KB at 320px which
    is small enough to embed inline without bloating the PDF."""
    import qrcode
    # ERROR_CORRECT_M is the typical phone-camera-friendly level — high
    # enough to survive small print smudges, low enough to keep the
    # cell density readable from a normal phone distance.
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    # qrcode returns a PIL.Image-like object. Save to bytes.
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
