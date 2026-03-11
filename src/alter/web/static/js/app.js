/* LifeOS UI — Global JS */

// ---- Toast notifications ----

function showToast(title, message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const colors = {
    success: 'border-emerald-500/30 text-emerald-400',
    error: 'border-red-500/30 text-red-400',
    info: 'border-pulse/30 text-pulse',
  };
  const color = colors[type] || colors.info;

  const toast = document.createElement('div');
  toast.className = 'animate-slide-up';
  toast.innerHTML = `
    <div class="glass-sm p-4 ${color}">
      <p class="text-sm font-medium" style="color: rgba(255,255,255,0.95);">${title}</p>
      <p class="text-xs mt-1" style="color: rgba(255,255,255,0.65);">${message}</p>
    </div>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ---- HTMX error listener (no generic success toast) ----

document.addEventListener('htmx:responseError', function(evt) {
  showToast('Error', 'Something went wrong. Please try again.', 'error');
});

// ---- Check-in form ----

function checkinForm() {
  return {
    mood: 5, energy: 5, stress: 3, sleep: 7, exercise: 0,
    note: '',
    saving: false, saved: false,
    async submit() {
      this.saving = true;
      this.saved = false;
      const today = new Date().toISOString().split('T')[0];
      try {
        // 1. Log daily data
        const res = await fetch(`/api/v1/users/${USER_ID}/daily-data`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            date: today,
            health: {
              sleep_hours: parseFloat(this.sleep),
              exercise_minutes: parseInt(this.exercise)
            },
            emotions: {
              mood: parseInt(this.mood),
              energy: parseInt(this.energy),
              stress: parseInt(this.stress)
            }
          })
        });

        if (res.ok) {
          this.saved = true;

          // 2. Save free-text note as import (if provided)
          if (this.note.trim()) {
            try {
              await fetch(`/api/v1/users/${USER_ID}/import`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source: 'text', content: this.note })
              });
            } catch(e) { /* non-critical */ }
            this.note = '';
          }

          // 3. Trigger background observe for immediate feedback
          let observeMsg = "Got it. I'll factor this into tonight's review.";
          try {
            const obsRes = await fetch('/api/v1/consciousness/observe', { method: 'POST' });
            if (obsRes.ok) {
              const obsData = await obsRes.json();
              const critical = (obsData.observations || []).filter(o => o.severity === 'critical');
              if (critical.length > 0 && critical[0].summary) {
                const s = critical[0].summary;
                observeMsg = `I noticed ${s.toLowerCase().startsWith('i') ? '' : 'that '}${s.charAt(0).toLowerCase() + s.slice(1)} — I'll think about this.`;
              }
            }
          } catch(e) { /* observe may not be running */ }

          showToast('Check-in Logged', observeMsg, 'success');

          // 4. Refresh relevant sections
          htmx.trigger(document.body, 'refreshInbox');
          if (document.getElementById('narrative-section')) {
            htmx.trigger('#narrative-section', 'load');
          }

          setTimeout(() => this.saved = false, 4000);
        }
      } catch(e) {
        showToast('Error', 'Could not save check-in data.', 'error');
      }
      finally { this.saving = false; }
    }
  };
}

// ---- Goal form ----

function goalForm() {
  return {
    description: '', domain: 'health', horizon: 'month',
    saving: false,
    async submit() {
      if (!this.description.trim()) return;
      this.saving = true;
      try {
        const res = await fetch(`/api/v1/users/${USER_ID}/goals`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            description: this.description,
            domain: this.domain,
            time_horizon: this.horizon
          })
        });
        if (res.ok) {
          this.description = '';
          showToast('Goal Added', 'Added to your goals.', 'success');
          htmx.trigger('#goal-tree', 'refresh');
        }
      } catch(e) {
        showToast('Error', 'Could not add goal.', 'error');
      }
      finally { this.saving = false; }
    }
  };
}

// ---- Quick Scan (nav orb) ----

