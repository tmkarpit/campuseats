# CampusEats Orders REST service

Run the service with `python3 app.py`. It listens on `http://127.0.0.1:8001`.
Set `PAYMENTS_URL` to the base URL of the Tutorial 4 Payments service to enable
the outbound payment POST; leaving it unset demonstrates the documented
`PAYMENT_PENDING` fallback.

Validate the contract with `python3 validate_openapi.py openapi.yaml`. For the
full validator and test runner, install `requirements.txt` in a normal Python
environment and run:

```sh
python3 -m pip install -r requirements.txt
openapi-spec-validator openapi.yaml
python3 -m pytest -q
```

The local environment used to build this submission has Python but no `pip` or
`pytest`; the four test functions were therefore run directly and passed.
