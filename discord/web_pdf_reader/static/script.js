let currentPdfs = [];
let activePdfIndex = 0;
let currentViewMode = 'pdf'; // 'pdf' | 'text'

// Cache halaman yang sudah dimuat
// Map: pdfId -> { pageNum: { image, text } }
const loadedPagesCache = new Map();

// Intersection Observer untuk Lazy Loading halaman saat scroll
let pageObserver = null;

// DOM Elements
const form = document.getElementById('fetch-form');
const discordInput = document.getElementById('discord-input');
const btnSubmit = document.getElementById('btn-submit');
const submitSpinner = document.getElementById('submit-spinner');
const btnText = btnSubmit.querySelector('.btn-text');

const sidebar = document.getElementById('sidebar');
const fileList = document.getElementById('file-list');
const pdfCountBadge = document.getElementById('pdf-count');
const metaCard = document.getElementById('meta-card');
const metaChannel = document.getElementById('meta-channel');
const metaAuthor = document.getElementById('meta-author');

const toolbar = document.getElementById('viewer-toolbar');
const activeFilename = document.getElementById('active-filename');
const activeSize = document.getElementById('active-size');
const btnViewPdf = document.getElementById('btn-view-pdf');
const btnViewText = document.getElementById('btn-view-text');
const btnDownload = document.getElementById('btn-download');
const btnOpenUrl = document.getElementById('btn-open-url');

const placeholderScreen = document.getElementById('placeholder-screen');
const pdfContainer = document.getElementById('pdf-container');
const textContainer = document.getElementById('text-container');
const textPages = document.getElementById('text-pages');
const statusOverlay = document.getElementById('status-overlay');
const statusText = document.getElementById('status-text');

function formatBytes(bytes) {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showLoading(msg = "Memuat data...") {
    statusText.textContent = msg;
    statusOverlay.classList.remove('hidden');
    submitSpinner.classList.remove('hidden');
    btnText.textContent = 'Memproses...';
    btnSubmit.disabled = true;
}

function hideLoading() {
    statusOverlay.classList.add('hidden');
    submitSpinner.classList.add('hidden');
    btnText.textContent = 'Buka PDF';
    btnSubmit.disabled = false;
}

// Fetch Metadata PDF dari FastAPI (Cepat)
async function loadDiscordPDF(inputVal) {
    showLoading("Menghubungi Discord bot & mengambil daftar dokumen...");
    try {
        let apiUrl = `/api/pdf?link=${encodeURIComponent(inputVal)}`;

        const res = await fetch(apiUrl);
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Gagal mengambil pesan PDF.");
        }

        renderResult(data);
    } catch (err) {
        alert("Error: " + err.message);
    } finally {
        hideLoading();
    }
}

function renderResult(data) {
    currentPdfs = data.pdfs || [];
    if (currentPdfs.length === 0) {
        alert("Tidak ada file PDF pada pesan ini.");
        return;
    }

    metaChannel.textContent = data.channel_name;
    metaAuthor.textContent = data.author;
    metaCard.classList.remove('hidden');

    pdfCountBadge.textContent = `${currentPdfs.length} File`;

    fileList.innerHTML = '';
    currentPdfs.forEach((pdf, index) => {
        const item = document.createElement('div');
        item.className = `file-item ${index === 0 ? 'active' : ''}`;
        item.innerHTML = `
            <div class="file-item-name">${pdf.filename}</div>
            <div class="file-item-meta">
                <span>${formatBytes(pdf.size)}</span>
                <span>${pdf.total_pages || 0} Halaman</span>
            </div>
        `;
        item.addEventListener('click', () => selectPdf(index));
        fileList.appendChild(item);
    });

    selectPdf(0);
}

function selectPdf(index) {
    activePdfIndex = index;
    const pdf = currentPdfs[index];

    const items = fileList.querySelectorAll('.file-item');
    items.forEach((item, idx) => {
        item.classList.toggle('active', idx === index);
    });

    toolbar.classList.remove('hidden');
    placeholderScreen.classList.add('hidden');
    activeFilename.textContent = pdf.filename;
    activeSize.textContent = `${formatBytes(pdf.size)} • ${pdf.total_pages || 0} Hal`;

    btnDownload.href = pdf.url;
    btnOpenUrl.href = pdf.url;

    initPartialView(pdf);
}