async function triggerObserve() {
  const spinner = document.getElementById('orb-spinner');
  if (spinner) spinner.classList.remove('hidden');
  // Also show mobile orb spinners
  document.querySelectorAll('[data-orb-spinner-ring]').forEach(el => el.classList.remove('hidden'));

  try {
    const res = await fetch('/api/v1/consciousness/observe', { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      const count = data.observation_count || 0;
      const critical = (data.observations || []).filter(o => o.severity === 'critical').length;
      if (critical > 0) {
        showToast('Quick Scan', `${count} signals found — ${critical} need attention.`, 'info');
      } else if (count > 0) {
        showToast('Quick Scan', `${count} signals checked. All normal.`, 'info');
      } else {
        showToast('Quick Scan', 'No new data to check.', 'info');
      }
      htmx.trigger(document.body, 'refreshInbox');
    } else {
      showToast('Offline', 'Background reviews are not running.', 'error');
    }
  } catch(e) {
    showToast('Offline', 'Could not connect.', 'error');
  }
  finally {
    if (spinner) spinner.classList.add('hidden');
    document.querySelectorAll('[data-orb-spinner-ring]').forEach(el => el.classList.add('hidden'));
  }
}

// ---- Ask LifeOS (conversational tick with user context) ----

async function askAlter(question) {
  if (!question || !question.trim()) return;

  document.dispatchEvent(new CustomEvent('alter:thinking', { detail: { on: true } }));

  showProcessingOverlay(
    'LifeOS is thinking...',
    question.length > 60 ? question.substring(0, 60) + '...' : question
  );

  try {
    const res = await fetch('/api/v1/consciousness/tick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tick_type: 'urgent', context: question })
    });

    await new Promise(r => setTimeout(r, 500));

    if (res.ok) {
      const data = await res.json();
      const titleEl = document.getElementById('processing-title');
      const detailEl = document.getElementById('processing-detail');
      if (titleEl) titleEl.textContent = 'Done!';
      if (detailEl) detailEl.textContent = 'New thoughts added.';
      await new Promise(r => setTimeout(r, 800));

      const total = (data.insights || 0) + (data.notifications || 0) + (data.discoveries || 0);
      showToast('LifeOS Responded', `${total} thought${total !== 1 ? 's' : ''} generated about your question.`, 'success');

      htmx.trigger(document.body, 'refreshInbox');
      if (document.getElementById('narrative-section')) {
        htmx.trigger('#narrative-section', 'load');
      }
    } else {
      showToast('Error', 'LifeOS could not process your question.', 'error');
    }
  } catch(e) {
    showToast('Connection Error', 'Could not reach the server.', 'error');
  }
  finally {
    hideProcessingOverlay();
    document.dispatchEvent(new CustomEvent('alter:thinking', { detail: { on: false } }));
  }
}

// ---- Run a Review (with processing overlay) ----

const REVIEW_LABELS = {
  daily_review:    { title: 'Reviewing your day...', detail: 'Looking at patterns and progress' },
  weekly_reflect:  { title: 'Running weekly check-in...', detail: 'Reflecting on your week' },
  goal_analysis:   { title: 'Analyzing your goals...', detail: 'Checking progress and suggesting next steps' },
  discovery:       { title: 'Looking for patterns...', detail: 'Connecting dots across your life' },
};

let _overlayTimeout = null;

function showProcessingOverlay(title, detail) {
  const overlay = document.getElementById('processing-overlay');
  const titleEl = document.getElementById('processing-title');
  const detailEl = document.getElementById('processing-detail');
  if (!overlay) return;
  titleEl.textContent = title;
  detailEl.textContent = detail;
  overlay.classList.remove('hidden');
  overlay.style.opacity = '1';
  // Safety timeout — auto-dismiss after 60s to prevent soft-lock
  if (_overlayTimeout) clearTimeout(_overlayTimeout);
  _overlayTimeout = setTimeout(() => hideProcessingOverlay(), 60000);
}

function hideProcessingOverlay() {
  const overlay = document.getElementById('processing-overlay');
  if (!overlay) return;
  if (_overlayTimeout) { clearTimeout(_overlayTimeout); _overlayTimeout = null; }
  overlay.style.opacity = '0';
  setTimeout(() => {
    overlay.classList.add('hidden');
    overlay.style.opacity = '1';
  }, 300);
}

async function triggerTick(tickType = 'daily_review') {
  const labels = REVIEW_LABELS[tickType] || { title: 'Processing...', detail: 'This may take a moment' };
  showProcessingOverlay(labels.title, labels.detail);

  try {
    const res = await fetch('/api/v1/consciousness/tick', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tick_type: tickType })
    });

    // Brief pause so animation feels complete
    await new Promise(r => setTimeout(r, 500));

    if (res.ok) {
      // Show completion state briefly
      const titleEl = document.getElementById('processing-title');
      const detailEl = document.getElementById('processing-detail');
      if (titleEl) titleEl.textContent = 'Done!';
      if (detailEl) detailEl.textContent = 'New updates have been added.';
      await new Promise(r => setTimeout(r, 800));

      showToast('Review Complete', 'New thoughts added to your stream.', 'success');
      htmx.trigger(document.body, 'refreshInbox');
      if (document.getElementById('narrative-section')) {
        htmx.trigger('#narrative-section', 'load');
      }
    } else {
      showToast('Review Failed', 'Something went wrong. Try again in a moment.', 'error');
    }
  } catch(e) {
    showToast('Connection Error', 'Could not reach the server.', 'error');
  }
  finally {
    hideProcessingOverlay();
  }
}

