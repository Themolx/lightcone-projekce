(() => {
  const VIDEO_ICON = 'img[src*="logo_video"]';
  const cache = new Map(); // URL filmu -> Promise<URL videa | null>

  function videoUrl(filmUrl) {
    if (!cache.has(filmUrl)) {
      cache.set(filmUrl, fetch(filmUrl, { credentials: 'include' })
        .then(r => r.text())
        .then(html => {
          const m = html.match(/<video[^>]*src="([^"]+)"/);
          return m ? m[1] : null;
        })
        .catch(() => null));
    }
    return cache.get(filmUrl);
  }

  const projekce = params => PROJEKCE_URL + '?' + new URLSearchParams(params).toString();

  // ---- řádky katalogu s ukázkou ----
  for (const row of document.querySelectorAll('table.catalogue tr')) {
    if (!row.querySelector(VIDEO_ICON)) continue;
    const link = row.querySelector('a[href*="/film-"]');
    const data = row.querySelector('td.catalogue_data');
    const thumbCell = row.querySelector('td.catalogue_miniature');
    if (!link || !data) continue;
    const filmUrl = link.href;
    row.classList.add('lcp-row');

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'lcp-play';
    btn.textContent = '▶ Přehrát ukázku';
    data.appendChild(btn);

    let playerRow = null;
    btn.addEventListener('click', async () => {
      if (playerRow) {
        playerRow.querySelector('video')?.pause();
        playerRow.remove(); playerRow = null;
        btn.textContent = '▶ Přehrát ukázku';
        return;
      }
      btn.textContent = 'Načítám…';
      const src = await videoUrl(filmUrl);
      if (!src) { btn.textContent = 'Ukázka nenalezena'; return; }
      playerRow = document.createElement('tr');
      playerRow.className = 'lcp-player-row';
      const td = document.createElement('td');
      td.colSpan = row.children.length || 2;
      const v = document.createElement('video');
      v.controls = true; v.autoplay = true; v.src = src;
      td.appendChild(v);
      playerRow.appendChild(td);
      row.after(playerRow);
      btn.textContent = '✕ Zavřít ukázku';
    });

    // náhled bez zvuku při najetí na miniaturu
    if (thumbCell) {
      const img = thumbCell.querySelector('img');
      if (!img) continue;
      thumbCell.classList.add('lcp-thumb');
      let timer, vid;
      thumbCell.addEventListener('mouseenter', () => {
        timer = setTimeout(async () => {
          const src = await videoUrl(filmUrl);
          if (!src || !thumbCell.matches(':hover')) return;
          vid = document.createElement('video');
          vid.muted = true; vid.loop = true; vid.playsInline = true;
          vid.src = src + '#t=10';
          vid.style.width = img.offsetWidth + 'px';
          vid.style.height = img.offsetHeight + 'px';
          vid.addEventListener('canplay', () => { thumbCell.classList.add('lcp-hovering'); vid.play().catch(() => {}); }, { once: true });
          thumbCell.appendChild(vid);
        }, 400);
      });
      thumbCell.addEventListener('mouseleave', () => {
        clearTimeout(timer);
        thumbCell.classList.remove('lcp-hovering');
        if (vid) { vid.pause(); vid.removeAttribute('src'); vid.load(); vid.remove(); vid = null; }
      });
    }
  }

  // ---- odkazy do Projekce ----
  const main = document.getElementById('main');
  const bandeau = document.querySelector('#bandeau h1');
  const name = bandeau ? bandeau.textContent.trim() : '';
  const path = location.pathname;

  function banner(text, href) {
    if (!main) return;
    const a = document.createElement('a');
    a.className = 'lcp-banner';
    a.href = href; a.target = '_blank'; a.rel = 'noopener';
    a.innerHTML = '<b>Projekce</b> <span></span>';
    a.querySelector('span').textContent = text;
    main.prepend(a);
  }

  if (/\/filmmaker-\d+/.test(path) && name) {
    // jméno v Projekci je ve tvaru „Jméno PŘÍJMENÍ“, nadpis stránky bývá stejný
    banner('Všechny filmy tohoto filmaře s ukázkou →', projekce({ author: name }));
  } else if (/\/film-\d+/.test(path)) {
    const id = path.match(/\/film-(\d+)/)[1];
    const author = main?.querySelector('a[href*="/filmmaker-"]')?.textContent.trim();
    if (author) banner(`Další filmy: ${author} →`, projekce({ author }));
    if (document.querySelector('#main video')) {
      const a = document.createElement('a');
      a.className = 'lcp-inline';
      a.href = projekce({ film: id }); a.target = '_blank'; a.rel = 'noopener';
      a.textContent = 'Otevřít v Projekci';
      document.querySelector('#main video').after(a);
    }
  } else if (/\/catalogue/.test(path)) {
    const q = document.querySelector('input[name="recherche_catalogue_critere_global"]')?.value;
    banner(q ? `Hledat „${q}“ ve filmech s ukázkou →` : 'Chytré vyhledávání ve filmech s ukázkou →', q ? projekce({ q }) : PROJEKCE_URL);
  }

  // u vyhledávacího pole v hlavičce
  const form = document.querySelector('form[name="recherche_catalogue"]');
  if (form) {
    const a = document.createElement('a');
    a.className = 'lcp-header';
    a.textContent = 'hledat v Projekci';
    a.href = PROJEKCE_URL; a.target = '_blank'; a.rel = 'noopener';
    a.addEventListener('click', () => {
      const v = form.querySelector('input[type="text"]').value.trim();
      if (v) a.href = projekce({ q: v });
    });
    form.after(a);
  }
})();
