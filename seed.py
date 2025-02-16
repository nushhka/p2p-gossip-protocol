import threading
import socket
import signal
from threading import Lock

# Global dictionary to store peer lists for each seed node
seed_peer_lists = {}
log_lock = threading.Lock()  # Lock for thread-safe logging
peer_list_lock = Lock()
seed_sockets = {}  # Store seed sockets for cleanup
running = True  # Control flag for graceful shutdown

def log_activity(message):
    with log_lock:  # Ensure thread safety
        with open("outputfile.txt", "a") as log_file:
            log_file.write(message + "\n")
            log_file.flush()

def refresh_peers(seed_port,new_peer_ip,new_peer_port):
    for (peer_ip,peer_port) in seed_peer_lists[seed_port]:
        peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer_socket.connect((peer_ip, int(peer_port)))
        print(12)
        peer_socket.sendall(f"(SEED)ADDED NEW NODE TO NETWORK:{seed_port}:{new_peer_ip}:{new_peer_port}".encode())
        peer_socket.close()
        
def add_peer(seed_port, peer_ip, peer_port):
    """Adds a peer to the seed's peer list in a thread-safe manner."""
    with peer_list_lock:
        if seed_port not in seed_peer_lists:
            seed_peer_lists[seed_port] = set()
        seed_peer_lists[seed_port].add((peer_ip, peer_port))
    log_activity(f"[Seed {seed_port}] Connected peer: {peer_ip}:{peer_port}")
    refresh_peers(seed_port,peer_ip,peer_port)


def remove_peer(seed_port, peer_ip, peer_port):
    """Removes a peer from the seed's peer list in a thread-safe manner."""
    with peer_list_lock:
        if seed_port in seed_peer_lists and (peer_ip, peer_port) in seed_peer_lists[seed_port]:
            seed_peer_lists[seed_port].remove((peer_ip, peer_port))
            log_activity(f"[Seed {seed_port}] Removed peer: {peer_ip}:{peer_port}")

def handle_peer_connection(client_socket, seed_port):
    """Handles communication with a newly connected peer."""
    try:
        message = client_socket.recv(1024).decode()

        if message.startswith("Dead Node"):
            print(2)
            try:
                _, peer_ip, peer_port, timestamp, reporter_ip = message.split(":")
                if (peer_ip, peer_port) in seed_peer_lists[seed_port]:
                    remove_peer(seed_port, peer_ip, peer_port)
            except ValueError:
                log_activity(f"[Seed {seed_port}] Malformed Dead Node message: {message}")
            
        else:  # Peer registration
            print(3)
            peer_ip, peer_port = message.split(":")
            add_peer(seed_port, peer_ip, peer_port)

            peer_list_str = "\n".join([f"{ip}:{port}" for ip, port in seed_peer_lists[seed_port]])
            client_socket.sendall(peer_list_str.encode())

    except Exception as e:
        log_activity(f"[Seed {seed_port}] Error handling peer: {str(e)}")
    finally:
        client_socket.close()

def start_seed(ip, port):
    """Starts a seed node to listen for peer connections."""
    global running
    try:
        seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        seed_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        seed_socket.bind((ip, port))
        seed_socket.listen(5)
        seed_sockets[port] = seed_socket  # Store socket reference

        log_activity(f"[Seed {port}] Running at {ip}:{port}")
        print(f"[Seed {port}] Running at {ip}:{port}")

        while running:
            try:
                seed_socket.settimeout(1)  # Allow checking for shutdown
                client_socket, _ = seed_socket.accept()
                threading.Thread(target=handle_peer_connection, args=(client_socket, port)).start()
            except socket.timeout:
                continue  # Timeout allows loop to check 'running' flag
    except Exception as e:
        log_activity(f"[Seed {port}] Failed to start: {str(e)}")
    finally:
        log_activity(f"[Seed {port}] Shutting down...")
        if port in seed_sockets:
            seed_sockets[port].close()  # Close listener socket
            del seed_sockets[port]

def read_config():
    """Reads config.txt and returns a list of (IP, Port) tuples."""
    with open("config.txt", "r") as f:
        lines = f.readlines()
    return [tuple(line.strip().split(":")) for line in lines]

def shutdown(signal_received, frame):
    """Handles graceful shutdown when Ctrl+C (SIGINT) is received."""
    global running
    print("\n[!] Shutting down gracefully...")
    log_activity("[System] Shutting down gracefully...")

    running = False  # Stop accepting new connections

    # Close all active seed sockets
    for port, sock in list(seed_sockets.items()):
        sock.close()
        log_activity(f"[Seed {port}] Closed listener socket.")

    exit(0)

if __name__ == "__main__":
    open("outputfile.txt", "w").close()  # Clear the log file at the start
    seed_nodes = read_config()
    threads = []

    signal.signal(signal.SIGINT, shutdown)  # Capture Ctrl+C for clean exit

    for ip, port in seed_nodes:
        port = int(port)  # Convert port from string to integer
        thread = threading.Thread(target=start_seed, args=(ip, port))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()  # Wait for all threads to finish