// ---- Complete goal ----

async function completeGoal(goalId) {
  try {
    const res = await fetch(`/api/v1/users/${USER_ID}/goals/${goalId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ outcome: 'success', notes: '' })
    });
    if (res.ok) {
      showToast('Goal Complete', 'Well done.', 'success');
      htmx.trigger('#goal-tree', 'refresh');
    } else {
      showToast('Error', 'Could not complete goal.', 'error');
    }
  } catch(e) {
    showToast('Error', 'Could not reach the server.', 'error');
  }
}

// ---- Goal decomposition ----

async function decomposeGoal(goalId) {
  showProcessingOverlay('Breaking down goal...', 'Suggesting sub-goals');
  try {
    const res = await fetch(`/api/v1/users/${USER_ID}/goals/${goalId}/decompose`, {
      method: 'POST'
    });

    await new Promise(r => setTimeout(r, 300));

    if (res.ok) {
      const data = await res.json();
      showToast('Done', `${data.sub_goals_created || 0} sub-goals suggested.`, 'success');
      htmx.trigger('#goal-tree', 'refresh');
    } else {
      showToast('Error', 'Could not break down goal.', 'error');
    }
  } catch(e) {
    showToast('Error', 'Could not reach the server.', 'error');
  }
  finally {
    hideProcessingOverlay();
  }
}

// ---- Delete goal ----

async function deleteGoal(goalId) {
  if (!confirm('Delete this goal?')) return;
  try {
    const res = await fetch(`/api/v1/users/${USER_ID}/goals/${goalId}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      showToast('Goal Deleted', 'Goal removed.', 'success');
      htmx.trigger('#goal-tree', 'refresh');
    } else {
      showToast('Error', 'Could not delete goal.', 'error');
    }
  } catch(e) {
    showToast('Error', 'Could not reach the server.', 'error');
  }
}

// ---- Save goal edit ----

async function saveGoalEdit(goalId, description, domain, horizon) {
  try {
    const body = {};
    if (description) body.description = description;
    if (domain) body.domain = domain;
    if (horizon) body.time_horizon = horizon;
    const res = await fetch(`/api/v1/users/${USER_ID}/goals/${goalId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (res.ok) {
      showToast('Goal Updated', 'Changes saved.', 'success');
      htmx.trigger('#goal-tree', 'refresh');
    } else {
      showToast('Error', 'Could not update goal.', 'error');
    }
  } catch(e) {
    showToast('Error', 'Could not reach the server.', 'error');
  }
}

// ---- Import form (Settings page) ----

function importForm() {
  return {
    source: '',
    textContent: '',
    fileContent: '',
    fileName: '',
    importing: false,
    imported: false,

    handleFile(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.fileName = file.name;
      const reader = new FileReader();
      reader.onload = (e) => { this.fileContent = e.target.result; };
      reader.readAsText(file);
    },

    async submitImport() {
      const content = this.source === 'text' ? this.textContent : this.fileContent;
      if (!content || !content.trim()) return;

      this.importing = true;
      this.imported = false;
      try {
        const res = await fetch(`/api/v1/users/${USER_ID}/import`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: this.source, content: content })
        });
        if (res.ok) {
          this.imported = true;
          this.textContent = '';
          this.fileContent = '';
          this.fileName = '';
          showToast('Imported', 'Your context has been absorbed.', 'success');
          htmx.trigger(document.body, 'refreshMemories');
          setTimeout(() => this.imported = false, 4000);
        } else {
          let msg = 'Import failed.';
          try { const data = await res.json(); msg = data.detail || msg; } catch(e) {}
          showToast('Error', msg, 'error');
        }
      } catch(e) {
        showToast('Error', 'Could not reach the server.', 'error');
      }
      finally { this.importing = false; }
    }
  };
}

// ---- Purpose editor ----

function purposeEditor(initialPurpose) {
  return {
    purpose: initialPurpose || '',
    editing: false,
    saving: false,
    async save() {
      this.saving = true;
      try {
        const res = await fetch(`/api/v1/users/${USER_ID}/purpose`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ purpose: this.purpose })
        });
        if (res.ok) {
          this.editing = false;
          showToast('Saved', 'Purpose updated.', 'success');
        } else {
          showToast('Error', 'Could not update purpose.', 'error');
        }
      } catch(e) {
        showToast('Error', 'Could not update purpose.', 'error');
      }
      finally { this.saving = false; }
    }
  };
}

// ---- Inbox actions (save, skip, convert) ----

async function pinInboxItem(itemId) {
  try {
    // Animate item out
    const el = document.getElementById('inbox-' + itemId);
    if (el) {
      el.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateX(-8px)';
    }
    const res = await fetch(`/api/v1/inbox/${itemId}/pin`, { method: 'POST' });
    if (res.ok) {
      showToast('Saved to Notes', 'Moved from stream to your saved notes.', 'success');
      setTimeout(() => {
        htmx.trigger(document.body, 'refreshInbox');
        htmx.trigger(document.body, 'refreshPinned');
      }, 200);
    }
  } catch(e) {
    showToast('Error', 'Could not save item.', 'error');
  }
}

async function dismissInboxItem(itemId) {
  try {
    const res = await fetch(`/api/v1/inbox/${itemId}/dismiss`, { method: 'POST' });
    if (res.ok) {
      const el = document.getElementById('inbox-' + itemId);
      if (el) {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.2s ease';
        setTimeout(() => htmx.trigger(document.body, 'refreshInbox'), 200);
      } else {
        htmx.trigger(document.body, 'refreshInbox');
      }
    }
  } catch(e) {
    showToast('Error', 'Could not skip item.', 'error');
  }
}

async function convertInboxItem(itemId, to) {
  try {
    // Animate item out
    const el = document.getElementById('inbox-' + itemId);
    if (el) {
      el.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateX(-8px)';
    }
    const res = await fetch(`/api/v1/inbox/${itemId}/convert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to })
    });
    if (res.ok) {
      const msgs = {
        goal: { title: 'Extracted to Goals', detail: 'Moved from stream to your goals.' },
        habit: { title: 'Extracted to Habits', detail: 'Moved from stream to your daily habits.' },
      };
      const msg = msgs[to] || { title: 'Converted', detail: `Moved to ${to}s.` };
      showToast(msg.title, msg.detail, 'success');
      setTimeout(() => {
        htmx.trigger(document.body, 'refreshInbox');
        if (to === 'habit') htmx.trigger(document.body, 'refreshHabits');
        if (to === 'goal') htmx.trigger('#goal-tree', 'refresh');
      }, 200);
    }
  } catch(e) {
    showToast('Error', `Could not create ${to}.`, 'error');
  }
}

