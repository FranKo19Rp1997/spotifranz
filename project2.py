# speech_app.py
from flask import Flask, render_template, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
from speech_transcriber import SpeechTranscriber
from text_classifier import TextClassifier
from audio_processor import AudioProcessor
import tempfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Inicializar componentes
transcriber = SpeechTranscriber()
classifier = TextClassifier()
audio_processor = AudioProcessor()


def cleanup_files(file_paths):
    """Limpiar archivos temporales"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path) and file_path != app.config['UPLOAD_FOLDER']:
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up {file_path}: {e}")


@app.route('/')
def index():
    # Pasar datos básicos para la plantilla del sistema de voz
    template_data = {
        'title': 'Sistema de Reconocimiento de Voz',
        'description': 'Convierte audio a texto y clasifica por tema o intención'
    }
    return render_template('project2.html', data=template_data)


# ... el resto de tus rutas del sistema de voz permanecen igual ...
@app.route('/upload', methods=['POST'])
def upload_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'})

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})

        if not audio_processor.is_audio_format_supported(audio_file.filename):
            return jsonify({
                'success': False,
                'error': f'Formato no soportado. Use: {", ".join(audio_processor.supported_formats)}'
            })

        filename = secure_filename(audio_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
        audio_file.save(filepath)

        processed_audio_path = None
        try:
            processed_audio_path = audio_processor.preprocess_audio(filepath)
            transcription = transcriber.transcribe(processed_audio_path)

            if not transcription:
                return jsonify({'success': False, 'error': 'No se pudo transcribir el audio'})

            intent = classifier.predict_intent(transcription)
            topic = classifier.predict_topic(transcription)
            confidence = classifier.get_confidence(transcription)

            return jsonify({
                'success': True,
                'transcription': transcription,
                'intent': intent,
                'topic': topic,
                'confidence': float(confidence)
            })

        finally:
            files_to_clean = [filepath]
            if processed_audio_path and processed_audio_path != filepath:
                files_to_clean.append(processed_audio_path)
            cleanup_files(files_to_clean)

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/record', methods=['POST'])
def record_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio data provided'})

        audio_file = request.files['audio']

        if not audio_file.filename.lower().endswith('.webm'):
            return jsonify({'success': False, 'error': 'Solo se soporta WebM para grabaciones'})

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_recording.webm")
        audio_file.save(filepath)

        processed_path = None
        try:
            processed_path = audio_processor.preprocess_audio(filepath)
            transcription = transcriber.transcribe(processed_path)

            if not transcription:
                return jsonify({'success': False, 'error': 'No se pudo transcribir el audio'})

            intent = classifier.predict_intent(transcription)
            topic = classifier.predict_topic(transcription)
            confidence = classifier.get_confidence(transcription)

            return jsonify({
                'success': True,
                'transcription': transcription,
                'intent': intent,
                'topic': topic,
                'confidence': float(confidence)
            })

        finally:
            files_to_clean = [filepath]
            if processed_path and processed_path != filepath:
                files_to_clean.append(processed_path)
            cleanup_files(files_to_clean)

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    try:
        data = request.get_json()
        text = data.get('text', '')

        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})

        intent = classifier.predict_intent(text)
        topic = classifier.predict_topic(text)
        confidence = classifier.get_confidence(text)

        return jsonify({
            'success': True,
            'intent': intent,
            'topic': topic,
            'confidence': float(confidence)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/supported_formats')
def supported_formats():
    return jsonify({
        'success': True,
        'formats': audio_processor.supported_formats,
        'note': 'Para grabación en vivo: WebM. Para archivos: WAV'
    })


@app.route('/health')
def health_check():
    return jsonify({
        'success': True,
        'status': 'running',
        'components': {
            'transcriber': 'ready',
            'classifier': 'ready',
            'audio_processor': 'ready'
        }
    })


if __name__ == '__main__':
    os.makedirs('models', exist_ok=True)
    os.makedirs('data/audio_samples', exist_ok=True)

    print("=" * 50)
    print("Sistema de Reconocimiento de Voz")
    print("=" * 50)
    print(f"Formatos soportados: {', '.join(audio_processor.supported_formats)}")
    print("Servidor iniciando en http://localhost:5002")
    print("=" * 50)

    app.run(debug=True, port=5002)