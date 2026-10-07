"""
A simple multi-client TCP server.

How it works:
  1. The server creates a socket and BINDS it to an address (host + port).
  2. It LISTENS for incoming connections.
  3. When a client connects, ACCEPT returns a new socket just for that client.
  4. Each client is handled in its own thread, so many clients can talk at once.
  5. The server reads a request, processes it, and sends back a response.

Protocol (text based, one message per line, ending with "\n"):
  ECHO <text>     -> server replies with the same text
  UPPER <text>    -> server replies with the text in UPPERCASE
  REVERSE <text>  -> server replies with the text backwards
  ADD <a> <b>     -> server replies with a + b
  TIME            -> server replies with the current server time
  CLIENTS         -> number of clients currently connected
  BROADCAST <msg> -> send a message to every connected client
  HELP            -> list of commands
  QUIT            -> server says goodbye and closes the connection

Run:  python server.py
"""

import socket
import threading
from datetime import datetime

HOST = "127.0.0.1"  # localhost: only this machine can connect. Use "0.0.0.0" to accept from the network.
PORT = 5000         # any free port above 1024 works
ENCODING = "utf-8"

# Shared state between threads -> must be protected with a lock.
clients = {}  # socket -> address
clients_lock = threading.Lock()


def log(message):
    print(f"[{datetime.now():%H:%M:%S}] {message}")


def send_line(conn, text):
    """Send one message. The trailing newline tells the receiver where the message ends."""
    conn.sendall((text + "\n").encode(ENCODING))


def broadcast(text, sender=None):
    with clients_lock:
        targets = [c for c in clients if c is not sender]
    for conn in targets:
        try:
            send_line(conn, text)
        except OSError:
            pass  # that client has probably disconnected; its own thread will clean up


def handle_request(line, conn, addr):
    """Turn one request line into a response string. Returns None to close the connection."""
    command, _, argument = line.partition(" ")
    command = command.upper()

    if command == "ECHO":
        return argument
    if command == "UPPER":
        return argument.upper()
    if command == "REVERSE":
        return argument[::-1]  # slice with step -1 walks the string from end to start
    if command == "ADD":
        try:
            a, b = argument.split()
            return str(float(a) + float(b))
        except ValueError:
            return "ERROR usage: ADD <number> <number>"
    if command == "TIME":
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if command == "CLIENTS":
        with clients_lock:
            return f"{len(clients)} client(s) connected"
    if command == "BROADCAST":
        broadcast(f"[broadcast from {addr[0]}:{addr[1]}] {argument}", sender=conn)
        return "OK broadcast sent"
    if command == "HELP":
        return "Commands: ECHO <text>, UPPER <text>, REVERSE <text>, ADD <a> <b>, TIME, CLIENTS, BROADCAST <msg>, HELP, QUIT"
    if command == "QUIT":
        return None
    return f"ERROR unknown command '{command}'. Type HELP."


def handle_client(conn, addr):
    """Runs in its own thread: one per connected client."""
    log(f"Connected: {addr}")
    with clients_lock:
        clients[conn] = addr

    send_line(conn, "Welcome! Type HELP to see the available commands.")

    buffer = ""
    try:
        while True:
            # recv() returns whatever bytes have arrived so far (up to 1024).
            # It may be half a message or several messages, so we buffer until "\n".
            data = conn.recv(1024)
            if not data:  # empty bytes = client closed the connection
                break
            buffer += data.decode(ENCODING)

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                log(f"{addr} -> {line}")
                response = handle_request(line, conn, addr)
                if response is None:
                    send_line(conn, "Goodbye!")
                    return
                send_line(conn, response)
                log(f"{addr} <- {response}")
    except (ConnectionResetError, ConnectionAbortedError):
        log(f"Connection lost: {addr}")
    finally:
        with clients_lock:
            clients.pop(conn, None)
        conn.close()
        log(f"Disconnected: {addr}")


def main():
    # AF_INET = IPv4, SOCK_STREAM = TCP (reliable, ordered byte stream)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Lets you restart the server immediately without "Address already in use"
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    # A timeout on accept() lets Ctrl+C work on Windows
    server.settimeout(1.0)
    log(f"Server listening on {HOST}:{PORT} (Ctrl+C to stop)")

    try:
        while True:
            try:
                conn, addr = server.accept()  # blocks until a client connects
            except socket.timeout:
                continue
            conn.settimeout(None)
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        log("Shutting down server...")
    finally:
        server.close()


if __name__ == "__main__":
    main()
