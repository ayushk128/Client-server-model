"""
A simple interactive TCP client.

How it works:
  1. The client creates a socket and CONNECTS to the server's address.
  2. It sends requests (what you type) and receives responses.
  3. A background thread keeps listening, so messages the server pushes
     (like broadcasts from other clients) show up even while you are typing.

Run:  python client.py            (connects to 127.0.0.1:5000)
      python client.py <host> <port>

Type hints (the ": str" and "-> None" parts) say what type each value should be.
Python does not check them when running; they are notes for readers and editors.
"""

import socket
import sys
import threading

HOST = "127.0.0.1"
PORT = 5000
ENCODING = "utf-8"


def receive_loop(sock: socket.socket) -> None:
    """Print every line the server sends until the connection closes."""
    buffer: str = ""  # text received but not yet ended with "\n"
    while True:
        try:
            data = sock.recv(1024)
        except OSError:
            break
        if not data:
            print("\n[connection closed by server]")
            break
        buffer += data.decode(ENCODING)
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            print(f"\rServer: {line}\n> ", end="", flush=True)


def main() -> None:
    host: str = sys.argv[1] if len(sys.argv) > 1 else HOST
    port: int = int(sys.argv[2]) if len(sys.argv) > 2 else PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except ConnectionRefusedError:
        print(f"Could not connect to {host}:{port}. Is the server running?")
        return
    print(f"Connected to {host}:{port}")

    receiver = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
    receiver.start()

    try:
        while receiver.is_alive():
            message = input("> ")
            if not message.strip():
                continue
            sock.sendall((message + "\n").encode(ENCODING))
            if message.strip().upper() == "QUIT":
                receiver.join(timeout=2)  # wait for the server's "Goodbye!"
                break
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        sock.close()


if __name__ == "__main__":
    main()
