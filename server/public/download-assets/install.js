/* The only script on /download: the browser's install prompt.
 *
 * Kept in its own file so the page needs no inline script and no
 * 'unsafe-inline' in its Content Security Policy.
 */
(function () {
  var standalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    navigator.standalone === true;

  var button = document.getElementById('install-button');
  var status = document.getElementById('install-status');
  var hint = document.getElementById('install-hint');
  if (!button || !status) return;

  function installed() {
    button.hidden = true;
    if (hint) hint.hidden = true;
    status.textContent =
      'Installed - open MLBB Tracker from your home screen or app list.';
    status.hidden = false;
  }

  if (standalone) { installed(); return; }

  var prompt = null;
  window.addEventListener('beforeinstallprompt', function (event) {
    event.preventDefault();
    prompt = event;
    button.hidden = false;
    status.hidden = true;
  });

  button.addEventListener('click', function () {
    if (!prompt) return;
    var current = prompt;
    prompt = null;
    button.hidden = true;
    current.prompt();
    current.userChoice.then(function (choice) {
      if (choice.outcome === 'accepted') {
        status.textContent = 'Installing...';
        status.hidden = false;
      } else {
        status.textContent =
          'Install cancelled - you can install any time from your browser menu.';
        status.hidden = false;
      }
    });
  });

  window.addEventListener('appinstalled', installed);
})();
