/**
 * ElevateIQ — Assessment Engine JavaScript
 * Timer · Navigation · Auto-Save · Anti-Cheat · Submission
 */

'use strict';

// ── State ────────────────────────────────────────────────────
let currentQuestion = 0;
let answers = {};          // { questionId: 'A'/'B'/'C'/'D'/null }
let violations = INITIAL_VIOLATIONS;
let timerInterval = null;
let secondsRemaining = 0;
let saveDebounceTimers = {};
let isSubmitting = false;

const LS_KEY_TIMER   = `eq_timer_${SUBMISSION_ID}`;
const LS_KEY_ANSWERS = `eq_answers_${SUBMISSION_ID}`;

// ── Initialization ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (!QUESTIONS || QUESTIONS.length === 0) {
    document.getElementById('questionContent').innerHTML =
      '<p style="color:var(--danger);text-align:center;padding:40px">No questions available.</p>';
    return;
  }

  // Restore saved answers from localStorage, then merge with server-saved
  const lsAnswers = JSON.parse(localStorage.getItem(LS_KEY_ANSWERS) || '{}');
  answers = { ...lsAnswers };

  // Merge server-side saved answers (server is authoritative)
  Object.entries(SAVED_ANSWERS).forEach(([qid, opt]) => {
    if (opt) answers[parseInt(qid)] = opt;
  });

  // Initialize violation counter UI
  updateViolationUI(violations);

  // Restore timer
  const savedSecondsStr = localStorage.getItem(LS_KEY_TIMER);
  const savedSeconds    = savedSecondsStr ? parseInt(savedSecondsStr) : null;
  secondsRemaining = (savedSeconds && savedSeconds > 0 && savedSeconds <= TOTAL_DURATION_SECONDS)
    ? savedSeconds
    : TOTAL_DURATION_SECONDS;

  // Check if screensharing is supported in this context (requires HTTPS or localhost)
  const isScreenshareSupported = !!(navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia);
  if (!isScreenshareSupported) {
    const titleEl = document.getElementById('screenshareOverlay').querySelector('.vio-title');
    const msgEl = document.getElementById('screenshareOverlay').querySelector('.vio-msg');
    const btnEl = document.getElementById('startScreenshareBtn');
    
    if (titleEl) titleEl.textContent = 'Proctoring Offline (HTTP/LAN)';
    if (msgEl) {
      msgEl.innerHTML = 'Screenshare monitoring requires a secure connection (HTTPS) or accessing via localhost. Since this is an insecure connection, proctoring is offline. Click below to continue.';
    }
    if (btnEl) {
      btnEl.textContent = 'Acknowledge & Start Test';
    }
  }
});

// ── Screenshare Proctoring Setup ─────────────────────────────
async function requestScreenshare() {
  const isScreenshareSupported = !!(navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia);
  if (!isScreenshareSupported) {
    // Graceful fallback for LAN HTTP
    document.getElementById('screenshareOverlay').style.display = 'none';
    const videoEl = document.getElementById('proctorVideo');
    const fallbackEl = document.getElementById('proctorVideoFallback');
    if (videoEl && fallbackEl) {
      videoEl.style.display = 'none';
      fallbackEl.style.display = 'flex';
    }
    startTimer();
    renderQuestion(currentQuestion);
    updateNavGrid();
    return;
  }

  const btn = document.getElementById('startScreenshareBtn');
  btn.disabled = true;
  btn.textContent = 'Requesting Permission...';
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: {
        displaySurface: "monitor" // hint to share entire screen
      },
      audio: false
    });
    
    // Ensure they shared their entire screen (monitor) and not a single tab/window
    const track = stream.getVideoTracks()[0];
    const settings = track.getSettings();
    if (settings.displaySurface && settings.displaySurface !== 'monitor') {
      track.stop();
      alert('Proctoring Violation: You must share your ENTIRE screen, not a window or tab. Please try again.');
      btn.disabled = false;
      btn.textContent = 'Enable Screenshare & Start Test';
      return;
    }
    
    // Trigger auto-submit if screensharing is stopped during the test
    track.addEventListener('ended', () => {
      if (!isSubmitting) {
        autoSubmit('Screenshare terminated by user');
      }
    });

    // Request Webcam feed (if supported)
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const webcamStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false
        });
        const videoEl = document.getElementById('proctorVideo');
        if (videoEl) {
          videoEl.srcObject = webcamStream;
        }
      }
    } catch (camErr) {
      console.warn('Webcam permission denied or unavailable:', camErr);
      const videoEl = document.getElementById('proctorVideo');
      const fallbackEl = document.getElementById('proctorVideoFallback');
      if (videoEl && fallbackEl) {
        videoEl.style.display = 'none';
        fallbackEl.style.display = 'flex';
      }
    }
    
    // Start the assessment
    document.getElementById('screenshareOverlay').style.display = 'none';
    startTimer();
    renderQuestion(currentQuestion);
    updateNavGrid();
  } catch (err) {
    console.error('Screenshare error:', err);
    alert('Screenshare permission is mandatory to attempt this assessment. Please click "Enable Screenshare" and select your "Entire Screen".');
    btn.disabled = false;
    btn.textContent = 'Enable Screenshare & Start Test';
  }
}


