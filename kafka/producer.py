from kafka import KafkaProducer
import json
import random
import time
from datetime import datetime

# Liste d'utilisateurs fictifs
USERS = [f"user{i}" for i in range(1, 21)]
ACTIONS = ["LIKE", "SHARE", "COMMENT"]

def create_event():
    """Création d'un événement d'interaction entre deux utilisateurs."""
    user_from = random.choice(USERS)
    user_to = random.choice([u for u in USERS if u != user_from])

    event = {
        "user_from": user_from,
        "user_to": user_to,
        "action": random.choice(ACTIONS),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return event

def main():
    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    print("🚀 Envoi des événements dans le topic 'social-events' (Ctrl+C pour arrêter)...")

    try:
        while True:
            event = create_event()
            producer.send("social-events", value=event)
            producer.flush()
            print("Event envoyé :", event)
            time.sleep(1)  # 1 événement / seconde
    except KeyboardInterrupt:
        print("\nArrêt du producteur.")
    finally:
        producer.close()

if __name__ == "__main__":
    main()

