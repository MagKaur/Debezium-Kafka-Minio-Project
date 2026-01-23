import json
import requests

url = "http://localhost:8081/subjects/olist.public.orders-value/versions"

with open("config/orders_event.schema.json", "r", encoding="utf-8") as f:
    schema_text = f.read()

payload = {
    "schemaType": "JSON",
    "schema": schema_text
}

r = requests.post(
    url,
    headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
    data=json.dumps(payload)
)

print("Status:", r.status_code)
print(r.text)