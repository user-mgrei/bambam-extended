#!/usr/bin/env python3
"""
BamBam Remote Parent Control - Flask Web App

Provides a simple web interface for parents to monitor and control
BamBam remotely. Designed for use with Tailscale or local network.

Usage:
    python3 bambam_remote.py [--port 8080] [--host 0.0.0.0]

The user should configure Tailscale to expose this on their network.
"""

import argparse
import sys
import threading
from datetime import datetime

try:
    from flask import Flask, jsonify, render_template_string, request
    _FLASK_AVAILABLE = True
except ImportError:
    _FLASK_AVAILABLE = False
    Flask = None

# Shared state between BamBam game and web server
_game_state = {
    'running': False,
    'muted': False,
    'current_extension': None,
    'current_theme': None,
    'session_start': None,
    'keypress_count': 0,
    'last_keypress': None,
    'profile_name': None,
}

_game_control = {
    'mute_requested': False,
    'unmute_requested': False,
    'pause_requested': False,
    'resume_requested': False,
    'stop_requested': False,
    'change_extension': None,
    'change_theme': None,
}

_state_lock = threading.Lock()


def update_game_state(**kwargs):
    """Update game state (called from BamBam game)."""
    with _state_lock:
        _game_state.update(kwargs)


def get_game_state() -> dict:
    """Get current game state."""
    with _state_lock:
        return dict(_game_state)


def get_pending_control() -> dict:
    """Get and clear pending control commands."""
    with _state_lock:
        control = dict(_game_control)
        # Clear after reading
        for key in _game_control:
            if isinstance(_game_control[key], bool):
                _game_control[key] = False
            else:
                _game_control[key] = None
        return control


def request_control(**kwargs):
    """Request a control action."""
    with _state_lock:
        _game_control.update(kwargs)


