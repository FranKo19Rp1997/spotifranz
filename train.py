# train.py
import os
import yaml
from ultralytics import YOLO
import torch
from pathlib import Path


class ModelTrainer:
    def __init__(self):
        self.models_dir = Path('models/trained_models')
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def prepare_dataset_config(self, data_path, class_names):
        """Preparar configuración del dataset YAML"""
        config = {
            'path': str(data_path),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'nc': len(class_names),
            'names': class_names
        }

        config_path = data_path / 'dataset.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        return config_path

    def train_model(self, dataset_path, model_name='yolov8n', epochs=50, imgsz=640):
        """Entrenar un modelo YOLOv8"""
        try:
            # Cargar modelo preentrenado
            model = YOLO(f'{model_name}.pt')

            # Entrenar el modelo
            results = model.train(
                data=str(dataset_path / 'dataset.yaml'),
                epochs=epochs,
                imgsz=imgsz,
                batch=16,
                patience=10,
                save=True,
                project=str(self.models_dir),
                name=f'{model_name}_custom',
                exist_ok=True
            )

            # Ruta del mejor modelo
            best_model_path = self.models_dir / f'{model_name}_custom' / 'weights' / 'best.pt'

            return {
                'success': True,
                'best_model_path': str(best_model_path),
                'results': {
                    'map50': results.results_dict.get('metrics/mAP50(B)', 0),
                    'map': results.results_dict.get('metrics/mAP50-95(B)', 0),
                    'precision': results.results_dict.get('metrics/precision(B)', 0),
                    'recall': results.results_dict.get('metrics/recall(B)', 0)
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def evaluate_model(self, model_path, dataset_path):
        """Evaluar un modelo entrenado"""
        try:
            model = YOLO(model_path)
            results = model.val(data=str(dataset_path / 'dataset.yaml'))

            return {
                'success': True,
                'metrics': {
                    'map50': results.box.map50,
                    'map': results.box.map,
                    'precision': results.box.mp,
                    'recall': results.box.mr
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Función principal para entrenamiento desde línea de comandos"""
    trainer = ModelTrainer()

    # Ejemplo de uso
    dataset_path = Path('data/datasets/custom')
    class_names = ['class1', 'class2', 'class3']  # Definir tus clases

    # Preparar configuración
    config_path = trainer.prepare_dataset_config(dataset_path, class_names)

    # Entrenar modelo
    results = trainer.train_model(
        dataset_path=dataset_path,
        model_name='yolov8n',
        epochs=100,
        imgsz=640
    )

    print("Training results:", results)


if __name__ == '__main__':
    main()