"""
SACA GUI - Graphical User Interface for Symptom Assessment

Simple desktop interface with:
- Voice recording
- Text input
- Results display
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import pyaudio
import wave
import os
from datetime import datetime


class SACAInterface:
    """Main GUI Application for SACA"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SACA - Smart Adaptive Clinical Assistant")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Audio recording variables
        self.is_recording = False
        self.audio_frames = []
        self.audio_filename = None
        
        # Import modules (delayed import)
        self.setup_complete = False
        
        self.setup_ui()
        self.load_backend()
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Title
        title_frame = tk.Frame(self.root, bg="#D4691B", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="SACA - Symptom Assessment",
            font=("Helvetica", 24, "bold"),
            bg="#000000",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # Main content frame
        content_frame = tk.Frame(self.root, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input section
        input_label = tk.Label(
            content_frame,
            text="Tell us how you feel:",
            font=("Helvetica", 14, "bold")
        )
        input_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Voice recording button
        self.voice_button = tk.Button(
            content_frame,
            text="🎤 Hold to Record Voice",
            font=("Helvetica", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2,
            cursor="hand2",
            relief=tk.RAISED,
            bd=3
        )
        self.voice_button.pack(fill=tk.X, pady=(0, 15))
        self.voice_button.bind("<ButtonPress-1>", self.start_recording)
        self.voice_button.bind("<ButtonRelease-1>", self.stop_recording)
        
        # OR separator
        separator_frame = tk.Frame(content_frame)
        separator_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            separator_frame,
            text="────── OR ──────",
            font=("Helvetica", 10),
            fg="gray"
        ).pack()
        
        # Text input
        tk.Label(
            content_frame,
            text="Type your symptoms:",
            font=("Helvetica", 12)
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.text_input = scrolledtext.ScrolledText(
            content_frame,
            height=5,
            font=("Helvetica", 12),
            wrap=tk.WORD
        )
        self.text_input.pack(fill=tk.X, pady=(0, 15))
        self.text_input.insert("1.0", "Example: I have a headache and fever")
        self.text_input.bind("<FocusIn>", self.clear_placeholder)
        
        # Submit button
        self.submit_button = tk.Button(
            content_frame,
            text="Submit ➤",
            font=("Helvetica", 14, "bold"),
            bg="#2196F3",
            fg="white",
            height=2,
            cursor="hand2",
            command=self.submit_input
        )
        self.submit_button.pack(fill=tk.X, pady=(0, 20))
        
        # Results section
        results_label = tk.Label(
            content_frame,
            text="Results:",
            font=("Helvetica", 14, "bold")
        )
        results_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Results display
        self.results_display = scrolledtext.ScrolledText(
            content_frame,
            height=15,
            font=("Courier", 11),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#F5F5F5"
        )
        self.results_display.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            font=("Helvetica", 10),
            bg="#E0E0E0",
            anchor=tk.W,
            padx=10
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_backend(self):
        """Load backend modules in background"""
        self.update_status("Loading AI models...")
        
        def load():
            try:
                # Import main pipeline
                from main import run_pipeline
                from nlp.voice_processor import VoiceProcessor
                
                self.run_pipeline = run_pipeline
                self.voice_processor = VoiceProcessor(model_name='small')
                
                self.setup_complete = True
                self.update_status("Ready")
                
            except Exception as e:
                self.update_status(f"Error loading: {e}")
                messagebox.showerror("Error", f"Failed to load backend:\n{e}")
        
        # Load in background thread
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def clear_placeholder(self, event):
        """Clear placeholder text on focus"""
        if self.text_input.get("1.0", tk.END).strip().startswith("Example:"):
            self.text_input.delete("1.0", tk.END)
    
    def start_recording(self, event):
        """Start recording audio"""
        if not self.setup_complete:
            messagebox.showwarning("Not Ready", "Please wait for system to load...")
            return
        
        self.is_recording = True
        self.audio_frames = []
        self.voice_button.config(bg="#F44336", text="🔴 Recording... (Release to stop)")
        self.update_status("Recording...")
        
        # Start recording in background thread
        thread = threading.Thread(target=self._record_audio, daemon=True)
        thread.start()
    
    def stop_recording(self, event):
        """Stop recording audio"""
        if self.is_recording:
            self.is_recording = False
            self.voice_button.config(bg="#4CAF50", text="🎤 Hold to Record Voice")
            self.update_status("Processing voice...")
    
    def _record_audio(self):
        """Record audio in background"""
        try:
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            audio = pyaudio.PyAudio()
            
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            while self.is_recording:
                data = stream.read(CHUNK)
                self.audio_frames.append(data)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save audio file
            if self.audio_frames:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.audio_filename = f"temp_recording_{timestamp}.wav"
                
                wf = wave.open(self.audio_filename, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.audio_frames))
                wf.close()
                
                # Process the audio
                self.root.after(100, self.process_voice_input)
            
        except Exception as e:
            self.update_status(f"Recording error: {e}")
            messagebox.showerror("Recording Error", f"Failed to record:\n{e}")
    
    def process_voice_input(self):
        """Process recorded voice input with automatic Kriol/English detection"""
        if not self.audio_filename or not os.path.exists(self.audio_filename):
            return
        
        self.update_status("Transcribing audio...")
        
        def process():
            try:
                # Transcribe audio with bilingual support
                result = self.voice_processor.transcribe_bilingual(self.audio_filename)
                
                original_text = result['original_text']
                detected_lang = result['detected_language']
                translated_text = result['translated_text']
                is_translated = result['is_translated']
                
                # Show detected language
                lang_display = detected_lang.capitalize()
                status_msg = f"Detected: {lang_display}"
                
                self.root.after(0, lambda: self.update_status(status_msg))
                
                # Update text input with ORIGINAL transcription (Kriol or English as-is)
                # The NLP pipeline will handle Kriol translation in run_pipeline()
                self.root.after(0, lambda: self.text_input.delete("1.0", tk.END))
                self.root.after(0, lambda: self.text_input.insert("1.0", original_text))
                
                # Auto-submit
                self.root.after(100, self.submit_input)
                
                # Clean up audio file
                try:
                    os.remove(self.audio_filename)
                except:
                    pass
                
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Voice processing failed:\n{e}"))
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def submit_input(self):
        """Submit text input for processing"""
        if not self.setup_complete:
            messagebox.showwarning("Not Ready", "Please wait for system to load...")
            return
        
        # Get text input
        text = self.text_input.get("1.0", tk.END).strip()
        
        if not text or text.startswith("Example:"):
            messagebox.showwarning("No Input", "Please enter symptoms or record voice")
            return
        
        self.update_status("Analyzing symptoms...")
        self.submit_button.config(state=tk.DISABLED)
        
        def process():
            try:
                # Run pipeline
                result = self.run_pipeline(text, source="gui")
                
                # Display results
                self.root.after(0, lambda: self.display_results(result))
                self.root.after(0, lambda: self.update_status("Complete"))
                self.root.after(0, lambda: self.submit_button.config(state=tk.NORMAL))
                
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"Error: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Processing failed:\n{e}"))
                self.root.after(0, lambda: self.submit_button.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def display_results(self, result):
        """Display results in the text area"""
        self.results_display.config(state=tk.NORMAL)
        self.results_display.delete("1.0", tk.END)
        
        # Format results nicely
        output = "=" * 60 + "\n"
        output += "SYMPTOM ASSESSMENT RESULTS\n"
        output += "=" * 60 + "\n\n"
        
        # Input type
        input_source = result.get('input_source', 'text')
        output += f"Input Type: {input_source.upper()}\n"
        
        # Original input
        output += f"Your Input: {result.get('input_text', '')}\n"
        
        # Translated text (from Kriol if applicable)
        translated = result.get('translated_text', '')
        if translated != result.get('input_text', ''):
            output += f"Translated: {translated}\n"
        
        output += f"\n{'-' * 60}\n\n"
        
        # Symptoms
        output += "DETECTED SYMPTOMS:\n\n"
        
        present = result.get('symptoms_present', [])
        negated = result.get('symptoms_negated', [])
        
        if present:
            output += "✓ Symptoms Present:\n"
            for symptom in present:
                output += f"  • {symptom.title()}\n"
        else:
            output += "✓ Symptoms Present: None\n"
        
        output += "\n"
        
        if negated:
            output += "✗ Symptoms Negated (you said you DON'T have):\n"
            for symptom in negated:
                output += f"  • {symptom.title()}\n"
        else:
            output += "✗ Symptoms Negated: None\n"
        
        output += f"\n{'-' * 60}\n"
        
        self.results_display.insert("1.0", output)
        self.results_display.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)


def main():
    """Launch the GUI application"""
    root = tk.Tk()
    app = SACAInterface(root)
    root.mainloop()


if __name__ == "__main__":
    main()
