
(() => {
  const cards = document.querySelectorAll('.card');
  for (const card of cards) {
    card.addEventListener('mouseenter', () => card.classList.add('card-hover'));
    card.addEventListener('mouseleave', () => card.classList.remove('card-hover'));
  }
})();
