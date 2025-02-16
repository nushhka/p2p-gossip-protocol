import threading
import socket
import random
import time
import hashlib
import os
from datetime import datetime

log_lock = threading.Lock()
hash_lock=threading.Lock()
available_peer_lock=threading.Lock()
connected_peer_lock=threading.Lock()
keep_adding_lock=threading.Lock()

def probability(num,den):
    
    random_number = random.randint(1, den)
    if random_number<=num:
        return True
    else:
        return False
    return True


def log_activity(message):
    """Logs activity to outputfile.txt AND prints to the terminal."""
    with log_lock:
        print(message)
        with open("outputfile.txt", "a", buffering=1) as log_file:
            log_file.write(message + "\n")
            log_file.flush()  # Ensure immediate write

def assign_port():
    """Assigns a port in the range 50000-55000."""
    return random.randint(50000, 55000)

def update_keep_adding(peer,new_val):
    if new_val==False:
        with keep_adding_lock:
            peer.keep_adding=False

class Peer:
    def __init__(self, peer_id, seed_nodes):
        self.peer_id = peer_id
        self.peer_ip = "127.0.0.1"
        self.peer_port = assign_port()
        self.seed_nodes = seed_nodes
        self.available_peers=set()
        self.connected_peers = set()
        self.seed_follower={} #whether to 
        self.message_list = set()  # Stores hashes of received messages
        self.liveness_status = {}  # Tracks ping failures for each peer
        self.running=True
        self.keep_adding=True
        self.max_connects=0
        self.max_total=0
        
        # Create a socket for peer communication
        self.peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.peer_socket.bind((self.peer_ip, self.peer_port))
        self.peer_socket.listen(5)

        log_activity(f"[Peer {self.peer_id}] Started at {self.peer_ip}:{self.peer_port}")
        
    def add_msg(self,hash):
        with hash_lock:
            self.message_list.add(hash)
          
            
    def stop(self):
        """Gracefully stop the peer."""
        self.running = False  # Tell threads to stop
        
        
        ### NOT USING THIS
        # log_degree=f"The maximum number of connections made by Peer {self.peer_id} (IP:{self.peer_ip}, Port:{self.peer_port}) is : {self.max_connects}\nThe available connections were however {self.max_total}"
        # print(log_degree)
        
        # log_activity(log_degree)
        
        self.peer_socket.close()  # Close the main listening socket


        log_activity(f"[Peer {self.peer_id}] Shutdown complete. Seed yet to be updated (to be informed by other peers in the network)")
        
    def register_with_seeds(self):
        """Registers with a subset of seed nodes."""
        num_seeds = len(self.seed_nodes)
        required_seeds = max(1, num_seeds // 2 + 1)
        chosen_seeds = random.sample(self.seed_nodes, required_seeds)

        for seed_ip, seed_port in chosen_seeds:
            try:
                seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                seed_socket.connect((seed_ip, int(seed_port)))
                seed_socket.sendall(f"{self.peer_ip}:{self.peer_port}".encode())
                peer_list_data = seed_socket.recv(1024).decode()
                seed_socket.close()

                for peer in peer_list_data.split("\n"):
                    if peer:
                        peer_ip, peer_port = peer.split(":")
                        if (peer_ip, peer_port) != (self.peer_ip, str(self.peer_port)):  # Prevent adding itself
                            self.available_peers.add((peer_ip, peer_port))


                log_activity(f"[Peer {self.peer_id}] Registered with Seed {seed_ip}:{seed_port}")
            except Exception as e:
                log_activity(f"[Peer {self.peer_id}] Failed to connect to Seed {seed_ip}:{seed_port}: {e}")
            
        for neighbour in self.available_peers.copy():  # Create a copy of the set
            if len(self.connected_peers)<2:
                og_size=len(self.connected_peers)
                while self.available_peers and len(self.connected_peers)<=og_size:  # Ensure there are nodes to select from
                    selected_peer = random.choice(tuple(self.available_peers))  # Convert set to tuple for random selection
                    if selected_peer==(self.peer_ip,self.peer_port) or selected_peer in self.connected_peers:
                        self.available_peers.remove(selected_peer)
                        continue
                    self.connected_peers.add(selected_peer)  # Add to connected nodes
                    self.liveness_status[selected_peer]=0
                    if len(self.connected_peers)>og_size:
                        log_activity(f"[Peer {self.peer_id}] Connected to new peer: {selected_peer}")
                    self.available_peers.remove(selected_peer)  # Remove from available nodes
            else:
                if self.keep_adding :
                    if len(self.connected_peers)>2 and probability(len(self.connected_peers)-2,len(self.connected_peers)-1):
                        update_keep_adding(self,False)
                if not self.keep_adding:
                    break
                og_size=len(self.connected_peers)
                while self.available_peers and len(self.connected_peers)<=og_size:  # Ensure there are nodes to select from
                    selected_peer = random.choice(tuple(self.available_peers))  # Convert set to tuple for random selection
                    if selected_peer==(self.peer_ip,self.peer_port):
                        continue
                    if len(self.connected_peers)>og_size:
                        log_activity(f"[Peer {self.peer_id}] Connected to new peer: {selected_peer}")
                        self.connected_peers.add(selected_peer)  # Add to connected nodes
                    self.available_peers.remove(selected_peer)  # Remove from available nodes
                

    def start_listening(self):
        """Listens for incoming messages from peers/seeds."""
        while self.running:
            try:
                client_socket, _ = self.peer_socket.accept()
                threading.Thread(target=self.handle_connection, args=(client_socket,)).start()
            except OSError:
                break  # Happens if socket is closed

    def handle_connection(self, client_socket):
        """Handles incoming messages from peers."""
        try:
            message = client_socket.recv(1024).decode()
            message_hash = hashlib.sha256(message.encode()).hexdigest()

            if message.startswith("(PEER)PING_REPLY"):
                peer_ip, peer_port = message.split(":")[1:]
                self.liveness_status[(peer_ip, peer_port)] = 0  # Reset failure counter
                log_activity(f"[Peer {self.peer_id}] Received PING_REPLY from {peer_ip}:{peer_port}")

            elif message.startswith("(PEER)PING"):
                peer_ip, peer_port = message.split(":")[1:]
                reply_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                reply_socket.connect((peer_ip, int(peer_port)))
                reply_socket.sendall(f"(PEER)PING_REPLY:{self.peer_ip}:{self.peer_port}".encode())
                reply_socket.close()
            
            elif message.startswith("(SEED)ADDED NEW NODE TO NETWORK"):
                if self.keep_adding : 
                    if len(self.connected_peers)>2 and not probability(len(self.connected_peers)-2,len(self.connected_peers)-1):
                        update_keep_adding(self,False)
                        
                if self.keep_adding:
                    seed_ip,new_peer_ip, new_peer_port = message.split(":")[1:]
                    og_size=len(self.connected_peers)
                    if (new_peer_ip,new_peer_port) not in self.connected_peers and (new_peer_ip,new_peer_port)!= (self.peer_ip, str(self.peer_port)):  # Prevent adding itself
                        self.connected_peers.add((new_peer_ip, new_peer_port))
                        if len(self.connected_peers)>og_size:
                            log_activity(f"[Peer {self.peer_id}] Connected to new peer: {new_peer_ip}: {new_peer_port}")
                            self.liveness_status[(new_peer_ip, new_peer_port)] = 0  # Initialize liveness counter
            
            elif message_hash not in self.message_list:
                self.add_msg(message_hash)
                log_activity(f"[Peer {self.peer_id}] Received Gossip Message: {message}")
                self.forward_message(message)

        except Exception as e:
            log_activity(f"[Peer {self.peer_id}] Error handling message: {e}")
        finally:
            client_socket.close()

    def send_ping(self):
        """Sends ping messages to all connected peers every 13 seconds."""
        while True:
            if not self.running:
                break
            time.sleep(13)
            dead_peers = []
            
            for peer_ip, peer_port in list(self.connected_peers):
                try:
                    log_activity(f"[Peer {self.peer_id}] Sending PING to {peer_ip}:{peer_port}")
                    ping_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    ping_socket.settimeout(2)
                    ping_socket.connect((peer_ip, int(peer_port)))
                    ping_socket.sendall(f"(PEER)PING:{self.peer_ip}:{self.peer_port}".encode())
                    ping_socket.close()
                except:
                    self.liveness_status[(peer_ip, peer_port)] += 1
                    log_activity(f"[Peer {self.peer_id}] Failed to PING {peer_ip}:{peer_port} ({self.liveness_status[(peer_ip, peer_port)]} failed attempts)")
            
                if self.liveness_status[(peer_ip, peer_port)] >= 3:
                    dead_peers.append((peer_ip, peer_port))

            for dead_peer in dead_peers:
                self.report_dead_node(dead_peer)
                self.connected_peers.remove(dead_peer)

    def report_dead_node(self, dead_peer):
        """Notifies seed nodes that a peer is dead."""
        dead_ip, dead_port = dead_peer
        timestamp = time.time()

        for seed_ip, seed_port in self.seed_nodes:
            try:
                seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                seed_socket.connect((seed_ip, int(seed_port)))
                seed_socket.sendall(f"Dead Node:{dead_ip}:{dead_port}:{timestamp}:{self.peer_ip}".encode())
                seed_socket.close()
            except:
                pass

        log_activity(f"[Peer {self.peer_id}] Reported Dead Peer: {dead_ip}:{dead_port}")

    def generate_gossip_message(self):
        time.sleep(30)
        """Generates and broadcasts a gossip message every 5 seconds."""
        for i in range(10):  # Generate 10 messages before stopping
            if not self.running:
                break
            time.sleep(5)
            timestamp = datetime.now().strftime("[%Y-%m-%d %H->%M.%S]")
            message = f"{timestamp}:{self.peer_ip}: Message {i} [Hello from {self.peer_id}]"
            message_hash = hashlib.sha256(message.encode()).hexdigest()

            if message_hash not in self.message_list:
                self.add_msg(message_hash)
                log_activity(f"[Peer {self.peer_id}] Generated Gossip Message: {message}")
                self.forward_message(message)

    def track_connections(self):
        self.max_connects=max(self.max_connects,len(self.connected_peers))
        self.max_total=max(self.max_total,len(self.connected_peers)+len(self.available_peers))
        time.sleep(1)
        
    
    def forward_message(self, message):
        """Forwards the message to connected peers, except the sender."""
        for peer_ip, peer_port in self.connected_peers:
            try:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.settimeout(5)
                peer_socket.connect((peer_ip, int(peer_port)))
                peer_socket.sendall(message.encode())
                peer_socket.close()
                log_activity(f"[Peer {self.peer_id}] Forwarded Gossip Message to {peer_ip}:{peer_port}")
            except:
                pass


if __name__ == "__main__":
    open("outputfile.txt", "a").close()  # Clear outputfile file

    with open("config.txt", "r") as f:
        seed_nodes = [tuple(line.strip().split(":")) for line in f.readlines()]
        
    name=input("Enter a name for this peer: ")
    single_peer_list=[]
    try:
        peer = Peer(name, seed_nodes)
        single_peer_list.append(peer)

        threading.Thread(target=peer.start_listening, daemon=True).start()
        threading.Thread(target=peer.send_ping, daemon=True).start()
        threading.Thread(target=peer.generate_gossip_message, daemon=True).start()
        # threading.Thread(target=peer.track_connections, daemon=True).start()
        
        time.sleep(2)  # Ensure peers start before registering
        
        peer.register_with_seeds()
        
        print("All peers are registered and running. Press Ctrl+C to stop.")

        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        for peer in single_peer_list:
            peer.stop()  # Close sockets and notify seeds
        print("The peer has stopped. Exiting.")