# HTML template for the control interface
CONTROL_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BamBam Remote Control</title>
    <style>
        * {
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        body {
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 20px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        h2 {
            margin: 0 0 16px 0;
            color: #333;
            font-size: 1.1em;
        }
        .status {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .status:last-child {
            border-bottom: none;
        }
        .status-label {
            color: #666;
        }
        .status-value {
            font-weight: 600;
            color: #333;
        }
        .status-value.active {
            color: #22c55e;
        }
        .status-value.inactive {
            color: #ef4444;
        }
        .btn-row {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        .btn {
            flex: 1;
            padding: 16px;
            border: none;
            border-radius: 12px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s, box-shadow 0.1s;
        }
        .btn:active {
            transform: scale(0.98);
        }
        .btn-mute {
            background: #fbbf24;
            color: #92400e;
        }
        .btn-pause {
            background: #60a5fa;
            color: #1e3a8a;
        }
        .btn-stop {
            background: #ef4444;
            color: white;
        }
        .btn-calm {
            background: #a78bfa;
            color: #4c1d95;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .timer {
            font-size: 2em;
            text-align: center;
            color: #333;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }
        .mode-badge {
            display: inline-block;
            padding: 4px 12px;
            background: #e0e7ff;
            color: #3730a3;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .refresh-note {
            text-align: center;
            color: rgba(255,255,255,0.7);
            font-size: 0.85em;
            margin-top: 16px;
        }
        @media (max-width: 420px) {
            body { padding: 12px; }
            .btn { padding: 14px; font-size: 0.95em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 BamBam Remote</h1>

        <div class="card">
            <h2>⏱️ Session</h2>
            <div class="timer" id="timer">--:--</div>
            <div class="status">
                <span class="status-label">Status</span>
                <span class="status-value" id="status">Loading...</span>
            </div>
            <div class="status">
                <span class="status-label">Keypresses</span>
                <span class="status-value" id="keypresses">0</span>
            </div>
        </div>

        <div class="card">
            <h2>🎛️ Controls</h2>
            <div class="btn-row">
                <button class="btn btn-mute" id="btn-mute" onclick="toggleMute()">
                    🔇 Mute
                </button>
                <button class="btn btn-pause" id="btn-pause" onclick="togglePause()">
                    ⏸️ Pause
                </button>
            </div>
            <div class="btn-row">
                <button class="btn btn-calm" onclick="setCalm()">
                    🌙 Calm Mode
                </button>
            </div>
            <div class="btn-row">
                <button class="btn btn-stop" onclick="stopGame()">
                    🛑 End Session
                </button>
            </div>
        </div>

        <div class="card">
            <h2>📊 Current Mode</h2>
            <div class="status">
                <span class="status-label">Extension</span>
                <span class="status-value" id="extension">-</span>
            </div>
            <div class="status">
                <span class="status-label">Theme</span>
                <span class="status-value" id="theme">-</span>
            </div>
            <div class="status">
                <span class="status-label">Profile</span>
                <span class="status-value" id="profile">-</span>
            </div>
        </div>

        <p class="refresh-note">Auto-refreshes every 2 seconds</p>
    </div>

    <script>
        let isMuted = false;
        let isPaused = false;

        async function fetchStatus() {
            try {
                const resp = await fetch('/api/status');
                const data = await resp.json();

                // Update timer
                if (data.session_start) {
                    const start = new Date(data.session_start);
                    const now = new Date();
                    const diff = Math.floor((now - start) / 1000);
                    const mins = Math.floor(diff / 60).toString().padStart(2, '0');
                    const secs = (diff % 60).toString().padStart(2, '0');
                    document.getElementById('timer').textContent = `${mins}:${secs}`;
                } else {
                    document.getElementById('timer').textContent = '--:--';
                }

                // Update status
                const statusEl = document.getElementById('status');
                if (data.running) {
                    statusEl.textContent = 'Playing';
                    statusEl.className = 'status-value active';
                } else {
                    statusEl.textContent = 'Not Running';
                    statusEl.className = 'status-value inactive';
                }

                // Update other fields
                document.getElementById('keypresses').textContent = data.keypress_count || 0;
                document.getElementById('extension').textContent = data.current_extension || '-';
                document.getElementById('theme').textContent = data.current_theme || 'default';
                document.getElementById('profile').textContent = data.profile_name || 'default';

                // Update mute button
                isMuted = data.muted;
                document.getElementById('btn-mute').textContent = isMuted ? '🔊 Unmute' : '🔇 Mute';

            } catch (e) {
                console.error('Status fetch failed:', e);
            }
        }

        async function sendCommand(cmd) {
            try {
                await fetch('/api/control', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(cmd)
                });
            } catch (e) {
                console.error('Command failed:', e);
            }
        }

        function toggleMute() {
            if (isMuted) {
                sendCommand({unmute: true});
            } else {
                sendCommand({mute: true});
            }
            isMuted = !isMuted;
            document.getElementById('btn-mute').textContent = isMuted ? '🔊 Unmute' : '🔇 Mute';
        }

        function togglePause() {
            if (isPaused) {
                sendCommand({resume: true});
            } else {
                sendCommand({pause: true});
            }
            isPaused = !isPaused;
            document.getElementById('btn-pause').textContent = isPaused ? '▶️ Resume' : '⏸️ Pause';
        }

        function setCalm() {
            sendCommand({change_theme: 'dark', mute: false});
            alert('Calm mode activated!');
        }

        function stopGame() {
            if (confirm('End the current session?')) {
                sendCommand({stop: true});
            }
        }

        // Initial fetch and auto-refresh
        fetchStatus();
        setInterval(fetchStatus, 2000);
    </script>
</body>
</html>
"""


def create_app() -> 'Flask':
    """Create and configure the Flask application."""
    if not _FLASK_AVAILABLE:
        raise ImportError("Flask is required. Install with: pip install flask")

    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template_string(CONTROL_PAGE_HTML)

    @app.route('/api/status')
    def api_status():
        state = get_game_state()
        return jsonify(state)

    @app.route('/api/control', methods=['POST'])
    def api_control():
        data = request.get_json() or {}

        if data.get('mute'):
            request_control(mute_requested=True)
        if data.get('unmute'):
            request_control(unmute_requested=True)
        if data.get('pause'):
            request_control(pause_requested=True)
        if data.get('resume'):
            request_control(resume_requested=True)
        if data.get('stop'):
            request_control(stop_requested=True)
        if data.get('change_extension'):
            request_control(change_extension=data['change_extension'])
        if data.get('change_theme'):
            request_control(change_theme=data['change_theme'])

        return jsonify({'status': 'ok'})

    @app.route('/api/extensions')
    def api_extensions():
        # This would be populated from the game
        return jsonify({'extensions': []})

    @app.route('/api/themes')
    def api_themes():
        return jsonify({'themes': ['default', 'dark', 'farm', 'ocean', 'space', 'music', 'nature']})

    return app


class RemoteControlServer:
    """Manages the remote control web server."""

    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self._app = None
        self._thread = None
        self._running = False

    def start(self):
        """Start the web server in a background thread."""
        if not _FLASK_AVAILABLE:
            print("Warning: Flask not available, remote control disabled")
            print("Install with: pip install flask")
            return False

        self._app = create_app()
        self._running = True

        def run_server():
            # Suppress Flask's default logging for cleaner output
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)

            self._app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                threaded=True
            )

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._thread.start()

        print(f"Remote control server started at http://{self.host}:{self.port}")
        return True

    def stop(self):
        """Stop the web server."""
        self._running = False
        # Flask doesn't have a clean shutdown, but since it's a daemon thread,
        # it will stop when the main program exits

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running and self._thread and self._thread.is_alive()


def main():
    """Run the remote control server standalone (for testing)."""
    if not _FLASK_AVAILABLE:
        print("Error: Flask is required")
        print("Install with: pip install flask")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='BamBam Remote Control Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    # Simulate some game state for testing
    update_game_state(
        running=True,
        muted=False,
        current_extension='alphanumeric-en_US',
        current_theme='default',
        session_start=datetime.now().isoformat(),
        keypress_count=42,
        profile_name='Test Child',
    )

    app = create_app()
    print(f"Starting BamBam Remote Control at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    try:
        app.run(host=args.host, port=args.port, debug=True)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == '__main__':
    main()
