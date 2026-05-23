/* recipients.js — Alıcı ve grup yönetimi */
'use strict';

let selectedRecId = null;
let editingRecId  = null;
let editingGrpId  = null;

async function loadRecipients() {
  await loadGroups();
  await loadRecTable();
}
window.loadRecipients = loadRecipients;

async function loadGroups() {
  const groups = await api.get('/api/groups');
  PM.groups = groups;
  renderGroupList(groups);
  fillGroupSelect(groups);
}

function renderGroupList(groups) {
  const list = document.getElementById('group-list');
  list.innerHTML = '';
  const allItem = document.createElement('div');
  allItem.className = 'group-item' + (PM.selectedGroup===null?' active':'');
  allItem.innerHTML = `<span class="group-dot" style="background:#e8e4d9"></span>📋 Tüm Alıcılar`;
  allItem.addEventListener('click', () => { PM.selectedGroup=null; loadRecTable(); renderGroupList(PM.groups); });
  list.appendChild(allItem);
  groups.forEach(g => {
    const item = document.createElement('div');
    item.className = 'group-item' + (PM.selectedGroup===g.id?' active':'');
    item.innerHTML = `<span class="group-dot" style="background:${g.color}"></span>${g.name} <span style="font-size:10px;color:var(--muted)">(${g.count})</span>`;
    item.addEventListener('click', () => { PM.selectedGroup=g.id; loadRecTable(); renderGroupList(PM.groups); });
    list.appendChild(item);
  });
}

function fillGroupSelect(groups) {
  ['rec-group', 'send-group'].forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const prev = sel.value;
    sel.innerHTML = '<option value="">— Tüm / Grup yok —</option>';
    groups.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.id; opt.textContent = `${g.name} (${g.count})`;
      sel.appendChild(opt);
    });
    if (prev) sel.value = prev;
  });
}

async function loadRecTable() {
  const sub = document.getElementById('sub-filter').value;
  let url = `/api/recipients?active=1&subscribed=${sub}`;
  if (PM.selectedGroup) url += `&group_id=${PM.selectedGroup}`;
  const rows = await api.get(url);
  renderRecTable(rows);
}

function renderRecTable(rows) {
  const tbody = document.getElementById('rec-tbody');
  tbody.innerHTML = '';
  rows.forEach(r => {
    const tr = document.createElement('tr');
    tr.dataset.id = r.id;
    tr.style.cursor = 'pointer';
    tr.innerHTML = `
      <td>${escH(r.name||'')}</td>
      <td>${escH(r.email)}</td>
      <td>${escH(r.company||'')}</td>
      <td><span style="color:${r.group_color||'var(--muted)'}">${escH(r.group_name||'—')}</span></td>
      <td>${r.subscribed
        ? '<span class="badge ok">✅ Abone</span>'
        : '<span class="badge fail">⛔ İptal</span>'}</td>
      <td style="color:var(--muted);font-size:11px">${(r.created_at||'').slice(0,10)}</td>
    `;
    tr.addEventListener('click', () => {
      document.querySelectorAll('#rec-tbody tr').forEach(t => t.style.background='');
      tr.style.background = 'var(--card)';
      selectedRecId = r.id;
    });
    tr.addEventListener('dblclick', () => openRecModal(r));
    tbody.appendChild(tr);
  });
  document.getElementById('rec-count').textContent = `${rows.length} alıcı`;
}

