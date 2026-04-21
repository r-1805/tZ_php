
(() => {
  const revealItems = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealItems.length) {
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      }
    }, { threshold: 0.16 });
    for (const item of revealItems) observer.observe(item);
  } else {
    for (const item of revealItems) item.classList.add('is-visible');
  }
  const cards = document.querySelectorAll('.card');
  for (const card of cards) {
    card.addEventListener('mouseenter', () => card.classList.add('card-hover'));
    card.addEventListener('mouseleave', () => card.classList.remove('card-hover'));
  }
})();
