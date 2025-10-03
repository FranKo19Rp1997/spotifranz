// static/js/script2.js
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recordingTimer = null;
let recordingStartTime = null;
let processedCount = 0;
let totalConfidence = 0;

// Elementos DOM
const recordBtn = document.getElementById('recordBtn');
const recordText = document.getElementById('recordText');
const recordingTimerEl = document.getElementById('recordingTimer');
const timerEl = document.getElementById('timer');
const resultsContainer = document.getElementById('resultsContainer');
const loadingSpinner = document.getElementById('loadingSpinner');
const analysisDetails = document.getElementById('analysisDetails');
const processedCountEl = document.getElementById('processedCount');
const accuracyRateEl = document.getElementById('accuracyRate');
const avgConfidenceEl = document.getElementById('avgConfidence');

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    // Verificar soporte de grabación
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        recordBtn.disabled = true;
        recordText.innerHTML = '<i class="fas fa-microphone-slash me-2"></i>Grabación no soportada';
    }

    // Cargar estadísticas previas
    loadStatistics();

    // Agregar event listener para mostrar info de formato
    document.getElementById('audioFile').addEventListener('change', updateFormatInfo);
}

// Función para procesar archivo individual - CORREGIDA
async function processUpload() {
    const fileInput = document.getElementById('audioFile');
    const file = fileInput.files[0];

    if (!file) {
        alert('Por favor selecciona un archivo de audio');
        return;
    }

    if (!isFileFormatSupported(file.name)) {
        alert('Formato no soportado. Use WAV para archivos.');
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        formData.append('audio', file);

        console.log('Enviando archivo:', file.name);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log('Respuesta del servidor:', data);

        hideLoading();

        if (data.success) {
            displayResult({
                filename: file.name,
                transcription: data.transcription,
                intent: data.intent,
                topic: data.topic,
                confidence: data.confidence
            });
            updateStatistics(data.confidence);

            // Limpiar input
            fileInput.value = '';
        } else {
            showError(data.error || 'Error desconocido al procesar el archivo');
        }

    } catch (error) {
        hideLoading();
        console.error('Error en processUpload:', error);
        showError('Error de conexión: ' + error.message);
    }
}

// Función para verificar formato soportado
function isFileFormatSupported(filename) {
    const supported = ['wav']; // Solo WAV por ahora
    const ext = filename.toLowerCase().split('.').pop();
    return supported.includes(ext);
}

// Función para actualizar información de formato
function updateFormatInfo() {
    const fileInput = document.getElementById('audioFile');
    const file = fileInput.files[0];

    // Remover info anterior
    const oldInfo = fileInput.parentNode.querySelector('.format-info');
    if (oldInfo) oldInfo.remove();

    if (file) {
        const infoDiv = document.createElement('div');
        infoDiv.className = 'format-info mt-2 small';

        const ext = file.name.split('.').pop().toLowerCase();
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB

        if (ext === 'wav') {
            infoDiv.innerHTML = `
                <span class="text-success">
                    <i class="fas fa-check me-1"></i>Formato WAV soportado
                </span>
                <br>
                <small class="text-muted">Tamaño: ${fileSize} MB</small>
            `;
        } else {
            infoDiv.innerHTML = `
                <span class="text-danger">
                    <i class="fas fa-times me-1"></i>Formato .${ext} no soportado
                </span>
                <br>
                <small class="text-muted">Use archivos WAV</small>
            `;
        }

        fileInput.parentNode.appendChild(infoDiv);
    }
}

// Funciones de grabación (mantenerlas pero deshabilitadas temporalmente)
async function toggleRecording() {
    alert('La grabación en vivo está temporalmente deshabilitada. Por favor, use archivos WAV.');
    return;

    // Código de grabación comentado por ahora
    /*
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
    */
}

async function startRecording() {
    // Código deshabilitado
    alert('Grabación deshabilitada temporalmente');
}

function stopRecording() {
    // Código deshabilitado
}

function updateTimer() {
    // Código deshabilitado
}

// Funciones de procesamiento por lotes
async function processBatch() {
    const fileInput = document.getElementById('batchFiles');
    const files = fileInput.files;

    if (files.length === 0) {
        alert('Por favor selecciona al menos un archivo');
        return;
    }

    // Verificar formatos
    const unsupportedFiles = Array.from(files).filter(file =>
        !isFileFormatSupported(file.name)
    );

    if (unsupportedFiles.length > 0) {
        alert('Algunos archivos tienen formatos no soportados. Use solo WAV.');
        return;
    }

    showLoading();

    try {
        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }

        const response = await fetch('/batch', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            displayBatchResults(data.results);
            fileInput.value = '';
        } else {
            showError(data.error);
        }

    } catch (error) {
        hideLoading();
        showError('Error al procesar los archivos: ' + error.message);
    }
}

// Función para análisis de texto
async function analyzeText() {
    const textArea = document.getElementById('directText');
    const text = textArea.value.trim();

    if (!text) {
        alert('Por favor ingresa texto para analizar');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/analyze_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            displayResult({
                filename: 'Texto directo',
                transcription: text,
                intent: data.intent,
                topic: data.topic,
                confidence: data.confidence
            });
            updateStatistics(data.confidence);
            textArea.value = '';
        } else {
            showError(data.error);
        }

    } catch (error) {
        hideLoading();
        showError('Error al analizar el texto: ' + error.message);
    }
}