function escH(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

// ── Grup CRUD ─────────────────────────────────────────────────────────────────
document.getElementById('btn-add-group').addEventListener('click', () => openGrpModal());
document.getElementById('btn-edit-group').addEventListener('click', () => {
  const g = PM.groups.find(g => g.id === PM.selectedGroup);
  if (g) openGrpModal(g);
});
document.getElementById('btn-del-group').addEventListener('click', async () => {
  if (!PM.selectedGroup) return;
  if (!confirm('Grup silinsin mi?')) return;
  await api.del(`/api/groups/${PM.selectedGroup}`);
  PM.selectedGroup = null;
  await loadGroups(); await loadRecTable();
});

function openGrpModal(g=null) {
  editingGrpId = g?.id || null;
  document.getElementById('modal-grp-title').textContent = g ? 'Grubu Düzenle' : 'Yeni Grup';
  document.getElementById('grp-name').value  = g?.name  || '';
  document.getElementById('grp-color').value = g?.color || '#1B3A5C';
  document.getElementById('modal-group').classList.add('open');
}
document.getElementById('modal-grp-cancel').addEventListener('click', () =>
  document.getElementById('modal-group').classList.remove('open'));
document.getElementById('modal-grp-ok').addEventListener('click', async () => {
  const name  = document.getElementById('grp-name').value.trim();
  const color = document.getElementById('grp-color').value;
  if (!name) return alert('Grup adı boş olamaz.');
  if (editingGrpId)
    await api.put(`/api/groups/${editingGrpId}`, {name, color});
  else
    await api.post('/api/groups', {name, color});
  document.getElementById('modal-group').classList.remove('open');
  await loadGroups(); await loadRecTable();
});

// ── Alıcı CRUD ────────────────────────────────────────────────────────────────
document.getElementById('btn-add-rec').addEventListener('click', () => openRecModal());
document.getElementById('btn-edit-rec').addEventListener('click', async () => {
  if (!selectedRecId) return;
  const rows = await api.get('/api/recipients?active=0&subscribed=all');
  const r = rows.find(r => r.id === selectedRecId);
  if (r) openRecModal(r);
});
document.getElementById('btn-del-rec').addEventListener('click', async () => {
  if (!selectedRecId || !confirm('Alıcı silinsin mi?')) return;
  await api.del(`/api/recipients/${selectedRecId}`);
  selectedRecId = null; await loadRecTable();
});
document.getElementById('btn-unsub-rec').addEventListener('click', async () => {
  if (!selectedRecId) return;
  await api.post(`/api/recipients/${selectedRecId}/unsub`);
  await loadRecTable();
});
document.getElementById('btn-resub-rec').addEventListener('click', async () => {
  if (!selectedRecId) return;
  await api.post(`/api/recipients/${selectedRecId}/resub`);
  await loadRecTable();
});

function openRecModal(r=null) {
  editingRecId = r?.id || null;
  document.getElementById('modal-rec-title').textContent = r ? 'Alıcıyı Düzenle' : 'Yeni Alıcı';
  document.getElementById('rec-name').value       = r?.name       || '';
  document.getElementById('rec-email').value      = r?.email      || '';
  document.getElementById('rec-company').value    = r?.company    || '';
  document.getElementById('rec-notes').value      = r?.notes      || '';
  document.getElementById('rec-active').checked   = r ? !!r.active      : true;
  document.getElementById('rec-subscribed').checked = r ? !!r.subscribed : true;
  const sel = document.getElementById('rec-group');
  sel.innerHTML = '<option value="">— Grup yok —</option>';
  PM.groups.forEach(g => {
    const o = document.createElement('option');
    o.value = g.id; o.textContent = g.name;
    if (r?.group_id === g.id) o.selected = true;
    sel.appendChild(o);
  });
  document.getElementById('modal-recipient').classList.add('open');
}
document.getElementById('modal-rec-cancel').addEventListener('click', () =>
  document.getElementById('modal-recipient').classList.remove('open'));
document.getElementById('modal-rec-ok').addEventListener('click', async () => {
  const email = document.getElementById('rec-email').value.trim();
  if (!email || !email.includes('@')) return alert('Geçerli bir e-posta girin.');
  const data = {
    name:       document.getElementById('rec-name').value.trim(),
    email,
    company:    document.getElementById('rec-company').value.trim(),
    notes:      document.getElementById('rec-notes').value.trim(),
    group_id:   document.getElementById('rec-group').value || null,
    active:     document.getElementById('rec-active').checked ? 1 : 0,
    subscribed: document.getElementById('rec-subscribed').checked ? 1 : 0,
  };
  if (editingRecId)
    await api.put(`/api/recipients/${editingRecId}`, data);
  else
    await api.post('/api/recipients', data);
  document.getElementById('modal-recipient').classList.remove('open');
  await loadGroups(); await loadRecTable();
});

// ── CSV İçe Aktar ─────────────────────────────────────────────────────────────
document.getElementById('btn-import-csv').addEventListener('click', () =>
  document.getElementById('csv-file').click());
document.getElementById('csv-file').addEventListener('change', async e => {
  const file = e.target.files[0]; if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  if (PM.selectedGroup) fd.append('group_id', PM.selectedGroup);
  const res = await fetch('/api/recipients/import', {method:'POST', body: fd}).then(r=>r.json());
  alert(`✅ ${res.added} eklendi  ⏭ ${res.skipped} atlandı  ❌ ${res.errors} hata`);
  e.target.value = '';
  await loadGroups(); await loadRecTable();
});

// Filtre değişince
document.getElementById('sub-filter').addEventListener('change', loadRecTable);
document.getElementById('rec-search').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('#rec-tbody tr').forEach(tr => {
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
});
