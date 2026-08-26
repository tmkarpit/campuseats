# CampusEats SOAP Partner Integration

## Team Details

TeamID: 5

Members:

| Roll | Name |
| --- | --- |
| Not provided | Arpit Tamrakar |
| Not provided | Yash Namdev |

## Context

CampusEats integrates with TrustPay Payment Gateway for the `ChargePayment` operation used during checkout. This partner edge is SOAP because payment processing needs a strict message contract, message-level credentials, and predictable fault structures for transaction handling. The rest of CampusEats can remain REST because menu browsing, cart management, and order status queries are resource-oriented and can evolve with simpler JSON contracts. The payment edge is different because CampusEats must preserve a stable contract with an external financial partner and map partner failures into CampusEats errors without exposing partner vocabulary to students.

## HTTP Binding

Endpoint URL: `https://api.trustpay.example.com/soap/payment/v1`

SOAPAction: `urn:campuseats:partners:trustpay:ChargePayment`

```http
POST /soap/payment/v1 HTTP/1.1
Host: api.trustpay.example.com
Content-Type: text/xml; charset=utf-8
SOAPAction: "urn:campuseats:partners:trustpay:ChargePayment"
Content-Length: 896

<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:pay="http://campuseats.example.com/partners/trustpay/payment/v1">
  <soap:Header>
    <pay:AuthHeader>
      <pay:merchantId>CEATS-MERCHANT-0091</pay:merchantId>
      <pay:apiKey>test_9x83b7f2c1</pay:apiKey>
      <pay:requestTimestamp>2026-08-26T10:15:30Z</pay:requestTimestamp>
      <pay:nonce>f7c1f4a0-55a3-4b4e-8d37-0d10f7b12a40</pay:nonce>
    </pay:AuthHeader>
  </soap:Header>
  <soap:Body>
    <pay:ChargePaymentRequest>
      <pay:orderId>CE-ORD-20260826-1042</pay:orderId>
      <pay:studentId>STU-2024-0176</pay:studentId>
      <pay:amount>248.50</pay:amount>
      <pay:currency>USD</pay:currency>
      <pay:cardToken>tok_campus_visa_1881</pay:cardToken>
      <pay:capture>true</pay:capture>
    </pay:ChargePaymentRequest>
  </soap:Body>
</soap:Envelope>
```

## Discovery

CampusEats obtains the WSDL from a partner catalogue maintained by the platform integration team. At deployment time, the checkout service looks up the active payment gateway record, downloads the WSDL from the registered contract URL, and binds the generated SOAP client to the endpoint listed in the record.

| Field | Registry entry |
| --- | --- |
| business | TrustPay Gateway Services |
| service | TrustPayPaymentService |
| endpoint | `https://api.trustpay.example.com/soap/payment/v1` |
| WSDL/tModel pointer | `https://catalog.campuseats.example.com/wsdl/trustpay-payment-v1.wsdl` |
| binding | SOAP 1.1 over HTTP, document/literal |
| operation | `ChargePayment` |

## Fault Mapping

TrustPay returns payment-specific SOAP faults such as `CARD_DECLINED` inside `PaymentFault`. CampusEats maps this to the Assignment 2 `placeOrder` contract error `PAYMENT_DECLINED` with the student-facing message `Payment was declined. Please use another payment method.` The CampusEats API does not expose `CARD_DECLINED`, `TP-ERR-449102`, or any other TrustPay-only vocabulary to students; those details stay in internal logs for support and reconciliation.
