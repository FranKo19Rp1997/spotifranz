// static/js/script.js
let currentResults = null;
let availableModels = [];
let loadingModal = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Inicializando aplicación...");

    // Inicializar el modal de carga inmediatamente
    initializeLoadingModal();

    initializeApp();
});

function initializeLoadingModal() {
    console.log("🔄 Inicializando modal de carga...");
    const loadingModalElement = document.getElementById('loadingModal');
    if (loadingModalElement) {
        loadingModal = new bootstrap.Modal(loadingModalElement, {
            backdrop: 'static',
            keyboard: false
        });
        console.log("✅ Modal de carga inicializado");
    } else {
        console.error("❌ No se encontró el elemento loadingModal");
    }
}

async function initializeApp() {
    try {
        // Cargar modelos locales disponibles primero
        await loadAvailableModels();

        // Luego cargar información del modelo actual
        await loadModelInfo();

        // Configurar event listeners
        setupEventListeners();

        // Configurar drag and drop
        setupDragAndDrop();

        console.log("✅ Aplicación inicializada correctamente");
    } catch (error) {
        console.error("❌ Error en initializeApp:", error);
        showNotification('Error inicializando la aplicación: ' + error.message, 'error');
    }
}

async function loadAvailableModels() {
    console.log("🔍 Cargando modelos disponibles...");

    try {
        showLoading('Buscando modelos locales...');

        const response = await fetch('/available_models');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("📦 Respuesta de /available_models:", data);

        if (data.success) {
            availableModels = data.models;
            console.log(`📊 Se encontraron ${availableModels.length} modelos:`, availableModels);

            if (availableModels.length === 0) {
                showNoModelsMessage();
            } else {
                populateModelSelect(availableModels);
                populateModelsList(availableModels);
            }
        } else {
            throw new Error(data.error || 'Error desconocido en la respuesta');
        }
    } catch (error) {
        console.error('❌ Error cargando modelos disponibles:', error);
        showNotification('Error cargando modelos locales: ' + error.message, 'error');
        showNoModelsMessage();
    } finally {
        // Asegurarnos de que el loading se oculte
        hideLoading();
        console.log("✅ Finalizada la carga de modelos");
    }
}

function showNoModelsMessage() {
    console.log("📭 Mostrando mensaje de 'no hay modelos'");

    const modelSelect = document.getElementById('modelSelect');
    const modelsList = document.getElementById('modelsList');

    if (modelSelect) {
        modelSelect.innerHTML = '<option value="">No se encontraron modelos locales</option>';
    }

    const modelInfoText = document.getElementById('modelInfoText');
    if (modelInfoText) {
        modelInfoText.textContent = 'No hay modelos .pt en el directorio del proyecto';
    }

    if (modelsList) {
        modelsList.innerHTML = `
            <div class="col-12 text-center text-muted py-4">
                <i class="fas fa-folder-open fa-3x mb-3"></i>
                <h5>No se encontraron modelos locales</h5>
                <p>Coloca tus archivos .pt en el directorio del proyecto o en las carpetas:</p>
                <ul class="list-unstyled">
                    <li><code>models/</code></li>
                    <li><code>weights/</code></li>
                    <li><code>runs/</code></li>
                    <li><code>train/</code></li>
                </ul>
            </div>
        `;
    }
}

function populateModelSelect(models) {
    console.log("📝 Poblando selector de modelos con", models.length, "modelos");

    const modelSelect = document.getElementById('modelSelect');
    const modelInfoText = document.getElementById('modelInfoText');

    if (!modelSelect) {
        console.error("❌ No se encontró el elemento modelSelect");
        return;
    }

    modelSelect.innerHTML = '';

    models.forEach(model => {
        const option = createModelOption(model);
        modelSelect.appendChild(option);
    });

    if (modelInfoText) {
        modelInfoText.textContent = `${models.length} modelos locales disponibles`;
    }

    console.log("✅ Selector de modelos poblado correctamente");
}

function createModelOption(model) {
    const option = document.createElement('option');
    option.value = model.name;

    let text = ` ${model.name}`;
    if (model.size_mb && model.size_mb !== 'N/A') {
        text += ` (${model.size_mb} MB)`;
    }

    option.textContent = '💾' + text;
    return option;
}

