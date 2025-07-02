import socket
import io
import cv2
import numpy as np
from PIL import Image
from pynput import keyboard, mouse
from threading import Thread
import ssl


def send_to_server(data, client_socket):
    try:
        client_socket.sendall(data.encode('utf-8'))
    except BrokenPipeError:
        print("Connection lost to the server.")
        exit()


def on_key_press(key, client_socket):
    try:
        if hasattr(key, 'char') and key.char is not None:
            print(f"Sending key press: {key.char}")
            send_to_server(f"Key pressed: {key.char}\n", client_socket)
        else:
            print(f"Sending special key press: {key}")
            send_to_server(f"Special key pressed: {key}\n", client_socket)
    except Exception as e:
        print(f"Error in on_key_press: {e}")


def on_click(x, y, button, pressed, client_socket):
    if pressed:
        send_to_server(f"Mouse clicked at ({x}, {y}) with {button}\n", client_socket)


def on_move(x, y, client_socket):
    send_to_server(f"Mouse moved to ({x}, {y})\n", client_socket)


def handle_interactions(client_socket):
    keyboard_listener = keyboard.Listener(on_press=lambda key: on_key_press(key, client_socket))
    keyboard_listener.start()

    mouse_listener = mouse.Listener(
        on_click=lambda x, y, button, pressed: on_click(x, y, button, pressed, client_socket),
        on_move=lambda x, y: on_move(x, y, client_socket)
    )
    mouse_listener.start()

    keyboard_listener.join()
    mouse_listener.join()


def receive_and_display_images(client_socket):
    try:
        while True:
            img_size = int.from_bytes(client_socket.recv(4), 'big')
            img_bytes = b''
            while len(img_bytes) < img_size:
                packet = client_socket.recv(img_size - len(img_bytes))
                if not packet:
                    break
                img_bytes += packet

            img = Image.open(io.BytesIO(img_bytes))
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            img_resized = cv2.resize(img, (1000, 600))
            cv2.imshow('Screen', img_resized)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                quit()
    finally:
        client_socket.close()
        cv2.destroyAllWindows()


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_context.load_verify_locations("server.crt")
    ssl_context.check_hostname = False

    
    host_ip = '192.168.1.216'
    port = 12345

    secure_socket = ssl_context.wrap_socket(client_socket)

    try:
        secure_socket.connect((host_ip, port))
        print("Connected to server...")

        image_thread = Thread(target=receive_and_display_images, args=(secure_socket,))
        image_thread.start()

        handle_interactions(secure_socket)
    except Exception as e:
        print(f"Error: {e}")
        secure_socket.close()


if __name__ == "__main__":
    main()
