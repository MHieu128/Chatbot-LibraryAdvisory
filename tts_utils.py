#!/usr/bin/env python3
"""
Text-to-Speech Utilities for Library Advisory System
Provides HuggingFace TTS integration with audio generation and caching
"""

import os
import io
import hashlib
import time
import tempfile
import uuid
import logging
import re
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
import json

# Audio and ML imports
try:
    import torch
    import torchaudio
    from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
    from datasets import load_dataset
    import numpy as np
    import soundfile as sf
    TTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: TTS dependencies not installed. Run: pip install -r requirements.txt")
    print(f"Error: {e}")
    TTS_AVAILABLE = False

@dataclass
class TTSConfig:
    """TTS configuration settings"""
    model_name: str = "microsoft/speecht5_tts"
    vocoder_name: str = "microsoft/speecht5_hifigan"
    cache_dir: str = "./tts_cache"
    max_cache_size_mb: int = 500
    max_text_length: int = 1000
    sample_rate: int = 16000
    audio_format: str = "wav"
    enable_caching: bool = True
    device: str = "auto"  # "auto", "cpu", or "cuda"

@dataclass
class AudioResult:
    """Result of TTS audio generation"""
    success: bool
    audio_bytes: Optional[bytes] = None
    audio_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    cache_hit: bool = False
    processing_time: float = 0.0

