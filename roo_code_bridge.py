#!/usr/bin/env python3
"""
Roo Code MCP Bridge Server
--------------------------
A simple HTTP server that acts as an MCP bridge for Roo Code,
enabling communication with other agents using the ACP protocol.
"""

import http.server
import socketserver
import json
import os
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("roo_code_bridge.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RooCodeBridge")

# Configuration
PORT = 8000
COMMS_FILE = ".agntcy-comms.json"
MISSION_FILE = ".agntcy-mission"

class MCPBridgeHandler(http.server.BaseHTTPRequestHandler):
    """Handler for MCP Bridge HTTP requests."""
    
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - used for status checks and message polling."""
        if self.path == "/status":
            self._set_headers()
            status = {
                "status": "online",
                "agent": "roo-code",
                "type": "code_assistant",
                "capabilities": ["code_analysis", "refactoring"],
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(status).encode())
        elif self.path == "/messages":
            self._set_headers()
            if os.path.exists(COMMS_FILE):
                with open(COMMS_FILE, 'r') as f:
                    messages = json.load(f)
                self.wfile.write(json.dumps(messages).encode())
            else:
                self.wfile.write(json.dumps({"messages": []}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests - used for sending messages."""
        if self.path == "/send":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            message = json.loads(post_data.decode())
            
            # Validate message format
            if self._validate_message(message):
                self._store_message(message)
                self._set_headers()
                response = {"status": "message_received", "message_id": message.get("message_id")}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid message format"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def _validate_message(self, message):
        """Validate that the message follows ACP protocol."""
        required_fields = ["protocol", "message_id", "timestamp", "sender", "recipient", "message_type", "content"]
        return all(field in message for field in required_fields) and message.get("protocol") == "acp-1.0"
    
    def _store_message(self, message):
        """Store the message in the communications file."""
        messages = {"messages": []}
        
        if os.path.exists(COMMS_FILE):
            with open(COMMS_FILE, 'r') as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Error decoding {COMMS_FILE}, creating new file")
        
        messages["messages"].append(message)
        
        with open(COMMS_FILE, 'w') as f:
            json.dump(messages, f, indent=2)
        
        logger.info(f"Stored message {message.get('message_id')} from {message.get('sender', {}).get('id')}")
        
        # If this is a message for Roo Code, process it
        if message.get("recipient", {}).get("id") == "roo-code":
            self._process_message(message)
    
    def _process_message(self, message):
        """Process incoming messages for Roo Code."""
        logger.info(f"Processing message: {message.get('message_id')}")
        
        # Here we would implement logic to handle different message types
        # For now, we'll just log the message
        
        # If it's a conversation message, we could append it to the mission file
        if message.get("message_type") == "conversation":
            self._append_to_mission_file(message)
    
    def _append_to_mission_file(self, message):
        """Append a conversation message to the mission file."""
        if not os.path.exists(MISSION_FILE):
            logger.error(f"Mission file {MISSION_FILE} not found")
            return
        
        sender = message.get("sender", {}).get("id", "unknown")
        timestamp = datetime.fromisoformat(message.get("timestamp").replace("Z", "+00:00"))
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M PDT")
        
        content = message.get("content", {})
        role = content.get("role", "")
        text = content.get("text", "")
        
        entry = f"\n### {formatted_time} - {sender.capitalize()}\n"
        entry += f"**Message Type:** {message.get('message_type')}\n"
        if role:
            entry += f"**Role:** {role}\n"
        entry += f"**Content:** {text}\n"
        
        with open(MISSION_FILE, 'a') as f:
            f.write(entry)
        
        logger.info(f"Appended message to {MISSION_FILE}")

def run_server():
    """Run the MCP Bridge server."""
    handler = MCPBridgeHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        logger.info(f"Serving at port {PORT}")
        logger.info(f"Roo Code MCP Bridge is online")
        
        # Announce ourselves by creating an initial status message
        initial_message = {
            "protocol": "acp-1.0",
            "message_id": f"roo-status-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "sender": {
                "id": "roo-code",
                "type": "code_assistant"
            },
            "recipient": {
                "id": "broadcast",
                "type": "all"
            },
            "message_type": "status",
            "content": {
                "status": "online",
                "capabilities": ["code_analysis", "refactoring"],
                "listening_on": f"http://localhost:{PORT}"
            },
            "metadata": {
                "mission_file": MISSION_FILE,
                "workspace": os.getcwd()
            }
        }
        
        # Store the initial status message
        handler._store_message(handler, initial_message)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down server")
            httpd.server_close()

if __name__ == "__main__":
    run_server()