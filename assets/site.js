/* Chankhasi School · small enhancements. The page works fully without this. */
(function () {
  var doc = document.documentElement;

  // Header: settle onto paper once the page scrolls
  var header = document.querySelector('.site-header');
  function onScroll() {
    if (header) header.classList.toggle('scrolled', window.scrollY > 8);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Mobile menu
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  function closeNav() {
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) closeNav();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        closeNav();
        toggle.focus();
      }
    });
    document.addEventListener('click', function (e) {
      if (nav.classList.contains('open') && !e.target.closest('.site-header')) closeNav();
    });
  }

  // Share
  var share = document.querySelector('[data-share]');
  var shareStatus = null;
  if (share) {
    shareStatus = document.createElement('span');
    shareStatus.className = 'sr-only';
    shareStatus.setAttribute('aria-live', 'polite');
    share.parentNode.appendChild(shareStatus);
    share.addEventListener('click', function () {
      var data = {
        title: 'Chankhasi Private School',
        text: 'Chankhasi Private School, a community primary and secondary school by Lake Malawi',
        url: location.href.split('#')[0]
      };
      function showLink() {
        try { window.prompt('Copy this link:', data.url); } catch (e) {}
      }
      function copyLink() {
        if (!navigator.clipboard) { showLink(); return; }
        navigator.clipboard.writeText(data.url).then(function () {
          share.textContent = 'Link copied';
          if (shareStatus) shareStatus.textContent = 'Link copied';
          setTimeout(function () {
            share.textContent = 'Share this page';
            if (shareStatus) shareStatus.textContent = '';
          }, 2400);
        }, showLink);
      }
      if (navigator.share) {
        navigator.share(data).catch(function (err) {
          if (!err || err.name !== 'AbortError') copyLink();
        });
      } else {
        copyLink();
      }
    });
  }

  // Contact form: posts to the endpoint in data-endpoint (e.g. Formspree)
  var form = document.getElementById('contact-form');
  if (form) {
    form.noValidate = true; // our own messages replace the browser's; without JS the browser still validates
    var status = form.querySelector('.form-status');
    var button = form.querySelector('button[type="submit"]');
    function say(text, kind) {
      status.textContent = text;
      status.className = 'form-status ' + kind;
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) {
        var bad = form.querySelector(':invalid');
        say('Please add your name, a valid email and a message.', 'is-error');
        if (bad) bad.focus();
        return;
      }
      var endpoint = form.getAttribute('data-endpoint');
      if (!endpoint) {
        say('This form is not connected yet. It will be before the site goes live.', 'is-note');
        return;
      }
      button.disabled = true;
      button.textContent = 'Sending…';
      fetch(endpoint, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error(r.status);
          form.reset();
          say('Thank you. Your message is on its way, and we will reply as soon as we can.', 'is-ok');
        })
        .catch(function () {
          say('Sorry, that did not send. Please try again in a moment.', 'is-error');
        })
        .then(function () {
          button.disabled = false;
          button.textContent = 'Send message';
        });
    });
  }

  // Footer year
  var year = document.querySelector('[data-year]');
  if (year) year.textContent = new Date().getFullYear();

  // Draft review: toggle highlights, and show each note on hover or tap
  if (!doc.classList.contains('draft')) return;

  var KEY = 'chankhasi-hide-marks';
  var marksBtn = document.querySelector('[data-toggle-marks]');
  function setMarks(hide) {
    doc.classList.toggle('no-marks', hide);
    if (marksBtn) marksBtn.textContent = hide ? 'Show highlights' : 'Hide highlights';
    try { localStorage.setItem(KEY, hide ? '1' : ''); } catch (e) {}
  }
  var hidden = false;
  try { hidden = localStorage.getItem(KEY) === '1'; } catch (e) {}
  setMarks(hidden);
  if (marksBtn) {
    marksBtn.addEventListener('click', function () {
      setMarks(!doc.classList.contains('no-marks'));
    });
  }

  var pop = document.querySelector('.note-pop');
  var current = null;
  function show(el) {
    if (!pop || doc.classList.contains('no-marks')) return;
    var note = el.getAttribute('data-note');
    if (!note) return;
    current = el;
    pop.textContent = note;
    pop.hidden = false;
    var r = el.getBoundingClientRect();
    var w = pop.offsetWidth;
    var left = Math.min(Math.max(12, r.left + window.scrollX), window.scrollX + document.documentElement.clientWidth - w - 12);
    pop.style.left = left + 'px';
    pop.style.top = (r.bottom + window.scrollY + 8) + 'px';
  }
  function hide() {
    if (pop) pop.hidden = true;
    current = null;
  }
  document.addEventListener('mouseover', function (e) {
    var el = e.target.closest && e.target.closest('.tbc');
    if (el && el !== current) show(el);
    else if (!el && current) hide();
  });
  document.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('.tbc');
    if (el && !e.target.closest('a')) { show(el); return; }
    if (!el) hide();
  });
  window.addEventListener('scroll', function () { if (current && !current.matches(':hover')) hide(); }, { passive: true });
})();