// ---- Habits ----

async function toggleHabit(habitId) {
  try {
    const res = await fetch(`/api/v1/users/${USER_ID}/habits/${habitId}/toggle`, {
      method: 'POST'
    });
    if (res.ok) {
      htmx.trigger(document.body, 'refreshHabits');
    }
  } catch(e) {
    showToast('Error', 'Could not toggle habit.', 'error');
  }
}

async function addNewHabit() {
  const input = document.getElementById('new-habit-name');
  if (!input || !input.value.trim()) return;
  try {
    const res = await fetch(`/api/v1/users/${USER_ID}/habits`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: input.value.trim() })
    });
    if (res.ok) {
      input.value = '';
      htmx.trigger(document.body, 'refreshHabits');
    }
  } catch(e) {
    showToast('Error', 'Could not add habit.', 'error');
  }
}

// ---- Saved notes ----

async function archivePinnedNote(noteId) {
  try {
    const res = await fetch(`/api/v1/users/${USER_ID}/pinned/${noteId}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      htmx.trigger(document.body, 'refreshPinned');
    }
  } catch(e) {
    showToast('Error', 'Could not remove note.', 'error');
  }
}

// ---- Automatic Reviews config (Settings) ----

function thoughtLoops() {
  const scheduleLabels = {
    daily_review: 'Every day at 10:00 PM',
    weekly_reflect: 'Every Sunday at 8:00 PM',
    monthly_deep: '1st of each month at 10:00 AM',
    goal_analysis: 'Every Wednesday at 9:00 PM',
    discovery: '15th of each month at 10:00 AM',
  };

  return {
    loops: [],

    async init() {
      try {
        const res = await fetch('/api/v1/consciousness/loops');
        if (res.ok) {
          const data = await res.json();
          this.loops = Object.entries(data.loops).map(([id, config]) => ({
            id,
            label: config.label,
            description: config.description,
            enabled: config.enabled,
            schedule_type: config.schedule_type,
            schedule_label: scheduleLabels[id] || config.schedule_type,
          }));
        }
      } catch(e) {
        // Loops will be empty, that's fine
      }
    },

    async toggleLoop(loop) {
      const newState = !loop.enabled;
      try {
        const res = await fetch(`/api/v1/consciousness/loops/${loop.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: newState })
        });
        if (res.ok) {
          loop.enabled = newState;
          showToast(
            newState ? 'Enabled' : 'Paused',
            `${loop.label} ${newState ? 'will run on schedule' : 'has been paused'}.`,
            'info'
          );
        }
      } catch(e) {
        showToast('Error', 'Could not update setting.', 'error');
      }
    },
  };
}
