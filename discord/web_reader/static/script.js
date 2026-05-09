/* ==========================================================================
   COSMIC COMIC READER - INTERACTIVE JS LOGIC
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // --- STATE MANAGEMENT ---
    let state = {
        activeThreadId: null,
        comicTitle: '',
        category: '',
        pages: [], // {filename, url, width, height}
        currentPageIndex: 0,
        viewMode: 'webtoon', // 'webtoon' | 'book'
        zoomLevel: 100, // percentage
        sidebarOpen: true,
        history: JSON.parse(localStorage.getItem('comic_reader_history') || '[]')
    };

    // --- DOM ELEMENTS ---
    const threadIdInput = document.getElementById('threadIdInput');
    const loadBtn = document.getElementById('loadBtn');
    const btnText = loadBtn.querySelector('.btn-text');
    const btnLoader = loadBtn.querySelector('.btn-loader');
    
    const landingPage = document.getElementById('landingPage');
    const readerPage = document.getElementById('readerPage');
    const historyGrid = document.getElementById('historyGrid');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    
    const backBtn = document.getElementById('backBtn');
    const comicTitle = document.getElementById('comicTitle');
    const comicCategory = document.getElementById('comicCategory');
    const webtoonModeBtn = document.getElementById('webtoonModeBtn');
    const bookModeBtn = document.getElementById('bookModeBtn');
    
    const sidebarDrawer = document.getElementById('sidebarDrawer');
    const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
    const pageList = document.getElementById('pageList');
    const sidebarCount = document.getElementById('sidebarCount');
    
    const viewerViewport = document.getElementById('viewerViewport');
    const webtoonContainer = document.getElementById('webtoonContainer');
    const bookContainer = document.getElementById('bookContainer');
    const activeBookImage = document.getElementById('activeBookImage');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    
    const zoomInBtn = document.getElementById('zoomInBtn');
    const zoomOutBtn = document.getElementById('zoomOutBtn');
    const zoomIndicator = document.getElementById('zoomIndicator');
    const fitWidthBtn = document.getElementById('fitWidthBtn');
    const fitHeightBtn = document.getElementById('fitHeightBtn');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    const toastContainer = document.getElementById('toastContainer');

    // --- INITIALIZATION ---
    renderHistory();

    // --- EVENT LISTENERS ---
    loadBtn.addEventListener('click', () => loadComicFromInput());
    threadIdInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadComicFromInput();
    });

    backBtn.addEventListener('click', () => {
        readerPage.style.display = 'none';
        landingPage.style.display = 'flex';
        state.activeThreadId = null;
        renderHistory();
    });

    webtoonModeBtn.addEventListener('click', () => setViewMode('webtoon'));
    bookModeBtn.addEventListener('click', () => setViewMode('book'));
    toggleSidebarBtn.addEventListener('click', toggleSidebar);
    
    prevPageBtn.addEventListener('click', () => navigateBookPage(-1));
    nextPageBtn.addEventListener('click', () => navigateBookPage(1));
    
    zoomInBtn.addEventListener('click', () => adjustZoom(10));
    zoomOutBtn.addEventListener('click', () => adjustZoom(-10));
    fitWidthBtn.addEventListener('click', () => setFitMode('width'));
    fitHeightBtn.addEventListener('click', () => setFitMode('height'));
    fullscreenBtn.addEventListener('click', toggleFullscreen);
    
    clearHistoryBtn.addEventListener('click', clearAllHistory);

    // Keyboard Navigation
    document.addEventListener('keydown', (e) => {
        if (state.activeThreadId === null) return;
        
        if (state.viewMode === 'book') {
            if (e.key === 'ArrowLeft') navigateBookPage(-1);
            if (e.key === 'ArrowRight' || e.key === ' ') {
                e.preventDefault();
                navigateBookPage(1);
            }
        } else {
            // Webtoon scroll keyboard helpers
            if (e.key === 'ArrowUp') viewerViewport.scrollBy({ top: -100, behavior: 'smooth' });
            if (e.key === 'ArrowDown') viewerViewport.scrollBy({ top: 100, behavior: 'smooth' });
        }
    });

    // Handle scroll inside Webtoon viewport to update progress and active sidebar thumbnail
    viewerViewport.addEventListener('scroll', throttle(handleWebtoonScroll, 100));

    // --- CORE FUNCTIONS ---

    // Load Comic from Input Box
    function loadComicFromInput() {
        const id = threadIdInput.value.trim();
        if (!id) {
            showToast('Silakan masukkan ID Thread Discord Terlebih Dahulu!', 'error');
            return;
        }
        if (isNaN(id)) {
            showToast('ID Thread harus berupa angka/numeric!', 'error');
            return;
        }
        fetchComicData(id);
    }

    // Fetch dynamic URLs from Backend API
    async function fetchComicData(threadId) {
        setLoadingState(true);
        try {
            const response = await fetch(`/api/comic/${threadId}`);
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.detail || 'Gagal memuat komik dari Discord.');
            }

            if (data.pages.length === 0) {
                throw new Error('Tidak ditemukan file gambar komik di dalam Thread tersebut!');
            }

            // Update State
            state.activeThreadId = threadId;
            state.comicTitle = data.title;
            state.category = data.parent_category || 'Kategori Umum';
            state.pages = data.pages;
            state.currentPageIndex = 0;

            // Save to History
            addToHistory(threadId, data.title, state.category, data.pages.length);

            // Display UI
            initReaderUI();
            showToast(`Berhasil memuat ${data.pages.length} halaman komik!`, 'success');
        } catch (error) {
            showToast(error.message, 'error');
            console.error(error);
        } finally {
            setLoadingState(false);
        }
    }

    // Set Loading state on Header button
    function setLoadingState(isLoading) {
        if (isLoading) {
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
            loadBtn.disabled = true;
        } else {
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
            loadBtn.disabled = false;
        }
    }

    // Initialize Reader Workspace with active state
    function initReaderUI() {
        landingPage.style.display = 'none';
        readerPage.style.display = 'flex';

        comicTitle.textContent = state.comicTitle;
        comicCategory.textContent = state.category;
        sidebarCount.textContent = `${state.pages.length} Halaman`;

        // Render Sidebar page items
        renderSidebarPageList();

        // Load content based on mode
        setViewMode(state.viewMode);
    }

    // Render list of thumbnails in sidebar
    function renderSidebarPageList() {
        pageList.innerHTML = '';
        state.pages.forEach((page, index) => {
            const thumbItem = document.createElement('div');
            thumbItem.className = `thumb-item ${index === state.currentPageIndex ? 'active' : ''}`;
            thumbItem.dataset.index = index;
            
            thumbItem.innerHTML = `
                <div class="thumb-preview">
                    <img src="${page.url}" alt="Thumbnail ${index + 1}" loading="lazy">
                </div>
                <div class="thumb-info">
                    <div class="thumb-num">Halaman ${index + 1}</div>
                    <div class="thumb-name" style="font-size: 0.75rem; color: var(--text-muted); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${page.filename}</div>
                </div>
            `;
            
            thumbItem.addEventListener('click', () => jumpToPage(index));
            pageList.appendChild(thumbItem);
        });
    }

    // Set View Mode (Webtoon / Book)
    function setViewMode(mode) {
        state.viewMode = mode;
        if (mode === 'webtoon') {
            webtoonModeBtn.classList.add('active');
            bookModeBtn.classList.remove('active');
            webtoonContainer.style.display = 'flex';
            bookContainer.style.display = 'none';
            
            // Build continuous webtoon images
            renderWebtoonImages();
            
            // Scroll to the active page
            setTimeout(() => jumpToPage(state.currentPageIndex, false), 100);
        } else {
            bookModeBtn.classList.add('active');
            webtoonModeBtn.classList.remove('active');
            webtoonContainer.style.display = 'none';
            bookContainer.style.display = 'flex';
            
            // Update single page image
            updateBookPage();
        }
    }

    // Render Webtoon continuous scroll images
    function renderWebtoonImages() {
        webtoonContainer.innerHTML = '';
        state.pages.forEach((page, index) => {
            const img = document.createElement('img');
            img.src = page.url;
            img.alt = `Halaman ${index + 1}`;
            img.className = 'webtoon-page';
            img.id = `webtoon-page-${index}`;
            img.loading = 'lazy';
            
            // Preserve aspect ratio while loading
            if (page.width && page.height) {
                img.style.aspectRatio = `${page.width} / ${page.height}`;
            }
            
            webtoonContainer.appendChild(img);
        });
        applyZoom();
    }

    // Update single page in Book Mode
    function updateBookPage() {
        if (state.pages.length === 0) return;
        const page = state.pages[state.currentPageIndex];
        
        activeBookImage.src = page.url;
        activeBookImage.alt = `Halaman ${state.currentPageIndex + 1}`;
        
        // Highlight active thumbnail in sidebar and scroll it into view
        updateActiveSidebarItem();
        
        // Update progress indicators
        updateProgress();
    }

    // Navigate to page in Book Mode
    function navigateBookPage(direction) {
        const targetIndex = state.currentPageIndex + direction;
        if (targetIndex >= 0 && targetIndex < state.pages.length) {
            state.currentPageIndex = targetIndex;
            updateBookPage();
        } else if (targetIndex < 0) {
            showToast('Ini adalah halaman pertama!', 'success');
        } else {
            showToast('Kamu sudah sampai di halaman terakhir!', 'success');
        }
    }

    // Jump directly to specific page
    function jumpToPage(index, smoothScroll = true) {
        state.currentPageIndex = index;
        
        if (state.viewMode === 'webtoon') {
            const targetImg = document.getElementById(`webtoon-page-${index}`);
            if (targetImg) {
                targetImg.scrollIntoView({ behavior: smoothScroll ? 'smooth' : 'auto', block: 'start' });
            }
        } else {
            updateBookPage();
        }
        updateActiveSidebarItem();
    }

    // Update sidebar highlighted thumbnail
    function updateActiveSidebarItem() {
        const items = pageList.querySelectorAll('.thumb-item');
        items.forEach((item, index) => {
            if (index === state.currentPageIndex) {
                item.classList.add('active');
                item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                item.classList.remove('active');
            }
        });
    }

    // Handle webtoon mode scroll event to identify current active page
    function handleWebtoonScroll() {
        if (state.viewMode !== 'webtoon' || state.pages.length === 0) return;

        const pages = webtoonContainer.querySelectorAll('.webtoon-page');
        const viewportTop = viewerViewport.scrollTop;
        const viewportHeight = viewerViewport.clientHeight;
        const halfViewport = viewportTop + (viewportHeight / 3);

        let currentActive = 0;
        
        pages.forEach((page, index) => {
            const pageTop = page.offsetTop;
            if (pageTop <= halfViewport) {
                currentActive = index;
            }
        });

        if (state.currentPageIndex !== currentActive) {
            state.currentPageIndex = currentActive;
            updateActiveSidebarItem();
            updateProgress();
        }
    }

    // Update Progress Bar & Text
    function updateProgress() {
        const total = state.pages.length;
        const current = state.currentPageIndex + 1;
        progressText.textContent = `Halaman ${current} / ${total}`;
        
        const percent = (current / total) * 100;
        progressBar.style.width = `${percent}%`;
    }

    // Toggle Sidebar Drawer open/collapsed
    function toggleSidebar() {
        state.sidebarOpen = !state.sidebarOpen;
        if (state.sidebarOpen) {
            sidebarDrawer.classList.remove('collapsed');
            toggleSidebarBtn.classList.add('active');
        } else {
            sidebarDrawer.classList.add('collapsed');
            toggleSidebarBtn.classList.remove('active');
        }
    }

    // Adjust Zoom In/Out
    function adjustZoom(amount) {
        state.zoomLevel = Math.max(30, Math.min(200, state.zoomLevel + amount));
        zoomIndicator.textContent = `${state.zoomLevel}%`;
        applyZoom();
    }

    // Apply active Zoom Level
    function applyZoom() {
        if (state.viewMode === 'webtoon') {
            webtoonContainer.style.maxWidth = `${800 * (state.zoomLevel / 100)}px`;
        } else {
            activeBookImage.style.transform = `scale(${state.zoomLevel / 100})`;
        }
    }

    // Set Fit width / Fit height modes
    function setFitMode(mode) {
        if (mode === 'width') {
            fitWidthBtn.classList.add('active');
            fitHeightBtn.classList.remove('active');
            
            if (state.viewMode === 'book') {
                activeBookImage.className = 'book-image fit-width';
                activeBookImage.style.transform = 'none';
                state.zoomLevel = 100;
                zoomIndicator.textContent = '100%';
            } else {
                webtoonContainer.style.maxWidth = '100%';
                state.zoomLevel = 150;
                zoomIndicator.textContent = 'Fit';
            }
        } else {
            fitHeightBtn.classList.add('active');
            fitWidthBtn.classList.remove('active');
            
            if (state.viewMode === 'book') {
                activeBookImage.className = 'book-image fit-height';
                activeBookImage.style.transform = 'none';
                state.zoomLevel = 100;
                zoomIndicator.textContent = '100%';
            } else {
                webtoonContainer.style.maxWidth = '600px';
                state.zoomLevel = 80;
                zoomIndicator.textContent = 'Compact';
            }
        }
    }

    // Fullscreen support
    function toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen()
                .then(() => {
                    fullscreenBtn.classList.add('active');
                    showToast('Masuk Mode Layar Penuh', 'success');
                })
                .catch(err => {
                    showToast(`Gagal mengaktifkan Fullscreen: ${err.message}`, 'error');
                });
        } else {
            document.exitFullscreen();
            fullscreenBtn.classList.remove('active');
        }
    }

    // --- RECENTLY READ HISTORY LOGIC ---

    function addToHistory(threadId, title, category, totalPages) {
        // Remove duplicates if exist
        state.history = state.history.filter(item => item.threadId !== threadId);
        
        // Add new item to front
        state.history.unshift({
            threadId,
            title,
            category,
            totalPages,
            timestamp: new Date().toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
        });

        // Limit history to 8 items
        if (state.history.length > 8) state.history.pop();

        localStorage.setItem('comic_reader_history', JSON.stringify(state.history));
    }

    function renderHistory() {
        historyGrid.innerHTML = '';
        if (state.history.length === 0) {
            historyGrid.innerHTML = `
                <div class="empty-history">
                    <div class="empty-icon">📖</div>
                    <p>Belum ada riwayat baca. Masukkan ID Thread Discord di atas untuk memulai!</p>
                </div>
            `;
            clearHistoryBtn.style.display = 'none';
            return;
        }

        clearHistoryBtn.style.display = 'inline-block';

        state.history.forEach(item => {
            const card = document.createElement('div');
            card.className = 'history-card';
            
            card.innerHTML = `
                <span class="card-category">${item.category}</span>
                <h3 class="card-title" title="${item.title}">${item.title}</h3>
                <div class="card-meta">
                    <span>${item.totalPages} Halaman</span>
                    <span>${item.timestamp}</span>
                </div>
                <button class="btn-delete-card" title="Hapus dari Riwayat">
                    <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                </button>
            `;

            // Click card to open comic
            card.addEventListener('click', (e) => {
                if (e.target.closest('.btn-delete-card')) return; // ignore delete click
                threadIdInput.value = item.threadId;
                fetchComicData(item.threadId);
            });

            // Delete single item
            card.querySelector('.btn-delete-card').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteHistoryItem(item.threadId);
            });

            historyGrid.appendChild(card);
        });
    }

    function deleteHistoryItem(threadId) {
        state.history = state.history.filter(item => item.threadId !== threadId);
        localStorage.setItem('comic_reader_history', JSON.stringify(state.history));
        renderHistory();
        showToast('Riwayat berhasil dihapus!', 'success');
    }

    function clearAllHistory() {
        if (confirm('Apakah kamu yakin ingin menghapus semua riwayat baca?')) {
            state.history = [];
            localStorage.removeItem('comic_reader_history');
            renderHistory();
            showToast('Semua riwayat berhasil dihapus!', 'success');
        }
    }

    // --- HELPERS ---

    // Toast Notifications
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? '✨' : '⚠️';
        toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
        
        toastContainer.appendChild(toast);
        
        // Remove toast after animation
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // Throttle helper to reduce scroll performance hitches
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
});
