# inference.py
import torch
import cv2
import numpy as np
from ultralytics import YOLO
import os
from pathlib import Path
import json
import glob


class ImageClassifier:
    def __init__(self, model_path=None):
        self.model = None
        self.current_model = None
        self.available_models = {}
        self.load_available_models()

        # Cargar modelo por defecto o el especificado
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self.load_default_model()

    def load_available_models(self):
        """Cargar SOLO modelos .pt locales del proyecto - EXCLUIR YOLO preentrenados"""
        print("Buscando modelos .pt locales en el directorio del proyecto...")

        # Buscar en todo el directorio del proyecto y subdirectorios
        project_root = Path('.')
        pt_files = list(project_root.rglob('*.pt'))

        # También buscar en directorios comunes
        common_dirs = ['models', 'weights', 'runs', 'train', 'yolo']
        for dir_name in common_dirs:
            if os.path.exists(dir_name):
                pt_files.extend(Path(dir_name).rglob('*.pt'))

        # SOLO modelos locales - EXCLUIR modelos preentrenados de YOLO
        for pt_file in pt_files:
            try:
                model_name = pt_file.stem
                model_path = str(pt_file)

                # Verificar que el archivo no esté corrupto
                file_size = os.path.getsize(model_path)
                if file_size > 1000:  # Mínimo 1KB para ser un modelo válido
                    # EXCLUIR modelos preentrenados estándar de YOLO
                    if not self._is_pretrained_yolo_model(model_name):
                        self.available_models[model_name] = model_path
                        print(f"✓ Modelo local encontrado: {model_name} ({file_size / 1024 / 1024:.1f} MB)")
                    else:
                        print(f"✗ Modelo preentrenado excluido: {model_name}")
                else:
                    print(f"✗ Archivo muy pequeño, posiblemente corrupto: {model_name}")

            except Exception as e:
                print(f"✗ Error cargando {pt_file}: {e}")

        if not self.available_models:
            print("⚠ No se encontraron modelos .pt locales en el proyecto")
            # Forzar la descarga de YOLOv8n como último recurso
            try:
                print("📥 Descargando YOLOv8n como modelo base...")
                self.available_models['yolov8n'] = 'yolov8nano.pt'
            except Exception as e:
                print(f"❌ Error descargando modelo base: {e}")
        else:
            print(f"✅ Se encontraron {len(self.available_models)} modelos locales")

    def _is_pretrained_yolo_model(self, model_name):
        """Verificar si es un modelo preentrenado estándar de YOLO"""
        pretrained_models = {
            'yolov8n', 'yolov8s', 'yolov8m', 'yolov8l', 'yolov8x',
            'yolov5n', 'yolov5s', 'yolov5m', 'yolov5l', 'yolov5x',
            'yolov9c', 'yolov9e', 'yolov9t'
        }
        return model_name in pretrained_models

    def load_default_model(self):
        """Cargar el primer modelo local disponible"""
        try:
            if self.available_models:
                # Cargar el primer modelo local disponible
                first_model_name = list(self.available_models.keys())[0]
                first_model_path = self.available_models[first_model_name]
                self.load_model(first_model_path)
                print(f"✅ Modelo por defecto cargado: {self.current_model}")
            else:
                # Último recurso: cargar YOLOv8n pero NO agregarlo a available_models
                print("⚠ No hay modelos locales, cargando YOLOv8n temporalmente...")
                self.model = YOLO('yolov8nano.pt')
                self.current_model = 'yolov8n-temp'
                print("✅ YOLOv8n cargado como modelo temporal")

        except Exception as e:
            print(f"❌ Error cargando modelo por defecto: {e}")
            raise Exception("No se pudo cargar ningún modelo")

    def load_model(self, model_path):
        """Cargar un modelo específico"""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelo no encontrado: {model_path}")

            self.model = YOLO(model_path)
            self.current_model = Path(model_path).stem

            print(f"✅ Modelo cargado: {self.current_model}")

            # Verificar que el modelo funcione
            test_result = self.model('https://ultralytics.com/images/bus.jpg', verbose=False)
            if test_result and len(test_result) > 0:
                print("✅ Modelo verificado correctamente")
            else:
                print("⚠ Advertencia: El modelo no produjo resultados en prueba básica")

        except Exception as e:
            print(f"❌ Error cargando modelo {model_path}: {e}")
            raise

    def switch_model(self, model_name):
        """Cambiar al modelo especificado"""
        if model_name in self.available_models:
            try:
                model_path = self.available_models[model_name]
                self.load_model(model_path)
                return True
            except Exception as e:
                print(f"❌ Error cambiando al modelo {model_name}: {e}")
                return False
        else:
            print(f"❌ Modelo no disponible: {model_name}")
            return False

    def classify_image(self, image_path, confidence_threshold=0.5):
        """Clasificar objetos en una imagen"""
        try:
            # Verificar que el modelo esté cargado
            if self.model is None:
                return {
                    'success': False,
                    'error': 'No hay modelo cargado. Por favor, carga un modelo primero.'
                }

            # Verificar que la imagen existe
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

            # Realizar detección
            results = self.model(image_path, conf=confidence_threshold, verbose=False)

            # Procesar resultados
            predictions = []
            total_objects = 0

            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Obtener información de la detección
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]

                        # Coordenadas del bounding box
                        x1, y1, x2, y2 = map(int, box.xyxy[0])

                        predictions.append({
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': round(confidence, 3),
                            'bbox': [x1, y1, x2, y2],
                            'area': (x2 - x1) * (y2 - y1)
                        })

                        total_objects += 1

            # Resumen estadístico
            class_counts = {}
            for pred in predictions:
                class_name = pred['class_name']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

            summary = {
                'total_objects': total_objects,
                'class_distribution': class_counts,
                'average_confidence': round(
                    sum(p['confidence'] for p in predictions) / max(len(predictions), 1), 3
                ) if predictions else 0
            }

            return {
                'success': True,
                'predictions': predictions,
                'summary': summary
            }

        except Exception as e:
            print(f"❌ Error durante la clasificación: {e}")
            return {
                'success': False,
                'error': str(e),
                'predictions': [],
                'summary': {}
            }

    def visualize_detections(self, image_path, results, output_path):
        """Visualizar detecciones en la imagen"""
        try:
            # Leer imagen
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("No se pudo leer la imagen")

            # Dibujar bounding boxes y etiquetas
            for prediction in results['predictions']:
                x1, y1, x2, y2 = prediction['bbox']
                class_name = prediction['class_name']
                confidence = prediction['confidence']

                # Color basado en la clase
                color = self._get_color(class_name)

                # Dibujar bounding box
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

                # Dibujar etiqueta
                label = f"{class_name} {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]

                # Fondo para la etiqueta
                cv2.rectangle(
                    image,
                    (x1, y1 - label_size[1] - 10),
                    (x1 + label_size[0], y1),
                    color,
                    -1
                )

                # Texto
                cv2.putText(
                    image,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2
                )

            # Guardar imagen resultante
            cv2.imwrite(output_path, image)
            return True

        except Exception as e:
            print(f"❌ Error visualizando detecciones: {e}")
            return False

    def _get_color(self, class_name):
        """Generar color consistente para cada clase"""
        # Usar hash para generar color consistente
        hash_val = hash(class_name) % 16777215  # 256^3
        return [
            int((hash_val >> 16) & 255),  # R
            int((hash_val >> 8) & 255),  # G
            int(hash_val & 255)  # B
        ]

    def get_model_info(self):
        """Obtener información del modelo actual"""
        if self.model is None:
            return {
                'name': 'No cargado',
                'error': 'No hay modelo cargado',
                'available_models': list(self.available_models.keys())
            }

        try:
            # Información básica del modelo
            model_info = {
                'name': self.current_model,
                'input_shape': getattr(self.model.model, 'img_size', [640, 640]),
                'classes': len(self.model.names) if hasattr(self.model, 'names') else 0,
                'class_names': list(self.model.names.values()) if hasattr(self.model, 'names') else [],
                'model_type': 'YOLO',
                'available_models': list(self.available_models.keys()),
                'is_local_model': self.current_model in self.available_models
            }

            # Información adicional si está disponible
            try:
                if hasattr(self.model, 'model'):
                    model_info['parameters'] = sum(p.numel() for p in self.model.model.parameters())
            except:
                model_info['parameters'] = 'N/A'

            return model_info

        except Exception as e:
            print(f"❌ Error obteniendo información del modelo: {e}")
            return {
                'name': self.current_model,
                'error': str(e),
                'available_models': list(self.available_models.keys())
            }

    def get_available_models(self):
        """Obtener lista de modelos disponibles LOCALES"""
        models_info = []

        for model_name, model_path in self.available_models.items():
            try:
                model_data = {
                    'name': model_name,
                    'path': model_path,
                    'is_local': True,
                    'size': os.path.getsize(model_path) if os.path.exists(model_path) else 'N/A'
                }

                # Convertir tamaño a MB si es posible
                if isinstance(model_data['size'], int):
                    model_data['size_mb'] = round(model_data['size'] / (1024 * 1024), 1)
                else:
                    model_data['size_mb'] = 'N/A'

                models_info.append(model_data)
            except Exception as e:
                print(f"❌ Error obteniendo info del modelo {model_name}: {e}")

        return models_info


# Función de utilidad para probar el clasificador
def test_classifier():
    """Función para probar el clasificador"""
    print("🧪 Probando el clasificador de imágenes...")

    try:
        classifier = ImageClassifier()
        print(f"✅ Clasificador inicializado con modelo: {classifier.current_model}")
        print(f"📊 Modelos locales disponibles: {list(classifier.available_models.keys())}")

        if classifier.available_models:
            # Probar con una imagen de ejemplo si existe
            test_images = ['test.jpg', 'example.jpg', 'sample.jpg', 'demo.jpg']
            for test_img in test_images:
                if os.path.exists(test_img):
                    print(f"🖼️ Probando con imagen: {test_img}")
                    results = classifier.classify_image(test_img)
                    if results['success']:
                        print(f"📈 Objetos detectados: {results['summary']['total_objects']}")
                    else:
                        print(f"❌ Error: {results['error']}")
                    break
            else:
                print("ℹ️ No se encontraron imágenes de prueba")
        else:
            print("⚠ No hay modelos locales disponibles")

    except Exception as e:
        print(f"❌ Error en prueba: {e}")


if __name__ == '__main__':
    test_classifier()