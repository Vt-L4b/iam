// Lightbox das fotos de outros grupos
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightbox-img');
const lightboxLegenda = document.getElementById('lightbox-legenda');
const lightboxDesc = document.getElementById('lightbox-desc');

function openLightbox(img) {
    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt;
    lightboxLegenda.textContent = img.dataset.legenda;
    lightboxDesc.textContent = img.dataset.description;
    lightbox.classList.remove('hidden');
    lightbox.classList.add('flex');
}

function closeLightbox() {
    lightbox.classList.add('hidden');
    lightbox.classList.remove('flex');
}

document.querySelectorAll('.thumbnail').forEach(card => {
    card.addEventListener('click', () => openLightbox(card.querySelector('img')));
});

document.getElementById('lightbox-close').addEventListener('click', closeLightbox);

// Fecha ao clicar no fundo escuro (fora da caixa branca)
lightbox.addEventListener('click', event => {
    if (event.target === lightbox) closeLightbox();
});

document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeLightbox();
});
