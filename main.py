from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'message': 'Bienvenido al portafolio de Francisco Rivera',
        'status': 'ok'
    })

@app.route('/health')
def health_check():
    return jsonify({
        'success': True,
        'status': 'running'
    })

if __name__ == '__main__':
    # Ejecutar la aplicación en el puerto proporcionado por Render
    print(f"App corriendo en el puerto {port}")