// ── Timer ─────────────────────────────────────────────────── 
function startTimer() {
  updateTimerDisplay(secondsRemaining);
  timerInterval = setInterval(() => {
    secondsRemaining--;
    localStorage.setItem(LS_KEY_TIMER, secondsRemaining);
    updateTimerDisplay(secondsRemaining);

    if (secondsRemaining <= 0) {
      clearInterval(timerInterval);
      autoSubmit('Timer expired');
    }
  }, 1000);
}

function updateTimerDisplay(secs) {
  const mins = Math.floor(Math.abs(secs) / 60);
  const s    = Math.abs(secs) % 60;
  const display = `${String(mins).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  const el = document.getElementById('timerDisplay');
  const wrapper = document.getElementById('timerWrapper');
  if (!el || !wrapper) return;
  el.textContent = display;

  // Color transitions
  wrapper.classList.remove('timer-warning', 'timer-danger');
  if (secs <= 60)  wrapper.classList.add('timer-danger');
  else if (secs <= 300) wrapper.classList.add('timer-warning');
}


// ── Question Rendering ───────────────────────────────────────
function renderQuestion(index) {
  if (index < 0 || index >= QUESTIONS.length) return;
  currentQuestion = index;
  const q = QUESTIONS[index];
  const savedOpt = answers[q.id] || null;
  const totalQ   = QUESTIONS.length;

  // Progress
  document.getElementById('currentQNum').textContent = index + 1;
  const progressPct = ((index + 1) / totalQ * 100).toFixed(1);
  document.getElementById('progressFill').style.width = progressPct + '%';

  // Build HTML
  const optionLetters = ['A', 'B', 'C', 'D'];
  const optionTexts   = [q.option_a, q.option_b, q.option_c, q.option_d];

  const optionsHTML = optionLetters.map((letter, i) => `
    <div class="option-item ${savedOpt === letter ? 'selected' : ''}"
         id="opt-${letter}" data-letter="${letter}"
         onclick="selectOption(${q.id}, '${letter}', this)">
      <span class="opt-key">${letter}</span>
      <span class="opt-text">${escapeHtml(optionTexts[i])}</span>
    </div>
  `).join('');

  document.getElementById('questionContent').innerHTML = `
    <span class="question-num">Question ${index + 1} of ${totalQ}</span>
    <div class="question-text">${escapeHtml(q.question)}</div>
    <div class="options-list">${optionsHTML}</div>
  `;

  // Nav buttons state
  document.getElementById('prevBtn').disabled = (index === 0);
  const nextBtn = document.getElementById('nextBtn');
  if (index === totalQ - 1) {
    nextBtn.style.display = 'none';
  } else {
    nextBtn.style.display = '';
    nextBtn.disabled = false;
  }

  updateNavGrid();
  updateSummaryCount();
}


// ── Option Selection ─────────────────────────────────────────
function selectOption(questionId, letter, el) {
  // Toggle — click same again to deselect
  const current = answers[questionId];
  const newOpt  = (current === letter) ? null : letter;
  answers[questionId] = newOpt;

  // Update UI
  document.querySelectorAll('.option-item').forEach(item => item.classList.remove('selected'));
  if (newOpt) el.classList.add('selected');

  // Persist to localStorage immediately
  localStorage.setItem(LS_KEY_ANSWERS, JSON.stringify(answers));

  // Debounced server save
  if (saveDebounceTimers[questionId]) clearTimeout(saveDebounceTimers[questionId]);
  saveDebounceTimers[questionId] = setTimeout(() => {
    saveAnswer(questionId, newOpt);
  }, 400);

  updateNavGrid();
  updateSummaryCount();
}


// ── Auto-Save to Server ──────────────────────────────────────
async function saveAnswer(questionId, selectedOption) {
  try {
    await apiPost(SAVE_URL, {
      question_id: questionId,
      selected_option: selectedOption,
    });
  } catch (err) {
    console.warn('Auto-save failed (will retry on next selection):', err);
  }
}


// ── Navigation ───────────────────────────────────────────────
function navigateTo(index) {
  if (index < 0 || index >= QUESTIONS.length) return;
  renderQuestion(index);
  // Scroll question panel to top
  const panel = document.querySelector('.question-panel');
  if (panel) panel.scrollTop = 0;
}


// ── Nav Grid Update ──────────────────────────────────────────
function updateNavGrid() {
  QUESTIONS.forEach((q, i) => {
    const btn = document.getElementById(`nav-${i}`);
    if (!btn) return;
    btn.className = 'nav-btn';
    if (i === currentQuestion)     btn.classList.add('nav-current');
    else if (answers[q.id])        btn.classList.add('nav-answered');
  });
}

function updateSummaryCount() {
  const answeredCount  = Object.values(answers).filter(Boolean).length;
  const unansweredCount = QUESTIONS.length - answeredCount;
  const ac = document.getElementById('answeredCount');
  const uc = document.getElementById('unansweredCount');
  if (ac) ac.textContent = answeredCount;
  if (uc) uc.textContent = unansweredCount;
}


// ── Submit Logic ─────────────────────────────────────────────
function confirmSubmit() {
  const answeredCount  = Object.values(answers).filter(Boolean).length;
  const unansweredCount = QUESTIONS.length - answeredCount;
  let msg = `You are about to submit the assessment.`;
  if (unansweredCount > 0) {
    msg += `<br><br><strong style="color:var(--warning)">${unansweredCount} question(s) unanswered.</strong>`;
  }
  msg += '<br>This action cannot be undone.';
  confirmAction(msg, () => doSubmit());
}

function showSubmittingOverlay(title, msg) {
  const overlay = document.getElementById('submittingOverlay');
  const titleEl = document.getElementById('submittingTitle');
  const msgEl   = document.getElementById('submittingMsg');
  if (titleEl) titleEl.textContent = title;
  if (msgEl)   msgEl.textContent   = msg;
  if (overlay)  overlay.style.display = 'flex';
}

async function doSubmit() {
  if (isSubmitting) return;
  isSubmitting = true;

  // Show full-page overlay immediately so user sees clean screen
  showSubmittingOverlay(
    'Submitting Your Assessment…',
    'Saving your answers and calculating your score. Please wait.'
  );

  clearInterval(timerInterval);
  localStorage.removeItem(LS_KEY_TIMER);
  localStorage.removeItem(LS_KEY_ANSWERS);

  // Save all pending answers first
  const savePromises = QUESTIONS.map(q =>
    saveAnswer(q.id, answers[q.id] || null)
  );
  await Promise.allSettled(savePromises);

  // Submit
  document.getElementById('submitForm').submit();
}

async function autoSubmit(reason) {
  if (isSubmitting) return;
  isSubmitting = true;

  // Determine the right message based on reason
  const isViolation = reason.toLowerCase().includes('violation');
  const isTimer     = reason.toLowerCase().includes('timer');
  showSubmittingOverlay(
    isViolation
      ? '⚠️ Auto-Submitted: Violation Limit Reached'
      : isTimer
        ? '⏰ Time’s Up — Auto-Submitting…'
        : '🚨 Auto-Submitted',
    isViolation
      ? 'You exceeded 3 tab switches. Your assessment has been submitted. Calculating your score…'
      : isTimer
        ? 'The time limit has been reached. Your answers are being saved and scored…'
        : 'Your assessment is being submitted. Please wait…'
  );

  clearInterval(timerInterval);
  localStorage.removeItem(LS_KEY_TIMER);
  localStorage.removeItem(LS_KEY_ANSWERS);

  // Save all pending answers
  try {
    await Promise.allSettled(
      QUESTIONS.map(q => saveAnswer(q.id, answers[q.id] || null))
    );
  } catch (_) {}

  document.getElementById('submitForm').submit();
}


// ── Anti-Cheat ───────────────────────────────────────────────

// 1. Tab Switch Detection
document.addEventListener('visibilitychange', async () => {
  if (document.visibilityState === 'hidden') return; // only trigger on return
  if (isSubmitting) return;

  violations++;
  updateViolationUI(violations);

  // Notify server
  let serverViolations = violations;
  try {
    const res = await apiPost(VIOLATION_URL, {});
    if (res && res.data) {
      serverViolations = res.data.violations;
      if (res.data.auto_submit) {
        showAutoSubmitOverlay();
        await autoSubmit('3 violations');
        return;
      }
    }
  } catch (_) {}

  if (serverViolations >= 3 || violations >= 3) {
    showAutoSubmitOverlay();
    await autoSubmit('3 violations');
    return;
  }

  showViolationWarning(violations);
});

function showViolationWarning(count) {
  const overlay = document.getElementById('violationOverlay');
  const title   = document.getElementById('vioTitle');
  const msg     = document.getElementById('vioMsg');
  const counter = document.getElementById('vioCount');

  if (title)   title.textContent = 'Tab Switch Detected!';
  if (msg)     msg.textContent   = 'Switching away from this tab is not allowed during the assessment.';
  if (counter) counter.textContent = count;
  if (overlay) overlay.style.display = 'flex';
}

function dismissViolation() {
  const overlay = document.getElementById('violationOverlay');
  if (overlay) overlay.style.display = 'none';
}

function showAutoSubmitOverlay() {
  // legacy — now handled by showSubmittingOverlay inside autoSubmit
  const vOverlay = document.getElementById('violationOverlay');
  if (vOverlay) vOverlay.style.display = 'none';
}

function updateViolationUI(count) {
  const indicator = document.getElementById('vioIndicator');
  const header    = document.getElementById('vioHeader');
  if (header)    header.textContent = count;
  if (indicator) {
    indicator.className = count > 0 ? 'vio-indicator' : 'vio-indicator vio-clear';
    indicator.innerHTML = count > 0
      ? `⚠ <span id="vioHeader">${count}</span>/3 violations`
      : `✓ <span id="vioHeader">${count}</span>/3 violations`;
  }
}


// 2. Right-Click Disable
document.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  return false;
});

// 3. Copy / Paste / Cut / Select-All
document.addEventListener('keydown', (e) => {
  const blocked = [
    // Copy/paste/cut
    (e.ctrlKey || e.metaKey) && ['c', 'v', 'x', 'a'].includes(e.key.toLowerCase()),
    // Developer tools
    e.key === 'F12',
    (e.ctrlKey && e.shiftKey && ['i', 'j', 'c'].includes(e.key.toLowerCase())),
    (e.ctrlKey && e.key.toLowerCase() === 'u'),
  ];
  if (blocked.some(Boolean)) {
    e.preventDefault();
    e.stopPropagation();
    return false;
  }
});

// 4. Prevent text selection via mouse
document.addEventListener('selectstart', (e) => {
  // Allow selection in form inputs but not question text
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  e.preventDefault();
});


// ── Utilities ────────────────────────────────────────────────
function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(String(str)));
  return div.innerHTML;
}

// Periodic full-state sync to server (every 30s)
setInterval(() => {
  if (isSubmitting) return;
  QUESTIONS.forEach(q => {
    if (answers[q.id] !== undefined) {
      saveAnswer(q.id, answers[q.id] || null);
    }
  });
}, 30000);

// Save on window unload / beforeunload
window.addEventListener('beforeunload', (e) => {
  if (isSubmitting) return;
  localStorage.setItem(LS_KEY_ANSWERS, JSON.stringify(answers));
  localStorage.setItem(LS_KEY_TIMER, secondsRemaining);
});
