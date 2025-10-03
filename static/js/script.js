// static/js/script.js
let currentRating = 0;

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    await loadUsers();
    await loadProducts();
    initializeStarRating();
}

async function loadUsers() {
    try {
        const response = await fetch('/users');
        const data = await response.json();

        if (data.success) {
            const userSelect = document.getElementById('userSelect');
            const ratingUserSelect = document.getElementById('ratingUserSelect');

            userSelect.innerHTML = '<option value="">Select a user...</option>';
            ratingUserSelect.innerHTML = '<option value="">Select user...</option>';

            data.users.forEach(userId => {
                const option = `<option value="${userId}">User ${userId}</option>`;
                userSelect.innerHTML += option;
                ratingUserSelect.innerHTML += option;
            });
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function loadProducts() {
    try {
        const response = await fetch('/products');
        const data = await response.json();

        if (data.success) {
            const productSelect = document.getElementById('productSelect');
            productSelect.innerHTML = '<option value="">Select product...</option>';

            data.products.forEach(product => {
                const option = `<option value="${product.product_id}">${product.name}</option>`;
                productSelect.innerHTML += option;
            });
        }
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

function initializeStarRating() {
    const stars = document.querySelectorAll('.star');
    stars.forEach(star => {
        star.addEventListener('click', function() {
            const rating = parseInt(this.getAttribute('data-rating'));
            setRating(rating);
        });

        star.addEventListener('mouseover', function() {
            const rating = parseInt(this.getAttribute('data-rating'));
            highlightStars(rating);
        });
    });

    document.querySelector('.star-rating').addEventListener('mouseleave', function() {
        highlightStars(currentRating);
    });
}

function setRating(rating) {
    currentRating = rating;
    highlightStars(rating);
}

function highlightStars(rating) {
    const stars = document.querySelectorAll('.star');
    stars.forEach(star => {
        const starRating = parseInt(star.getAttribute('data-rating'));
        if (starRating <= rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

async function getUserRecommendations() {
    const userSelect = document.getElementById('userSelect');
    const userId = userSelect.value;

    if (!userId) {
        alert('Please select a user');
        return;
    }

    await getRecommendations({ user_id: parseInt(userId) });
}

async function getPreferenceRecommendations() {
    const categories = getSelectedCategories();
    const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
    const maxPrice = parseFloat(document.getElementById('maxPrice').value) || 1000;
    const minRating = parseFloat(document.getElementById('minRating').value) || 0;

    const preferences = {
        categories: categories,
        price_range: [minPrice, maxPrice],
        min_rating: minRating
    };

    await getRecommendations({ preferences: preferences });
}

async function getRecommendations(requestData) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const recommendationsContainer = document.getElementById('recommendationsContainer');

    loadingSpinner.classList.remove('d-none');
    recommendationsContainer.innerHTML = '';

    try {
        const response = await fetch('/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();

        if (data.success) {
            displayRecommendations(data.recommendations);
        } else {
            showError('Failed to get recommendations: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        showError('An error occurred while fetching recommendations');
    } finally {
        loadingSpinner.classList.add('d-none');
    }
}

function displayRecommendations(recommendations) {
    const container = document.getElementById('recommendationsContainer');

    if (recommendations.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center text-muted">
                <i class="fas fa-frown fa-3x mb-3"></i>
                <p>No recommendations found. Try adjusting your preferences.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = recommendations.map(product => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card product-card">
                <div class="product-image position-relative">
                    <i class="fas fa-cube"></i>
                    <span class="product-category badge bg-primary">${product.category}</span>
                </div>
                <div class="card-body">
                    <h6 class="card-title">${product.name}</h6>
                    <p class="card-text small text-muted">${product.description}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="product-price">$${product.price}</span>
                        <div class="product-rating">
                            <i class="fas fa-star"></i>
                            <span>${product.rating}</span>
                        </div>
                    </div>
                    <div class="mt-2">
                        ${product.tags.split(', ').map(tag => 
                            `<span class="badge bg-light text-dark me-1">${tag}</span>`
                        ).join('')}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

async function submitRating() {
    const userId = document.getElementById('ratingUserSelect').value;
    const productId = document.getElementById('productSelect').value;

    if (!userId || !productId || currentRating === 0) {
        alert('Please select a user, product, and provide a rating');
        return;
    }

    try {
        const response = await fetch('/rate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: parseInt(userId),
                product_id: parseInt(productId),
                rating: currentRating
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('Rating submitted successfully!');
            // Reset form
            document.getElementById('ratingUserSelect').value = '';
            document.getElementById('productSelect').value = '';
            setRating(0);
        } else {
            alert('Failed to submit rating: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while submitting the rating');
    }
}

function getSelectedCategories() {
    const checkboxes = document.querySelectorAll('.category-checkboxes input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(checkbox => checkbox.value);
}

function showError(message) {
    const container = document.getElementById('recommendationsContainer');
    container.innerHTML = `
        <div class="col-12 text-center text-danger">
            <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
            <p>${message}</p>
        </div>
    `;
}