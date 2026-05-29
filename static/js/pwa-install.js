(function() {
  let deferredPrompt = null;
  const DISMISSED_KEY = 'pwa-install-dismissed';
  const INSTALLED_KEY = 'pwa-installed';

  if (localStorage.getItem(INSTALLED_KEY)) return;

  const dismissed = localStorage.getItem(DISMISSED_KEY);
  if (dismissed && Date.now() - parseInt(dismissed) < 7 * 24 * 60 * 60 * 1000) return;

  function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  }

  if (isStandalone()) return;

  function createBanner() {
    const banner = document.createElement('div');
    banner.id = 'pwa-install-banner';
    banner.setAttribute('role', 'alert');
    banner.innerHTML = `
      <div class="pwa-banner-content">
        <img src="/static/img/icons/icon-72x72.png" alt="" class="pwa-banner-icon">
        <div class="pwa-banner-text">
          <strong>Install Seamless</strong>
          <span>Add to your home screen for quick access</span>
        </div>
        <div class="pwa-banner-actions">
          <button id="pwa-install-btn" class="pwa-banner-install">Install</button>
          <button id="pwa-dismiss-btn" class="pwa-banner-dismiss" aria-label="Dismiss">&times;</button>
        </div>
      </div>
    `;
    document.body.appendChild(banner);

    requestAnimationFrame(function() {
      banner.classList.add('pwa-banner-visible');
    });

    document.getElementById('pwa-install-btn').addEventListener('click', handleInstall);
    document.getElementById('pwa-dismiss-btn').addEventListener('click', handleDismiss);
  }

  function handleInstall() {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function(choice) {
        if (choice.outcome === 'accepted') {
          localStorage.setItem(INSTALLED_KEY, '1');
        }
        removeBanner();
        deferredPrompt = null;
      });
    } else {
      showIOSInstructions();
    }
  }

  function handleDismiss() {
    localStorage.setItem(DISMISSED_KEY, Date.now().toString());
    removeBanner();
  }

  function removeBanner() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
      banner.classList.remove('pwa-banner-visible');
      setTimeout(function() { banner.remove(); }, 300);
    }
  }

  function showIOSInstructions() {
    var modal = document.createElement('div');
    modal.id = 'pwa-ios-modal';
    modal.innerHTML = `
      <div class="pwa-ios-overlay" id="pwa-ios-overlay"></div>
      <div class="pwa-ios-content">
        <h3>Install Seamless</h3>
        <p>To install this app on your device:</p>
        <ol>
          <li>Tap the <strong>Share</strong> button <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle"><path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg></li>
          <li>Scroll down and tap <strong>"Add to Home Screen"</strong></li>
          <li>Tap <strong>"Add"</strong> to confirm</li>
        </ol>
        <button id="pwa-ios-close" class="pwa-banner-install" style="width:100%;margin-top:12px">Got it</button>
      </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('pwa-ios-close').addEventListener('click', function() {
      modal.remove();
      handleDismiss();
    });
    document.getElementById('pwa-ios-overlay').addEventListener('click', function() {
      modal.remove();
    });
  }

  function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  }

  window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
    createBanner();
  });

  window.addEventListener('appinstalled', function() {
    localStorage.setItem(INSTALLED_KEY, '1');
    removeBanner();
  });

  if (isIOS()) {
    window.addEventListener('load', function() {
      setTimeout(createBanner, 2000);
    });
  }
})();
