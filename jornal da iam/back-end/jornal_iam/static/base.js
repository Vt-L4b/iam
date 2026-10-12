// Menu mobile
const seeMenu = document.getElementById('menu');
const theMenu = document.getElementById('mobile-menu');
const menuOverlay = document.getElementById('menu-overlay');

function openMenu() {
    theMenu.classList.remove('translate-x-full');
    menuOverlay.classList.remove('hidden');
    seeMenu.setAttribute('aria-expanded', 'true');
}

function closeMenu() {
    theMenu.classList.add('translate-x-full');
    menuOverlay.classList.add('hidden');
    seeMenu.setAttribute('aria-expanded', 'false');
}

seeMenu.addEventListener('click', openMenu);
document.getElementById('menu-close').addEventListener('click', closeMenu);
menuOverlay.addEventListener('click', closeMenu);
theMenu.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));

document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeMenu();
});
