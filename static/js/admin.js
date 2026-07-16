/**
 * ElevateIQ — Admin JavaScript
 * Modal management, CRUD interactions, table helpers.
 */

// ── Modal Management ────────────────────────────────────────
function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove('open');
  document.body.style.overflow = '';
}

// Close modals on overlay click
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// Close on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
});


// ── Assessment Edit Modal ────────────────────────────────────
function openEditModal(assessment) {
  document.getElementById('edit-title').value        = assessment.title        || '';
  document.getElementById('edit-description').value  = assessment.description  || '';
  document.getElementById('edit-duration').value     = assessment.duration     || 60;
  document.getElementById('edit-pass-pct').value     = assessment.pass_percentage || 60;
  document.getElementById('editForm').action         = `/admin/assessments/${assessment.id}/edit`;
  openModal('editModal');
}

function deleteAssessment(id, title) {
  confirmAction(
    `Delete assessment "<strong>${title}</strong>"?<br><small>All questions and results will be permanently removed.</small>`,
    () => {
      const form = document.getElementById('deleteForm');
      form.action = `/admin/assessments/${id}/delete`;
      form.submit();
    }
  );
}


// ── Table Sorting (client-side) ──────────────────────────────
(function initTableSort() {
  document.querySelectorAll('th.sortable').forEach(th => {
    let dir = 1;
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      const table = th.closest('table');
      if (!table) return;
      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
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

      // Update header arrow indicator
      table.querySelectorAll('th.sortable').forEach(t => {
        t.textContent = t.textContent.replace(' ↑', '').replace(' ↓', '').replace(' ↕', '') + ' ↕';
      });
      th.textContent = th.textContent.replace(' ↕', '') + (dir === -1 ? ' ↑' : ' ↓');
    });
  });
})();


// ── Form validation feedback ─────────────────────────────────
document.querySelectorAll('.auth-form, .modal-form').forEach(form => {
  form.querySelectorAll('input[required], textarea[required], select[required]').forEach(input => {
    input.addEventListener('blur', () => {
      if (!input.value.trim()) {
        input.style.borderColor = 'var(--danger)';
      } else {
        input.style.borderColor = '';
      }
    });
    input.addEventListener('input', () => {
      input.style.borderColor = '';
    });
  });
});
