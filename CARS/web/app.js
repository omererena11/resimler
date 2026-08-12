// GitHub Raw URL (kendi repo adresinize göre değiştirin)
const GITHUB_RAW = 'https://raw.githubusercontent.com/omererena11/otomobil-verileri/main';
const BASE_PATH = GITHUB_RAW + '/';
const DATA_URL = BASE_PATH + 'data.json';

// Uygulama durumu
let appData = null;
let activeBrand = null;

// Lightbox durumu
let currentImages = [];
let currentIndex = 0;
let scale = 1;

document.addEventListener('DOMContentLoaded', () => {
    loadData();
});

async function loadData() {
    const contentDiv = document.getElementById('content');
    contentDiv.innerHTML = '<div class="loading">Veriler yükleniyor...</div>';

    try {
        const response = await fetch(DATA_URL);
        if (!response.ok) throw new Error('Veri alınamadı');
        appData = await response.json();
        renderBrands();
        if (appData.brands && appData.brands.length > 0) {
            setActiveBrand(appData.brands[0].id);
        } else {
            contentDiv.innerHTML = '<div class="loading">Henüz marka eklenmemiş.</div>';
        }
    } catch (error) {
        contentDiv.innerHTML = '<div class="loading">Hata oluştu: ' + error.message + '</div>';
        console.error(error);
    }
}

function getImageUrl(relativePath) {
    if (!relativePath) return '';
    // Eğer başında 'data/' varsa veya zaten tam URL ise olduğu gibi döndür
    if (relativePath.startsWith('http') || relativePath.startsWith('data/')) return relativePath;
    return BASE_PATH + relativePath;
}

function renderBrands() {
    const container = document.getElementById('brands-container');
    container.innerHTML = '';

    if (!appData.brands) return;

    const brands = [...appData.brands].sort((a, b) => a.order - b.order);

    brands.forEach(brand => {
        const brandDiv = document.createElement('div');
        brandDiv.className = 'brand-logo';
        brandDiv.dataset.brandId = brand.id;
        const logoSrc = brand.logo ? getImageUrl(brand.logo) : '';
        brandDiv.innerHTML = `
            <div class="logo-circle">
                ${logoSrc ? `<img src="${logoSrc}" alt="${brand.name}" onerror="this.style.display='none'; this.parentElement.innerHTML='🏢'">` : '🏢'}
            </div>
            <span class="brand-name">${brand.name}</span>
        `;
        brandDiv.addEventListener('click', () => setActiveBrand(brand.id));
        container.appendChild(brandDiv);
    });
}

