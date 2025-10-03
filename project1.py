# app.py
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from recomendation_engine import RecommendationEngine
import os

app = Flask(__name__)

# Inicializar el motor de recomendación
engine = RecommendationEngine()


@app.route('/')
def index():
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
            recommendations = engine.get_recommendations_for_user(user_id, top_n)
        else:
            # Obtener recomendaciones basadas en preferencias específicas
            recommendations = engine.get_recommendations_based_on_preferences(preferences, top_n)

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
    products = engine.get_available_products()
    return jsonify({
        'success': True,
        'products': products
    })


@app.route('/users')
def get_users():
    """Endpoint para obtener la lista de usuarios"""
    users = engine.get_available_users()
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

        success = engine.add_rating(user_id, product_id, rating)

        return jsonify({
            'success': success,
            'message': 'Rating added successfully' if success else 'Failed to add rating'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


if __name__ == '__main__':
    app.run(debug=True, port=5001)