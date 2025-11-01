import os
import json
import webbrowser
import speech_recognition as sr
import pyttsx3
from vosk import Model, KaldiRecognizer, SetLogLevel
from fuzzywuzzy import process
import subprocess
import platform
import time
import urllib.parse

WAKE_WORD = "siri" 

# Listening modes
CONTINUOUS_MODE = False  # Set to True for always listening, False for push-to-talk
SILENCE_TIMEOUT = 2.0    # Seconds of silence before stopping listening

# Platform-specific app commands
def get_app_map():
    system = platform.system()
    if system == "Darwin":  # macOS
        return {
            "chrome": "Google Chrome",
            "spotify": "Spotify", 
            "safari": "Safari",
            "firefox": "Firefox",
            "code": "Visual Studio Code",
            "terminal": "Terminal"
        }
    elif system == "Windows":
        return {
            "chrome": "chrome.exe",
            "spotify": "Spotify.exe",
            "firefox": "firefox.exe", 
            "code": "Code.exe",
            "notepad": "notepad.exe"
        }
    else:  # Linux
        return {
            "chrome": "google-chrome",
            "firefox": "firefox",
            "spotify": "spotify",
            "code": "code",
            "terminal": "gnome-terminal"
        }

APP_MAP = get_app_map()

# Enhanced web defaults with search capabilities
WEB_DEFAULTS = {
    "youtube": "https://youtube.com",
    "gmail": "https://mail.google.com", 
    "google": "https://google.com",
    "facebook": "https://facebook.com",
    "twitter": "https://twitter.com",
    "github": "https://github.com",
    "stackoverflow": "https://stackoverflow.com",
    # Add your custom websites here
    "netflix": "https://netflix.com",
    "amazon": "https://amazon.com",
    "reddit": "https://reddit.com",
    "instagram": "https://instagram.com",
    "linkedin": "https://linkedin.com",
    "whatsapp": "https://web.whatsapp.com",
    "discord": "https://discord.com",
    "notion": "https://notion.so",
    # Example of custom website - replace with your daily sites
    "chatgpt": "https://chat.openai.com",
    "claude": "https://claude.ai",
    "spotify": "https://open.spotify.com"
}

# Search patterns for different platforms
SEARCH_PATTERNS = {
    "youtube": "https://www.youtube.com/results?search_query=",
    "spotify": "https://open.spotify.com/search/",
    "google": "https://www.google.com/search?q=",
    "amazon": "https://www.amazon.com/s?k=",
    "netflix": "https://www.netflix.com/search?q="
}

VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
CUSTOM_VOCAB = list(APP_MAP.keys()) + ["youtube", "gmail", "google", "facebook", "twitter", "netflix", "amazon", "reddit", "spotify"] + ["open", "siri", "launch", "start", "shutdown", "stop", "help", "play", "search", "find", "watch", "listen"]

engine = pyttsx3.init()
try:
    # Get available voices
    voices = engine.getProperty('voices')
    if voices:
        # Try to set a good voice (prefer female voice for Siri)
        for voice in voices:
            if 'female' in voice.name.lower() or 'samantha' in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        else:
            # If no female voice, use the first available
            engine.setProperty('voice', voices[0].id)
    
    # Set speech properties
    engine.setProperty('rate', 180)  # Slightly faster
    engine.setProperty('volume', 0.9)  # Louder
    
    print(f"[INFO] TTS engine initialized successfully")
    
except Exception as e:
    print(f"[WARN] TTS setup issue: {e}")
    engine.setProperty('rate', 175)
    engine.setProperty('volume', 1.0)

SetLogLevel(-1)

# Load Vosk model with check
if os.path.exists(VOSK_MODEL_PATH) and os.path.isdir(VOSK_MODEL_PATH):
    print(f"[DEBUG] Loading Vosk model from: {VOSK_MODEL_PATH}")
    vosk_model = Model(VOSK_MODEL_PATH)
else:
    print(f"[ERROR] Vosk model not found at: {VOSK_MODEL_PATH}")
    vosk_model = None