function setActiveBrand(brandId) {
    document.querySelectorAll('.brand-logo').forEach(el => {
        el.classList.remove('active');
        if (el.dataset.brandId === brandId) {
            el.classList.add('active');
            el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
    });
    activeBrand = brandId;
    renderModels(brandId);
}

function renderModels(brandId) {
    const contentDiv = document.getElementById('content');
    const brand = appData.brands.find(b => b.id === brandId);
    if (!brand) {
        contentDiv.innerHTML = '<div class="loading">Marka bulunamadı.</div>';
        return;
    }

    const models = [...brand.models].sort((a, b) => a.order - b.order);
    
    let html = `<div class="brand-section">
        <h2 class="brand-title">${brand.name}</h2>
        <div class="models-row">`;

    if (models.length === 0) {
        html += '<p style="padding: 20px; color: #666;">Henüz model eklenmemiş.</p>';
    } else {
        models.forEach(car => {
            const firstImage = car.images && car.images.length > 0 ? getImageUrl(car.images[0]) : '';
            html += `
            <div class="model-card" data-car-id="${car.id}">
                ${firstImage 
                    ? `<img src="${firstImage}" alt="${car.name}" loading="lazy" onerror="this.parentElement.querySelector('.placeholder-img').style.display='flex'; this.style.display='none';">`
                    : ''}
                <div class="placeholder-img" style="display: ${firstImage ? 'none' : 'flex'};">🚗</div>
                <div class="model-info">
                    <div class="model-name">${car.name}</div>
                    <div class="model-year">${car.year}</div>
                    <div class="model-price">${car.price || 'Fiyat bilgisi yok'}</div>
                </div>
            </div>`;
        });
    }
    html += '</div></div>';
    contentDiv.innerHTML = html;

    // Kartlara tıklama olayı
    document.querySelectorAll('.model-card').forEach(card => {
        card.addEventListener('click', (e) => {
            const carId = card.dataset.carId;
            const car = brand.models.find(m => m.id === carId);
            if (car && car.images && car.images.length > 0) {
                openLightbox(car);
            }
        });
    });
}

/* ========= LIGHTBOX FONKSİYONLARI ========= */
function openLightbox(car) {
    currentImages = car.images.map(img => getImageUrl(img));
    currentIndex = 0;
    scale = 1;
    document.getElementById('lightbox').classList.add('active');
    document.body.style.overflow = 'hidden';
    showImage();
    bindLightboxEvents();
}

function closeLightbox() {
    document.getElementById('lightbox').classList.remove('active');
    document.body.style.overflow = '';
    unbindLightboxEvents();
    scale = 1;
}

function showImage() {
    const content = document.getElementById('lightbox-content');
    content.innerHTML = `<img src="${currentImages[currentIndex]}" alt="Model resmi" id="lightbox-img">`;
    document.getElementById('image-counter').textContent = `${currentIndex + 1} / ${currentImages.length}`;
    
    const img = document.getElementById('lightbox-img');
    if (img) {
        img.style.transform = `scale(${scale})`;
        bindZoomEvents(img);
    }
}

function navigate(direction) {
    currentIndex += direction;
    if (currentIndex < 0) currentIndex = currentImages.length - 1;
    if (currentIndex >= currentImages.length) currentIndex = 0;
    scale = 1;
    showImage();
}

// Zoom (pinch) desteği
function bindZoomEvents(img) {
    let startDistance = 0;
    let startScale = 1;

    img.addEventListener('touchstart', (e) => {
        if (e.touches.length === 2) {
            e.preventDefault();
            startDistance = getDistance(e.touches[0], e.touches[1]);
            startScale = scale;
        }
    }, { passive: false });

    img.addEventListener('touchmove', (e) => {
        if (e.touches.length === 2) {
            e.preventDefault();
            const currentDistance = getDistance(e.touches[0], e.touches[1]);
            scale = Math.min(Math.max(startScale * (currentDistance / startDistance), 1), 4);
            img.style.transform = `scale(${scale})`;
        }
    }, { passive: false });

    // Fare tekerleği ile zoom (masaüstü test için)
    img.addEventListener('wheel', (e) => {
        e.preventDefault();
        scale += e.deltaY * -0.01;
        scale = Math.min(Math.max(scale, 1), 4);
        img.style.transform = `scale(${scale})`;
    });
}

function getDistance(touch1, touch2) {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
}

// Swipe (parmakla kaydırma) desteği
let touchStartX = 0;
let touchStartY = 0;
let touchMoved = false;

function onTouchStart(e) {
    if (e.touches.length === 1) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        touchMoved = false;
    }
}

function onTouchMove(e) {
    if (e.touches.length === 1 && touchStartX !== null) {
        const dx = e.touches[0].clientX - touchStartX;
        const dy = e.touches[0].clientY - touchStartY;
        if (Math.abs(dx) > 10 || Math.abs(dy) > 10) {
            touchMoved = true;
        }
    }
}

function onTouchEnd(e) {
    if (touchMoved && e.changedTouches.length === 1) {
        const dx = e.changedTouches[0].clientX - touchStartX;
        const dy = e.changedTouches[0].clientY - touchStartY;
        if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
            if (dx < 0) navigate(1);
            else navigate(-1);
        }
    }
    touchStartX = null;
    touchStartY = null;
    touchMoved = false;
}

function bindLightboxEvents() {
    document.getElementById('lightbox').addEventListener('touchstart', onTouchStart, { passive: false });
    document.getElementById('lightbox').addEventListener('touchmove', onTouchMove, { passive: false });
    document.getElementById('lightbox').addEventListener('touchend', onTouchEnd);
    document.addEventListener('keydown', onKeyDown);
}

function unbindLightboxEvents() {
    document.getElementById('lightbox').removeEventListener('touchstart', onTouchStart);
    document.getElementById('lightbox').removeEventListener('touchmove', onTouchMove);
    document.getElementById('lightbox').removeEventListener('touchend', onTouchEnd);
    document.removeEventListener('keydown', onKeyDown);
}

function onKeyDown(e) {
    if (e.key === 'ArrowLeft') navigate(-1);
    else if (e.key === 'ArrowRight') navigate(1);
    else if (e.key === 'Escape') closeLightbox();
}

// Lightbox butonları
document.querySelector('.close-btn').addEventListener('click', closeLightbox);
document.querySelector('.prev-btn').addEventListener('click', () => navigate(-1));
document.querySelector('.next-btn').addEventListener('click', () => navigate(1));
// Arka plana tıklayınca kapatma
document.getElementById('lightbox').addEventListener('click', (e) => {
    if (e.target === document.getElementById('lightbox')) closeLightbox();
});