/**
 * ElevateIQ — Results Page JavaScript
 * Client-side search highlight, sort enhancement.
 */

'use strict';

// ── Live search highlight ─────────────────────────────────────
(function initSearch() {
  const input = document.getElementById('searchInput');
  if (!input) return;

  input.addEventListener('input', function() {
    const val = this.value.trim().toLowerCase();
    const rows = document.querySelectorAll('#resultsTable tbody tr.result-tr');
    rows.forEach(row => {
      const text = row.innerText.toLowerCase();
      row.style.display = (val === '' || text.includes(val)) ? '' : 'none';
    });
  });

  // Focus search on Ctrl+F within the page (prevent browser's native)
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
      e.preventDefault();
      input.focus();
      input.select();
    }
  });
})();


// ── Export button feedback ────────────────────────────────────
['export-csv', 'export-xlsx'].forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('click', function() {
    const orig = this.textContent.trim();
    this.textContent = '⏳ Preparing…';
    this.style.opacity = '0.7';
    setTimeout(() => {
      this.textContent = orig;
      this.style.opacity = '';
    }, 3000);
  });
});


// ── Table Sort ────────────────────────────────────────────────
(function initTableSort() {
  document.querySelectorAll('th.sortable').forEach(th => {
    let dir = 1;
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
      const table = th.closest('table');
      if (!table) return;
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr.result-tr'));
      const idx = Array.from(th.parentElement.children).indexOf(th);

      rows.sort((a, b) => {
        const av = a.cells[idx]?.innerText.trim() || '';
        const bv = b.cells[idx]?.innerText.trim() || '';
        const an = parseFloat(av.replace(/[%,]/g, ''));
        const bn = parseFloat(bv.replace(/[%,]/g, ''));
        if (!isNaN(an) && !isNaN(bn)) return dir * (an - bn);
        return dir * av.localeCompare(bv);
      });

      dir *= -1;
      rows.forEach(r => tbody.appendChild(r));

      table.querySelectorAll('th.sortable').forEach(t => {
        t.textContent = t.textContent.replace(/\s[↑↓↕]$/, '') + ' ↕';
      });
      th.textContent = th.textContent.replace(/\s[↑↓↕]$/, '') + (dir === -1 ? ' ↑' : ' ↓');
    });
  });
})();
