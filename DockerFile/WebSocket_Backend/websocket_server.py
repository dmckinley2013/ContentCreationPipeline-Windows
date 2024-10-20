import asyncio
import websockets
import json
import pika
from bson import BSON, ObjectId
from db_handler import DBHandler

connected_clients = set()
db_handler = DBHandler()
db_handler.init_db()

def convert_bson_to_json(data):
    if isinstance(data, bytes):
        return data.decode('utf-8', errors='replace')
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {k: convert_bson_to_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_bson_to_json(item) for item in data]
    return data

async def send_initial_messages(websocket):
    try:
        messages = db_handler.load_messages()
        serialized_messages = [convert_bson_to_json(msg) for msg in messages]
        await websocket.send(json.dumps({'type': 'initialMessages', 'data': serialized_messages}))
    except Exception as e:
        print(f"Error sending initial messages: {e}")

async def handler(websocket, path):
    connected_clients.add(websocket)
    await send_initial_messages(websocket)

    try:
        async for message in websocket:
            message_data = json.loads(message)
            json_message = convert_bson_to_json(message_data)

            db_handler.save_message_to_db(json_message)
            await broadcast_to_clients({'type': 'newMessage', 'data': json_message})
    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
    finally:
        connected_clients.remove(websocket)

async def broadcast_to_clients(data):
    if connected_clients:
        await asyncio.gather(
            *[client.send(json.dumps(data)) for client in connected_clients],
            return_exceptions=True
        )

def consume_rabbitmq():
    connection_parameters = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()

    queue_name = 'Dashboard'
    channel.queue_declare(queue=queue_name, durable=True)

    def callback(ch, method, properties, body):
        try:
            message = BSON(body).decode()
            json_message = convert_bson_to_json(message)

            db_handler.save_message_to_db(json_message)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(broadcast_to_clients({'type': 'newMessage', 'data': json_message}))
        except Exception as e:
            print(f"Error processing message: {e}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

async def main():
    server = await websockets.serve(handler, "localhost", 5001)
    await server.wait_closed()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, consume_rabbitmq)
    asyncio.run(main())
