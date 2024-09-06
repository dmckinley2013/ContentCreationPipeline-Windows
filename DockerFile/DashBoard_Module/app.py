import threading
from rabbitmq_consumer import consume_messages

def handle_message(message):
    # You can keep this function if needed for other purposes
    print(f"Received message: {message}")  # Simple print instead of emitting via WebSocket

if __name__ == '__main__':
    # Start RabbitMQ consumer in a separate thread
    threading.Thread(target=consume_messages, args=(handle_message,)).start()

