// Abre e fecha cada edição (acordeão)
document.querySelectorAll('.edition').forEach(edition => {
    const header = edition.querySelector('.header');
    const content = edition.querySelector('.content');
    const icon = edition.querySelector('.arrow');

    let isOpen = false;

    header.addEventListener('click', () => {
        isOpen = !isOpen;
        header.setAttribute('aria-expanded', isOpen);

        if (isOpen) {
            content.classList.remove('max-h-0');
            content.classList.add('max-h-[1000px]');
            icon.classList.add('rotate-180');
        } else {
            content.classList.add('max-h-0');
            content.classList.remove('max-h-[1000px]');
            icon.classList.remove('rotate-180');
        }
    });
});
