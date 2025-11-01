#!/usr/bin/env python3
"""
Siri Voice Assistant Web Server
A Flask-based web interface for voice commands
"""

import os
import sys
from flask import Flask, request, jsonify, render_template_string

# Initialize Flask app
app = Flask(__name__)

# Check if siri.py backend is available
try:
    # Try to import the siri backend functions
    from siri import open_command, handle_system_commands
    BACKEND_AVAILABLE = True
    print("✅ Siri backend (siri.py) loaded successfully!")
except ImportError:
    print("⚠️  siri.py not found - running in demo mode")
    BACKEND_AVAILABLE = False
    
    # Define dummy functions for demo mode
    def open_command(command):
        print(f"Demo: Would execute open_command('{command}')")
        return True
    
    def handle_system_commands(command):
        if any(word in command.lower() for word in ["shutdown", "quit", "exit", "stop"]):
            return True
        return False

# HTML Template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 Siri Voice Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
            width: 100%;
        }
        
        .title {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #333;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .status {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 30px;
            font-weight: 600;
        }
        
        .status.connected {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.demo {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .voice-btn {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 3em;
            cursor: pointer;
            margin: 20px auto;
            display: block;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        .voice-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
        }
        
        .voice-btn:active {
            transform: translateY(-2px);
        }
        
        .voice-btn.listening {
            animation: pulse 1.5s infinite;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7); }
            70% { box-shadow: 0 0 0 20px rgba(255, 107, 107, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }
        }
        
        .input-container {
            margin: 30px 0;
        }
        
        .text-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1.1em;
            margin-bottom: 15px;
            outline: none;
            transition: border-color 0.3s ease;
        }
        
        .text-input:focus {
            border-color: #667eea;
        }
        
        .send-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .send-btn:hover {
            background: #5a67d8;
        }
        
        .response {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            text-align: left;
            font-size: 1.1em;
            line-height: 1.6;
            display: none;
        }
        
        .examples {
            margin-top: 30px;
            text-align: left;
        }
        
        .examples h3 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .examples ul {
            list-style: none;
            padding: 0;
        }
        
        .examples li {
            background: #f8f9fa;
            padding: 10px 15px;
            margin: 8px 0;
            border-radius: 8px;
            border-left: 3px solid #667eea;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .examples li:hover {
            background: #e9ecef;
        }
        
        .footer {
            margin-top: 30px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">🎤 Siri Assistant</h1>
        <p class="subtitle">Voice-controlled web interface</p>
        
        <div class="status {% if backend_available %}connected{% else %}demo{% endif %}">
            {% if backend_available %}
                ✅ Backend Connected - Full functionality available
            {% else %}
                🔧 Demo Mode - siri.py backend not connected
            {% endif %}
        </div>
        
        <button class="voice-btn" id="voiceBtn" title="Click and speak">🎤</button>
        
        <div class="input-container">
            <input type="text" class="text-input" id="textInput" placeholder="Or type your command here..." />
            <button class="send-btn" id="sendBtn">Send Command</button>
        </div>
        
        <div class="response" id="response"></div>
        
        <div class="examples">
            <h3>📝 Example Commands:</h3>
            <ul>
                <li onclick="executeCommand('Siri, open YouTube and find cooking videos')">🎬 "Siri, open YouTube and find cooking videos"</li>
                <li onclick="executeCommand('Siri, open Spotify')">🎵 "Siri, open Spotify"</li>
                <li onclick="executeCommand('Siri, open Chrome')">🌐 "Siri, open Chrome"</li>
                <li onclick="executeCommand('Siri, help')">🆘 "Siri, help"</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>🔊 Click the microphone to start voice recognition</p>
            <p>💬 Or type commands in the text box above</p>
        </div>
    </div>

    <script>
        const voiceBtn = document.getElementById('voiceBtn');
        const textInput = document.getElementById('textInput');
        const sendBtn = document.getElementById('sendBtn');
        const responseDiv = document.getElementById('response');
        
        let recognition = null;
        let isListening = false;
        
        // Initialize speech recognition if available
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = true;  // Keep listening
            recognition.interimResults = true;  // Show real-time results
            recognition.lang = 'en-US';
            recognition.maxAlternatives = 1;
            
            recognition.onstart = function() {
                isListening = true;
                voiceBtn.classList.add('listening');
                voiceBtn.innerHTML = '🔴';
                voiceBtn.title = 'Click to stop listening';
                showResponse('🎤 Always listening... Say your commands! Click microphone to stop.', 'info');
            };
            
            recognition.onresult = function(event) {
                let finalTranscript = '';
                let interimTranscript = '';
                
                // Process all results
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                // Show interim results in real-time
                if (interimTranscript) {
                    textInput.value = finalTranscript + interimTranscript;
                    showResponse('🎤 Listening: "' + (finalTranscript + interimTranscript) + '"', 'info');
                }
                
                // When we have a final result, process it but KEEP listening
                if (finalTranscript) {
                    const command = finalTranscript.trim();
                    textInput.value = command;
                    
                    if (command) {
                        executeCommand(command);
                        // Clear the text input after processing but keep listening
                        setTimeout(() => {
                            textInput.value = '';
                            if (isListening) {
                                showResponse('🎤 Ready for next command... (Click microphone to stop)', 'info');
                            }
                        }, 2000);
                    }
                }
            };
            
            recognition.onerror = function(event) {
                console.error('Speech recognition error:', event.error);
                showResponse('❌ Speech recognition error: ' + event.error, 'error');
                resetVoiceButton();
            };
            
            recognition.onend = function() {
                // If we're still supposed to be listening, restart automatically
                if (isListening) {
                    setTimeout(() => {
                        if (isListening) {
                            try {
                                recognition.start();
                            } catch (e) {
                                console.log('Recognition restart failed:', e);
                                resetVoiceButton();
                            }
                        }
                    }, 100);
                } else {
                    resetVoiceButton();
                }
            };
        } else {
            voiceBtn.style.display = 'none';
            showResponse('❌ Speech recognition not supported in this browser. Please use the text input.', 'error');
        }
        
        // Voice button click handler
        voiceBtn.addEventListener('click', function() {
            if (!recognition) {
                showResponse('❌ Speech recognition not available', 'error');
                return;
            }
            
            if (isListening) {
                // Stop listening permanently
                isListening = false; // Set this first to prevent auto-restart
                recognition.stop();
                showResponse('🛑 Stopping voice recognition...', 'info');
            } else {
                // Start permanent listening
                textInput.value = ''; // Clear previous text
                try {
                    recognition.start();
                } catch (e) {
                    showResponse('❌ Could not start voice recognition. Try again.', 'error');
                }
            }
        });
        
        // Send button click handler
        sendBtn.addEventListener('click', function() {
            const command = textInput.value.trim();
            if (command) {
                executeCommand(command);
            }
        });
        
        // Enter key handler for text input
        textInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const command = textInput.value.trim();
                if (command) {
                    executeCommand(command);
                }
            }
        });
        
        function resetVoiceButton() {
            isListening = false;
            voiceBtn.classList.remove('listening');
            voiceBtn.innerHTML = '🎤';
            voiceBtn.title = 'Click and speak';
            showResponse('🔇 Voice recognition stopped. Click microphone to start listening again.', 'info');
        }
        
        function executeCommand(command) {
            showResponse('🔄 Processing command...', 'info');
            
            fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showResponse(data.response, 'success');
                } else {
                    showResponse('❌ Error: ' + data.response, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showResponse('❌ Network error: Could not connect to server', 'error');
            });
        }
        
        function showResponse(message, type) {
            responseDiv.innerHTML = message;
            responseDiv.style.display = 'block';
            
            // Update styling based on response type
            responseDiv.className = 'response';
            if (type === 'error') {
                responseDiv.style.borderLeftColor = '#dc3545';
                responseDiv.style.backgroundColor = '#f8d7da';
            } else if (type === 'success') {
                responseDiv.style.borderLeftColor = '#28a745';
                responseDiv.style.backgroundColor = '#d4edda';
            } else {
                responseDiv.style.borderLeftColor = '#667eea';
                responseDiv.style.backgroundColor = '#f8f9fa';
            }
            
            // Auto-scroll to response
            responseDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Test server connection on page load
        fetch('/api/test')
            .then(response => response.json())
            .then(data => {
                console.log('Server connection test:', data.message);
            })
            .catch(error => {
                console.error('Server connection failed:', error);
                showResponse('⚠️ Warning: Could not connect to server', 'error');
            });
    </script>
</body>
</html>
"""

def process_voice_command(command):
    """Process voice command using your existing Siri backend"""
    try:
        command = command.lower().strip()
        print(f"🎤 Processing command: '{command}'")
        
        if not BACKEND_AVAILABLE:
            return simulate_command(command)
        
        # Check for system commands first
        if handle_system_commands(command):
            return "I would shut down the voice assistant, but I'm running in web mode!"
        
        # Check if it's an open/search command
        if any(keyword in command for keyword in ["open", "play", "search", "find", "watch", "listen", "launch", "start"]):
            # Remove "siri" from command if present
            clean_command = command.replace("siri", "").strip()
            
            # Process the command using your Siri backend
            open_command(clean_command)
            
            # Generate appropriate response
            if "youtube" in command and any(word in command for word in ["find", "search", "watch", "play"]):
                return "🎬 I've opened YouTube with your search. The videos should be loading now!"
            elif "spotify" in command:
                return "🎵 Opening Spotify for you. Enjoy your music!"
            elif any(app in command for app in ["chrome", "safari", "firefox"]):
                return "🌐 Opening your browser now."
            elif "help" in command:
                return "🆘 I can open apps and websites for you. Try: 'Siri, open YouTube and find cooking videos', 'Siri, open Spotify', or 'Siri, open Chrome'."
            else:
                return "✅ Command processed successfully! Check if the app/website opened."
        else:
            if "help" in command:
                return "🆘 I can open apps and websites for you. Try: 'Siri, open YouTube and find cooking videos', 'Siri, open Spotify', or 'Siri, open Chrome'."
            else:
                return "🤔 Please tell me what to open, or say 'help' for assistance."
                
    except Exception as e:
        print(f"❌ Error processing command: {e}")
        return f"❌ Sorry, I encountered an error: {str(e)}"

def simulate_command(command):
    """Simulate command processing when Siri backend is not available"""
    command = command.lower()
    
    if "youtube" in command:
        if any(word in command for word in ["find", "search", "watch", "cooking", "video"]):
            return "🎬 I would open YouTube and search for cooking videos! (Demo mode - siri.py not connected)"
        else:
            return "🎬 I would open YouTube for you! (Demo mode - siri.py not connected)"
    elif "spotify" in command:
        return "🎵 I would open Spotify and play your music! (Demo mode - siri.py not connected)"
    elif "chrome" in command or "browser" in command:
        return "🌐 I would open Chrome browser for you! (Demo mode - siri.py not connected)"
    elif "help" in command:
        return "🆘 I can help you open apps and websites. Try: 'Siri, open YouTube and find cooking videos' (Demo mode - your siri.py backend is not connected)"
    else:
        return f"🤖 I heard: '{command}'. I would process this command if siri.py was connected! (Demo mode)"

@app.route('/')
def home():
    """Serve the main web interface"""
    return render_template_string(HTML_TEMPLATE, backend_available=BACKEND_AVAILABLE)

@app.route('/api/command', methods=['POST'])
def handle_command():
    """Handle voice commands from the web interface"""
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({
                'success': False,
                'response': 'No command received'
            })
        
        print(f"📨 Received command from web: {command}")
        
        # Process the command
        response = process_voice_command(command)
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        print(f"❌ Error in handle_command: {e}")
        return jsonify({
            'success': False,
            'response': f'Server error: {str(e)}'
        })

@app.route('/api/test')
def test_connection():
    """Test endpoint to check server connectivity"""
    backend_status = "Connected to siri.py" if BACKEND_AVAILABLE else "Demo Mode (siri.py not found)"
    return jsonify({
        'success': True,
        'message': f'✅ Siri web server is running! Backend status: {backend_status}'
    })

def main():
    """Main function to start the Flask server"""
    print("🚀 Starting Siri Voice Assistant Web Server...")
    print("🌐 Server will run on: http://127.0.0.1:8080")
    print("📱 Open http://127.0.0.1:8080 in your browser to use the web interface")
    print("🎤 Make sure to allow microphone access when prompted")
    
    if BACKEND_AVAILABLE:
        print("✅ Siri voice assistant backend (siri.py) is connected and ready!")
    else:
        print("⚠️  Running in demo mode - siri.py functions not available")
        print("   Make sure siri.py is in the same directory as this file")
        
    print("\n📝 Available commands:")
    print("   - 'Siri, open YouTube and find cooking videos'")
    print("   - 'Siri, open Spotify and play jazz music'")
    print("   - 'Siri, open Chrome'")
    print("   - 'Siri, help'")
    print("\n🔧 Press Ctrl+C to stop the server\n")
    
    # Run Flask app
    try:
        app.run(host='127.0.0.1', port=8080, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Shutting down Siri web server...")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()