import json
from confluent_kafka import Consumer

TOPIC = "olist.public.orders"

def main():
    c = Consumer({
        "bootstrap.servers": "localhost:9092",
        "group.id": "task3-json-consumer",
        "auto.offset.reset": "latest",  # "earliest" jeśli chcesz czytać od początku
    })
    c.subscribe([TOPIC])

    print(f"Listening on {TOPIC} ... (Ctrl+C to stop)")
    try:
        while True:
            msg = c.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Kafka error:", msg.error())
                continue

            event = json.loads(msg.value().decode("utf-8", errors="replace"))
            payload = event.get("payload", {})
            op = payload.get("op")
            after = payload.get("after") or {}

            print({
                "op": op,
                "order_id": after.get("order_id"),
                "order_status": after.get("order_status"),
            })
    except KeyboardInterrupt:
        pass
    finally:
        c.close()

if __name__ == "__main__":
    main()