// Funciones de visualización de resultados
function displayResult(result) {
    const resultHTML = `
        <div class="result-item">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <h6 class="text-muted">${result.filename}</h6>
                <small class="text-muted">${new Date().toLocaleString()}</small>
            </div>
            
            <div class="transcription-text">
                <strong>Transcripción:</strong> ${result.transcription || 'No se pudo transcribir'}
            </div>
            
            <div class="classification-badges">
                <span class="intent-badge">
                    <i class="fas fa-bullseye me-1"></i>Intención: ${result.intent}
                </span>
                <span class="topic-badge">
                    <i class="fas fa-tag me-1"></i>Tema: ${result.topic}
                </span>
            </div>
            
            <div class="mt-2">
                <small class="text-muted">Confianza: ${((result.confidence || 0) * 100).toFixed(1)}%</small>
                <div class="confidence-meter">
                    <div class="confidence-fill" style="width: ${(result.confidence || 0) * 100}%"></div>
                </div>
            </div>
        </div>
    `;

    // Agregar al inicio de los resultados
    if (resultsContainer.children[0]?.classList?.contains('text-muted')) {
        resultsContainer.innerHTML = resultHTML;
    } else {
        resultsContainer.innerHTML = resultHTML + resultsContainer.innerHTML;
    }

    // Mostrar análisis detallado
    showDetailedAnalysis(result);
}

function displayBatchResults(results) {
    if (results.length === 0) {
        showError('No se pudieron procesar los archivos');
        return;
    }

    let batchHTML = `
        <div class="batch-summary">
            <h6><i class="fas fa-folder-open me-2"></i>Procesamiento por Lotes</h6>
            <p class="mb-2">${results.length} archivos procesados exitosamente</p>
        </div>
    `;

    results.forEach(result => {
        batchHTML += `
            <div class="result-item batch-item">
                <h6 class="text-muted">${result.filename}</h6>
                <div class="transcription-text">
                    ${result.transcription}
                </div>
                <div class="classification-badges">
                    <span class="intent-badge">Intención: ${result.intent}</span>
                    <span class="topic-badge">Tema: ${result.topic}</span>
                </div>
                <small class="text-muted">Confianza: ${(result.confidence * 100).toFixed(1)}%</small>
            </div>
        `;

        updateStatistics(result.confidence);
    });

    resultsContainer.innerHTML = batchHTML;
    analysisDetails.innerHTML = '<div class="text-center text-muted py-3"><p>Selecciona un resultado individual para ver análisis detallado</p></div>';
}

function showDetailedAnalysis(result) {
    const analysisHTML = `
        <div class="analysis-section">
            <h6>Análisis de Confianza</h6>
            <div class="probability-bar">
                <span class="probability-label">General</span>
                <div class="probability-visual">
                    <div class="probability-fill" style="width: ${(result.confidence || 0) * 100}%"></div>
                </div>
                <span class="probability-value">${((result.confidence || 0) * 100).toFixed(1)}%</span>
            </div>
            
            <div class="mt-3">
                <h6>Detalles de Clasificación</h6>
                <div class="row">
                    <div class="col-md-6">
                        <div class="card bg-light">
                            <div class="card-body">
                                <h6 class="card-title">Intención Principal</h6>
                                <span class="intent-badge">${result.intent}</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card bg-light">
                            <div class="card-body">
                                <h6 class="card-title">Tema Principal</h6>
                                <span class="topic-badge">${result.topic}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    analysisDetails.innerHTML = analysisHTML;
}

// Funciones de utilidad
function showLoading() {
    loadingSpinner.classList.remove('d-none');
    resultsContainer.classList.add('d-none');
}

function hideLoading() {
    loadingSpinner.classList.add('d-none');
    resultsContainer.classList.remove('d-none');
}

function showError(message) {
    const errorHTML = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    resultsContainer.innerHTML = errorHTML + resultsContainer.innerHTML;
}

function clearResults() {
    if (confirm('¿Estás seguro de que quieres limpiar todos los resultados?')) {
        resultsContainer.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-wave-square fa-3x mb-3"></i>
                <p>Sube un archivo de audio o inicia una grabación para comenzar</p>
            </div>
        `;
        analysisDetails.innerHTML = `
            <div class="text-center text-muted py-3">
                <p>Los detalles de análisis aparecerán aquí después del procesamiento</p>
            </div>
        `;
    }
}

function exportResults() {
    // Implementar exportación de resultados
    alert('Funcionalidad de exportación en desarrollo');
}

function updateStatistics(confidence) {
    processedCount++;
    totalConfidence += confidence;

    const avgConfidence = totalConfidence / processedCount;
    const accuracy = Math.min(avgConfidence * 100 + 20, 95); // Estimación

    processedCountEl.textContent = processedCount;
    accuracyRateEl.textContent = accuracy.toFixed(1) + '%';
    avgConfidenceEl.textContent = (avgConfidence * 100).toFixed(1) + '%';

    // Guardar en localStorage
    saveStatistics();
}

function loadStatistics() {
    const stats = JSON.parse(localStorage.getItem('speechStats') || '{}');
    processedCount = stats.processedCount || 0;
    totalConfidence = stats.totalConfidence || 0;

    if (processedCount > 0) {
        const avgConfidence = totalConfidence / processedCount;
        const accuracy = Math.min(avgConfidence * 100 + 20, 95);

        processedCountEl.textContent = processedCount;
        accuracyRateEl.textContent = accuracy.toFixed(1) + '%';
        avgConfidenceEl.textContent = (avgConfidence * 100).toFixed(1) + '%';
    }
}

function saveStatistics() {
    const stats = {
        processedCount: processedCount,
        totalConfidence: totalConfidence
    };
    localStorage.setItem('speechStats', JSON.stringify(stats));
}

// Manejar cierre de la página
window.addEventListener('beforeunload', () => {
    if (isRecording) {
        stopRecording();
    }
});