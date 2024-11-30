import asyncio
import websockets
import json
import pika
from bson import BSON, ObjectId
from db_handler import DBHandler
from datetime import datetime
class WebSocketServer:
    def __init__(self):
        self.connected_clients = set()
        self.db_handler = DBHandler()
        self.db_handler.init_db()
        self.message_queue = asyncio.Queue()

    def convert_bson_to_json(self, data):
        if isinstance(data, bytes):
            return data.decode('utf-8', errors='replace')
        elif isinstance(data, ObjectId):
            return str(data)
        elif isinstance(data, dict):
            # Convert the message to the expected format
            if 'ID' in data:
                print("PIC PRINTED HERE")
                print(data.get('PictureID'))
                return {
                    'time': data.get('time', datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')),
                    'job_id': data.get('ID'),
                    'content_id': data.get('content_id'),
                    'content_type': self._determine_content_type(data),
                    'media_id': data.get('DocumentId') or data.get('PictureID') or data.get('AudioID') or data.get('VideoID'),
                    'file_name': data.get('file_name'),
                    'status': 'Processed',
                    'message': self._generate_message(data)
                }
            return {k: self.convert_bson_to_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.convert_bson_to_json(item) for item in items]
        return data

    def _determine_content_type(self, data):
        if 'DocumentId' in data:
            return 'Document'
        elif 'PictureID' in data:
            return 'Picture'
        elif 'AudioID' in data:
            return 'Audio'
        return data.get('content_type', 'Unknown Type')

    def _generate_message(self, data):
        file_name = data.get('file_name', 'unknown file')
        if 'DocumentId' in data:
            return f"Document file '{file_name}' was successfully processed"
        elif 'PictureID' in data:
            return f"Picture file '{file_name}' was successfully processed"
        elif 'AudioID' in data:
            return f"Audio file '{file_name}' was successfully processed"
        return 'No additional information'

    async def send_initial_messages(self, websocket):
        try:
            messages = self.db_handler.load_messages()
            serialized_messages = [self.convert_bson_to_json(msg) for msg in messages]
            await websocket.send(json.dumps({
                'type': 'initialMessages',
                'data': serialized_messages
            }))
        except Exception as e:
            print(f"Error sending initial messages: {e}")
            raise

    async def handle_client(self, websocket, path):
        try:
            self.connected_clients.add(websocket)
            print(f"Client connected. Total clients: {len(self.connected_clients)}")

            await self.send_initial_messages(websocket)
            broadcast_task = asyncio.create_task(self.broadcast_messages(websocket))

            async for message in websocket:
                try:
                    message_data = json.loads(message)
                    json_message = self.convert_bson_to_json(message_data)
                    
                    # Save the message to the database
                    self.db_handler.save_message_to_db(json_message)
                    
                    # Put the message in the queue for broadcasting
                    await self.message_queue.put({
                        'type': 'newMessage',
                        'data': json_message
                    })
                except Exception as e:
                    print(f"Error processing message: {e}")

        except websockets.ConnectionClosedError:
            print("WebSocket connection closed normally")
        except Exception as e:
            print(f"Error in WebSocket handler: {e}")
        finally:
            self.connected_clients.remove(websocket)
            broadcast_task.cancel()
            print(f"Client disconnected. Total clients: {len(self.connected_clients)}")

    async def broadcast_messages(self, websocket):
        try:
            while True:
                message = await self.message_queue.get()
                websockets_to_remove = set()

                for client in self.connected_clients:
                    try:
                        await client.send(json.dumps(message))
                    except websockets.ConnectionClosed:
                        websockets_to_remove.add(client)
                    except Exception as e:
                        print(f"Error sending to client: {e}")
                        websockets_to_remove.add(client)

                self.connected_clients -= websockets_to_remove
                self.message_queue.task_done()
        except asyncio.CancelledError:
            pass

    async def consume_rabbitmq(self):
        def callback(ch, method, properties, body):
            try:
                message = BSON(body).decode()
                json_message = self.convert_bson_to_json(message)
                
                # Print debug information
                print(f"Received RabbitMQ message: {json_message}")
                
                # Save the message to the database
                self.db_handler.save_message_to_db(json_message)
                
                # Put the message in the queue for broadcasting
                asyncio.run_coroutine_threadsafe(
                    self.message_queue.put({
                        'type': 'newMessage',
                        'data': json_message
                    }), 
                    self.loop
                )
            except Exception as e:
                print(f"Error processing RabbitMQ message: {e}")

        try:
            connection = await self.loop.run_in_executor(
                None,
                lambda: pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            )
            channel = await self.loop.run_in_executor(None, connection.channel)
            
            queue_name = 'Dashboard'
            await self.loop.run_in_executor(
                None,
                lambda: channel.queue_declare(queue=queue_name, durable=True)
            )
            
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=True
            )
            
            await self.loop.run_in_executor(None, channel.start_consuming)
        except Exception as e:
            print(f"Error in RabbitMQ consumer: {e}")

    async def start(self):
        self.loop = asyncio.get_event_loop()
        server = await websockets.serve(self.handle_client, "localhost", 5001)
        
        # Start RabbitMQ consumer in the background
        asyncio.create_task(self.consume_rabbitmq())
        
        print("WebSocket server started on ws://localhost:5001")
        await server.wait_closed()

if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.run(server.start())