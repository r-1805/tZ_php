
(() => {
  const key = 'siteConsentAccepted';
  const root = document.getElementById('cookie-banner');
  if (!root) return;
  if (localStorage.getItem(key) === 'yes') {
    root.remove();
    return;
  }
  const button = root.querySelector('[data-cookie-accept]');
  button?.addEventListener('click', () => {
    localStorage.setItem(key, 'yes');
    root.remove();
  });
})();
