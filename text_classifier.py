# text_classifier.py
import pandas as pd
import numpy as np
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import pickle

# Importaciones condicionales de TensorFlow
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import Dense, Dropout, LSTM, Embedding, Bidirectional
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences

    TENSORFLOW_AVAILABLE = True
except ImportError:
    print("TensorFlow no está disponible. Usando modo simulado.")
    TENSORFLOW_AVAILABLE = False


class TextClassifier:
    def __init__(self):
        self.intent_model = None
        self.topic_model = None
        self.intent_vectorizer = None
        self.topic_vectorizer = None
        self.intent_encoder = None
        self.topic_encoder = None
        self.tokenizer = None
        self.max_sequence_length = 100

        self.load_or_train_models()

    def load_or_train_models(self):
        """Cargar modelos existentes o usar modo simulado"""
        if not TENSORFLOW_AVAILABLE:
            print("TensorFlow no disponible - usando clasificador simulado")
            return

        try:
            # Intentar cargar modelos guardados
            self.intent_model = load_model('models/intent_classifier.h5')
            self.topic_model = load_model('models/topic_classifier.h5')

            with open('models/intent_vectorizer.pkl', 'rb') as f:
                self.intent_vectorizer = pickle.load(f)
            with open('models/topic_vectorizer.pkl', 'rb') as f:
                self.topic_vectorizer = pickle.load(f)
            with open('models/intent_encoder.pkl', 'rb') as f:
                self.intent_encoder = pickle.load(f)
            with open('models/topic_encoder.pkl', 'rb') as f:
                self.topic_encoder = pickle.load(f)
            with open('models/tokenizer.pkl', 'rb') as f:
                self.tokenizer = pickle.load(f)

            print("Models loaded successfully")

        except Exception as e:
            print(f"Could not load models: {e}")
            print("Using simulated classification")

    def preprocess_text(self, text):
        """Preprocesar texto para clasificación"""
        if not text or not isinstance(text, str):
            return ""

        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        return text

    def predict_intent(self, text):
        """Predecir intención del texto"""
        if not TENSORFLOW_AVAILABLE or not self.intent_model:
            return self._simulate_intent_prediction(text)

        try:
            text_processed = self.preprocess_text(text)
            X = self.intent_vectorizer.transform([text_processed]).toarray()

            prediction = self.intent_model.predict(X, verbose=0)
            intent_idx = np.argmax(prediction[0])

            return self.intent_encoder.inverse_transform([intent_idx])[0]
        except Exception as e:
            print(f"Error in intent prediction: {e}")
            return self._simulate_intent_prediction(text)

    def predict_topic(self, text):
        """Predecir tema del texto"""
        if not TENSORFLOW_AVAILABLE or not self.topic_model:
            return self._simulate_topic_prediction(text)

        try:
            text_processed = self.preprocess_text(text)
            sequence = self.tokenizer.texts_to_sequences([text_processed])
            X = pad_sequences(sequence, maxlen=self.max_sequence_length)

            prediction = self.topic_model.predict(X, verbose=0)
            topic_idx = np.argmax(prediction[0])

            return self.topic_encoder.inverse_transform([topic_idx])[0]
        except Exception as e:
            print(f"Error in topic prediction: {e}")
            return self._simulate_topic_prediction(text)

    def _simulate_intent_prediction(self, text):
        """Simular predicción de intención cuando TensorFlow no está disponible"""
        text_lower = text.lower()

        # Reglas simples para simular clasificación
        if any(word in text_lower for word in ['hola', 'buenos', 'buenas', 'saludos']):
            return "saludo"
        elif any(word in text_lower for word in ['adiós', 'hasta', 'nos vemos', 'chao']):
            return "despedida"
        elif any(word in text_lower for word in ['qué', 'cuándo', 'dónde', 'cómo', 'por qué']):
            return "pregunta"
        elif any(word in text_lower for word in ['enciende', 'apaga', 'reproduce', 'detén']):
            return "comando"
        elif any(word in text_lower for word in ['busca', 'encuentra', 'información']):
            return "busqueda"
        else:
            return "general"

    def _simulate_topic_prediction(self, text):
        """Simular predicción de tema cuando TensorFlow no está disponible"""
        text_lower = text.lower()

        # Reglas simples para simular clasificación
        if any(word in text_lower for word in ['música', 'canción', 'artista']):
            return "musica"
        elif any(word in text_lower for word in ['tiempo', 'clima', 'temperatura']):
            return "clima"
        elif any(word in text_lower for word in ['noticias', 'actualidad', 'periódico']):
            return "noticias"
        elif any(word in text_lower for word in ['receta', 'comida', 'cocinar']):
            return "cocina"
        else:
            return "general"

    def get_confidence(self, text):
        """Obtener confianza de la clasificación"""
        if not TENSORFLOW_AVAILABLE:
            # Confianza simulada basada en la longitud del texto
            return min(len(text) / 100, 0.95)

        try:
            text_processed = self.preprocess_text(text)

            # Calcular confianza para intención
            X_intent = self.intent_vectorizer.transform([text_processed]).toarray()
            intent_pred = self.intent_model.predict(X_intent, verbose=0)[0]
            intent_confidence = np.max(intent_pred)

            # Calcular confianza para tema
            sequence = self.tokenizer.texts_to_sequences([text_processed])
            X_topic = pad_sequences(sequence, maxlen=self.max_sequence_length)
            topic_pred = self.topic_model.predict(X_topic, verbose=0)[0]
            topic_confidence = np.max(topic_pred)

            # Confianza promedio
            return (intent_confidence + topic_confidence) / 2
        except Exception as e:
            print(f"Error calculating confidence: {e}")
            return min(len(text) / 100, 0.8)