# recommendation_engine.py
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import MinMaxScaler
import warnings

warnings.filterwarnings('ignore')


class RecommendationEngine:
    def __init__(self):
        self.products_df = None
        self.user_preferences_df = None
        self.user_item_matrix = None
        self.product_similarity_matrix = None
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.svd_model = None
        self.load_data()
        self.prepare_data()

    def load_data(self):
        """Cargar o generar datos de ejemplo"""
        # Generar datos de productos si no existen
        try:
            self.products_df = pd.read_csv('data/products.csv')
            self.user_preferences_df = pd.read_csv('data/user_preferences.csv')
        except FileNotFoundError:
            self.generate_sample_data()

    def generate_sample_data(self):
        """Generar datos de ejemplo para el sistema"""
        import os
        os.makedirs('data', exist_ok=True)

        # Generar productos de ejemplo
        products_data = {
            'product_id': range(1, 51),
            'name': [f'Product {i}' for i in range(1, 51)],
            'category': np.random.choice(['Electronics', 'Books', 'Clothing', 'Home', 'Sports'], 50),
            'price': np.random.uniform(10, 500, 50).round(2),
            'description': [f'This is a great product in category {cat}' for cat in
                            np.random.choice(['Electronics', 'Books', 'Clothing', 'Home', 'Sports'], 50)],
            'tags': [', '.join(np.random.choice(['popular', 'new', 'trending', 'bestseller', 'discounted'],
                                                np.random.randint(2, 4), replace=False))
                     for _ in range(50)],
            'rating': np.random.uniform(3, 5, 50).round(1)
        }

        self.products_df = pd.DataFrame(products_data)

        # Generar preferencias de usuarios
        user_preferences = []
        for user_id in range(1, 21):
            # Cada usuario califica entre 5 y 15 productos
            rated_products = np.random.choice(self.products_df['product_id'],
                                              np.random.randint(5, 16), replace=False)
            for product_id in rated_products:
                # Los ratings tienden a ser más altos para productos de categorías preferidas
                base_rating = np.random.normal(4, 1)
                rating = max(1, min(5, round(base_rating)))
                user_preferences.append({
                    'user_id': user_id,
                    'product_id': product_id,
                    'rating': rating,
                    'timestamp': pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(0, 30))
                })

        self.user_preferences_df = pd.DataFrame(user_preferences)

        # Guardar datos generados
        self.products_df.to_csv('data/products.csv', index=False)
        self.user_preferences_df.to_csv('data/user_preferences.csv', index=False)

    def prepare_data(self):
        """Preparar datos para el modelo de recomendación"""
        # Crear matriz usuario-ítem
        self.user_item_matrix = self.user_preferences_df.pivot(
            index='user_id',
            columns='product_id',
            values='rating'
        ).fillna(0)

        # Preparar características de productos para contenido-based filtering
        self.products_df['content'] = (
                self.products_df['category'] + ' ' +
                self.products_df['description'] + ' ' +
                self.products_df['tags']
        )

        # TF-IDF Vectorizer para características de productos
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.products_df['content'])

        # Matriz de similitud entre productos
        self.product_similarity_matrix = cosine_similarity(self.tfidf_matrix)

        # SVD para collaborative filtering
        self.svd_model = TruncatedSVD(n_components=10)
        self.user_factors = self.svd_model.fit_transform(self.user_item_matrix)
        self.item_factors = self.svd_model.components_.T

    def content_based_recommendations(self, product_ids, top_n=5):
        """Recomendaciones basadas en contenido"""
        similar_products = []

        for product_id in product_ids:
            if product_id not in self.products_df['product_id'].values:
                continue

            idx = self.products_df[self.products_df['product_id'] == product_id].index[0]
            similarity_scores = list(enumerate(self.product_similarity_matrix[idx]))
            similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

            # Obtener productos similares (excluyendo el propio producto)
            similar_indices = [i for i, score in similarity_scores[1:top_n + 1]]
            similar_products.extend(similar_indices)

        # Eliminar duplicados y obtener productos únicos
        similar_products = list(set(similar_products))
        recommendations = self.products_df.iloc[similar_products]

        return recommendations.to_dict('records')

    def collaborative_filtering_recommendations(self, user_id, top_n=5):
        """Recomendaciones basadas en filtrado colaborativo"""
        if user_id not in self.user_item_matrix.index:
            return []

        user_idx = list(self.user_item_matrix.index).index(user_id)
        user_vector = self.user_factors[user_idx]

        # Predecir ratings para todos los productos
        predicted_ratings = np.dot(user_vector, self.item_factors.T)

        # Obtener productos no vistos por el usuario
        user_rated_products = self.user_preferences_df[
            self.user_preferences_df['user_id'] == user_id
            ]['product_id'].values

        all_products = self.products_df['product_id'].values
        unseen_products = [p for p in all_products if p not in user_rated_products]

        # Crear DataFrame con predicciones
        predictions_df = pd.DataFrame({
            'product_id': all_products,
            'predicted_rating': predicted_ratings
        })

        # Filtrar productos no vistos y ordenar por rating predicho
        recommendations = predictions_df[
            predictions_df['product_id'].isin(unseen_products)
        ].nlargest(top_n, 'predicted_rating')

        # Combinar con información de productos
        result = recommendations.merge(
            self.products_df,
            on='product_id',
            how='left'
        )

        return result.to_dict('records')

    def hybrid_recommendations(self, user_id=None, preferences=None, top_n=5):
        """Recomendaciones híbridas combinando múltiples enfoques"""
        recommendations = []

        if user_id and user_id in self.user_item_matrix.index:
            # Collaborative filtering para usuarios existentes
            cf_recs = self.collaborative_filtering_recommendations(user_id, top_n)
            recommendations.extend(cf_recs)

        if preferences:
            # Content-based para preferencias específicas
            liked_categories = preferences.get('categories', [])
            price_range = preferences.get('price_range', [0, 1000])
            min_rating = preferences.get('min_rating', 0)

            # Filtrar productos basados en preferencias
            filtered_products = self.products_df[
                (self.products_df['category'].isin(liked_categories)) &
                (self.products_df['price'] >= price_range[0]) &
                (self.products_df['price'] <= price_range[1]) &
                (self.products_df['rating'] >= min_rating)
                ]

            # Ordenar por rating y precio
            content_recs = filtered_products.sort_values(
                ['rating', 'price'],
                ascending=[False, True]
            ).head(top_n)

            recommendations.extend(content_recs.to_dict('records'))

        # Combinar y eliminar duplicados
        seen_products = set()
        unique_recommendations = []

        for rec in recommendations:
            product_id = rec['product_id']
            if product_id not in seen_products:
                seen_products.add(product_id)
                unique_recommendations.append(rec)

        return unique_recommendations[:top_n]

    def get_recommendations_for_user(self, user_id, top_n=5):
        """Obtener recomendaciones para un usuario específico"""
        return self.hybrid_recommendations(user_id=user_id, top_n=top_n)

    def get_recommendations_based_on_preferences(self, preferences, top_n=5):
        """Obtener recomendaciones basadas en preferencias"""
        return self.hybrid_recommendations(preferences=preferences, top_n=top_n)

    def get_available_products(self):
        """Obtener lista de productos disponibles"""
        return self.products_df.to_dict('records')

    def get_available_users(self):
        """Obtener lista de usuarios disponibles"""
        return self.user_preferences_df['user_id'].unique().tolist()

    def add_rating(self, user_id, product_id, rating):
        """Agregar una nueva calificación"""
        try:
            # Verificar si ya existe la calificación
            existing_rating = self.user_preferences_df[
                (self.user_preferences_df['user_id'] == user_id) &
                (self.user_preferences_df['product_id'] == product_id)
                ]

            if not existing_rating.empty:
                # Actualizar calificación existente
                self.user_preferences_df.loc[
                    (self.user_preferences_df['user_id'] == user_id) &
                    (self.user_preferences_df['product_id'] == product_id),
                    'rating'
                ] = rating
            else:
                # Agregar nueva calificación
                new_rating = {
                    'user_id': user_id,
                    'product_id': product_id,
                    'rating': rating,
                    'timestamp': pd.Timestamp.now()
                }
                self.user_preferences_df = pd.concat([
                    self.user_preferences_df,
                    pd.DataFrame([new_rating])
                ], ignore_index=True)

            # Recalcular modelos
            self.prepare_data()

            # Guardar datos actualizados
            self.user_preferences_df.to_csv('data/user_preferences.csv', index=False)

            return True

        except Exception as e:
            print(f"Error adding rating: {e}")
            return False