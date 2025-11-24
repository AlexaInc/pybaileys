console.log("Node process started...");
const path = require('path');
const WebSocket = require('ws');
const P = require('pino');
const Baileys = require('./vendor/baileys-main/lib/index'); 

const wss = new WebSocket.Server({ host: '0.0.0.0', port: 0 });

let sock;
let activeSocket = null;
const subscriptions = new Set();

const jsonReplacer = (key, value) => {
    if (typeof value === 'bigint') return value.toString();
    if (value && value.type === 'Buffer' && Array.isArray(value.data)) {
        return { type: 'Buffer', data: Buffer.from(value.data).toString('base64') };
    }
    return value;
};

wss.on('connection', (ws) => {
    activeSocket = ws;
    console.log('Client connected');

    ws.on('message', async (message) => {
        try {
            const request = JSON.parse(message);
            
            if (request.cmd === 'INIT') {
                const authPath = request.auth_path || 'baileys_auth_info';
                console.log(`[Node] Using Auth Path: ${authPath}`);

                const { state, saveCreds } = await Baileys.useMultiFileAuthState(authPath);
                
                const logLevel = request.config.log_level || 'info';
                const logger = P({ level: logLevel });
                delete request.config.log_level;

                const config = {
                    auth: state,
                    printQRInTerminal: false,
                    logger: logger,
                    ...request.config
                };

                sock = Baileys.default(config);

                sock.ev.on('creds.update', saveCreds);
                sock.ev.on('connection.update', (u) => sendEvent('connection.update', u));

                for (const eventName of subscriptions) {
                    sock.ev.on(eventName, (d) => sendEvent(eventName, d));
                }

                ws.send(JSON.stringify({ type: 'RESPONSE', id: request.id, result: 'Initialized' }));
            }

            else if (request.cmd === 'CALL') {
                if (!sock) throw new Error("Socket not initialized");
                const result = await sock[request.method](...request.args);
                ws.send(JSON.stringify({ type: 'RESPONSE', id: request.id, result }, jsonReplacer));
            }

            else if (request.cmd === 'STATIC_CALL') {
                const result = await Baileys[request.method](...request.args);
                ws.send(JSON.stringify({ type: 'RESPONSE', id: request.id, result }, jsonReplacer));
            }

            else if (request.cmd === 'SUBSCRIBE') {
                const eventName = request.event;
                subscriptions.add(eventName);
                if (sock && sock.ev) {
                    sock.ev.on(eventName, (d) => sendEvent(eventName, d));
                }
            }

        } catch (err) {
            if (activeSocket) {
                const reqId = tryGetId(message);
                activeSocket.send(JSON.stringify({ type: 'ERROR', id: reqId, error: err.message }));
            }
        }
    });

    function tryGetId(msg) {
        try { return JSON.parse(msg).id; } catch { return null; }
    }

    function sendEvent(name, data) {
        if (activeSocket) {
            activeSocket.send(JSON.stringify({ type: 'EVENT', name, data }, jsonReplacer));
        }
    }
});

wss.on('listening', () => console.log(`PORT:${wss.address().port}`));