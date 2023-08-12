import asyncio
import websockets
import json

# Dicionário para armazenar as conexões dos clientes por sala
rooms = {}

async def chat_server(websocket, path):
    room_id = path.strip("/")
    if room_id not in rooms:
        rooms[room_id] = set()

    rooms[room_id].add(websocket)

    # Carrega mensagens arquivadas da sala
    archive = load_archive(room_id)
    if archive:
        for message in archive:
            await websocket.send(message)

    try:
        async for message in websocket:

 # Envia a mensagem recebida para todos os clientes conectados na sala
            await asyncio.gather(*[client.send(message) for client in rooms[room_id] if client != websocket])

            # Arquiva a mensagem
            archive_message(room_id, message)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        rooms[room_id].remove(websocket)

def load_archive(room_id):
    archive = {}
    try:
        with open("chat_archive.json", "r") as f:
            archive = json.load(f)
    except FileNotFoundError:
        pass

    return archive.get(room_id, [])

def archive_message(room_id, message):
    archive = load_archive(room_id)
    if len(archive) >= 100:
        archive.pop(0)  # Remove a mensagem mais antiga para manter um histórico limitado
    archive.append(message)
    with open("chat_archive.json", "w") as f:
        json.dump({room_id: archive}, f)

# Função para enviar mensagens para uma sala específica
async def send_message_to_room(room_id, message):
    if room_id in rooms:
        await asyncio.gather(*[client.send(message) for client in rooms[room_id]])

# Inicia o servidor WebSocket na porta 8765
start_server = websockets.serve(chat_server, "0.0.0.0", 8765)

# Inicia o loop de eventos
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
