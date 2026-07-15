"""System under test: a small shop API (simulates the client's application)."""
from flask import Flask, jsonify, request

app = Flask(__name__)

ORDERS = {}
NEXT_ID = [1]
PRICE_PER_UNIT = 19.99


@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.json or {}
    items = data.get("items", [])
    order_id = "ORD-{:05d}".format(NEXT_ID[0])
    NEXT_ID[0] += 1
    item_count = sum(i.get("qty", 0) for i in items)
    total = round(sum(i.get("qty", 0) * PRICE_PER_UNIT for i in items), 2)
    order = {
        "orderId": order_id,
        "status": "created",
        "total": total,
        "itemCount": item_count,
    }
    ORDERS[order_id] = order
    return jsonify(order), 201


@app.route("/api/orders/<oid>", methods=["GET"])
def get_order(oid):
    order = ORDERS.get(oid)
    if not order:
        return jsonify({"error": "not found"}), 404
    return jsonify(order)


if __name__ == "__main__":
    app.run(port=5001, debug=True)
