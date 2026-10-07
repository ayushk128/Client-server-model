# Client-Server Model in Python

A small project for learning the client-server model with plain TCP sockets. It uses only the Python standard library.

## Files

| File | Role |
|------|------|
| `server.py` | Waits for connections, handles each client in its own thread, and answers requests |
| `client.py` | Connects to the server, sends what you type, and prints the responses |

## How to run

1. Open a terminal and start the server:
   ```
   python server.py
   ```
2. Open a **second** terminal and start a client:
   ```
   python client.py
   ```
3. Type commands in the client:
   ```
   > HELP
   > ECHO hello
   > UPPER hello world
   > REVERSE hello
   > ADD 2 3
   > TIME
   > CLIENTS
   > QUIT
   ```
4. Open a third terminal, start another client, and try `BROADCAST hi everyone`. The message shows up in the other client.

Watch the server terminal while you do this. It logs every connection, request and response.

## The concepts, mapped to the code

```
        SERVER                                CLIENT
  socket()                               socket()
  bind(("127.0.0.1", 5000))
  listen()
  accept()  <------- TCP handshake ----  connect(("127.0.0.1", 5000))
     |                                       |
  recv()    <------- "ADD 2 3\n" --------  sendall()
  process
  sendall() -------- "5.0\n" ----------->  recv()
     |                                       |
  close()   <------- "QUIT\n" -----------  close()
```

- **Socket**: one endpoint of a network connection. `AF_INET` means IPv4 and `SOCK_STREAM` means TCP.
- **bind / listen / accept**: the server claims a port, waits, and gets a *new* socket for each client that connects.
- **connect**: the client starts a connection to the server's IP and port.
- **Protocol**: both sides must agree on the message format. This project uses one text command per line. TCP is a *byte stream* with no message boundaries, so the `\n` marks where each message ends. That's why both sides keep a `buffer`.
- **Concurrency**: `accept()` and `recv()` block (wait). Each client gets its own thread, so one slow client doesn't freeze the others.
- **Shared state**: the `clients` dictionary is used by many threads at once, so a `threading.Lock` protects it.

## Things to try next

1. ~~Add a new command such as `REVERSE <text>` in `handle_request()` in `server.py`.~~ Done. Try adding your own command the same way, e.g. `COUNT <text>` (number of characters).
2. Connect from another computer: set `HOST = "0.0.0.0"` in `server.py`, then run `python client.py <server-ip> 5000` on the other machine. You may need to allow Python through the firewall.
3. Make a chat room: let clients pick a name with `NICK <name>` and show it in broadcasts.
4. Switch the protocol to JSON messages (`json.dumps` / `json.loads`).
5. Rewrite the server with `asyncio` instead of threads and compare the two.
6. Try UDP (`SOCK_DGRAM`) to see how a connectionless protocol behaves differently.
