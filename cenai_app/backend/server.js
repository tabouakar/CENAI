const path = require('path');
const express = require('express');
const OpenAI = require('openai');
const sqlite3 = require('sqlite3');
const session = require('express-session');
const cookieParser = require('cookie-parser');
const { spawn } = require('child_process');
const { Ollama } = require('ollama');
const { ChromaClient } = require('chromadb');
const fs = require('node:fs');

console.log('Directory name:', __dirname);
console.log('Full .env path:', path.join(__dirname, '../.env'));
require('dotenv').config({ path: path.join(__dirname, '../.env') });
console.log('Environment variables loaded:', {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY ? 'Present' : 'Missing',
    ASSISTANT_ID: process.env.ASSISTANT_ID ? 'Present' : 'Missing'
});

const app = express();
app.use(express.json());

// Session management for logging
app.use(session({
    secret: 'random_string', // TODO: Replace with a secure secret
    resave: false,
    saveUninitialized: true
}));

app.use(cookieParser());
app.use((req, res, next) => {
    const authUser = req.cookies.auth_user;
    if (!authUser) return res.redirect('//cenai.cse.uconn.edu/');
    req.session.user = authUser;
    next();
});

// Serve static frontend
app.use(express.static(path.join(__dirname, '../frontend')));

// SQLite setup
const db = new sqlite3.Database('chat.logs');
db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS Logs (
        SessionID TEXT, 
        dt DATETIME DEFAULT CURRENT_TIMESTAMP, 
        UserQuery TEXT, 
        Response TEXT
    )`);
});

// Load system instructions
const raw_hr_instr = fs.readFileSync('/opt/team/cenai/backend/HR_SYS_INSTRUCTIONS', 'utf8');

// Ollama-based local request handler
async function ollama_request(model, collection_name, input, res) {
    const client = new ChromaClient({ path: "https://cenai.cse.uconn.edu/chroma/" });
    const collection = await client.getCollection({ name: collection_name });
    const results = await collection.query({ queryTexts: input, nResults: 1 });
    console.log(results);

    res.setHeader("Content-Type", "text/plain");
    res.setHeader("Transfer-Encoding", "chunked");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.flushHeaders();

    const urls = results.metadatas[0].map(d => d.source).join(" or ");
    const sys_instructions = raw_hr_instr.replaceAll("[specific URL]", urls);
    const context = results.documents.join("\n");
    const prompt = `${sys_instructions}\nUse this context: ${context}\nTo answer this prompt: ${input}`;
    
    const ollama = new Ollama({ host: 'https://cenai.cse.uconn.edu/ollama/' });
    const response = await ollama.chat({
        model: 'gemma3:27b',
        messages: [{ role: 'user', content: prompt }],
        stream: true
    });

    for await (const chunk of response) {
        console.log(chunk.message.content);
        res.write(chunk.message.content);
    }
    res.end();
}

// ChatGPT-based fallback handler
async function chatGPT_request(input, res) {
    try {
        if (!process.env.OPENAI_API_KEY || !process.env.ASSISTANT_ID) {
            res.status(400).json({
                error: "OpenAI API is not configured Add an API key and Assistant ID to .env to enable this feature."
            });
            return;
        }

        const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
        const thread = await openai.beta.threads.create();
        await openai.beta.threads.messages.create(thread.id, {
            role: "user",
            content: input
        });

        const run = await openai.beta.threads.runs.create(thread.id, {
            assistant_id: process.env.ASSISTANT_ID
        });

        let runStatus = await openai.beta.threads.runs.retrieve(thread.id, run.id);
        while (runStatus.status !== 'completed') {
            await new Promise(resolve => setTimeout(resolve, 1000));
            runStatus = await openai.beta.threads.runs.retrieve(thread.id, run.id);
        }

        const messages = await openai.beta.threads.messages.list(thread.id);
        const output = messages.data[0].content[0].text.value;
        res.write(output);
        res.end();

    } catch (err) {
        console.error("OpenAI error:", err.message);
        res.status(500).json({ error: "OpenAI GPT failed: " + err.message });
    }
}

// Main chat endpoint
app.post('/api/chat', async (req, res) => {
    try {
        const { message, model, implementation, type } = req.body;

        if (implementation === "ollama") {
            await ollama_request(model, type, message, res);
        } else if (implementation === "chatGPT") {
            await chatGPT_request(message, res);
        } else {
            res.status(400).json({ error: "Unknown implementation type." });
        }

    } catch (error) {
        console.error('Chat handler error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Logs endpoints
app.get('/api/logs', (req, res) => {
    db.all("SELECT * FROM Logs ORDER BY dt DESC", (err, rows) => {
        if (err) return res.status(500).json({ error: 'Failed to fetch logs' });
        res.json({ logs: rows });
    });
});

app.get('/api/logs/:sessionId', (req, res) => {
    const { sessionId } = req.params;
    db.all("SELECT * FROM Logs WHERE SessionID = ? ORDER BY dt DESC", [sessionId], (err, rows) => {
        if (err) return res.status(500).json({ error: 'Failed to fetch logs' });
        res.json({ logs: rows });
    });
});

app.delete('/api/deleteAllLogs', (req, res) => {
    db.run("DELETE FROM Logs", function(err) {
        if (err) return res.status(500).json({ error: 'Failed to delete logs' });
        res.status(200).json({ message: 'All logs deleted' });
    });
});

const PORT = 10000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

// Optional: Langchain experimentation endpoint
app.post('/api/rag-chat', async (req, res) => {
    try {
        const userInput = req.body.message;
        const pythonProcess = spawn('python', ['langchain_experiment.py']);

        let response = '', error = '';
        pythonProcess.stdout.on('data', data => response += data.toString());
        pythonProcess.stderr.on('data', data => error += data.toString());

        pythonProcess.on('close', code => {
            if (code !== 0) {
                res.status(500).json({ error });
            } else {
                res.json({ response });
            }
        });

        pythonProcess.stdin.write(userInput + '\n');
        pythonProcess.stdin.end();

    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Global error handlers
process.on('uncaughtException', err => {
    console.error('Uncaught Exception:', err);
});
process.on('unhandledRejection', reason => {
    console.error('Unhandled Rejection:', reason);
});
