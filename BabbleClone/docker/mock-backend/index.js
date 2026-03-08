const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

const messages = [];

app.get('/messages', (req, res) => {
  res.json(messages.sort((a,b)=>a.ts - b.ts));
});

const server = http.createServer(app);
const wss = new WebSocket.Server({ noServer: true });

server.on('upgrade', (req, socket, head) => {
  if (req.url === '/ws') {
    wss.handleUpgrade(req, socket, head, ws => {
      wss.emit('connection', ws, req);
    });
  } else {
    socket.destroy();
  }
});

let idCounter = 1;

function broadcast(msgObj) {
  const data = JSON.stringify(msgObj);
  wss.clients.forEach(c => {
    if (c.readyState === WebSocket.OPEN) c.send(data);
  });
}

wss.on('connection', ws => {
  // send welcome info
  ws.send(JSON.stringify({ info: 'welcome' }));

  ws.on('message', raw => {
    try {
      const payload = JSON.parse(raw.toString());
      if (!payload || typeof payload.text !== 'string' || payload.text.trim() === '') return;
      const msg = {
        id: String(idCounter++),
        author: payload.author || 'anon',
        text: payload.text.slice(0, 1000),
        ts: Date.now()
      };
      messages.push(msg);
      broadcast(msg);
    } catch (err) {
      // ignore malformed
    }
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log('Mock backend listening on', PORT);
});
