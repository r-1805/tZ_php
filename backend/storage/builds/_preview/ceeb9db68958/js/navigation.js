
(() => {
  const currentPath = window.location.pathname.split('/').pop() || 'index.php';
  const links = document.querySelectorAll('.site-nav a');
  for (const link of links) {
    const href = link.getAttribute('href');
    if (href && href.endsWith(currentPath)) {
      link.setAttribute('aria-current', 'page');
    }
  }
})();
