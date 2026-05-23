/* send.js — Gönderim sekmesi + SSE canlı ilerleme */
'use strict';

let evtSource = null;
let sentCnt = 0, failedCnt = 0;

function initSendTab() {
  loadGroups().then(() => {
    const gsel = document.getElementById('send-group');
    updateSendCount();
    gsel.addEventListener('change', updateSendCount);
  });
}
window.initSendTab = initSendTab;

async function loadGroups() {
  const groups = await api.get('/api/groups');
  PM.groups = groups;
  const sel = document.getElementById('send-group');
  const prev = sel.value;
  sel.innerHTML = '<option value="">Tüm aktif & abone alıcılar</option>';
  groups.forEach(g => {
    const o = document.createElement('option');
    o.value = g.id;
    o.textContent = `${g.name} (${g.count})`;
    sel.appendChild(o);
  });
  if (prev) sel.value = prev;
}

async function updateSendCount() {
  const gid = document.getElementById('send-group').value;
  let url = '/api/recipients?subscribed=yes';
  if (gid) url += `&group_id=${gid}`;
  const rows = await api.get(url);
  document.getElementById('send-count').textContent = `${rows.length} alıcı seçili`;
}

document.getElementById('btn-start-send').addEventListener('click', async () => {
  const subj = PM.subject || document.getElementById('subject').value || 'ProactiveMail';
  if (!subj) return alert('Konu satırı boş!');

  const gid      = document.getElementById('send-group').value || null;
  const testMode = document.getElementById('test-mode').checked;
  const campaign = `${subj} [${new Date().toLocaleString('tr-TR')}]`;

  const payload = {
    subject:   subj,
    blocks:    PM.blocks,
    settings:  PM.settings,
    group_id:  gid ? parseInt(gid) : null,
    test_mode: testMode,
    campaign,
  };

  const confirm_msg = testMode
    ? 'Test modunda sadece kendi adresinize gönderilecek. Devam edilsin mi?'
    : `Campaign gönderilsin mi?`;
  if (!confirm(confirm_msg)) return;

  const res = await api.post('/api/send/start', payload);
  if (res.error) return alert('Hata: ' + res.error);

  sentCnt = failedCnt = 0;
  document.getElementById('send-log').innerHTML = '';
  document.getElementById('send-progress-fill').style.width = '0%';
  updateStats(0, res.total);

  document.getElementById('btn-start-send').disabled = true;
  document.getElementById('btn-stop-send').disabled  = false;

  // SSE
  evtSource = new EventSource('/api/send/progress');
  evtSource.onmessage = e => {
    const ev = JSON.parse(e.data);
    if (ev.type === 'progress') {
      const pct = Math.round(ev.current / ev.total * 100);
      document.getElementById('send-progress-fill').style.width = pct + '%';
      if (ev.ok) { sentCnt++;   addLog(`✅ ${ev.email}`, 'log-ok'); }
      else        { failedCnt++; addLog(`❌ ${ev.email} — ${ev.error}`, 'log-fail'); }
      updateStats(ev.current, ev.total);
    } else if (ev.type === 'done') {
      addLog(`✅ Tamamlandı! Başarılı: ${ev.sent}  Başarısız: ${ev.failed}`, 'log-info');
      done();
    } else if (ev.type === 'stopped') {
      addLog('⏹ Durduruldu.', 'log-info'); done();
    }
  };
  evtSource.onerror = () => { addLog('❌ Bağlantı kesildi.', 'log-fail'); done(); };
});

document.getElementById('btn-stop-send').addEventListener('click', async () => {
  await api.post('/api/send/stop');
  if (evtSource) { evtSource.close(); evtSource = null; }
  done();
});

function done() {
  document.getElementById('btn-start-send').disabled = false;
  document.getElementById('btn-stop-send').disabled  = true;
  if (evtSource) { evtSource.close(); evtSource = null; }
}

function addLog(msg, cls='') {
  const log = document.getElementById('send-log');
  const ts  = new Date().toLocaleTimeString('tr-TR');
  const div = document.createElement('div');
  div.className = cls;
  div.textContent = `[${ts}] ${msg}`;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

function updateStats(cur, total) {
  document.getElementById('stat-sent').textContent   = `✅ ${sentCnt}`;
  document.getElementById('stat-failed').textContent = `❌ ${failedCnt}`;
  document.getElementById('stat-total').textContent  = `/ ${total}`;
}
