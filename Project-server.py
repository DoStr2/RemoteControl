import socket
import threading
import io
from PIL import ImageGrab
import numpy as np
import ssl
from pynput import keyboard, mouse


def capture_and_stream(client_socket):
    while True:
        try:
            img = ImageGrab.grab()

            if img.mode == 'RGBA':
                img = img.convert('RGB')

            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            img_bytes = buf.getvalue()

            client_socket.sendall(len(img_bytes).to_bytes(4, 'big'))
            client_socket.sendall(img_bytes)
        except Exception as e:
            print(f"Error capturing or sending screen: {e}")
            break
    client_socket.close()


SPECIAL_KEYS = {
    f'Key.{key}': getattr(keyboard.Key, key)
    for key in dir(keyboard.Key)
    if not key.startswith('_')
}

def simulate_key_press(key_str):
    try:
        controller = keyboard.Controller()
        key = SPECIAL_KEYS.get(key_str, key_str)
        controller.press(key)
        controller.release(key)
    except Exception as e:
        print(f"Error simulating key press for '{key_str}': {e}")


def simulate_mouse_move(x, y):
    try:
        mouse_controller = mouse.Controller()
        mouse_controller.position = (x, y)
    except Exception as e:
        print(f"Error simulating mouse movement: {e}")


def simulate_mouse_click(x, y, button):
    try:
        mouse_controller = mouse.Controller()
        mouse_controller.position = (x, y)
        if button == 'Button.left':
            mouse_controller.click(mouse.Button.left)
        elif button == 'Button.right':
            mouse_controller.click(mouse.Button.right)
    except Exception as e:
        print(f"Error simulating mouse click: {e}")


def receive_client_data(client_socket):
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            print(f"Received data: {data}")

            if "Key pressed:" in data or "Special key pressed:" in data:
                key_str = data.split(":")[1].strip()
                simulate_key_press(key_str)
            elif "Mouse clicked at" in data:
                _, action_details = data.split("Mouse clicked at ")
                coords, button = action_details.split(" with ")
                x, y = map(int, coords.strip('()\n').split(', '))
                button = button.strip()
                simulate_mouse_click(x, y, button)
            elif "Mouse moved to" in data:
                coords = data.split("Mouse moved to ")[1].strip('()\n')
                x, y = map(int, coords.split(', '))
                simulate_mouse_move(x, y)
        except Exception as e:
            print(f'Error receiving or processing data: {e}')
            break

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    host_ip = '192.168.1.216'
    port = 12345
    server_socket.bind((host_ip, port))
    server_socket.listen(1)
    print('Listening at:', (host_ip, port))

    client_socket, client_address = server_socket.accept()
    print('Connected to:', client_address)

    secure_socket = ssl_context.wrap_socket(client_socket, server_side=True)

    threading.Thread(target=capture_and_stream, args=(secure_socket,)).start()
    threading.Thread(target=receive_client_data, args=(secure_socket,)).start()

if __name__ == "__main__":
    main()
