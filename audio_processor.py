# audio_processor.py
import librosa
import numpy as np
import soundfile as sf
import tempfile
import os
from scipy import signal
import wave
import base64
import io


class AudioProcessor:
    def __init__(self):
        self.supported_formats = ['wav']  # Por ahora solo WAV

    def preprocess_audio(self, audio_path):
        """
        Preprocesar audio para mejorar la transcripción - solo WAV
        """
        try:
            # Verificar que sea WAV
            if not audio_path.lower().endswith('.wav'):
                # Intentar convertir si es WebM
                if audio_path.lower().endswith('.webm'):
                    audio_path = self._handle_webm_file(audio_path)
                else:
                    raise ValueError(f"Formato no soportado: {audio_path}")

            # Cargar audio
            y, sr = librosa.load(audio_path, sr=16000, mono=True)

            # Aplicar preprocesamiento
            y_processed = self._apply_preprocessing(y, sr)

            # Guardar audio procesado
            output_path = self._get_output_path(audio_path)
            sf.write(output_path, y_processed, sr, subtype='PCM_16')

            return output_path

        except Exception as e:
            print(f"Audio preprocessing error: {e}")
            # Si falla, devolver el original
            return audio_path

    def _handle_webm_file(self, webm_path):
        """
        Manejar archivos WebM - crear un WAV de prueba
        """
        try:
            # Para WebM, creamos un archivo WAV de prueba
            # En un sistema real, necesitarías una biblioteca WebM/Opus
            wav_path = os.path.join(tempfile.gettempdir(), f"converted_{os.urandom(8).hex()}.wav")

            # Crear un WAV de silencio de 2 segundos (para testing)
            duration = 2.0
            sample_rate = 16000
            samples = int(duration * sample_rate)
            silent_audio = np.zeros(samples, dtype=np.float32)

            sf.write(wav_path, silent_audio, sample_rate, subtype='PCM_16')
            print(f"Created placeholder WAV for WebM: {wav_path}")

            return wav_path

        except Exception as e:
            print(f"WebM handling error: {e}")
            raise ValueError("No se pudo procesar el archivo WebM")

    def _apply_preprocessing(self, y, sr):
        """Aplicar técnicas de preprocesamiento de audio"""
        if len(y) == 0:
            return y

        # 1. Reducción de ruido simple
        y_denoised = self._simple_denoise(y, sr)

        # 2. Normalización de volumen
        y_normalized = librosa.util.normalize(y_denoised)

        # 3. Mejora de voces
        y_enhanced = self._enhance_voice(y_normalized, sr)

        return y_enhanced

    def _simple_denoise(self, y, sr, cutoff_freq=8000):
        """Reducción simple de ruido"""
        if len(y) < 10:  # Muy corto para filtrar
            return y

        nyquist = sr / 2
        normal_cutoff = cutoff_freq / nyquist

        try:
            b, a = signal.butter(4, normal_cutoff, btype='low', analog=False)
            y_filtered = signal.filtfilt(b, a, y)
            return y_filtered
        except:
            return y

    def _enhance_voice(self, y, sr):
        """Mejorar frecuencias de voz humana"""
        if len(y) < 10:
            return y

        nyquist = sr / 2
        low = 300 / nyquist
        high = 3400 / nyquist

        try:
            b, a = signal.butter(4, [low, high], btype='band')
            y_filtered = signal.filtfilt(b, a, y)
            return y_filtered
        except:
            return y

    def _get_output_path(self, original_name):
        """Generar ruta para archivo procesado"""
        base_name = os.path.basename(original_name)
        name, ext = os.path.splitext(base_name)
        return os.path.join(tempfile.gettempdir(), f"processed_{name}.wav")

    def is_audio_format_supported(self, filename):
        """Verificar si el formato de audio es soportado"""
        if not filename:
            return False
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return ext in self.supported_formats

    def get_audio_info(self, audio_path):
        """Obtener información del archivo de audio"""
        try:
            if audio_path.lower().endswith('.wav'):
                with wave.open(audio_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / float(rate)

                    return {
                        'duration': duration,
                        'sample_rate': rate,
                        'channels': wav_file.getnchannels(),
                        'sample_width': wav_file.getsampwidth()
                    }
            else:
                y, sr = librosa.load(audio_path, sr=None)
                return {
                    'duration': librosa.get_duration(y=y, sr=sr),
                    'sample_rate': sr,
                    'channels': 1 if y.ndim == 1 else 2
                }
        except Exception as e:
            print(f"Audio info error: {e}")
            return {}

    def create_test_wav(self, duration=3.0, sample_rate=16000):
        """Crear un archivo WAV de prueba con tono de audio"""
        try:
            # Crear un tono de prueba (440 Hz - LA musical)
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)  # Ton de 440 Hz

            # Guardar como WAV
            wav_path = os.path.join(tempfile.gettempdir(), f"test_audio_{os.urandom(4).hex()}.wav")
            sf.write(wav_path, audio_data, sample_rate, subtype='PCM_16')

            return wav_path
        except Exception as e:
            print(f"Test WAV creation error: {e}")
            return None