const path = require('path');
const WebSocket = require('ws');
const Baileys = require('./vendor/baileys-main/lib/index'); 

const wss = new WebSocket.Server({ port: 0 });

let sock;
let activeSocket = null;

// Helper to safely serialize BigInt and Buffers
const jsonReplacer = (key, value) => {
    // 1. Handle BigInt (Baileys uses this for IDs)
    if (typeof value === 'bigint') {
        return value.toString(); 
    }
    // 2. Handle Buffers (Convert to Base64 string to reduce size)
    if (value && value.type === 'Buffer' && Array.isArray(value.data)) {
        return { type: 'Buffer', data: Buffer.from(value.data).toString('base64') };
    }
    return value;
};

wss.on('connection', (ws) => {
    activeSocket = ws;
    console.log('Client connected');

    ws.on('message', async (message) => {
        const request = JSON.parse(message);
        
        if (request.cmd === 'INIT') {
            try {
                const { state, saveCreds } = await Baileys.useMultiFileAuthState('baileys_auth_info');
                const config = {
                    auth: state,
                    printQRInTerminal: true,
                    ...request.config
                };

                sock = Baileys.default(config);

                // Internal listener for auth persistence
                sock.ev.on('creds.update', saveCreds);

                // Internal listener for connection updates (to handle reconnects)
                sock.ev.on('connection.update', (update) => {
                    const { connection, lastDisconnect } = update;
                    if(connection === 'close') {
                        const shouldReconnect = (lastDisconnect.error)?.output?.statusCode !== Baileys.DisconnectReason.loggedOut;
                        // Reconnect logic can be added here if needed
                    }
                    // We DON'T force sendEvent here anymore to avoid duplicates
                    // if the user subscribes manually below.
                });

                ws.send(JSON.stringify({ 
                    type: 'RESPONSE', 
                    id: request.id, 
                    result: 'Initialized' 
                }));

            } catch (err) {
                sendError(request.id, err.message);
            }
        }

        else if (request.cmd === 'CALL') {
            if (!sock || typeof sock[request.method] !== 'function') {
                return sendError(request.id, `Method ${request.method} not found`);
            }
            try {
                const result = await sock[request.method](...request.args);
                // Use jsonReplacer for return values too
                ws.send(JSON.stringify({ 
                    type: 'RESPONSE', 
                    id: request.id, 
                    result: result 
                }, jsonReplacer));
            } catch (err) {
                sendError(request.id, err.message);
            }
        }

        else if (request.cmd === 'STATIC_CALL') {
            if (typeof Baileys[request.method] !== 'function') {
                return sendError(request.id, `Static method ${request.method} not found`);
            }
            try {
                const result = await Baileys[request.method](...request.args);
                ws.send(JSON.stringify({ 
                    type: 'RESPONSE', 
                    id: request.id, 
                    result: result 
                }, jsonReplacer));
            } catch (err) {
                sendError(request.id, err.message);
            }
        }

        else if (request.cmd === 'SUBSCRIBE') {
            const eventName = request.event;
            // Only register if we haven't already to avoid duplicates
            // Baileys 'ev' is an EventEmitter, so we just add a listener
            sock.ev.on(eventName, (data) => {
                sendEvent(eventName, data);
            });
        }
    });

    function sendError(id, message) {
        if (activeSocket) {
            activeSocket.send(JSON.stringify({ type: 'ERROR', id, error: message }));
        }
    }

    function sendEvent(name, data) {
        if (activeSocket) {
            // USE THE SAFE REPLACER HERE
            activeSocket.send(JSON.stringify({ type: 'EVENT', name, data }, jsonReplacer));
        }
    }
});

wss.on('listening', () => {
    console.log(`PORT:${wss.address().port}`);
});