class AudioCacheManager:
    """Manages audio file caching with size limits"""
    
    def __init__(self, cache_dir: str, max_size_mb: int = 500):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.cache_index_file = os.path.join(cache_dir, "cache_index.json")
        self.cache_index = {}
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load existing cache index
        self._load_cache_index()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__ + ".AudioCacheManager")
    
    def _load_cache_index(self):
        """Load cache index from file"""
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r') as f:
                    self.cache_index = json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load cache index: {e}")
                self.cache_index = {}
    
    def _save_cache_index(self):
        """Save cache index to file"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save cache index: {e}")
    
    def get_cache_key(self, text: str, model_name: str = "") -> str:
        """Generate cache key for text and model"""
        content = f"{model_name}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_audio(self, cache_key: str) -> Optional[bytes]:
        """Retrieve cached audio bytes"""
        if cache_key not in self.cache_index:
            return None
        
        cache_file = self.cache_index[cache_key]["file_path"]
        
        if not os.path.exists(cache_file):
            # Remove from index if file doesn't exist
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                # Update access time
                self.cache_index[cache_key]["last_accessed"] = time.time()
                self._save_cache_index()
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read cached audio: {e}")
            return None
    
    def cache_audio(self, cache_key: str, audio_bytes: bytes) -> bool:
        """Cache audio bytes with size management"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.wav")
            
            # Write audio file
            with open(cache_file, 'wb') as f:
                f.write(audio_bytes)
            
            # Update cache index
            self.cache_index[cache_key] = {
                "file_path": cache_file,
                "size_bytes": len(audio_bytes),
                "created": time.time(),
                "last_accessed": time.time()
            }
            
            # Check and cleanup cache if needed
            self._cleanup_cache_if_needed()
            
            # Save updated index
            self._save_cache_index()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache audio: {e}")
            return False
    
    def _cleanup_cache_if_needed(self):
        """Remove old cache files if size limit exceeded"""
        total_size = sum(item["size_bytes"] for item in self.cache_index.values())
        max_size_bytes = self.max_size_mb * 1024 * 1024
        
        if total_size <= max_size_bytes:
            return
        
        # Sort by last accessed time (oldest first)
        sorted_items = sorted(
            self.cache_index.items(),
            key=lambda x: x[1]["last_accessed"]
        )
        
        # Remove oldest files until under limit
        for cache_key, item in sorted_items:
            if total_size <= max_size_bytes:
                break
            
            try:
                if os.path.exists(item["file_path"]):
                    os.remove(item["file_path"])
                total_size -= item["size_bytes"]
                del self.cache_index[cache_key]
                self.logger.info(f"Removed cached audio file: {cache_key}")
            except OSError as e:
                self.logger.warning(f"Failed to remove cache file {item['file_path']}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size = sum(item["size_bytes"] for item in self.cache_index.values())
        return {
            "total_files": len(self.cache_index),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.max_size_mb,
            "usage_percentage": (total_size / (self.max_size_mb * 1024 * 1024)) * 100
        }

class TextPreprocessor:
    """Preprocesses text for better TTS pronunciation"""
    
    def __init__(self):
        # Technical term pronunciation mapping
        self.tech_pronunciations = {
            "JavaScript": "Java Script",
            "API": "A P I",
            "JSON": "Jay Son",
            "HTTP": "H T T P",
            "HTTPS": "H T T P S",
            "CSS": "C S S",
            "HTML": "H T M L",
            "SQL": "S Q L",
            "React.js": "React JS",
            "Vue.js": "Vue JS",
            "Node.js": "Node JS",
            "Express.js": "Express JS",
            "Angular.js": "Angular JS",
            "Django": "Jango",
            "PostgreSQL": "Postgres Q L",
            "MySQL": "My S Q L",
            "MongoDB": "Mongo D B",
            "GitHub": "Git Hub",
            "GitLab": "Git Lab",
            "OAuth": "O Auth",
            "REST": "Rest",
            "GraphQL": "Graph Q L",
            "npm": "N P M",
            "pip": "pip",
            "CLI": "C L I",
            "IDE": "I D E",
            "URL": "U R L",
            "URI": "U R I",
            "UUID": "U U I D",
            "XML": "X M L",
            "YAML": "Yaml",
            "TCP": "T C P",
            "UDP": "U D P",
            "SSH": "S S H",
            "FTP": "F T P",
            "DNS": "D N S",
            "CDN": "C D N",
            "AWS": "A W S",
            "GCP": "G C P",
            "UI": "U I",
            "UX": "U X",
            "AI": "A I",
            "ML": "M L",
            "NLP": "N L P",
            "GPT": "G P T",
            "CRUD": "crud",
            "ORM": "O R M",
            "MVC": "M V C",
            "MVP": "M V P",
            "SPA": "S P A",
            "PWA": "P W A",
            "SSR": "S S R",
            "CSR": "C S R",
            "JWT": "J W T",
            "CORS": "C O R S",
            "CSRF": "C S R F",
            "XSS": "X S S"
        }
        
        # Common abbreviations
        self.abbreviations = {
            "vs": "versus",
            "etc": "etcetera",
            "e.g.": "for example",
            "i.e.": "that is",
            "w/": "with",
            "w/o": "without"
        }
    
    def preprocess(self, text: str) -> str:
        """Preprocess text for better TTS pronunciation"""
        if not text:
            return ""
        
        processed_text = text
        
        # Apply technical term pronunciations
        for term, pronunciation in self.tech_pronunciations.items():
            # Case-insensitive replacement but preserve original case context
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            processed_text = pattern.sub(pronunciation, processed_text)
        
        # Apply abbreviation expansions
        for abbrev, expansion in self.abbreviations.items():
            pattern = re.compile(r'\b' + re.escape(abbrev) + r'\b', re.IGNORECASE)
            processed_text = pattern.sub(expansion, processed_text)
        
        # Clean up markdown formatting
        processed_text = self._remove_markdown_formatting(processed_text)
        
        # Remove or replace special characters that confuse TTS
        processed_text = self._clean_special_characters(processed_text)
        
        # Limit text length for better TTS performance
        if len(processed_text) > 1000:
            processed_text = self._truncate_text_intelligently(processed_text, 1000)
        
        return processed_text.strip()
    
    def _remove_markdown_formatting(self, text: str) -> str:
        """Remove markdown formatting for cleaner TTS"""
        # Remove headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # Remove bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
        
        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
        
        # Clean up list markers
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        return text
    
    def _clean_special_characters(self, text: str) -> str:
        """Clean special characters that may confuse TTS"""
        # Replace common symbols with words
        replacements = {
            '&': ' and ',
            '@': ' at ',
            '%': ' percent ',
            '$': ' dollars ',
            '#': ' hash ',
            '+': ' plus ',
            '=': ' equals ',
            '<': ' less than ',
            '>': ' greater than ',
            '→': ' arrow ',
            '←': ' left arrow ',
            '↑': ' up arrow ',
            '↓': ' down arrow ',
            '✓': ' checkmark ',
            '✗': ' cross ',
            '●': ' bullet ',
            '•': ' bullet ',
            '◦': ' bullet ',
            '▪': ' bullet ',
            '▫': ' bullet '
        }
        
        for symbol, replacement in replacements.items():
            text = text.replace(symbol, replacement)
        
        # Remove other problematic characters
        text = re.sub(r'[^\w\s.,;:!?\'"-]', ' ', text)
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _truncate_text_intelligently(self, text: str, max_length: int) -> str:
        """Truncate text at sentence boundaries when possible"""
        if len(text) <= max_length:
            return text
        
        # Try to truncate at sentence boundary
        sentences = re.split(r'[.!?]+', text[:max_length])
        if len(sentences) > 1:
            # Remove the last potentially incomplete sentence
            truncated = '.'.join(sentences[:-1]) + '.'
            if len(truncated) > 50:  # Ensure we have meaningful content
                return truncated
        
        # Fallback: truncate at word boundary
        words = text[:max_length].split()
        return ' '.join(words[:-1]) + '.'

class TTSManager:
    """Main TTS manager using HuggingFace models"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """
        Initialize TTS manager
        
        Args:
            config: TTS configuration settings
        """
        if not TTS_AVAILABLE:
            raise ImportError("TTS dependencies not available. Install requirements.txt")
        
        self.config = config or TTSConfig()
        
        # Initialize components
        self.processor = None
        self.model = None
        self.vocoder = None
        self.speaker_embeddings = None
        
        # Determine device
        if self.config.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "mps"
        else:
            self.device = self.config.device
        
        # Initialize managers
        self.cache_manager = AudioCacheManager(
            self.config.cache_dir, 
            self.config.max_cache_size_mb
        ) if self.config.enable_caching else None
        
        self.text_preprocessor = TextPreprocessor()
        
        # Initialize logging
        self.logger = logging.getLogger(__name__ + ".TTSManager")
        
        # Model initialization flag
        self._models_loaded = False
    
    def initialize_models(self) -> bool:
        """Initialize TTS models with proper error handling"""
        try:
            self.logger.info(f"Initializing TTS models on device: {self.device}")
            
            # Load processor
            self.processor = SpeechT5Processor.from_pretrained(self.config.model_name)
            
            # Load TTS model
            self.model = SpeechT5ForTextToSpeech.from_pretrained(self.config.model_name)
            self.model.to(self.device)
            
            # Load vocoder
            self.vocoder = SpeechT5HifiGan.from_pretrained(self.config.vocoder_name)
            self.vocoder.to(self.device)
            
            # Load speaker embeddings
            self._load_speaker_embeddings()
            
            self._models_loaded = True
            self.logger.info("TTS models initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS models: {e}")
            return False
    
    def _load_speaker_embeddings(self):
        """Load default speaker embeddings"""
        try:
            # Load embeddings from HuggingFace datasets
            embeddings_dataset = load_dataset(
                "Matthijs/cmu-arctic-xvectors", 
                split="validation"
            )
            
            # Use the first speaker embedding as default
            if len(embeddings_dataset) > 0:
                self.speaker_embeddings = torch.tensor(
                    embeddings_dataset[0]["xvector"]
                ).unsqueeze(0)
            else:
                # Fallback: create random speaker embedding
                self.speaker_embeddings = torch.randn((1, 512))
            
            self.logger.info("Speaker embeddings loaded successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to load speaker embeddings, using random: {e}")
            # Fallback: create random speaker embedding
            self.speaker_embeddings = torch.randn((1, 512))
    
    def generate_audio(self, text: str, use_cache: bool = True) -> AudioResult:
        """
        Generate audio from text
        
        Args:
            text: Input text to convert to speech
            use_cache: Whether to use cached audio if available
            
        Returns:
            AudioResult with success status and audio data
        """
        start_time = time.time()
        
        # Validate input
        if not text or not text.strip():
            return AudioResult(
                success=False,
                error_message="Empty text provided",
                processing_time=time.time() - start_time
            )
        
        if len(text) > self.config.max_text_length:
            return AudioResult(
                success=False,
                error_message=f"Text too long (max {self.config.max_text_length} characters)",
                processing_time=time.time() - start_time
            )
        
        # Initialize models if not already loaded
        if not self._models_loaded:
            if not self.initialize_models():
                return AudioResult(
                    success=False,
                    error_message="Failed to initialize TTS models",
                    processing_time=time.time() - start_time
                )
        
        # Preprocess text
        processed_text = self.text_preprocessor.preprocess(text)
        
        # Check cache if enabled
        cache_hit = False
        if use_cache and self.cache_manager:
            cache_key = self.cache_manager.get_cache_key(processed_text, self.config.model_name)
            cached_audio = self.cache_manager.get_cached_audio(cache_key)
            
            if cached_audio:
                self.logger.info(f"Cache hit for text: {processed_text[:50]}...")
                return AudioResult(
                    success=True,
                    audio_bytes=cached_audio,
                    cache_hit=True,
                    processing_time=time.time() - start_time
                )
        
        # Generate audio
        try:
            audio_bytes = self._generate_audio_internal(processed_text)
            
            if audio_bytes is None:
                return AudioResult(
                    success=False,
                    error_message="Audio generation failed",
                    processing_time=time.time() - start_time
                )
            
            # Cache the result
            if use_cache and self.cache_manager:
                self.cache_manager.cache_audio(cache_key, audio_bytes)
            
            # Estimate duration
            duration = self._estimate_audio_duration(audio_bytes)
            
            self.logger.info(f"Generated audio for text: {processed_text[:50]}... (duration: {duration:.1f}s)")
            
            return AudioResult(
                success=True,
                audio_bytes=audio_bytes,
                duration_seconds=duration,
                cache_hit=False,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Audio generation failed: {e}")
            return AudioResult(
                success=False,
                error_message=f"Audio generation error: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def _generate_audio_internal(self, text: str) -> Optional[bytes]:
        """Internal audio generation method"""
        try:
            # Tokenize input text
            inputs = self.processor(text=text, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self.device)
            
            # Generate speech
            with torch.no_grad():
                speech = self.model.generate_speech(
                    input_ids,
                    self.speaker_embeddings.to(self.device),
                    vocoder=self.vocoder
                )
            
            # Convert to audio bytes
            return self._tensor_to_audio_bytes(speech)
            
        except Exception as e:
            self.logger.error(f"Internal audio generation failed: {e}")
            return None
    
    def _tensor_to_audio_bytes(self, speech_tensor: torch.Tensor) -> bytes:
        """Convert speech tensor to audio bytes"""
        # Ensure proper format
        if speech_tensor.dim() == 1:
            speech_tensor = speech_tensor.unsqueeze(0)
        
        # Convert to numpy
        audio_numpy = speech_tensor.cpu().numpy()
        
        # Create audio buffer
        buffer = io.BytesIO()
        
        # Save as WAV using soundfile
        sf.write(
            buffer,
            audio_numpy.T,  # Transpose for soundfile
            self.config.sample_rate,
            format='WAV'
        )
        
        return buffer.getvalue()
    
    def _estimate_audio_duration(self, audio_bytes: bytes) -> float:
        """Estimate audio duration from audio bytes"""
        try:
            # Load audio data
            buffer = io.BytesIO(audio_bytes)
            data, sample_rate = sf.read(buffer)
            
            # Calculate duration
            duration = len(data) / sample_rate
            return duration
            
        except Exception:
            # Fallback estimation based on file size
            # Rough estimate: WAV files are about 176KB per second for 16kHz mono
            estimated_duration = len(audio_bytes) / (16000 * 2)  # 2 bytes per sample
            return max(1.0, estimated_duration)  # Minimum 1 second
    
    def save_audio_to_file(self, audio_bytes: bytes, file_path: str) -> bool:
        """Save audio bytes to file"""
        try:
            with open(file_path, 'wb') as f:
                f.write(audio_bytes)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save audio to {file_path}: {e}")
            return False
    
    def create_temporary_audio_file(self, audio_bytes: bytes) -> Optional[str]:
        """Create temporary audio file and return path"""
        try:
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.wav',
                prefix='tts_'
            )
            temp_file.write(audio_bytes)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            self.logger.error(f"Failed to create temporary audio file: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get TTS system status"""
        cache_stats = self.cache_manager.get_cache_stats() if self.cache_manager else {}
        
        return {
            "models_loaded": self._models_loaded,
            "model_name": self.config.model_name,
            "vocoder_name": self.config.vocoder_name,
            "device": self.device,
            "cache_enabled": self.config.enable_caching,
            "cache_stats": cache_stats,
            "max_text_length": self.config.max_text_length,
            "sample_rate": self.config.sample_rate,
            "audio_format": self.config.audio_format
        }

# Global instance
_tts_manager = None

def get_tts_manager(config: Optional[TTSConfig] = None) -> TTSManager:
    """Get or create global TTS manager instance"""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager(config)
    return _tts_manager

def initialize_tts() -> bool:
    """Initialize TTS system"""
    try:
        manager = get_tts_manager()
        return manager.initialize_models()
    except Exception as e:
        print(f"Failed to initialize TTS: {e}")
        return False

if __name__ == "__main__":
    # Test the TTS implementation
    logging.basicConfig(level=logging.INFO)
    
    print("Testing TTS implementation...")
    
    # Test text preprocessing
    preprocessor = TextPreprocessor()
    test_text = "React.js vs Vue.js: Which JavaScript framework is better for APIs?"
    processed = preprocessor.preprocess(test_text)
    print(f"Original: {test_text}")
    print(f"Processed: {processed}")
    
    if TTS_AVAILABLE:
        try:
            # Initialize TTS manager
            config = TTSConfig(cache_dir="./test_tts_cache")
            manager = TTSManager(config)
            
            if manager.initialize_models():
                print("✓ TTS models initialized successfully")
                
                # Test audio generation
                test_text = "Hello, this is a test of the text to speech system."
                result = manager.generate_audio(test_text)
                
                if result.success:
                    print(f"✓ Audio generated successfully")
                    print(f"  Duration: {result.duration_seconds:.1f}s")
                    print(f"  Processing time: {result.processing_time:.2f}s")
                    print(f"  Cache hit: {result.cache_hit}")
                    print(f"  Audio size: {len(result.audio_bytes)} bytes")
                else:
                    print(f"✗ Audio generation failed: {result.error_message}")
                
                # Test status
                status = manager.get_status()
                print(f"✓ TTS Status: {status}")
                
            else:
                print("✗ Failed to initialize TTS models")
        
        except Exception as e:
            print(f"✗ TTS test failed: {e}")
    else:
        print("✗ TTS dependencies not available")