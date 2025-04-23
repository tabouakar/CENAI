# CenAI: Dual-Mode Chatbot for HR & Engineering Support

**CenAI** is a web-based AI assistant platform developed as a senior design project at UConn. The platform includes two distinct chatbots:

- 🧑‍💼 **HR & Ethics Policy Assistant** — designed to answer questions using university-specific HR documentation.
- 🔧 **Engineering Troubleshooting Assistant** — built using Retrieval-Augmented Generation (RAG) to provide guidance based on Cisco documentation and similar technical resources.

CenAI can run in two modes:
- **Local Mode**: Using the [Ollama](https://ollama.com) framework to host large language models like *Gemma* on a GPU server.
- **Cloud Mode**: Using OpenAI’s API and assistant tools via `OPENAI_API_KEY` and `ASSISTANT_ID`.

The platform initially only used OpenAI’s cloud-based models via API but has since been transitioned to a locally-hosted inference setup using **Ollama** and the **Gemini 3 model**, improving data security, latency, and cost-efficiency.

---

## 🔧 Project Structure

```
SDP_Project/
├── cenai_app/              # Core web application (frontend + backend)
│   ├── backend/            # Node.js server (OpenAI or Ollama + RAG logic)
│   ├── frontend/           # Static site (HTML/CSS/JS)
│   ├── php/                # PHPCAS login (NetID-based auth)
│   ├── chat.logs/          # SQLite DB for message history (ignored)
│   ├── node_modules/       # Node packages (ignored)
│   ├── vendor/             # Composer packages (ignored)
│   ├── .env                # API keys and secrets (ignored)
│   ├── package*.json       # Node dependency definitions
│   ├── composer*.json      # PHP dependency definitions
│   └── README.md           # App-specific docs (optional)
│
├── retrieval/              # All Python-based RAG + vector store logic
│   ├── *.py                # Scripts for preprocessing & vector DB
│   ├── *.json              # Embeddable HR/technical documents
│   └── start-chroma.sh     # ChromaDB launch script
│
├── scripts/                # Bootstrapping, orchestration, system utils
│   └── spin-up.sh          # tmux-based launcher for Node, PHP, Chroma
│
├── README.md               # Main documentation (you're reading it)
└── .gitignore              # Prevent secrets and dependencies from uploading

```

---

## 🔧 Tech Stack

- **Frontend**: HTML/CSS/JS served via Node.js
- **Backend**: Node.js (Express), PHP login server
- **Authentication**: UConn NetID (via UConn’s PHPCAS system)
- **Database**: SQLite (chat logs)
- **Vector Store**: [ChromaDB](https://www.trychroma.com/)
- **LLM Inference**: Ollama with locally hosted [Gemma 3](https://ollama.com/library/gemma)
- **Webserver**: nginx (reverse proxy)
- **Environment**: Ubuntu 24.04 LTS on shared VM

---

## ⚙️ System Requirements

- Node.js (v18+ recommended)
- PHP 8.1+ (for NetID login via PHPCAS)
- Composer (for PHP dependencies)
- Python 3.9+ (for Chroma vector database and if modifying RAG components)
- GPU: H100/A100 or better if using local LLMs

> Note: The project **does not** include LLM model weights. You must install `.gguf` or `.bin` models manually via Ollama or HuggingFace.

---

## 🔐 Authentication

CenAI includes UConn NetID login powered by PHPCAS (Central Authentication Service). There is also a guest mode with no auth (`no_auth/`) if needed for testing or demos.

---

## 📦 Installation

### 1. Clone the Repo

```bash
git clone https://github.com/tabouakar/cenai.git
cd cenai
```

### 2. Install Node Dependencies

```bash
npm install
```

### 3. Install PHP and Composer Dependencies

```bash
sudo apt install php composer
cd php
composer require jasig/phpcas
```

### 4. Python (For ChromaDB RAG)

```bash
cd ../retrieval_docs
python3 -m venv .venv
source .venv/bin/activate
pip install chromadb
```

---

## 🔍 Retrieval Pipeline (ChromaDB + JSON Ingestion)

The **retrieval** directory includes scripts and documents for building the ChromaDB vector store. The pipeline uses `.json` files containing HR policies or engineering docs and passes them into Chroma for indexing.

### Preprocessing & Upload

- `upload_to_chroma.py`: Ingests local JSON docs and populates Chroma with embeddings.
- `start-chroma.sh`: Boots the local Chroma server (`chroma run --path chroma_data`).
- `langchain_experiment.py`: Alternative Python-based RAG handler.

You can update or re-ingest new source files by modifying the relevant `.json` (e.g., `ethics.json`, `ctgov-site.json`) and re-running the upload script.

---

## 🗃 Chroma Vector Store Setup

CenAI uses a self-hosted **ChromaDB** instance via the Python client. It is run separately and accessed from Node via REST API.

### Chroma Server

```bash
cd retrieval
./start-chroma.sh
```

> This launches Chroma on port `:9000`. Make sure this path is reverse-proxied through `nginx`.

You can also test the status with:

```bash
curl http://localhost:9000/api/v1/heartbeat
```

---

## 🌐 nginx Reverse Proxy

nginx handles routing traffic to various services:

| Path Prefix | Destination             |
|-------------|-------------------------|
| `/index/`   | Node backend on `:10000`|
| `/ollama/`  | Ollama API on `:11434`  |
| `/chroma/`  | ChromaDB on `:9000`     |
| `/`         | PHP login on `:8000`    |

### nginx Config

The nginx reverse proxy config is located at:

```
/etc/nginx/sites-available/reverse-proxy
```

Make sure it is linked to `sites-enabled`:

```bash
sudo ln -s /etc/nginx/sites-available/reverse-proxy /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## 📜 Scripts Overview

The `scripts/` folder contains supporting utilities:

- `spin-up.sh`: TMUX-based launcher for Chroma, Node, and PHP services.
- `check_chroma.py`: Heartbeat test for Chroma availability.
- `upload_to_chroma.py`: Loads documents from `.json` files into Chroma.

These scripts can be chained in a deployment pipeline or cron job if needed.

---

## 🧪 Running the Application

### Option 1: Recommended Spin-Up Script (All Services)

```bash
sudo ./spin-up.sh
```

This script launches:

- ChromaDB on `:9000`
- Node.js backend on `:10000`
- PHP login server on `:8000`

### Option 2: Run Manually

```bash
# In retrieval_docs
./start-chroma.sh

# In cenai/
sudo npm start

# In cenai/php
sudo php -S localhost:8000
```

Ensure `nginx` is running with `/etc/nginx/sites-enabled/reverse-proxy` forwarding traffic to the right ports.

---

## 🌐 Environment Variables (`.env`)

Create a `.env` file in the `cenai/` root:

```
OPENAI_API_KEY=your-openai-api-key
ASSISTANT_ID=your-assistant-id
```

---

## 🧠 Dual Mode: Local vs API

In `server.js`, the backend switches between local Ollama and OpenAI’s API depending on which code blocks are uncommented.

- ✅ **Local**: Uses `Ollama.chat()` with stream support and embedded vector search via `chromadb`.
- ✅ **API**: Uses `OpenAI.beta.threads` and assistants (commented out for now).

> You can toggle between the two by switching the blocks in `/backend/server.js`.

---

## 🧼 .gitignore

```
.env
chat.logs/
node_modules/
vendor/
*.gguf
chroma_data/
```

---

## ✅ Status

- ✅ Working UConn login
- ✅ Deployed Node/PHP frontend
- ✅ Integrated RAG w/ Chroma
- ✅ Ollama + local Gemini/Gemma3 models
- ✅ Logs stored in SQLite
- 🧪 OpenAI assistant fallback supported (currently disabled)

---

## 📣 Maintainers

Built by Tony A., Aidan P., and team. Maintained under UConn CSE 4939W/94W — Spring 2025.

---

## 🧠 Future Plans

- Improve document chunking and ranking pipeline for longer context documents.
- Add UI for log browsing and file-based policy management.
- Expand to more internal UConn systems with chatbot wrappers.
