/* logs.js — Gönderim geçmişi */
'use strict';

async function loadLogs() {
  const campaigns = await api.get('/api/logs/campaigns');
  const sel = document.getElementById('log-campaign');
  const prev = sel.value;
  sel.innerHTML = '<option value="">— Kampanya seç —</option>';
  campaigns.forEach(c => {
    const o = document.createElement('option');
    o.value = c; o.textContent = c;
    sel.appendChild(o);
  });
  if (prev) sel.value = prev;
  if (sel.value) loadLogTable();
}
window.loadLogs = loadLogs;

async function loadLogTable() {
  const camp   = document.getElementById('log-campaign').value;
  const status = document.getElementById('log-status').value;
  if (!camp) return;

  let url = `/api/logs?limit=1000`;
  if (camp)   url += `&campaign=${encodeURIComponent(camp)}`;
  if (status) url += `&status=${status}`;

  const rows = await api.get(url);
  renderLogTable(rows);

  // Özet
  if (camp) {
    const s = await api.get(`/api/logs/summary/${encodeURIComponent(camp)}`);
    const stats = document.getElementById('log-stats');
    stats.innerHTML = `
      <div class="stat-box"><div class="stat-num">${s.total}</div><div class="stat-lbl">Toplam</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#2ecc71">${s.summary.sent||0}</div><div class="stat-lbl">Başarılı</div></div>
      <div class="stat-box"><div class="stat-num" style="color:#e94560">${s.summary.failed||0}</div><div class="stat-lbl">Başarısız</div></div>
      <div class="stat-box"><div class="stat-num">%${s.rate}</div><div class="stat-lbl">Başarı Oranı</div></div>
    `;
  }
}

function renderLogTable(rows) {
  const tbody = document.getElementById('log-tbody');
  tbody.innerHTML = '';
  rows.forEach(r => {
    const tr = document.createElement('tr');
    const ok = r.status === 'sent';
    tr.innerHTML = `
      <td>${r.name||'—'}</td>
      <td>${r.email}</td>
      <td>${ok ? '<span class="badge ok">✅ Gönderildi</span>' : '<span class="badge fail">❌ Başarısız</span>'}</td>
      <td style="font-size:11px;color:var(--muted)">${r.error_msg||''}</td>
      <td style="font-size:11px;color:var(--muted)">${(r.sent_at||'').slice(0,16)}</td>
      <td style="text-align:center">${r.retried||0}</td>
    `;
    tbody.appendChild(tr);
  });
}

document.getElementById('log-campaign').addEventListener('change', loadLogTable);
document.getElementById('log-status').addEventListener('change', loadLogTable);
document.getElementById('btn-refresh-logs').addEventListener('click', loadLogs);

document.getElementById('btn-retry-failed').addEventListener('click', async () => {
  const camp = document.getElementById('log-campaign').value;
  if (!camp) return;
  const res = await api.post('/api/logs/retry', {campaign: camp});
  if (res.error) return alert(res.error);
  // Gönder sekmesine yönlendir
  alert(`${res.count} başarısız alıcı için Gönder sekmesinden tekrar gönderim başlatabilirsiniz.`);
});

document.getElementById('btn-export-logs').addEventListener('click', async () => {
  const camp = document.getElementById('log-campaign').value;
  const rows = await api.get(`/api/logs?limit=10000${camp?'&campaign='+encodeURIComponent(camp):''}`);
  const header = ['ID','Ad','E-posta','Durum','Hata','Tarih','Tekrar'];
  const csv = [header, ...rows.map(r => [
    r.id, r.name, r.email, r.status, r.error_msg, r.sent_at, r.retried
  ])].map(row => row.map(v => `"${String(v||'').replace(/"/g,'""')}"`).join(',')).join('\n');
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,\uFEFF' + encodeURIComponent(csv);
  a.download = 'log.csv'; a.click();
});
