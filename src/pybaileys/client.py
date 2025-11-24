import subprocess
import os
import json
import time
import threading
import uuid
import asyncio
import websocket

class BaileysError(Exception):
    pass

class BaileysClient:
    def __init__(self):
        self.process = None
        self.ws = None
        self.connected_event = threading.Event()
        self.responses = {} 
        self.event_listeners = {} 
        self._response_waiters = {}
        # Access static utils via client.utils.MethodName()
        self.utils = self._UtilsProxy(self)

    class _UtilsProxy:
        def __init__(self, client):
            self.client = client
        def __getattr__(self, name):
            def method_proxy(*args):
                return self.client._call_rpc('STATIC_CALL', {'method': name, 'args': args})
            return method_proxy

    def start(self):
        """Starts the Node.js engine."""
        base_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_path, 'engine', 'bridge.js')
        
        if not os.path.exists(os.path.join(base_path, 'engine', 'node_modules')):
            raise RuntimeError("Please run 'npm install' in the engine directory first.")

        self.process = subprocess.Popen(
            ['node', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.join(base_path, 'engine')
        )

        port = None
        while True:
            line = self.process.stdout.readline()
            if "PORT:" in line:
                port = line.strip().split(":")[1]
                break
            if line == '' and self.process.poll() is not None:
                err = self.process.stderr.read()
                raise RuntimeError(f"Engine failed to start:\n{err}")

        self.ws = websocket.WebSocketApp(
            f"ws://localhost:{port}",
            on_message=self._on_ws_message,
            on_open=self._on_ws_open,
            on_error=self._on_ws_error
        )
        
        t = threading.Thread(target=self.ws.run_forever)
        t.daemon = True
        t.start()
        
        self.connected_event.wait(timeout=5)
        self._send_init()

    def _on_ws_open(self, ws):
        self.connected_event.set()

    def _on_ws_error(self, ws, error):
        print(f"WebSocket Error: {error}")

    def _on_ws_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'RESPONSE':
                req_id = data['id']
                self.responses[req_id] = data['result']
                if req_id in self._response_waiters:
                    self._response_waiters[req_id].set()

            elif msg_type == 'ERROR':
                req_id = data.get('id')
                err_msg = data.get('error', 'Unknown Error')
                if req_id:
                    self.responses[req_id] = BaileysError(err_msg)
                    if req_id in self._response_waiters:
                        self._response_waiters[req_id].set()
                else:
                    print(f"Async Error from Engine: {err_msg}")

            elif msg_type == 'EVENT':
                name = data['name']
                payload = data['data']
                if name in self.event_listeners:
                    for callback in self.event_listeners[name]:
                        threading.Thread(target=callback, args=(payload,)).start()

        except Exception as e:
            print(f"Error parsing message: {e}")

    def _send_init(self):
        self._call_rpc('INIT', {}, wait=True)

    def _call_rpc(self, cmd, payload, wait=True):
        req_id = str(uuid.uuid4())
        payload['id'] = req_id
        payload['cmd'] = cmd
        
        if wait:
            waiter = threading.Event()
            self._response_waiters[req_id] = waiter
        
        self.ws.send(json.dumps(payload))
        
        if wait:
            sent = waiter.wait(timeout=30)
            del self._response_waiters[req_id]
            if not sent:
                raise TimeoutError("Node.js bridge timed out")
            
            response = self.responses.pop(req_id)
            if isinstance(response, Exception):
                raise response
            return response

    def __getattr__(self, name):
        def method_proxy(*args):
            return self._call_rpc('CALL', {'method': name, 'args': args})
        return method_proxy

    def on(self, event_name):
        def decorator(func):
            if event_name not in self.event_listeners:
                self.event_listeners[event_name] = []
                self._call_rpc('SUBSCRIBE', {'event': event_name}, wait=False)
            self.event_listeners[event_name].append(func)
            return func
        return decorator

    def stop(self):
        if self.process:
            self.process.terminate()