function populateModelsList(models) {
    console.log("📋 Poblando lista de modelos");

    const modelsList = document.getElementById('modelsList');
    if (!modelsList) {
        console.error("❌ No se encontró el elemento modelsList");
        return;
    }

    const modelsHTML = models.map(model => `
        <div class="col-md-6 col-lg-4 mb-3">
            <div class="card model-card h-100 border-primary">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-0">${model.name}</h6>
                        <span class="badge bg-primary">Local</span>
                    </div>
                    <div class="model-details">
                        <small class="text-muted d-block">
                            <i class="fas fa-hdd me-1"></i>
                            ${model.size_mb && model.size_mb !== 'N/A' ? model.size_mb + ' MB' : 'Tamaño no disponible'}
                        </small>
                        <small class="text-muted d-block text-truncate">
                            <i class="fas fa-folder me-1"></i>
                            ${model.path}
                        </small>
                    </div>
                    <button class="btn btn-sm btn-outline-primary w-100 mt-2" 
                            onclick="switchModel('${model.name}')">
                        <i class="fas fa-play me-1"></i>
                        Usar este modelo
                    </button>
                </div>
            </div>
        </div>
    `).join('');

    modelsList.innerHTML = modelsHTML;
    console.log("✅ Lista de modelos poblada correctamente");
}

function setupEventListeners() {
    console.log("🔧 Configurando event listeners...");

    // Slider de confianza
    const confidenceSlider = document.getElementById('confidenceSlider');
    const confidenceValue = document.getElementById('confidenceValue');

    if (confidenceSlider && confidenceValue) {
        confidenceSlider.addEventListener('input', function() {
            confidenceValue.textContent = this.value;
        });
        console.log("✅ Slider de confianza configurado");
    }

    // Selección de modelo
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.addEventListener('change', function() {
            if (this.value) {
                switchModel(this.value);
            }
        });
        console.log("✅ Selector de modelos configurado");
    }

    // Upload de imagen única
    const imageUpload = document.getElementById('imageUpload');
    if (imageUpload) {
        imageUpload.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                processSingleImage(e.target.files[0]);
            }
        });
        console.log("✅ Upload de imagen configurado");
    }

    console.log("✅ Todos los event listeners configurados");
}

function setupDragAndDrop() {
    console.log("🔧 Configurando drag and drop...");

    const uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) {
        console.error("❌ No se encontró el área de upload");
        return;
    }

    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            processSingleImage(files[0]);
        }
    });

    console.log("✅ Drag and drop configurado");
}

async function loadModelInfo() {
    console.log("🔍 Cargando información del modelo...");

    try {
        const response = await fetch('/model_info');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("📦 Respuesta de /model_info:", data);

        if (data.success) {
            updateModelInfo(data.model_info);
        } else {
            throw new Error(data.error || 'Error desconocido en la respuesta');
        }
    } catch (error) {
        console.error('❌ Error cargando información del modelo:', error);
        showNotification('Error cargando información del modelo: ' + error.message, 'error');
    }
}

function updateModelInfo(modelInfo) {
    console.log("🔄 Actualizando información del modelo:", modelInfo);

    // Actualizar elementos de la interfaz
    const elementsToUpdate = {
        'infoClasses': modelInfo.classes || '-',
        'infoInputSize': modelInfo.input_shape ? `${modelInfo.input_shape[0]}x${modelInfo.input_shape[1]}` : '-',
        'currentModel': modelInfo.name || 'No cargado',
        'infoModelName': modelInfo.name || '-'
    };

    Object.entries(elementsToUpdate).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });

    // Actualizar estado
    const statusElement = document.getElementById('infoStatus');
    if (statusElement) {
        if (modelInfo.name && modelInfo.name !== 'No cargado') {
            statusElement.textContent = 'Listo';
            statusElement.className = 'value text-success';
        } else {
            statusElement.textContent = 'Sin modelo';
            statusElement.className = 'value text-danger';
        }
    }

    // Seleccionar el modelo actual en el dropdown
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect && modelInfo.name) {
        modelSelect.value = modelInfo.name;
    }

    console.log("✅ Información del modelo actualizada");
}

