import pika
import json

def consume_messages(callback):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    def callback_wrapper(ch, method, properties, body):
        message = json.loads(body)
        print(f"Message received from RabbitMQ: {message}")
        callback(message)


    channel.basic_consume(queue='your_queue_name', on_message_callback=callback_wrapper, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
