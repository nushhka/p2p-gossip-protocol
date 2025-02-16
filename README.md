# **P2P Network with Gossip Protocol**
A Python-based **peer-to-peer (P2P) network** implementing **gossip protocol** for message dissemination and **power-law degree distribution** for peer connections. This system consists of **seed nodes** for peer discovery and **peer nodes** for message exchange.

## **📌 Features**

### **🔹 Seed Nodes**
- Manage peer discovery and maintain a list of connected peers.
- Keep listning to connected peers and **removing dead peers** as reported by connected peers.
- Actively listens for newly joined peer seeking connections.
- Notify other peers about **newly registered peers**.

### **🔹 Peer Nodes**
- Register with randomly chosen **seed nodes** (at least ⌊n/2⌋ + 1).
- Select connected peers using a **power-law distribution**.
- Periodically send **gossip messages** after every **5 seconds**, stopping after **10 messages**.
- Monitor **peer liveness** using **ping messages** every 13 seconds.
- Report **dead peers** to seed nodes if they fail **3 consecutive pings**.
- **Logging**:
  - Logs all important activities (`outputfile.txt`).

---

## **📂 Project Structure**
```
📦 P2P-Gossip-Network
 ├── 📜 seed.py: Manages peer registration, provides peer lists, and removes dead peers.
 ├── 📜 peer.py: Implements the peer logic, including gossip messaging, peer connections, and liveness checks.
 ├── 📜 config.txt: Stores seed node details (`IP:Port` pairs).
 ├── 📜 outputfile.txt: Stores seed node details (`IP:Port` pairs).
 ├── 📜 readme.md

```

---

## **🚀 Setup & Installation**
### **1️⃣ Install Dependencies**
Ensure you have **Python 3.x** installed. Then, install required libraries:
```sh
pip install numpy matplotlib
```

### **2️⃣ Configure Seed Nodes**
Edit `config.txt` to specify **seed node IPs and ports**:
```
127.0.0.1:5002
127.0.0.1:7234
127.0.0.1:6071
```
Each line represents a **seed node**.

---

## **🖥️ Running the Project**

### **1️⃣ Start Seed Nodes**
Run the seed script in **one terminal**:
```sh
python seed.py
```
It will start all seed nodes **as per `config.txt`**.

### **2️⃣ Start Peer Nodes**
Open multiple terminals and run:
```sh
python peer.py
```
- Enter a **unique name** for each peer.
- Peers will register with **seed nodes** and connect using **power-law distribution**.
- They will start **exchanging gossip messages** that are generated after 30sec of peer creation and generates gossips every 5sec till 10 gossips.

### **3️⃣ Check Network Logs**
- `outputfile.txt`: Logs peer and seed activities.

### **4️⃣ Monitor Dead Peers**
- If a peer disconnects (e.g., pressing `Ctrl+C`), **ping failures** will remove it after 3 failed ping attempts.
- The **seed node will update the peer list** accordingly.

---


## **🛠️ Testing & Debugging**

### **🔹 Simulate Peer Failure**
To test peer failure handling:
1. **Start multiple peers.**
2. **Stop a peer manually** (`Ctrl+C`).
3. Other peers should detect failure after **3 failed pings**.
4. Seed nodes should remove the failed peer.

---