recognizer = sr.Recognizer()
# Improved settings to avoid false triggers
recognizer.energy_threshold = 4500  # Higher threshold to ignore background noise
recognizer.dynamic_energy_threshold = True  # Adjust to environment
recognizer.pause_threshold = 1.0   # Longer pause before considering speech ended
recognizer.phrase_threshold = 0.3   # Minimum audio length to consider as speech
recognizer.non_speaking_duration = 0.8  # Time of non-speaking before stopping

try:
    # Find the correct microphone (avoid speakers)
    available_mics = sr.Microphone.list_microphone_names()
    print(f"[INFO] Available microphones: {len(available_mics)}")
    
    mic_index = None
    for i, mic_name in enumerate(available_mics):
        print(f"  {i}: {mic_name}")
        # Select first device that's clearly a microphone
        if mic_index is None and ("microphone" in mic_name.lower() or "mic" in mic_name.lower()):
            mic_index = i
            print(f"[INFO] Selected microphone: {mic_name}")
    
    # Use the found microphone or default
    if mic_index is not None:
        mic = sr.Microphone(device_index=mic_index, sample_rate=16000, chunk_size=1024)
    else:
        mic = sr.Microphone(sample_rate=16000, chunk_size=1024)
    
    # Test microphone
    with mic as source:
        print("[INFO] Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"[INFO] Energy threshold set to: {recognizer.energy_threshold}")
        
except OSError as e:
    print(f"[ERROR] Microphone setup failed: {e}")
    print("[WARN] Using system default microphone")
    mic = sr.Microphone(sample_rate=16000, chunk_size=1024)

def speak(text):
    print(f"Siri: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[ERROR] Speech failed: {e}")
        # Fallback - just print if speech fails
        print(f"[FALLBACK] Siri would say: {text}")

def fuzzy_match(query, choices):
    if not query.strip():
        return None
    match, score = process.extractOne(query, choices)
    print(f"[DEBUG] Fuzzy match: '{query}' -> '{match}' (score: {score})")
    return match if score >= 60 else None  # Lowered threshold

def open_app(app_name):
    """Open application based on platform"""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", "-a", app_name], check=True)
        elif system == "Windows":
            subprocess.run(["start", "", app_name], shell=True, check=True)
        else:  # Linux
            subprocess.run([app_name], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to open app {app_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"[ERROR] App {app_name} not found")
        return False

def open_website(url):
    """Open website in default browser"""
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to open website {url}: {e}")
        return False

def parse_search_command(cmd):
    """Parse command to extract platform and search query"""
    cmd = cmd.lower().strip()
    print(f"[DEBUG] Parsing search command: '{cmd}'")
    
    # Remove common words but keep original for reference
    clean_cmd = cmd.replace("open", "").replace("launch", "").replace("start", "").replace(WAKE_WORD, "").replace("please", "").strip()
    
    # Check if it's a search command (contains "play", "search", "find", etc.)
    search_keywords = ["play", "search", "find", "look for", "show me", "watch", "listen to", "listen", "watch"]
    has_search = any(keyword in cmd for keyword in search_keywords)
    
    print(f"[DEBUG] Has search keywords: {has_search}")
    
    if not has_search:
        return None, None, cmd  # No search, just regular open command
    
    # Find the platform - check in original command
    platform = None
    for platform_name in SEARCH_PATTERNS.keys():
        if platform_name in cmd:
            platform = platform_name
            break
    
    print(f"[DEBUG] Detected platform: {platform}")
    
    if not platform:
        # Default to YouTube for video searches, Google for everything else
        if any(word in cmd for word in ["video", "videos", "watch", "movie", "song", "music"]):
            platform = "youtube"
        else:
            platform = "google"
        print(f"[DEBUG] Defaulting to platform: {platform}")
    
    # Extract search query - be more intelligent about this
    query = cmd
    
    # Remove platform name and search keywords
    for keyword in search_keywords + [platform]:
        query = query.replace(keyword, "")
    
    # Remove other common words
    query = query.replace("and", "").replace("for", "").replace("some", "").replace("a", "").replace("the", "").strip()
    
    print(f"[DEBUG] Extracted search query: '{query}'")
    
    if not query:
        return platform, None, None
    
    return platform, query, None

def open_with_search(platform, query):
    """Open platform with search query"""
    if platform not in SEARCH_PATTERNS:
        print(f"[ERROR] Platform {platform} not supported for search")
        return False
    
    # URL encode the search query
    encoded_query = urllib.parse.quote_plus(query)
    search_url = SEARCH_PATTERNS[platform] + encoded_query
    
    print(f"[DEBUG] Opening {platform} with search: {query}")
    print(f"[DEBUG] URL: {search_url}")
    
    try:
        webbrowser.open(search_url)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to open search URL: {e}")
        return False

def open_command(target):
    """Main function to handle open commands - now with search support"""
    target = target.lower().strip()
    print(f"[DEBUG] Processing open command for: '{target}'")
    
    if not target:
        speak("I didn't catch what you want me to open. Please try again.")
        return
    
    # First, try to parse as a search command
    platform, query, remaining_cmd = parse_search_command(target)
    
    if platform and query:
        # It's a search command
        speak(f"Searching for {query} on {platform}")
        if open_with_search(platform, query):
            speak(f"I've opened {platform} and searched for {query}")
            return
        else:
            speak(f"Sorry, I couldn't search for {query} on {platform}")
            return
    elif platform and not query:
        # Platform mentioned but no search query
        speak(f"What would you like me to search for on {platform}?")
        return
    
    # Not a search command, proceed with regular open logic
    if remaining_cmd:
        target = remaining_cmd
    
    # Try to match with apps first
    app_match = fuzzy_match(target, APP_MAP.keys())
    if app_match:
        app_name = APP_MAP[app_match]
        print(f"[DEBUG] Attempting to open app: {app_name}")
        speak(f"Opening {app_match}")
        if open_app(app_name):
            speak(f"{app_match} is now open")
            return
        else:
            speak(f"Sorry, I couldn't open {app_match}. Make sure it's installed.")
            return
    
    # Try to match with websites
    web_match = fuzzy_match(target, WEB_DEFAULTS.keys())
    if web_match:
        url = WEB_DEFAULTS[web_match]
        print(f"[DEBUG] Attempting to open website: {url}")
        speak(f"Opening {web_match}")
        if open_website(url):
            speak(f"{web_match} is now open in your browser")
            return
        else:
            speak(f"Sorry, I couldn't open {web_match}. Please check your internet connection.")
            return
    
    # If no match found, try as direct URL
    if target.startswith("http") or "." in target:
        if not target.startswith("http"):
            target = f"https://{target}"
        print(f"[DEBUG] Attempting to open URL: {target}")
        speak(f"Opening {target}")
        if open_website(target):
            speak("Website is now open in your browser")
            return
    
    speak(f"Sorry, I don't know how to open {target}. Try saying the name more clearly.")

def wait_for_speech():
    """Wait for actual speech, not just background noise"""
    print("[INFO] Waiting for speech...")
    try:
        with mic as source:
            # Listen with longer timeout to avoid false triggers
            audio = recognizer.listen(
                source, 
                timeout=10,      # Wait up to 10 seconds for speech
                phrase_time_limit=5  # Max 5 seconds of speech
            )
        return audio
    except sr.WaitTimeoutError:
        print("[DEBUG] No speech detected in timeout period")
        return None

def listen_google():
    print("[DEBUG] Listening with Google Speech API...")
    
    if not CONTINUOUS_MODE:
        print("Press ENTER and then speak, or just start speaking...")
        
    audio = wait_for_speech()
    if not audio:
        return ""
        
    try:
        print("[DEBUG] Processing audio...")
        # Convert audio to proper format for Google API
        try:
            text = recognizer.recognize_google(
                audio, 
                language='en-US',
                show_all=False
            ).lower()
            print(f"[DEBUG] Google heard: '{text}'")
            return text
        except sr.RequestError as e:
            print("[DEBUG] Trying alternative audio format...")
            raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
            audio_16k = sr.AudioData(raw_data, 16000, 2)
            text = recognizer.recognize_google(audio_16k, language='en-US').lower()
            print(f"[DEBUG] Google heard (16kHz): '{text}'")
            return text
        
    except sr.UnknownValueError:
        print("[WARN] Google could not understand audio.")
        return ""
    except sr.RequestError as e:
        error_msg = str(e).lower()
        print(f"[ERROR] Google Speech API: {e}")
        print("[INFO] Falling back to offline mode...")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error in Google recognition: {e}")
        return None

def listen_vosk():
    if not vosk_model:
        print("[ERROR] Offline mode unavailable. No Vosk model found.")
        return ""
    print("[DEBUG] Listening with Vosk offline mode...")
    
    audio = wait_for_speech()
    if not audio:
        return ""
        
    try:
        print("[DEBUG] Converting audio for Vosk...")
        rec = KaldiRecognizer(vosk_model, 16000)
        
        # Convert audio to 16kHz, 16-bit mono (Vosk requirement)
        audio_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
        print(f"[DEBUG] Audio data length: {len(audio_data)} bytes")
        
        # Process audio in chunks (Vosk works better this way)
        chunk_size = 4000  # Process in smaller chunks
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            rec.AcceptWaveform(chunk)
        
        # Get final result
        final_result = rec.FinalResult()
        result = json.loads(final_result)
        
        text = result.get("text", "").lower().strip()
        print(f"[DEBUG] Vosk heard: '{text}'")
        
        # If no result, try partial result
        if not text:
            partial_result = rec.PartialResult()
            partial = json.loads(partial_result)
            text = partial.get("partial", "").lower().strip()
            print(f"[DEBUG] Vosk partial: '{text}'")
            
        return text
    except Exception as e:
        print(f"[ERROR] Vosk listening failed: {e}")
        return ""

def handle_system_commands(cmd):
    """Handle system commands like shutdown, stop, etc."""
    cmd = cmd.lower().strip()
    
    # Shutdown commands
    shutdown_keywords = ["shutdown", "stop", "quit", "exit", "bye", "goodbye", "sleep"]
    if any(keyword in cmd for keyword in shutdown_keywords):
        speak("Goodbye! Siri is shutting down now.")
        return True  # Signal to shut down
    
    # Help command
    if "help" in cmd or "what can you do" in cmd:
        speak("I can open apps like Chrome, Spotify, and Safari. I can also open websites like YouTube and Gmail. For advanced features, try saying: open YouTube and search for cooking videos, or open Spotify and find your favorite songs. Say shutdown to exit.")
        return False
    
    return False  # Continue running

def main():
    speak("Siri is online and listening.")
    
    # Show listening mode
    mode_text = "continuous listening" if CONTINUOUS_MODE else "speech detection mode"
    speak(f"Running in {mode_text}")
    
    # Test microphone first
    print(f"\n[INFO] Mode: {'Continuous' if CONTINUOUS_MODE else 'Smart Detection'}")
    print("[INFO] Testing microphone...")
    speak("Testing microphone and speech systems.")
    
    while True:
        print(f"\n🎤 Waiting for wake word '{WAKE_WORD}'...")
        if not CONTINUOUS_MODE:
            print("💡 Tip: Start speaking when you're ready - I'll detect your voice!")
            
        text = listen_google()
        if text is None:  # Google failed → try offline
            text = listen_vosk()
        
        # Skip empty results or background noise
        if not text or len(text.strip()) < 2:
            continue
            
        if WAKE_WORD not in text:
            print(f"[DEBUG] No wake word in: '{text}' - continuing to listen...")
            continue
            
        print(f"[DEBUG] Wake word detected in: '{text}'")
        speak("Yes, what would you like me to do?")
        
        # Listen for command with a timeout
        print("🎤 Listening for your command...")
        cmd = listen_google()
        if cmd is None:
            cmd = listen_vosk()
        
        if not cmd or len(cmd.strip()) < 2:
            speak("I didn't hear a clear command. Please try again.")
            continue
            
        print(f"[DEBUG] Command received: '{cmd}'")
        
        # Check for system commands first
        if handle_system_commands(cmd):
            break  # Exit the main loop
        
        # Check if it's an open/search command
        if any(keyword in cmd for keyword in ["open", "play", "search", "find", "watch", "listen", "launch", "start"]) or any(app in cmd for app in APP_MAP.keys()) or any(site in cmd for site in WEB_DEFAULTS.keys()):
            # Pass the full command to open_command for processing
            open_command(cmd)
        else:
            speak("Please tell me what to open, or say help for assistance.")
        
        # Small pause before listening again
        time.sleep(1)

def test_speech():
    """Test text-to-speech"""
    print("\n=== SPEECH TEST ===")
    try:
        voices = engine.getProperty('voices')
        if voices:
            current_voice = engine.getProperty('voice')
            print("Available voices:")
            for i, voice in enumerate(voices):
                marker = "* " if voice.id == current_voice else "  "
                print(f"{marker}{i}: {voice.name} ({voice.id})")
        
        print(f"Rate: {engine.getProperty('rate')}")
        print(f"Volume: {engine.getProperty('volume')}")
        
        print("Testing speech...")
        speak("Hello, this is Siri speaking. Can you hear me clearly?")
        return True
    except Exception as e:
        print(f"Speech test failed: {e}")
        return False

def test_microphone():
    """Test microphone and speech recognition"""
    print("\n=== MICROPHONE TEST ===")
    print("Available audio devices:")
    available_mics = sr.Microphone.list_microphone_names()
    for i, device in enumerate(available_mics):
        device_type = "🎤 INPUT" if "microphone" in device.lower() or "mic" in device.lower() else "🔊 OUTPUT" 
        print(f"  {i}: {device} ({device_type})")
    
    print(f"\nTesting with MacBook Air Microphone (should be device 0)...")
    print("Please say 'hello siri' clearly when you see 'Listening now...'")
    
    # Test with explicit microphone selection
    try:
        test_mic = sr.Microphone(device_index=0, sample_rate=16000, chunk_size=1024)
        test_recognizer = sr.Recognizer()
        
        with test_mic as source:
            print("Calibrating...")
            test_recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold: {test_recognizer.energy_threshold}")
            print("Listening now... (speak clearly)")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
        
        print(f"Captured audio: {len(audio.frame_data)} bytes")
        
        print("Testing Google Speech API...")
        try:
            # Try with 16kHz conversion
            raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
            audio_16k = sr.AudioData(raw_data, 16000, 2)
            result = test_recognizer.recognize_google(audio_16k)
            print(f"✅ Google Speech API working: '{result}'")
            return True
        except Exception as e:
            print(f"❌ Google Speech API failed: {e}")
    
        # Test Vosk if Google fails
        if vosk_model:
            print("Testing Vosk offline recognition...")
            try:
                rec = KaldiRecognizer(vosk_model, 16000)
                audio_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                
                # Process in chunks
                chunk_size = 4000
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i+chunk_size]
                    rec.AcceptWaveform(chunk)
                
                final_result = rec.FinalResult()
                result_dict = json.loads(final_result)
                result = result_dict.get("text", "")
                
                if result:
                    print(f"✅ Vosk working: '{result}'")
                    return True
                else:
                    print("❌ Vosk returned empty result")
            except Exception as e:
                print(f"❌ Vosk failed: {e}")
                
    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
    
    print("\n❌ All speech recognition systems failed")
    print("\n🔧 Troubleshooting suggestions:")
    print("1. Make sure you're using 'MacBook Air Microphone' (device 0)")
    print("2. Check System Preferences → Security & Privacy → Microphone")
    print("3. Grant microphone permission to Terminal/Python")
    print("4. Speak loudly and clearly")
    print("5. Try in a quiet environment")
    print("6. Check internet connection for Google API")
    return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_microphone()
        sys.exit()
    elif len(sys.argv) > 1 and sys.argv[1] == "speech":
        test_speech()
        sys.exit()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        speak("Goodbye!")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        speak("Sorry, something went wrong.")