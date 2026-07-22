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
    this.style.opacity = '0.5';
    this.style.pointerEvents = 'none';
    setTimeout(() => {
      this.style.opacity = '';
      this.style.pointerEvents = '';
    }, 3000);
  });
});


// ── Table Sort ────────────────────────────────────────────────
(function initTableSort() {
  document.querySelectorAll('th.sortable').forEach(th => {
    // Default score and percentage to descending order (-1) on first click
    let dir = (th.dataset.col === 'score' || th.dataset.col === 'pct') ? -1 : 1;
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

      rows.forEach(r => tbody.appendChild(r));

      table.querySelectorAll('th.sortable').forEach(t => {
        t.textContent = t.textContent.replace(/\s[↑↓↕]$/, '') + ' ↕';
      });
      th.textContent = th.textContent.replace(/\s[↑↓↕]$/, '') + (dir === -1 ? ' ↓' : ' ↑');
      dir *= -1;
    });
  });
})();
