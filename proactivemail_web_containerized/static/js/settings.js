/* settings.js — SMTP ayarları */
'use strict';

const PRESETS = {
  gmail:   {host:'smtp.gmail.com',      port:587, conn:'starttls', auth:true,
             hint:'Gmail → Google Hesabım > Güvenlik > Uygulama Şifresi'},
  outlook: {host:'smtp.office365.com',  port:587, conn:'starttls', auth:true,
             hint:'Outlook → Hesap Ayarları > Uygulama Şifresi (2FA açıksa)'},
  exim:    {host:'localhost',           port:25,  conn:'plain',    auth:false,
             hint:'Exim local relay — kullanıcı adı / şifre gerekmez'},
};

document.getElementById('smtp-mode').addEventListener('change', applyPreset);
document.getElementById('smtp-conn').addEventListener('change', () => {
  const port = {starttls:587,ssl:465,plain:25}[document.getElementById('smtp-conn').value];
  document.getElementById('smtp-port').value = port;
});

function applyPreset() {
  const mode = document.getElementById('smtp-mode').value;
  const p    = PRESETS[mode];
  if (!p) return;
  document.getElementById('smtp-host').value = p.host;
  document.getElementById('smtp-port').value = p.port;
  document.getElementById('smtp-conn').value = p.conn;
  document.getElementById('smtp-hint').textContent = p.hint || '';
  document.getElementById('auth-group').style.display = p.auth ? '' : 'none';
}

async function loadSettings() {
  const s = await api.get('/api/settings');
  if (s.smtp_mode) {
    const sel = document.getElementById('smtp-mode');
    [...sel.options].forEach(o => { if (o.value === s.smtp_mode) sel.value = o.value; });
  }
  if (s.smtp_host)       document.getElementById('smtp-host').value    = s.smtp_host;
  if (s.smtp_port)       document.getElementById('smtp-port').value    = s.smtp_port;
  if (s.smtp_user)       document.getElementById('smtp-user').value    = s.smtp_user;
  if (s.smtp_from_email) document.getElementById('smtp-from').value    = s.smtp_from_email;
  if (s.smtp_from_name)  document.getElementById('smtp-name').value    = s.smtp_from_name;
  if (s.smtp_bounce)     document.getElementById('smtp-bounce').value  = s.smtp_bounce;
  if (s.smtp_reply_to)   document.getElementById('smtp-replyto').value = s.smtp_reply_to;
  if (s.smtp_conn_type)  document.getElementById('smtp-conn').value    = s.smtp_conn_type;
  if (s.smtp_delay_ms)   document.getElementById('smtp-delay').value   = s.smtp_delay_ms;
  if (s.smtp_batch_size) document.getElementById('smtp-batch').value   = s.smtp_batch_size;
  applyPreset();
}
window.loadSettings = loadSettings;

document.getElementById('btn-save-settings').addEventListener('click', async () => {
  const data = {
    smtp_mode:       document.getElementById('smtp-mode').value,
    smtp_host:       document.getElementById('smtp-host').value.trim(),
    smtp_port:       document.getElementById('smtp-port').value,
    smtp_user:       document.getElementById('smtp-user').value.trim(),
    smtp_password:   document.getElementById('smtp-pass').value,
    smtp_from_email: document.getElementById('smtp-from').value.trim(),
    smtp_from_name:  document.getElementById('smtp-name').value.trim(),
    smtp_bounce:     document.getElementById('smtp-bounce').value.trim(),
    smtp_reply_to:   document.getElementById('smtp-replyto').value.trim(),
    smtp_conn_type:  document.getElementById('smtp-conn').value,
    smtp_delay_ms:   document.getElementById('smtp-delay').value,
    smtp_batch_size: document.getElementById('smtp-batch').value,
  };
  await api.post('/api/settings', data);
  document.getElementById('smtp-test-result').textContent = '✅ Ayarlar kaydedildi.';
  document.getElementById('smtp-test-result').style.color = '#2ecc71';
});

document.getElementById('btn-test-smtp').addEventListener('click', async () => {
  const res = document.getElementById('smtp-test-result');
  res.textContent = '🔄 Test ediliyor...';
  res.style.color = 'var(--muted)';
  const data = {
    smtp_mode:      document.getElementById('smtp-mode').value,
    smtp_host:      document.getElementById('smtp-host').value.trim(),
    smtp_port:      document.getElementById('smtp-port').value,
    smtp_user:      document.getElementById('smtp-user').value.trim(),
    smtp_password:  document.getElementById('smtp-pass').value,
    smtp_conn_type: document.getElementById('smtp-conn').value,
  };
  const r = await api.post('/api/settings/test', data);
  res.textContent = r.message;
  res.style.color  = r.ok ? '#2ecc71' : '#e94560';
});
