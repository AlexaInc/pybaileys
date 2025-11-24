import subprocess
import os
import json
import time
import threading
import uuid
import websocket
import sys
from . import bootstrap

sys.stdout.reconfigure(line_buffering=True)

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
        self.utils = self._UtilsProxy(self)
        self.port = None
        self.auth_path = None 
        self.socket_config = {}
        self.node_executable = None

    class _UtilsProxy:
        def __init__(self, client):
            self.client = client
        def __getattr__(self, name):
            def method_proxy(*args):
                return self.client._call_rpc('STATIC_CALL', {'method': name, 'args': args})
            return method_proxy

    def _reader_thread(self, pipe, prefix):
        for line in iter(pipe.readline, ''):
            clean_line = line.strip()
            if clean_line:
                print(f"[{prefix}] {clean_line}")
                if prefix == "NODE" and "PORT:" in clean_line:
                    self.port = clean_line.split(":")[1]
        pipe.close()

    def start(self, auth_path="baileys_auth_info", **kwargs):
        self.auth_path = os.path.abspath(auth_path)
        self.socket_config = kwargs
        
        # 1. Get Node Executable (Modules are already installed!)
        self.node_executable = bootstrap.setup()
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_path, 'engine', 'bridge.js')
        cwd_path = os.path.join(base_path, 'engine')
        
        print(f"[*] Starting Engine...")
        
        if not os.path.exists(script_path):
            raise RuntimeError(f"Bridge file missing: {script_path}")

        # 2. Check if node_modules exists (sanity check)
        if not os.path.exists(os.path.join(cwd_path, 'node_modules')):
            raise RuntimeError("Corrupt installation: node_modules missing in package.")

        self.process = subprocess.Popen(
            [self.node_executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd_path,
            bufsize=1,
            universal_newlines=True
        )

        t_out = threading.Thread(target=self._reader_thread, args=(self.process.stdout, "NODE"))
        t_out.daemon = True
        t_out.start()

        t_err = threading.Thread(target=self._reader_thread, args=(self.process.stderr, "NODE_ERR"))
        t_err.daemon = True
        t_err.start()

        print("[*] Waiting for Port...")
        
        start_time = time.time()
        while self.port is None:
            if time.time() - start_time > 30:
                raise TimeoutError("Timed out waiting for Node.js engine.")
            if self.process.poll() is not None:
                raise RuntimeError("Node process died unexpectedly.")
            time.sleep(0.1)

        print(f"[*] Connecting to 127.0.0.1:{self.port}")

        self.ws = websocket.WebSocketApp(
            f"ws://127.0.0.1:{self.port}",
            on_message=self._on_ws_message,
            on_open=self._on_ws_open,
            on_error=self._on_ws_error
        )
        
        t = threading.Thread(target=self.ws.run_forever)
        t.daemon = True
        t.start()
        
        if not self.connected_event.wait(timeout=10):
            raise TimeoutError("WS Connection timed out")
            
        self._send_init()

    def _on_ws_open(self, ws):
        self.connected_event.set()

    def _on_ws_error(self, ws, error):
        print(f"[WS Error]: {error}")

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
                    print(f"[Engine Error]: {err_msg}")

            elif msg_type == 'EVENT':
                name = data['name']
                payload = data['data']
                if name in self.event_listeners:
                    for callback in self.event_listeners[name]:
                        threading.Thread(target=callback, args=(payload,)).start()

        except Exception as e:
            print(f"Error parsing message: {e}")

    def _send_init(self):
        payload = {'auth_path': self.auth_path, 'config': self.socket_config}
        self._call_rpc('INIT', payload, wait=False)

    def _call_rpc(self, cmd, payload, wait=True):
        req_id = str(uuid.uuid4())
        payload['id'] = req_id
        payload['cmd'] = cmd
        
        if wait:
            waiter = threading.Event()
            self._response_waiters[req_id] = waiter
        
        try:
            self.ws.send(json.dumps(payload))
        except Exception as e:
            if wait: del self._response_waiters[req_id]
            raise e
        
        if wait:
            sent = waiter.wait(timeout=30)
            del self._response_waiters[req_id]
            if not sent:
                raise TimeoutError("Bridge request timed out")
            
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