# voice_engine.py - Neural Clone + MP3 Reference
import torch
from TTS.api import TTS
# Import all flagged classes for the XTTS checkpoint
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig
import pygame
import hashlib
import threading
import os
import time
import speech_recognition as sr
import torchaudio
import pathlib


# 1. THE STABILIZER
# This forces torchaudio to use the standard backend.
# Make sure you've run: pip install soundfile
try:
    if "soundfile" in torchaudio.list_audio_backends():
        torchaudio.set_audio_backend("soundfile")
except:
    pass

# 2. SECURITY HANDSHAKE (PyTorch 2.6)
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig

torch.serialization.add_safe_globals([
    XttsConfig, 
    XttsAudioConfig, 
    XttsArgs, 
    BaseDatasetConfig
])
os.environ["COQUI_TOS_AGREED"] = "1"

class VoiceEngine:
    def __init__(self, callback):
        # 1. Define the device FIRST
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"LUMA_LOG: Initializing Neural Voice on {self.device.upper()}...")

        # 2. Now use self.device for both models
        from faster_whisper import WhisperModel
        self.stt_model = WhisperModel("tiny.en", device=self.device, compute_type="int8")
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        
        # 3. Status and hardware setup [cite: 2026-02-11]
        self.is_listening = False 
        self.is_speaking = False
        self.callback = callback
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Anchor to the 'luma-orb' folder where THIS file lives
        self.local_dir = pathlib.Path(__file__).parent.absolute()
        
        # Point to the assets folder sitting right next to this script
        self.voice_seed = str(self.local_dir / "assets" / "luma_identity.mp3")
        self.cache_dir = self.local_dir / "assets" / "voice_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        pygame.mixer.init()

    def _get_cache_path(self, text):
        """Hashes the text to check for existing neural audio."""
        text_hash = hashlib.md5(text.lower().strip().encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.wav"

    def start_listening(self, luma_instance):
        """Activates the sensory array's listening loop."""
        if not self.is_listening:
            self.is_listening = True
            # Threaded to keep the Herning Hub UI at 60FPS
            threading.Thread(target=self._listen_loop, args=(luma_instance,), daemon=True).start()
            print("LUMA_LOG: Sensory array active and listening.")
            
    def _listen_loop(self, luma):
        """Restored local listener loop using Faster-Whisper."""
        import io # Ensure this is at the top of your file
        
        # WARMUP: One dummy pass to ensure the model is in RAM
        try:
            self.stt_model.transcribe(io.BytesIO(b"")) 
        except:
            pass
        print("LUMA_LOG: Whisper engine is warm and listening.")

        while self.is_listening:
            # We only listen if I'm not already thinking or speaking
            if not luma.is_thinking and not self.is_speaking:
                try:
                    with self.microphone as source:
                        # Quick ambient check for better accuracy
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        # Short timeout for snappier response times
                        audio = self.recognizer.listen(source, timeout=0.8, phrase_time_limit=3)
                    
                    # 1. Convert audio to memory buffer
                    wav_data = io.BytesIO(audio.get_wav_data())
                    
                    # 2. Local Whisper Inference
                    segments, _ = self.stt_model.transcribe(wav_data, beam_size=1)
                    text = "".join([s.text for s in segments]).lower().strip()

                    # 3. Wake Word Detection [cite: 2026-02-10]
                    if "luma" in text:
                        # Snappy acknowledgement in the new neural voice
                        self.speak("Ready and waiting, Lau.") 
                        self._capture_cmd()
                        
                except (sr.WaitTimeoutError, sr.UnknownValueError):
                    continue
                except Exception as e:
                    print(f"LUMA_LOG: Sensory Error: {e}")
                    time.sleep(0.2)
            
            # Slight sleep to prevent CPU thread-locking
            time.sleep(0.05)

    def speak(self, text):
            """Speaks using the cache or generates a new Irish-lilted clone."""
            def _run():
                self.is_speaking = True
                cache_path = self._get_cache_path(text)
                
                # 1. FIXED PATHING
                # Always output new generations to a fixed temp file in the assets folder
                temp_output = str(self.local_dir / "assets" / "speech_temp.wav")
                audio_to_play = str(cache_path) if cache_path.exists() else temp_output
                
                if not cache_path.exists():
                    print(f"LUMA_LOG: Synthesizing Irish lilt for: '{text[:30]}...'")
                    self.tts.tts_to_file(
                        text=text,
                        speaker_wav=self.voice_seed,
                        language="en",
                        file_path=temp_output
                    )
                    # Cache it for next time so we save CPU cycles
                    import shutil
                    shutil.copy(temp_output, cache_path)

                # 2. STABLE PLAYBACK
                try:
                    if pygame.mixer.get_init() is None:
                        pygame.mixer.init()
                    
                    pygame.mixer.music.load(audio_to_play)
                    pygame.mixer.music.set_volume(1.0) 
                    pygame.mixer.music.play()
                    
                    # CRITICAL: Keep the thread alive while audio is playing
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                except Exception as e:
                    print(f"LUMA_LOG: Vocal Playback Error: {e}")

                self.is_speaking = False

            threading.Thread(target=_run, daemon=True).start()
            
    def stop(self):
        """Emergency stop for all sensory and vocal output."""
        # 1. Kill the vocal cords
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            self.is_speaking = False
            print("LUMA_LOG: Vocal output terminated.")
        except Exception as e:
            print(f"LUMA_LOG: Error stopping mixer: {e}")

        # 2. Silence the sensory array
        self.is_listening = False
        print("LUMA_LOG: Sensory array standing down.")

    def _capture_cmd(self):
        """Placeholder for command capture logic to prevent crashes."""
        # This ensures that when the wake word is hit, the engine doesn't 
        # trip over a missing method.
        pass