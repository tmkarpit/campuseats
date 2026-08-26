from pathlib import Path


OUT = Path("integration.pdf")


def esc(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap(text, width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


content = [
    ("TITLE", "CampusEats SOAP Partner Integration"),
    ("H", "Team Details"),
    ("P", "TeamID: TODO-TEAMID"),
    ("P", "Members: TODO-ROLL / TODO-NAME"),
    ("H", "Context"),
    (
        "P",
        "CampusEats integrates with TrustPay Payment Gateway for the ChargePayment operation used during checkout. "
        "This partner edge is SOAP because payment processing needs a strict message contract, message-level credentials, "
        "and predictable fault structures for transaction handling. The rest of CampusEats can remain REST because menu "
        "browsing, cart management, and order status queries are resource-oriented and can evolve with simpler JSON "
        "contracts. The payment edge is different because CampusEats must preserve a stable contract with an external "
        "financial partner and map partner failures into CampusEats errors without exposing partner vocabulary to students.",
    ),
    ("H", "HTTP Binding"),
    ("P", "Endpoint URL: https://api.trustpay.example.com/soap/payment/v1"),
    ("P", 'SOAPAction: "urn:campuseats:partners:trustpay:ChargePayment"'),
    ("CODE", "POST /soap/payment/v1 HTTP/1.1"),
    ("CODE", "Host: api.trustpay.example.com"),
    ("CODE", "Content-Type: text/xml; charset=utf-8"),
    ("CODE", 'SOAPAction: "urn:campuseats:partners:trustpay:ChargePayment"'),
    ("CODE", "Content-Length: 896"),
    ("CODE", ""),
    ("CODE", '<?xml version="1.0" encoding="UTF-8"?>'),
    ("CODE", '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"'),
    ("CODE", '    xmlns:pay="http://campuseats.example.com/partners/trustpay/payment/v1">'),
    ("CODE", "  <soap:Header>"),
    ("CODE", "    <pay:AuthHeader>"),
    ("CODE", "      <pay:merchantId>CEATS-MERCHANT-0091</pay:merchantId>"),
    ("CODE", "      <pay:apiKey>test_9x83b7f2c1</pay:apiKey>"),
    ("CODE", "      <pay:requestTimestamp>2026-08-26T10:15:30Z</pay:requestTimestamp>"),
    ("CODE", "      <pay:nonce>f7c1f4a0-55a3-4b4e-8d37-0d10f7b12a40</pay:nonce>"),
    ("CODE", "    </pay:AuthHeader>"),
    ("CODE", "  </soap:Header>"),
    ("CODE", "  <soap:Body>"),
    ("CODE", "    <pay:ChargePaymentRequest>"),
    ("CODE", "      <pay:orderId>CE-ORD-20260826-1042</pay:orderId>"),
    ("CODE", "      <pay:studentId>STU-2024-0176</pay:studentId>"),
    ("CODE", "      <pay:amount>248.50</pay:amount>"),
    ("CODE", "      <pay:currency>USD</pay:currency>"),
    ("CODE", "      <pay:cardToken>tok_campus_visa_1881</pay:cardToken>"),
    ("CODE", "      <pay:capture>true</pay:capture>"),
    ("CODE", "    </pay:ChargePaymentRequest>"),
    ("CODE", "  </soap:Body>"),
    ("CODE", "</soap:Envelope>"),
    ("PAGE", ""),
    ("H", "Discovery"),
    (
        "P",
        "CampusEats obtains the WSDL from a partner catalogue maintained by the platform integration team. At deployment "
        "time, the checkout service looks up the active payment gateway record, downloads the WSDL from the registered "
        "contract URL, and binds the generated SOAP client to the endpoint listed in the record.",
    ),
    ("P", "Registry entry:"),
    ("P", "business: TrustPay Gateway Services"),
    ("P", "service: TrustPayPaymentService"),
    ("P", "endpoint: https://api.trustpay.example.com/soap/payment/v1"),
    ("P", "WSDL/tModel pointer: https://catalog.campuseats.example.com/wsdl/trustpay-payment-v1.wsdl"),
    ("P", "binding: SOAP 1.1 over HTTP, document/literal"),
    ("P", "operation: ChargePayment"),
    ("H", "Fault Mapping"),
    (
        "P",
        "TrustPay returns payment-specific SOAP faults such as CARD_DECLINED inside PaymentFault. CampusEats maps this "
        "to the Assignment 2 placeOrder contract error PAYMENT_DECLINED with the student-facing message Payment was "
        "declined. Please use another payment method. The CampusEats API does not expose CARD_DECLINED, TP-ERR-449102, "
        "or any other TrustPay-only vocabulary to students; those details stay in internal logs for support and reconciliation.",
    ),
]


pages = []
commands = []
y = 790
page_no = 1


def new_page():
    global commands, y, page_no
    commands.append("BT /F1 9 Tf 72 34 Td (Page %d) Tj ET" % page_no)
    pages.append("\n".join(commands))
    commands = []
    y = 790
    page_no += 1


for kind, text in content:
    if kind == "PAGE":
        new_page()
        continue
    if kind == "TITLE":
        lines = [text]
        font = "/F2"
        size = 18
        leading = 24
    elif kind == "H":
        lines = [text]
        font = "/F2"
        size = 13
        leading = 20
        y -= 6
    elif kind == "CODE":
        lines = [text]
        font = "/F3"
        size = 8
        leading = 11
    else:
        lines = wrap(text, 88)
        font = "/F1"
        size = 10
        leading = 14

    for line in lines:
        if y < 62:
            new_page()
        commands.append(f"BT {font} {size} Tf 72 {y} Td ({esc(line)}) Tj ET")
        y -= leading
    if kind in {"TITLE", "H", "P"}:
        y -= 4

if commands:
    new_page()

objects = []
objects.append("<< /Type /Catalog /Pages 2 0 R >>")
kids = " ".join(f"{3 + i * 2} 0 R" for i in range(len(pages)))
objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")

for i, stream in enumerate(pages):
    page_obj = 3 + i * 2
    content_obj = page_obj + 1
    objects.append(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        f"/Resources << /Font << /F1 {3 + len(pages) * 2} 0 R /F2 {4 + len(pages) * 2} 0 R /F3 {5 + len(pages) * 2} 0 R >> >> "
        f"/Contents {content_obj} 0 R >>"
    )
    encoded = stream.encode("latin-1", "replace")
    objects.append(f"<< /Length {len(encoded)} >>\nstream\n{stream}\nendstream")

objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
offsets = [0]
for index, obj in enumerate(objects, 1):
    offsets.append(len(pdf))
    pdf.extend(f"{index} 0 obj\n".encode("ascii"))
    pdf.extend(obj.encode("latin-1", "replace"))
    pdf.extend(b"\nendobj\n")

xref = len(pdf)
pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
pdf.extend(b"0000000000 65535 f \n")
for offset in offsets[1:]:
    pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
pdf.extend(
    f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
)

OUT.write_bytes(pdf)
print(f"Wrote {OUT} with {len(pages)} pages")
