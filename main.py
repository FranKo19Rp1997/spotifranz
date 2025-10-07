from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uuid
from pathlib import Path
import tempfile
from typing import List, Optional, Dict, Any

# Para el proyecto de clasificación de imágenes
from inference import ImageClassifier

# Para el proyecto de reconocimiento de voz
from speech_transcriber import SpeechTranscriber
from text_classifier import TextClassifier
from audio_processor import AudioProcessor

# Para el sistema de recomendación
from recomendation_engine import RecommendationEngine

app = FastAPI(title="Portafolio - Francisco Rivera", version="1.0.0")

# Configuración general
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = tempfile.gettempdir()

# Configuración para el proyecto de imágenes
IMAGE_UPLOAD_FOLDER = 'static/uploads'
IMAGE_RESULTS_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif'}

# Crear directorios si no existen
Path(IMAGE_UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(IMAGE_RESULTS_FOLDER).mkdir(parents=True, exist_ok=True)
Path('models').mkdir(parents=True, exist_ok=True)
Path('data/audio_samples').mkdir(parents=True, exist_ok=True)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="templates")


# Función personalizada url_for para compatibilidad con Flask
def url_for(request: Request, name: str, **kwargs) -> str:
    """
    Función personalizada que simula url_for de Flask para mantener compatibilidad
    con las plantillas existentes.
    """
    if name == 'static':
        filename = kwargs.get('filename', '')
        return f"/static/{filename}"

    # Mapeo de nombres de rutas de Flask a FastAPI
    route_mapping = {
        'index': '/',
        'image_classifier': '/image-classifier',
        'speech_app': '/speech-app',
        'recommendation_system': '/recommendation-system',
        'classify': '/classify',
        'batch_classify': '/batch_classify',
        'upload': '/upload',
        'record': '/record',
        'analyze_text': '/analyze_text',
        'recommend': '/recommend',
        'rate': '/rate'
    }

    return route_mapping.get(name, f'/{name}')


# Inyectar la función url_for en todos los templates
@app.middleware("http")
async def add_url_for_to_templates(request: Request, call_next):
    response = await call_next(request)
    return response


# Sobrescribir el método TemplateResponse para inyectar url_for
original_template_response = templates.TemplateResponse


def custom_template_response(name: str, context: dict, **kwargs):
    if "request" in context:
        context["url_for"] = lambda endpoint, **params: url_for(context["request"], endpoint, **params)
    return original_template_response(name, context, **kwargs)


templates.TemplateResponse = custom_template_response

