from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
import tempfile

# Para el proyecto de clasificación de imágenes
from inference import ImageClassifier

# Para el proyecto de reconocimiento de voz
from speech_transcriber import SpeechTranscriber
from text_classifier import TextClassifier
from audio_processor import AudioProcessor

# Para el sistema de recomendación
from recomendation_engine import RecommendationEngine

app = Flask(__name__)

# Configuración general
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Configuración para el proyecto de imágenes
IMAGE_UPLOAD_FOLDER = 'static/uploads'
IMAGE_RESULTS_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif'}
app.config['IMAGE_UPLOAD_FOLDER'] = IMAGE_UPLOAD_FOLDER
app.config['IMAGE_RESULTS_FOLDER'] = IMAGE_RESULTS_FOLDER

# Crear directorios si no existen
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_RESULTS_FOLDER, exist_ok=True)
os.makedirs('models', exist_ok=True)
os.makedirs('data/audio_samples', exist_ok=True)

# Inicializar componentes
classifier = ImageClassifier()
transcriber = SpeechTranscriber()
text_classifier = TextClassifier()
audio_processor = AudioProcessor()
recommendation_engine = RecommendationEngine()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_files(file_paths):
    """Limpiar archivos temporales"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path) and file_path != app.config['UPLOAD_FOLDER']:
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up {file_path}: {e}")


# ==================== RUTAS DEL PORTAFOLIO ====================

@app.route('/')
def index():
    profile_data = {
        'name': 'Francisco Rivera',
        'title': 'Developer',
        'subtitle': 'Bachelor of Science in Systems Engineering',
        'email': 'franko19rp@gmail.com',
        'github': 'https://github.com/FranKo19Rp1997',
        'linkedin': 'www.linkedin.com/in/juan-francisco-rivera-perez-64b05932a',

        'about': (
        "Developer and Systems Engineering student passionate about creating robust and scalable software "
        "solutions. Experienced in building and integrating APIs, developing backend services "
        "and working with containerized environments using Docker. I thrive in collaborative teams that embrace "
        "innovation, continuous improvement, and clean code practices."
        ),
        'experience': [
            {
                'company': 'Freelance Project – Hotel Management System',
                'position': 'Full Stack Developer (Freelance)',
                'period': 'February 2024 – August 2024',
                'description': [
                    'Collaborated with a small team to develop a web-based hotel management system tailored for a local client',
                    'Implemented frontend components using React, focusing on user experience and responsiveness',
                    'Developed backend services with Node.js and Express, handling booking logic and user authentication',
                    'Designed and optimized a MySQL database for managing reservations, clients, and room availability'
                ],
                'icon': 'laptop-code'
            },
            {
                'company': 'IT Department - Municipal Cadastre, Bolivia',
                'position': 'Software Development Intern',
                'period': 'August 2024 - January 2025',
                'description': [
                    'Development and maintenance of internal systems for cadastral management',
                    'Developed web interfaces using Angular and React for geographic data visualization',
                    'Implemented backend functionalities with C# (.NET) and Python (Flask)'
                ],
                'icon': 'building'
            },
            {
                'company': 'Command, Control, Computing and Communications Center (C4)',
                'position': 'Software Development Intern',
                'period': 'February 2025 – August 2025',
                'description': [
                    'Designed and developed reusable components in Angular to build modular pages',
                    'Implemented UI components integrated with Laravel + Filament PHP',
                    'Standardized component patterns improving maintainability and consistency',
                    'Collaborated on backoffice development and Angular-Laravel integration'
                ],
                'icon': 'cogs'
            },

        ],

        'education': {
            'institution': 'Franz Tamayo University, Bolivia',
            'degree': 'Systems Engineering',
            'period': 'January 2021 - July 2025',
            'icon': 'graduation-cap'
        },

        'projects': [
            {
                'name': 'AI Image Classification',
                'description': 'Developing a model to detect and classify objects in images',
                'technologies': ['Python', 'Pytorch', 'YOLOv8'],
                'icon': 'robot',
                'url': '/image-classifier'
            },
            {
                'name': 'Speech Recognition System',
                'description': 'System that converts audio to text and classifies by topic or intent',
                'technologies': ['Python', 'librosa', 'SpeechRecognition', 'TensorFlow'],
                'icon': 'microphone',
                'url': '/speech-app'
            },
            {
                'name': 'Recommendation System',
                'description': 'Creation of an engine that suggests products or content based on user preferences',
                'technologies': ['Python', 'Pandas', 'Scikit-Learn'],
                'icon': 'chart-line',
                'url': '/recommendation-system'
            }
        ],

        'skills': {
            'languages': ['Typescript', 'JavaScript', 'Python', 'C#', 'PHP'],
            'frameworks': ['PyTorch', 'Scikit-learn', 'React', 'FastAPI', '.NET Core', 'Flask', 'Pandas',
                           'Filament', 'Node.js'],
            'databases': ['MySQL', 'PostgreSQL', 'Firebase', 'InfluxDB', 'MongoDB'],
            'tools': ['Git', 'GitHub', 'REST APIs', 'JWT', 'Docker', 'Grafana']
        },

        'soft_skills': [
            {'name': 'Problem Solving', 'icon': 'puzzle-piece'},
            {'name': 'Attention to Detail', 'icon': 'search'},
            {'name': 'Task Organization', 'icon': 'tasks'},
            {'name': 'Effective Communication', 'icon': 'comments'},
            {'name': 'Analytical Thinking', 'icon': 'brain'},
            {'name': 'Following Standards', 'icon': 'clipboard-check'}
        ],

        'languages': [
            {'name': 'Spanish', 'level': 'Native', 'percentage': 100},
            {'name': 'English', 'level': 'C2 (Advanced)', 'percentage': 95}
        ]
    }

    return render_template('index.html', data=profile_data)


# ==================== RUTAS DEL CLASIFICADOR DE IMÁGENES ====================

@app.route('/image-classifier')
def image_classifier():
    return render_template('project3.html')


@app.route('/classify', methods=['POST'])
def classify_image():
    """Endpoint para clasificar una imagen"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})

        if file and allowed_file(file.filename):
            # Generar nombre único para el archivo
            filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
            filepath = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Procesar imagen
            confidence_threshold = float(request.form.get('confidence', 0.5))
            results = classifier.classify_image(filepath, confidence_threshold)

            # Guardar imagen con anotaciones
            result_filename = f"result_{filename}"
            result_path = os.path.join(app.config['IMAGE_RESULTS_FOLDER'], result_filename)

            # Visualizar resultados en la imagen
            annotated_image = classifier.visualize_detections(filepath, results, result_path)

            return jsonify({
                'success': True,
                'original_image': f'/static/uploads/{filename}',
                'result_image': f'/static/results/{result_filename}',
                'predictions': results['predictions'],
                'summary': results['summary']
            })

        return jsonify({'success': False, 'error': 'Invalid file type'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/batch_classify', methods=['POST'])
def batch_classify():
    """Endpoint para clasificación por lotes"""
    try:
        files = request.files.getlist('files[]')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': 'No files selected'})

        confidence_threshold = float(request.form.get('confidence', 0.5))
        results = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
                filepath = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Clasificar imagen
                classification_result = classifier.classify_image(filepath, confidence_threshold)

                results.append({
                    'filename': file.filename,
                    'original_image': f'/static/uploads/{filename}',
                    'predictions': classification_result['predictions'],
                    'summary': classification_result['summary']
                })

        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(results)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/model_info')
def get_model_info():
    """Obtener información del modelo"""
    try:
        model_info = classifier.get_model_info()
        return jsonify({'success': True, 'model_info': model_info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/available_models')
def get_available_models():
    """Obtener lista de modelos disponibles"""
    try:
        models = classifier.get_available_models()
        return jsonify({'success': True, 'models': models})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/switch_model', methods=['POST'])
def switch_model():
    """Cambiar el modelo activo"""
    try:
        data = request.get_json()
        model_name = data.get('model_name')

        if classifier.switch_model(model_name):
            return jsonify({'success': True, 'message': f'Model switched to {model_name}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to switch model'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== RUTAS DEL SISTEMA DE RECONOCIMIENTO DE VOZ ====================

@app.route('/speech-app')
def speech_app():
    template_data = {
        'title': 'Sistema de Reconocimiento de Voz',
        'description': 'Convierte audio a texto y clasifica por tema o intención'
    }
    return render_template('project2.html', data=template_data)


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

            intent = text_classifier.predict_intent(transcription)
            topic = text_classifier.predict_topic(transcription)
            confidence = text_classifier.get_confidence(transcription)

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

            intent = text_classifier.predict_intent(transcription)
            topic = text_classifier.predict_topic(transcription)
            confidence = text_classifier.get_confidence(transcription)

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

        intent = text_classifier.predict_intent(text)
        topic = text_classifier.predict_topic(text)
        confidence = text_classifier.get_confidence(text)

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


# ==================== RUTAS DEL SISTEMA DE RECOMENDACIÓN ====================

@app.route('/recommendation-system')
def recommendation_system():
    return render_template('recommendation_index.html')


@app.route('/recommend', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        preferences = data.get('preferences', {})
        top_n = data.get('top_n', 5)

        if user_id:
            # Obtener recomendaciones basadas en el historial del usuario
            recommendations = recommendation_engine.get_recommendations_for_user(user_id, top_n)
        else:
            # Obtener recomendaciones basadas en preferencias específicas
            recommendations = recommendation_engine.get_recommendations_based_on_preferences(preferences, top_n)

        return jsonify({
            'success': True,
            'recommendations': recommendations
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/products')
def get_products():
    """Endpoint para obtener la lista de productos disponibles"""
    products = recommendation_engine.get_available_products()
    return jsonify({
        'success': True,
        'products': products
    })


@app.route('/users')
def get_users():
    """Endpoint para obtener la lista de usuarios"""
    users = recommendation_engine.get_available_users()
    return jsonify({
        'success': True,
        'users': users
    })


@app.route('/rate', methods=['POST'])
def rate_product():
    """Endpoint para calificar un producto"""
    try:
        data = request.get_json()
        user_id = data['user_id']
        product_id = data['product_id']
        rating = data['rating']

        success = recommendation_engine.add_rating(user_id, product_id, rating)

        return jsonify({
            'success': success,
            'message': 'Rating added successfully' if success else 'Failed to add rating'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== RUTAS GENERALES ====================

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    # Obtener el puerto dinámico asignado por Render (o 5000 si no está disponible)
    port = int(os.environ.get('PORT', 5000))

    # Imprimir detalles en los logs
    print("=" * 50)
    print("Portafolio - Francisco Rivera")
    print("=" * 50)
    print("Proyectos incluidos:")
    print(f"  • Portafolio personal: http://0.0.0.0:{port}")
    print(f"  • Clasificador de imágenes: http://0.0.0.0:{port}/image-classifier")
    print(f"  • Sistema de reconocimiento de voz: http://0.0.0.0:{port}/speech-app")
    print(f"  • Sistema de recomendación: http://0.0.0.0:{port}/recommendation-system")
    print("=" * 50)

    # Iniciar la aplicación Flask
    app.run(host='0.0.0.0', port=port)