function initPartialView(pdf) {
    if (pageObserver) {
        pageObserver.disconnect();
    }

    // Setup Lazy Loader
    pageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const pageElem = entry.target;
                const pageNum = parseInt(pageElem.dataset.pageNumber);
                loadPageContent(pdf, pageNum, pageElem);
                pageObserver.unobserve(pageElem);
            }
        });
    }, {
        rootMargin: '300px 0px' // Pre-load saat user scroll mendekat
    });

    renderPlaceholders(pdf);
}

// Buat kerangka placeholder per halaman (Instant render)
function renderPlaceholders(pdf) {
    pdfContainer.innerHTML = '';
    textPages.innerHTML = '';

    const total = pdf.total_pages || 1;

    for (let i = 1; i <= total; i++) {
        // PDF Canvas Wrapper Placeholder
        const pageWrapper = document.createElement('div');
        pageWrapper.className = 'pdf-page-wrapper loading-skeleton';
        pageWrapper.dataset.pageNumber = i;
        pageWrapper.style.minHeight = '650px';
        pageWrapper.style.width = '100%';
        pageWrapper.style.maxWidth = '750px';
        pageWrapper.innerHTML = `
            <div class="page-loader-placeholder">
                <div class="spinner"></div>
                <span>Memuat Halaman ${i}...</span>
            </div>
        `;
        pdfContainer.appendChild(pageWrapper);
        pageObserver.observe(pageWrapper);

        // Text Page Card Placeholder
        const textCard = document.createElement('div');
        textCard.className = 'text-page-card';
        textCard.id = `text-card-${pdf.id}-${i}`;
        textCard.innerHTML = `
            <div class="text-page-header">Halaman ${i}</div>
            <div class="text-page-content"><i>Memuat teks...</i></div>
        `;
        textPages.appendChild(textCard);
    }

    renderActiveView();
}

// Fetch 1 Halaman Spesifik (Partial Content On-Demand)
async function loadPageContent(pdf, pageNum, targetWrapper) {
    const cacheKey = `${pdf.id}_${pageNum}`;
    
    // Cek cache client
    if (loadedPagesCache.has(cacheKey)) {
        applyPageData(loadedPagesCache.get(cacheKey), targetWrapper, pdf.id);
        return;
    }

    try {
        const url = `/api/pdf/${pdf.id}/page/${pageNum}`;
        const res = await fetch(url);
        const data = await res.json();

        if (res.ok) {
            loadedPagesCache.set(cacheKey, data);
            applyPageData(data, targetWrapper, pdf.id);
        } else {
            targetWrapper.innerHTML = `<div style="padding: 20px; color: var(--danger);">Gagal memuat halaman ${pageNum}: ${data.detail || ''}</div>`;
        }
    } catch (err) {
        console.error(`Error loading page ${pageNum}:`, err);
    }
}

function applyPageData(data, wrapper, pdfId) {
    // 1. Update PDF Visual Image Canvas
    wrapper.classList.remove('loading-skeleton');
    wrapper.style.minHeight = 'auto';
    wrapper.innerHTML = `
        <img 
            src="${data.image}" 
            alt="Halaman ${data.page_number}" 
            style="display: block; width: 100%; height: auto; border-radius: 4px;"
            loading="lazy"
        />
    `;

    // 2. Update Text Card
    const textCard = document.getElementById(`text-card-${pdfId}-${data.page_number}`);
    if (textCard) {
        const contentElem = textCard.querySelector('.text-page-content');
        if (contentElem) {
            contentElem.innerHTML = data.text ? escapeHtml(data.text) : '<i>[Halaman kosong / tidak ada teks]</i>';
        }
    }
}

function renderActiveView() {
    if (currentViewMode === 'pdf') {
        pdfContainer.classList.remove('hidden');
        textContainer.classList.add('hidden');
    } else {
        pdfContainer.classList.add('hidden');
        textContainer.classList.remove('hidden');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event Listeners
form.addEventListener('submit', (e) => {
    e.preventDefault();
    const val = discordInput.value.trim();
    if (val) {
        loadDiscordPDF(val);
    }
});

btnViewPdf.addEventListener('click', () => {
    currentViewMode = 'pdf';
    btnViewPdf.classList.add('active');
    btnViewText.classList.remove('active');
    renderActiveView();
});

btnViewText.addEventListener('click', () => {
    currentViewMode = 'text';
    btnViewText.classList.add('active');
    btnViewPdf.classList.remove('active');
    renderActiveView();
});
