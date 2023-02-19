import socket
import threading
import sqlite3
from profanity_filter import ProfanityFilter

# Define the host and port to use for the chat application
HOST = '127.0.0.1'
PORT = 55555

# Create a new socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the specified host and port
server.bind((HOST, PORT))

# Listen for incoming connections
server.listen()

# List to hold all connected clients
clients = []

# Create a new instance of the profanity filter
pf = ProfanityFilter()

# Connect to the database
conn = sqlite3.connect('chat_users.db')
c = conn.cursor()

# Create a table to store user information if it doesn't already exist
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (username text, password text)''')
conn.commit()

# Function to handle incoming client connections
def handle_client(client):
    while True:
        try:
            # Receive data from the client
            message = client.recv(1024).decode('utf-8')
            
            # Check if the message is a login attempt
            if message.startswith('/login'):
                username, password = message[7:].split(':')
                # Check if the user exists in the database
                c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
                user = c.fetchone()
                if user is not None:
                    client.send("Login successful!".encode('utf-8'))
                else:
                    client.send("Invalid username or password".encode('utf-8'))
            
            # Check if the message is a signup attempt
            elif message.startswith('/signup'):
                username, password = message[8:].split(':')
                # Check if the username already exists in the database
                c.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = c.fetchone()
                if user is not None:
                    client.send("Username already exists".encode('utf-8'))
                else:
                    c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                    conn.commit()
                    client.send("Signup successful!".encode('utf-8'))
            
            else:
                # Check if the message contains any profanity and replace it with *
                if pf.is_profane(message):
                    message = pf.censor(message)
                # Broadcast the message to all connected clients
                for c in clients:
                    c.send(message.encode('utf-8'))
        except:
            # If there is an error, remove the client from the list of connected clients
            clients.remove(client)
            client.close()
            break

# Function to start the server and accept incoming connections
def start_server():
    print(f"Server is listening on {HOST}:{PORT}")
    while True:
        # Accept incoming connections
        client, address = server.accept()
        # Add the new client to the list of connected clients
        clients.append(client)
        # Create a new thread to handle the client's connection
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

if __name__ == '__main__':
    start_server()
