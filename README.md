# **P2P Network with Gossip Protocol**
A Python-based **peer-to-peer (P2P) network** implementing **gossip protocol** for message dissemination and **power-law degree distribution** for peer connections. This system consists of **seed nodes** for peer discovery and **peer nodes** for message exchange.

## **📌 Features**

- **Seed Nodes**: Manage peer discovery and maintain a list of connected peers.

- **Peer Nodes**:
  - Register with seed nodes.
  - Select connected peers using **power-law distribution**.
  - Periodically send **gossip messages**.
  - Monitor **peer liveness** with **ping messages**.
  - Remove **dead peers** from the network.
  
- **Logging**:
  - Logs all important activities (`output.txt`).
  - Stores gossip messages in a separate log (`ML.txt`).

---

## **📂 Project Structure**
```
📦 P2P-Gossip-Network
 ├── 📜 seed.py                 (Seed node implementation)
 ├── 📜 peer.py                 (Peer node implementation)
 ├── 📜 config.txt              (Configuration file for seed nodes)
 ├── 📜 output.txt              (Logs all peer/seed activities)
 ├── 📜 ML.txt                  (Stores received gossip messages)

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
- `output.txt`: Logs peer and seed activities.
- `ML.txt`: Stores **received gossip messages**.

### **4️⃣ Monitor Dead Peers**
- If a peer disconnects (e.g., pressing `Ctrl+C`), **ping failures** will remove it after 3 failed ping attempts.
- The **seed node will update the peer list** accordingly.

---


## **🛠️ Testing & Debugging**
### **🔹 Check Running Peers**
To list active peer connections:
```sh
netstat -ano | findstr :<PORT>
```
Replace `<PORT>` with a known peer port.

### **🔹 Simulate Peer Failure**
To test peer failure handling:
1. **Start multiple peers.**
2. **Stop a peer manually** (`Ctrl+C`).
3. Other peers should detect failure after **3 failed pings**.
4. Seed nodes should remove the failed peer.

### **🔹 Verify Gossip Propagation**
- Each peer **generates** a gossip message every **10 seconds**.
- Messages should be **received** and stored in `ML.txt`.

---

