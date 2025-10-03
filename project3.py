# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
from inference import ImageClassifier
import os
import uuid
from werkzeug.utils import secure_filename
import cv2
import numpy as np

app = Flask(__name__)

# Configuración
UPLOAD_FOLDER = 'static/uploads'
RESULTS_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Crear directorios si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Inicializar el clasificador
classifier = ImageClassifier()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
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
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Procesar imagen
            confidence_threshold = float(request.form.get('confidence', 0.5))
            results = classifier.classify_image(filepath, confidence_threshold)

            # Guardar imagen con anotaciones
            result_filename = f"result_{filename}"
            result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

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
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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


if __name__ == '__main__':
    app.run(debug=True, port=5003)