# Inicializar componentes
classifier = ImageClassifier()
transcriber = SpeechTranscriber()
text_classifier = TextClassifier()
audio_processor = AudioProcessor()
recommendation_engine = RecommendationEngine()


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_files(file_paths: List[str]) -> None:
    """Limpiar archivos temporales"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path) and file_path != UPLOAD_FOLDER:
                os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up {file_path}: {e}")


# ==================== RUTAS DEL PORTAFOLIO ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
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

    return templates.TemplateResponse("index.html", {"request": request, "data": profile_data})


# ==================== RUTAS DEL CLASIFICADOR DE IMÁGENES ====================

@app.get("/image-classifier", response_class=HTMLResponse)
async def image_classifier(request: Request):
    return templates.TemplateResponse("project3.html", {"request": request})


@app.post("/classify")
async def classify_image(
        file: UploadFile = File(...),
        confidence: float = Form(0.5)
):
    """Endpoint para clasificar una imagen"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        if not allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type")

        # Generar nombre único para el archivo
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(IMAGE_UPLOAD_FOLDER, filename)

        # Guardar archivo
        contents = await file.read()
        with open(filepath, "wb") as f:
            f.write(contents)

        # Procesar imagen
        results = classifier.classify_image(filepath, confidence)

        # Guardar imagen con anotaciones
        result_filename = f"result_{filename}"
        result_path = os.path.join(IMAGE_RESULTS_FOLDER, result_filename)

        # Visualizar resultados en la imagen
        annotated_image = classifier.visualize_detections(filepath, results, result_path)

        return {
            'success': True,
            'original_image': f'/static/uploads/{filename}',
            'result_image': f'/static/results/{result_filename}',
            'predictions': results['predictions'],
            'summary': results['summary']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_classify")
async def batch_classify(
        files: List[UploadFile] = File(...),
        confidence: float = Form(0.5)
):
    """Endpoint para clasificación por lotes"""
    try:
        if not files or not files[0].filename:
            raise HTTPException(status_code=400, detail="No files selected")

        results = []

        for file in files:
            if file.filename and allowed_file(file.filename):
                filename = f"{uuid.uuid4()}_{file.filename}"
                filepath = os.path.join(IMAGE_UPLOAD_FOLDER, filename)

                # Guardar archivo
                contents = await file.read()
                with open(filepath, "wb") as f:
                    f.write(contents)

                # Clasificar imagen
                classification_result = classifier.classify_image(filepath, confidence)

                results.append({
                    'filename': file.filename,
                    'original_image': f'/static/uploads/{filename}',
                    'predictions': classification_result['predictions'],
                    'summary': classification_result['summary']
                })

        return {
            'success': True,
            'results': results,
            'total_processed': len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model_info")
async def get_model_info():
    """Obtener información del modelo"""
    try:
        model_info = classifier.get_model_info()
        return {'success': True, 'model_info': model_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/available_models")
async def get_available_models():
    """Obtener lista de modelos disponibles"""
    try:
        models = classifier.get_available_models()
        return {'success': True, 'models': models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/switch_model")
async def switch_model(data: dict):
    """Cambiar el modelo activo"""
    try:
        model_name = data.get('model_name')

        if classifier.switch_model(model_name):
            return {'success': True, 'message': f'Model switched to {model_name}'}
        else:
            raise HTTPException(status_code=400, detail="Failed to switch model")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RUTAS DEL SISTEMA DE RECONOCIMIENTO DE VOZ ====================

@app.get("/speech-app", response_class=HTMLResponse)
async def speech_app(request: Request):
    template_data = {
        'title': 'Sistema de Reconocimiento de Voz',
        'description': 'Convierte audio a texto y clasifica por tema o intención'
    }
    return templates.TemplateResponse("project2.html", {"request": request, "data": template_data})


@app.post("/upload")
async def upload_audio(audio: UploadFile = File(...)):
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        if not audio_processor.is_audio_format_supported(audio.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Formato no soportado. Use: {', '.join(audio_processor.supported_formats)}"
            )

        filename = audio.filename
        filepath = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")

        # Guardar archivo
        contents = await audio.read()
        with open(filepath, "wb") as f:
            f.write(contents)

        processed_audio_path = None
        try:
            processed_audio_path = audio_processor.preprocess_audio(filepath)
            transcription = transcriber.transcribe(processed_audio_path)

            if not transcription:
                raise HTTPException(status_code=400, detail="No se pudo transcribir el audio")

            intent = text_classifier.predict_intent(transcription)
            topic = text_classifier.predict_topic(transcription)
            confidence = text_classifier.get_confidence(transcription)

            return {
                'success': True,
                'transcription': transcription,
                'intent': intent,
                'topic': topic,
                'confidence': float(confidence)
            }

        finally:
            files_to_clean = [filepath]
            if processed_audio_path and processed_audio_path != filepath:
                files_to_clean.append(processed_audio_path)
            cleanup_files(files_to_clean)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/record")
async def record_audio(audio: UploadFile = File(...)):
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No audio data provided")

        if not audio.filename.lower().endswith('.webm'):
            raise HTTPException(status_code=400, detail="Solo se soporta WebM para grabaciones")

        filepath = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_recording.webm")

        # Guardar archivo
        contents = await audio.read()
        with open(filepath, "wb") as f:
            f.write(contents)

        processed_path = None
        try:
            processed_path = audio_processor.preprocess_audio(filepath)
            transcription = transcriber.transcribe(processed_path)

            if not transcription:
                raise HTTPException(status_code=400, detail="No se pudo transcribir el audio")

            intent = text_classifier.predict_intent(transcription)
            topic = text_classifier.predict_topic(transcription)
            confidence = text_classifier.get_confidence(transcription)

            return {
                'success': True,
                'transcription': transcription,
                'intent': intent,
                'topic': topic,
                'confidence': float(confidence)
            }

        finally:
            files_to_clean = [filepath]
            if processed_path and processed_path != filepath:
                files_to_clean.append(processed_path)
            cleanup_files(files_to_clean)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze_text")
async def analyze_text(data: dict):
    try:
        text = data.get('text', '')

        if not text:
            raise HTTPException(status_code=400, detail="No text provided")

        intent = text_classifier.predict_intent(text)
        topic = text_classifier.predict_topic(text)
        confidence = text_classifier.get_confidence(text)

        return {
            'success': True,
            'intent': intent,
            'topic': topic,
            'confidence': float(confidence)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/supported_formats")
async def supported_formats():
    return {
        'success': True,
        'formats': audio_processor.supported_formats,
        'note': 'Para grabación en vivo: WebM. Para archivos: WAV'
    }


@app.get("/health")
async def health_check():
    return {
        'success': True,
        'status': 'running',
        'components': {
            'transcriber': 'ready',
            'classifier': 'ready',
            'audio_processor': 'ready'
        }
    }


# ==================== RUTAS DEL SISTEMA DE RECOMENDACIÓN ====================

@app.get("/recommendation-system", response_class=HTMLResponse)
async def recommendation_system(request: Request):
    return templates.TemplateResponse("recommendation_index.html", {"request": request})


@app.post("/recommend")
async def get_recommendations(data: dict):
    try:
        user_id = data.get('user_id')
        preferences = data.get('preferences', {})
        top_n = data.get('top_n', 5)

        if user_id:
            # Obtener recomendaciones basadas en el historial del usuario
            recommendations = recommendation_engine.get_recommendations_for_user(user_id, top_n)
        else:
            # Obtener recomendaciones basadas en preferencias específicas
            recommendations = recommendation_engine.get_recommendations_based_on_preferences(preferences, top_n)

        return {
            'success': True,
            'recommendations': recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/products")
async def get_products():
    """Endpoint para obtener la lista de productos disponibles"""
    products = recommendation_engine.get_available_products()
    return {
        'success': True,
        'products': products
    }


@app.get("/users")
async def get_users():
    """Endpoint para obtener la lista de usuarios"""
    users = recommendation_engine.get_available_users()
    return {
        'success': True,
        'users': users
    }


@app.post("/rate")
async def rate_product(data: dict):
    """Endpoint para calificar un producto"""
    try:
        user_id = data['user_id']
        product_id = data['product_id']
        rating = data['rating']

        success = recommendation_engine.add_rating(user_id, product_id, rating)

        return {
            'success': success,
            'message': 'Rating added successfully' if success else 'Failed to add rating'
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== RUTAS GENERALES ====================

@app.get("/favicon.ico")
async def favicon():
    favicon_path = os.path.join("static", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    raise HTTPException(status_code=404, detail="Favicon not found")


if __name__ == "__main__":
    #import uvicorn

    print("=" * 50)
    print("Portafolio - Francisco Rivera")
    print("=" * 50)
    print("Proyectos incluidos:")
    print("  • Portafolio personal: http://localhost:8000")
    print("  • Clasificador de imágenes: http://localhost:8000/image-classifier")
    print("  • Sistema de reconocimiento de voz: http://localhost:8000/speech-app")
    print("  • Sistema de recomendación: http://localhost:8000/recommendation-system")
    print("=" * 50)

    #uvicorn.run(app, host="0.0.0.0", port=8000)