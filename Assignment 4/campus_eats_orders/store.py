from threading import Lock


class OrderStore:
    def __init__(self):
        self._orders = {}
        self._by_key = {}
        self._lock = Lock()

    def create_once(self, order):
        """Atomically return an existing order for a repeated idempotency key."""
        with self._lock:
            existing_id = self._by_key.get(order.idempotency_key)
            if existing_id:
                return self._orders[existing_id], False
            self._orders[order.order_id] = order
            self._by_key[order.idempotency_key] = order.order_id
            return order, True

    def get(self, order_id):
        return self._orders.get(order_id)

    def list(self, status=None):
        values = list(self._orders.values())
        return [o for o in values if status is None or o.status == status]

    def clear(self):
        with self._lock:
            self._orders.clear()
            self._by_key.clear()