async function switchModel(modelName) {
    console.log(`🔄 Cambiando al modelo: ${modelName}`);

    showLoading(`Cambiando a modelo: ${modelName}`);

    try {
        const response = await fetch('/switch_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ model_name: modelName })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            console.log(`✅ Modelo cambiado correctamente a: ${modelName}`);
            await loadModelInfo();
            showNotification(`Modelo cambiado a: ${modelName}`, 'success');
        } else {
            throw new Error(data.error || 'Error desconocido al cambiar modelo');
        }
    } catch (error) {
        console.error('❌ Error cambiando modelo:', error);
        showNotification('Error cambiando modelo: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function processSingleImage(file) {
    console.log("🖼️ Procesando imagen:", file.name);

    if (!file.type.match('image.*')) {
        showNotification('Por favor selecciona un archivo de imagen válido', 'error');
        return;
    }

    showLoading('Analizando imagen...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('confidence', document.getElementById('confidenceSlider').value);

    try {
        const startTime = performance.now();

        const response = await fetch('/classify', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const endTime = performance.now();
        const processingTime = Math.round(endTime - startTime);

        console.log("📊 Resultados de clasificación:", data);

        if (data.success) {
            displaySingleResult(data, processingTime);
            currentResults = data;
            showNotification('Imagen analizada correctamente', 'success');
        } else {
            throw new Error(data.error || 'Error desconocido en la clasificación');
        }
    } catch (error) {
        console.error('❌ Error procesando imagen:', error);
        showNotification('Error procesando imagen: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function displaySingleResult(data, processingTime) {
    console.log("🎨 Mostrando resultados...");

    const container = document.getElementById('singleImageResults');
    if (!container) {
        console.error("❌ No se encontró el contenedor de resultados");
        return;
    }

    const predictionsHTML = data.predictions.map(pred => `
        <div class="detection-item">
            <span class="detection-class">${pred.class_name}</span>
            <div>
                <span class="detection-confidence">${(pred.confidence * 100).toFixed(1)}%</span>
                <div class="confidence-bar">
                    <div class="confidence-level" style="width: ${pred.confidence * 100}%"></div>
                </div>
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="row fade-in">
            <div class="col-md-6">
                <div class="result-card">
                    <div class="result-image">
                        <img src="${data.original_image}" alt="Original" onerror="this.src='https://via.placeholder.com/400x300?text=Error+loading+image'">
                        <span class="result-badge">Original</span>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="result-card">
                    <div class="result-image">
                        <img src="${data.result_image}" alt="Result" onerror="this.src='https://via.placeholder.com/400x300?text=Error+loading+result'">
                        <span class="result-badge">Detectado</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="row mt-3 fade-in">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-list me-2"></i>
                            Objetos Detectados (${data.predictions.length})
                        </h6>
                    </div>
                    <div class="card-body p-0">
                        <div class="detection-list">
                            ${predictionsHTML.length > 0 ? predictionsHTML : '<div class="text-center py-3 text-muted">No se detectaron objetos</div>'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    console.log("✅ Resultados mostrados correctamente");
}

function showLoading(message) {
    console.log("⏳ Mostrando loading:", message);

    const loadingMessage = document.getElementById('loadingMessage');
    if (loadingMessage) {
        loadingMessage.textContent = message;
    }

    if (loadingModal) {
        loadingModal.show();
    } else {
        console.error("❌ loadingModal no está inicializado, intentando inicializar...");
        initializeLoadingModal();
        if (loadingModal) {
            loadingModal.show();
        }
    }
}

function hideLoading() {
    console.log("✅ Ocultando loading...");

    if (loadingModal) {
        // Usar Bootstrap para ocultar el modal
        loadingModal.hide();

        // Limpieza adicional para asegurar que se cierre completamente
        setTimeout(() => {
            const modalElement = document.getElementById('loadingModal');
            if (modalElement) {
                modalElement.style.display = 'none';
                modalElement.classList.remove('show');
            }

            // Remover backdrop si existe
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                backdrop.remove();
            });

            // Restaurar el scroll del body
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }, 300);
    } else {
        console.error("❌ loadingModal no está inicializado al intentar ocultar");
        // Limpieza de emergencia
        const modalElement = document.getElementById('loadingModal');
        if (modalElement) {
            modalElement.style.display = 'none';
            modalElement.classList.remove('show');
        }

        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            backdrop.remove();
        });

        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }
}

function showNotification(message, type = 'info') {
    console.log(`📢 Mostrando notificación [${type}]:`, message);

    const toastContainer = document.getElementById('toastContainer') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    console.log("📝 Creando contenedor de toasts...");

    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Función de utilidad para debugging y limpieza manual
window.forceHideLoading = function() {
    console.log("🛠️ Forzando ocultación del loading...");
    hideLoading();
};

window.debugApp = function() {
    console.log("🐛 DEBUG INFO:");
    console.log("- availableModels:", availableModels);
    console.log("- currentResults:", currentResults);
    console.log("- loadingModal:", loadingModal);
    console.log("- Modal element:", document.getElementById('loadingModal'));
    console.log("- Backdrops:", document.querySelectorAll('.modal-backdrop'));
};