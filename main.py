from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uuid
from pathlib import Path
import tempfile
from typing import List, Optional, Dict, Any

app = FastAPI(title="Portafolio - Francisco Rivera", version="1.0.0")




# Crear directorios si no existen


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
















# ==================== RUTAS DEL SISTEMA DE RECONOCIMIENTO DE VOZ ====================















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















# ==================== RUTAS GENERALES ====================


