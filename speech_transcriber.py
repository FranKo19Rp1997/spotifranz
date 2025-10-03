# speech_transcriber.py
import speech_recognition as sr
import librosa
import numpy as np
import tempfile
import os
import wave
from scipy import signal


class SpeechTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

    def transcribe(self, audio_path):
        """
        Transcribe audio file to text using multiple engines
        """
        try:
            # Primero intentar con Google Speech Recognition
            transcription = self._transcribe_google(audio_path)
            if transcription:
                return transcription

            # Fallback a Sphinx (offline)
            transcription = self._transcribe_sphinx(audio_path)
            return transcription

        except Exception as e:
            print(f"Transcription error: {e}")
            return None

    def _transcribe_google(self, audio_path):
        """Usar Google Speech Recognition API"""
        try:
            # Verificar que el archivo existe y tiene contenido
            if not os.path.exists(audio_path):
                print(f"Audio file not found: {audio_path}")
                return None

            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                print("Audio file is empty")
                return None

            with sr.AudioFile(audio_path) as source:
                # Ajustar para ruido ambiental
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)

            text = self.recognizer.recognize_google(audio, language='es-ES')
            return text

        except sr.UnknownValueError:
            print("Google Speech Recognition no pudo entender el audio")
            return None
        except sr.RequestError as e:
            print(f"Error en la solicitud a Google Speech Recognition; {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in Google transcription: {e}")
            return None

    def _transcribe_sphinx(self, audio_path):
        """Usar CMU Sphinx (reconocimiento offline)"""
        try:
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)

            text = self.recognizer.recognize_sphinx(audio, language='es-ES')
            return text

        except sr.UnknownValueError:
            print("Sphinx no pudo entender el audio")
            return None
        except sr.RequestError as e:
            print(f"Error en Sphinx; {e}")
            return None
        except Exception as e:
            print(f"Unexpected error in Sphinx transcription: {e}")
            return None

    def transcribe_with_timestamps(self, audio_path):
        """Transcribir con marcas de tiempo a nivel de palabra"""
        try:
            # Cargar audio para análisis detallado
            y, sr = librosa.load(audio_path, sr=16000)

            # Detectar segmentos con voz
            voiced_segments = self._detect_voiced_segments(y, sr)

            transcriptions = []
            for start, end in voiced_segments:
                segment = y[start:end]

                # Guardar segmento en archivo temporal
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                    self._save_audio_segment(segment, sr, temp_path)

                    # Transcribir segmento
                    transcription = self.transcribe(temp_path)
                    if transcription:
                        transcriptions.append({
                            'start': start / sr,
                            'end': end / sr,
                            'text': transcription
                        })

                    # Limpiar archivo temporal
                    os.unlink(temp_path)

            return transcriptions

        except Exception as e:
            print(f"Timestamp transcription error: {e}")
            return None

    def _detect_voiced_segments(self, y, sr, frame_length=2048, hop_length=512):
        """Detectar segmentos con voz en el audio"""
        if len(y) < frame_length:
            return []

        # Calcular energía RMS
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]

        # Segmentación basada en umbral
        threshold = np.mean(rms) * 0.3  # Umbral más bajo para ser más sensible
        voiced_frames = rms > threshold

        # Convertir frames a samples
        segments = []
        start = None

        for i, voiced in enumerate(voiced_frames):
            sample_start = i * hop_length
            sample_end = sample_start + hop_length

            if voiced and start is None:
                start = sample_start
            elif not voiced and start is not None:
                # Solo agregar segmentos de al menos 0.5 segundos
                segment_duration = (sample_end - start) / sr
                if segment_duration >= 0.5:
                    segments.append((start, sample_end))
                start = None

        if start is not None:
            segment_duration = (len(y) - start) / sr
            if segment_duration >= 0.5:
                segments.append((start, len(y)))

        return segments

    def _save_audio_segment(self, y, sr, output_path):
        """Guardar segmento de audio en archivo"""
        try:
            # Normalizar audio
            if len(y) > 0:
                y_normalized = librosa.util.normalize(y)
            else:
                y_normalized = y

            # Convertir a 16-bit PCM
            y_int = (y_normalized * 32767).astype(np.int16)

            with wave.open(output_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # mono
                wav_file.setsampwidth(2)  # 2 bytes (16-bit)
                wav_file.setframerate(sr)
                wav_file.writeframes(y_int.tobytes())

        except Exception as e:
            print(f"Error saving audio segment: {e}")

    def get_audio_duration(self, audio_path):
        """Obtener duración del archivo de audio"""
        try:
            y, sr = librosa.load(audio_path, sr=None)
            return librosa.get_duration(y=y, sr=sr)
        except:
            return 0

    def validate_audio_file(self, audio_path):
        """Validar que el archivo de audio sea procesable"""
        try:
            # Verificar que existe
            if not os.path.exists(audio_path):
                return False, "El archivo no existe"

            # Verificar tamaño
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                return False, "El archivo está vacío"

            # Verificar que se puede cargar
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)

            if duration < 0.1:  # Muy corto
                return False, "El audio es demasiado corto (< 0.1 segundos)"

            if duration > 300:  # Muy largo
                return False, "El audio es demasiado largo (> 5 minutos)"

            return True, f"Audio válido: {duration:.2f} segundos, {sr} Hz"

        except Exception as e:
            return False, f"Error validando audio: {str(e)}"