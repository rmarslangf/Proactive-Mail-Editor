/* app.js — ProactiveMail Web — Temel altyapı */
'use strict';

// ── Dil paketleri (EN BAŞTA tanımla) ────────────────────────────────────────
const LANGS = {
  TR: {
    tab_editor:'✍️ Editör', tab_recipients:'👥 Alıcılar',
    tab_send:'🚀 Gönder', tab_logs:'📋 Geçmiş', tab_settings:'⚙️ Ayarlar',
    btn_save:'💾 Kaydet', btn_load:'📂 Yükle',
    btn_copy_html:'📋 HTML Kopyala', btn_export_html:'⬇ İndir',
    sec_info:'CAMPAIGN BİLGİSİ', sec_header:'HEADER', sec_footer:'FOOTER',
    sec_colors:'RENKLER', sec_addblock:'BLOK EKLE', sec_blocks:'İÇERİK BLOKLARI',
    subject_ph:'Konu...', btn_apply:'✔ Uygula',
    footer_ph:'Bu e-posta otomatik olarak gönderilmiştir.',
    hide_subject:'Başlığı Gizle', hide_footer:'Alt Yazıyı Gizle',
    palette_label:'İçerik Kutusu:', accent_label:'Vurgu:',
    font_label:'Font:', size_label:'Punto:',
    btn_clear_all:'🗑 Temizle', btn_clear_cont:'🧹 İçeriği Temizle',
    heading:'📌 Başlık', paragraph:'📝 Paragraf', quote:'❝ Alıntı',
    bullet_list:'• Madde', numbered_list:'1. Numaralı', divider:'─ Ayraç',
    button:'🔗 Buton', image_url:'🖼 Görsel URL', image_file:'🖼 Görsel Dosya',
    spacer:'↕ Boşluk', section:'🎨 Bölüm', toc:'📋 İçindekiler',
    highlight:'💡 Highlight', table:'📊 Tablo', cards:'👤 Kişi Kartları',
    emoji_row:'😊 Emoji',
    send_title:'🚀 Campaign Gönder', send_group_lbl:'Alıcı Grubu:',
    test_mode_lbl:'Test modu — sadece kendi e-postama gönder',
    btn_start:'🚀 Gönderimi Başlat', btn_stop:'⏹ Durdur',
    send_log_lbl:'GÖNDERİM LOGU',
    smtp_title:'⚙️ SMTP Ayarları', smtp_provider:'Sağlayıcı:',
    smtp_host:'Sunucu:', smtp_port:'Port:', smtp_user:'Kullanıcı adı:',
    smtp_pass:'Şifre:', smtp_from:'Gönderen e-posta:',
    smtp_name:'Gönderen adı:', smtp_bounce:'Bounce / Return-Path:',
    smtp_replyto:'Reply-To:', smtp_delay:'Mail arası bekleme:',
    smtp_batch:'Batch boyutu:', btn_test:'🔌 Bağlantıyı Test Et',
    btn_save_set:'💾 Kaydet',
    logs_title:'📋 Gönderim Geçmişi', btn_refresh:'🔄 Yenile',
    btn_retry:'🔁 Başarısızları Tekrar', btn_export_csv:'⬇ CSV',
    grp_label:'GRUPLAR', btn_add_grp:'+ Grup', btn_import:'📂 CSV',
    sub_all:'Tümü', sub_yes:'Abone', sub_no:'İptal',
    no_blocks:'Henüz blok yok. Yukarıdan ekleyin ↑',
    preview_lbl:'ÖNİZLEME',
  },
  EN: {
    tab_editor:'✍️ Editor', tab_recipients:'👥 Recipients',
    tab_send:'🚀 Send', tab_logs:'📋 History', tab_settings:'⚙️ Settings',
    btn_save:'💾 Save', btn_load:'📂 Load',
    btn_copy_html:'📋 Copy HTML', btn_export_html:'⬇ Download',
    sec_info:'CAMPAIGN INFO', sec_header:'HEADER', sec_footer:'FOOTER',
    sec_colors:'COLORS', sec_addblock:'ADD BLOCK', sec_blocks:'CONTENT BLOCKS',
    subject_ph:'Subject...', btn_apply:'✔ Apply',
    footer_ph:'This email was sent automatically.',
    hide_subject:'Hide Subject', hide_footer:'Hide Footer Text',
    palette_label:'Content Box:', accent_label:'Accent:',
    font_label:'Font:', size_label:'Size:',
    btn_clear_all:'🗑 Clear All', btn_clear_cont:'🧹 Clear Content',
    heading:'📌 Heading', paragraph:'📝 Paragraph', quote:'❝ Quote',
    bullet_list:'• Bullet', numbered_list:'1. Numbered', divider:'─ Divider',
    button:'🔗 Button', image_url:'🖼 Image URL', image_file:'🖼 Image File',
    spacer:'↕ Spacer', section:'🎨 Section', toc:'📋 Table of Contents',
    highlight:'💡 Highlight', table:'📊 Table', cards:'👤 Person Cards',
    emoji_row:'😊 Emoji',
    send_title:'🚀 Send Campaign', send_group_lbl:'Recipients:',
    test_mode_lbl:'Test mode — send only to my email',
    btn_start:'🚀 Start Sending', btn_stop:'⏹ Stop',
    send_log_lbl:'SEND LOG',
    smtp_title:'⚙️ SMTP Settings', smtp_provider:'Provider:',
    smtp_host:'Server:', smtp_port:'Port:', smtp_user:'Username:',
    smtp_pass:'Password:', smtp_from:'From email:',
    smtp_name:'From name:', smtp_bounce:'Bounce / Return-Path:',
    smtp_replyto:'Reply-To:', smtp_delay:'Delay between mails:',
    smtp_batch:'Batch size:', btn_test:'🔌 Test Connection',
    btn_save_set:'💾 Save',
    logs_title:'📋 Send History', btn_refresh:'🔄 Refresh',
    btn_retry:'🔁 Retry Failed', btn_export_csv:'⬇ CSV',
    grp_label:'GROUPS', btn_add_grp:'+ Group', btn_import:'📂 CSV',
    sub_all:'All', sub_yes:'Subscribed', sub_no:'Unsubscribed',
    no_blocks:'No blocks yet. Add one above ↑',
    preview_lbl:'PREVIEW',
  }
};

function t(key) {
  return (LANGS[PM.lang] || LANGS.TR)[key] || key;
}
window.t = t;

// ── Global state ─────────────────────────────────────────────────────────────
window.PM = {
  blocks: [],
  settings: {
    header_bg:'#1B3A5C', header_text_color:'#ffffff',
    footer_text:'Bu e-posta otomatik olarak gönderilmiştir.',
    footer_bg:'#1B3A5C', footer_text_color:'#AABCD0',
    box_bg:'#ffffff', accent:'#1B3A5C',
    global_font_family:'Georgia, serif', global_font_size:15,
    show_subject:true, show_footer_text:true,
  },
  subject: '',
  campaignId: null,
  lang: 'TR',
  headerB64: null,
  footerB64: null,
  dirty: false,
  groups: [],
  selectedGroup: null,
  selectedRec: null,
};

// ── API yardımcıları ─────────────────────────────────────────────────────────
const api = {
  async get(url)     { return fetch(url).then(r=>r.json()); },
  async post(url, d) { return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(r=>r.json()); },
  async put(url, d)  { return fetch(url,{method:'PUT', headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).then(r=>r.json()); },
  async del(url)     { return fetch(url,{method:'DELETE'}).then(r=>r.json()); },
};
window.api = api;

// ── Dil uygula ───────────────────────────────────────────────────────────────
function applyLang() {
  // Sekme butonları
  document.querySelectorAll('.tab-btn').forEach(btn => {
    const map = {editor:'tab_editor',recipients:'tab_recipients',
                 send:'tab_send',logs:'tab_logs',settings:'tab_settings'};
    if (map[btn.dataset.tab]) btn.textContent = t(map[btn.dataset.tab]);
  });

  // Butonlar
  const btnMap = {
    'btn-save-campaign':  'btn_save',
    'btn-load-campaign':  'btn_load',
    'btn-copy-html':      'btn_copy_html',
    'btn-export-html':    'btn_export_html',
    'btn-apply':          'btn_apply',
    'btn-clear-all':      'btn_clear_all',
    'btn-clear-content':  'btn_clear_cont',
    'btn-start-send':     'btn_start',
    'btn-stop-send':      'btn_stop',
    'btn-test-smtp':      'btn_test',
    'btn-save-settings':  'btn_save_set',
    'btn-refresh-logs':   'btn_refresh',
    'btn-retry-failed':   'btn_retry',
    'btn-export-logs':    'btn_export_csv',
    'btn-add-group':      'btn_add_grp',
    'btn-import-csv':     'btn_import',
  };
  Object.entries(btnMap).forEach(([id, key]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = t(key);
  });

  // data-lang attribute'lu elementler
  document.querySelectorAll('[data-lang]').forEach(el => {
    const v = t(el.dataset.lang);
    if (v !== el.dataset.lang) el.textContent = v;
  });

  // data-lang-h2
  document.querySelectorAll('[data-lang-h2]').forEach(el => {
    const v = t(el.dataset.langH2);
    if (v !== el.dataset.langH2) el.textContent = v;
  });

  // Placeholder'lar
  const subj = document.getElementById('subject');
  if (subj) subj.placeholder = t('subject_ph');
  const ftxt = document.getElementById('footer-text');
  if (ftxt) ftxt.placeholder = t('footer_ph');

  // Önizleme etiketi
  const prevLbl = document.querySelector('#right-panel .section-label');
  if (prevLbl) prevLbl.textContent = t('preview_lbl');

  // Blok ekle butonları
  document.querySelectorAll('#add-block-grid .add-block-btn').forEach(btn => {
    if (btn.dataset.btype) btn.textContent = t(btn.dataset.btype);
  });

  // Filtre seçenekleri
  const sf = document.getElementById('sub-filter');
  if (sf && sf.options.length >= 3) {
    sf.options[0].textContent = t('sub_all');
    sf.options[1].textContent = t('sub_yes');
    sf.options[2].textContent = t('sub_no');
  }

  // Boş durum etiketi
  const empty = document.getElementById('empty-lbl');
  if (empty) empty.textContent = t('no_blocks');

  // Blok kartlarını yeniden render et (type label değişir)
  if (typeof window.renderBlocks === 'function' && PM.blocks.length) {
    window.renderBlocks();
  }
}
window.applyLang = applyLang;

// ── Sekme yönetimi ───────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-'+tab).classList.add('active');
    if (tab==='recipients') window.loadRecipients && window.loadRecipients();
    if (tab==='send')       window.initSendTab   && window.initSendTab();
    if (tab==='logs')       window.loadLogs      && window.loadLogs();
    if (tab==='settings')   window.loadSettings  && window.loadSettings();
  });
});

// ── Palet ────────────────────────────────────────────────────────────────────
const PALETTE = ['#F5F7FA','#EEF2F7','#F0F4EE','#FDF6EC',
                 '#F4F0F8','#EAF2FB','#FAFAFA','#E8EDF2'];
const palRow = document.getElementById('palette-row');
if (palRow) PALETTE.forEach(c => {
  const d = document.createElement('div');
  d.className = 'color-dot'; d.style.background = c; d.title = c;
  d.addEventListener('click', () => {
    document.getElementById('box-bg').value = c;
    PM.settings.box_bg = c; schedulePreview();
  });
  palRow.appendChild(d);
});

// ── Renk & ayar inputları → state ───────────────────────────────────────────
function bindColor(id, key) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('input', () => { PM.settings[key]=el.value; markDirty(); });
}
bindColor('header-bg',        'header_bg');
bindColor('header-txt',       'header_text_color');
bindColor('footer-bg',        'footer_bg');
bindColor('footer-txt-color', 'footer_text_color');
bindColor('box-bg',           'box_bg');
bindColor('accent-color',     'accent');

document.getElementById('footer-text').addEventListener('input', e => {
  PM.settings.footer_text = e.target.value; markDirty();
});
document.getElementById('hide-subject').addEventListener('change', e => {
  PM.settings.show_subject = !e.target.checked; markDirty();
});
document.getElementById('hide-footer-txt').addEventListener('change', e => {
  PM.settings.show_footer_text = !e.target.checked; markDirty();
});
document.getElementById('global-font').addEventListener('change', e => {
  PM.settings.global_font_family = e.target.value; markDirty();
});
document.getElementById('global-size').addEventListener('input', e => {
  PM.settings.global_font_size = parseInt(e.target.value)||15; markDirty();
});
document.getElementById('subject').addEventListener('input', e => {
  PM.subject = e.target.value;
});

// ── Dil değiştir ─────────────────────────────────────────────────────────────
document.getElementById('lang-sel').addEventListener('change', e => {
  PM.lang = e.target.value;
  applyLang();
  markDirty();
});

// ── Header / Footer dosya seçimi ─────────────────────────────────────────────
function fileToB64(file) {
  return new Promise(res => {
    const r = new FileReader();
    r.onload = () => res(r.result);
    r.readAsDataURL(file);
  });
}
document.getElementById('header-file').addEventListener('change', async e => {
  if (e.target.files[0]) { PM.headerB64 = await fileToB64(e.target.files[0]); markDirty(); }
});
document.getElementById('footer-file').addEventListener('change', async e => {
  if (e.target.files[0]) { PM.footerB64 = await fileToB64(e.target.files[0]); markDirty(); }
});
document.getElementById('btn-clear-header').addEventListener('click', () => {
  PM.headerB64 = null; document.getElementById('header-file').value=''; markDirty();
});
document.getElementById('btn-clear-footer').addEventListener('click', () => {
  PM.footerB64 = null; document.getElementById('footer-file').value=''; markDirty();
});

// ── Dirty / Önizleme ─────────────────────────────────────────────────────────
let previewTimer = null;
function markDirty() {
  PM.dirty = true;
  const btn = document.getElementById('btn-apply');
  if (btn) { btn.style.background='#e94560'; btn.style.fontWeight='700'; }
  schedulePreview();
}
function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(refreshPreview, 600);
}
async function refreshPreview() {
  const payload = {
    subject:  PM.subject || 'ProactiveMail',
    blocks:   PM.blocks,
    settings: {
      ...PM.settings,
      header_b64: PM.headerB64 || null,
      footer_b64: PM.footerB64 || null,
    },
  };
  try {
    const res = await api.post('/api/campaigns/preview', payload);
    const frame = document.getElementById('preview-frame');
    const doc   = frame.contentDocument || frame.contentWindow.document;
    doc.open(); doc.write(res.html||''); doc.close();
    setTimeout(fitPreview, 150);
  } catch(e) { console.error('preview error', e); }
}
function fitPreview() {
  const frame = document.getElementById('preview-frame');
  try {
    const doc = frame.contentDocument || frame.contentWindow.document;
    const tbl = doc.querySelector('table[width]') || doc.querySelector('table table');
    if (!tbl) return;
    const vw = frame.offsetWidth - 32;
    const tw = tbl.offsetWidth || 600;
    const s  = Math.min(1, vw/tw);
    doc.body.style.transformOrigin = 'top center';
    doc.body.style.transform = `scale(${s})`;
    doc.body.style.width = `${100/s}%`;
    doc.body.style.margin = '0';
  } catch(e) {}
}
window.addEventListener('resize', fitPreview);

document.getElementById('btn-apply').addEventListener('click', () => {
  refreshPreview();
  PM.dirty = false;
  const btn = document.getElementById('btn-apply');
  btn.style.background=''; btn.style.fontWeight='';
});
document.getElementById('btn-refresh-preview').addEventListener('click', refreshPreview);

// ── HTML kopyala / indir ─────────────────────────────────────────────────────
async function getHtml() {
  const res = await api.post('/api/campaigns/preview', {
    subject: PM.subject || 'ProactiveMail',
    blocks: PM.blocks,
    settings: {
      ...PM.settings,
      header_b64: PM.headerB64 || null,
      footer_b64: PM.footerB64 || null,
    },
  });
  return res.html || '';
}
document.getElementById('btn-copy-html').addEventListener('click', async () => {
  navigator.clipboard.writeText(await getHtml());
  alert('HTML panoya kopyalandı!');
});
document.getElementById('btn-export-html').addEventListener('click', async () => {
  const html = await getHtml();
  const a = document.createElement('a');
  a.href = 'data:text/html;charset=utf-8,' + encodeURIComponent(html);
  a.download = (PM.subject||'campaign') + '.html';
  a.click();
});

// ── Campaign kaydet / yükle ──────────────────────────────────────────────────
document.getElementById('btn-save-campaign').addEventListener('click', async () => {
  const res = await api.post('/api/campaigns', {
    id: PM.campaignId,
    title: PM.subject || 'Adsız',
    subject: PM.subject,
    blocks: PM.blocks,
    settings: PM.settings,
  });
  PM.campaignId = res.id;
  PM.dirty = false;
  alert(PM.lang==='EN' ? 'Campaign saved.' : 'Campaign kaydedildi.');
});

document.getElementById('btn-load-campaign').addEventListener('click', async () => {
  const list = await api.get('/api/campaigns');
  const cl   = document.getElementById('campaign-list');
  cl.innerHTML = '';
  if (!list.length) { cl.innerHTML = '<p style="color:var(--muted);padding:12px">Kayıtlı campaign yok.</p>'; }
  list.forEach(c => {
    const div = document.createElement('div');
    div.className = 'group-item';
    div.style.justifyContent = 'space-between';
    div.innerHTML = `<span>${c.title}</span><span style="font-size:11px;color:var(--muted)">${(c.updated_at||'').slice(0,10)}</span>`;
    div.addEventListener('click', () => loadCampaign(c.id));
    cl.appendChild(div);
  });
  document.getElementById('modal-campaigns').classList.add('open');
});

document.getElementById('modal-camp-cancel').addEventListener('click', () => {
  document.getElementById('modal-campaigns').classList.remove('open');
});

async function loadCampaign(id) {
  document.getElementById('modal-campaigns').classList.remove('open');
  const c = await api.get(`/api/campaigns/${id}`);
  PM.campaignId = c.id;
  PM.subject    = c.subject;
  PM.blocks     = c.blocks || [];
  PM.settings   = { ...PM.settings, ...c.settings };
  document.getElementById('subject').value = c.subject;
  syncSettingsToUI();
  if (typeof window.renderBlocks === 'function') window.renderBlocks();
  refreshPreview();
}

function syncSettingsToUI() {
  const s = PM.settings;
  const set = (id, val) => { const el=document.getElementById(id); if(el) el.value=val||''; };
  const chk = (id, val) => { const el=document.getElementById(id); if(el) el.checked=!!val; };
  set('header-bg',        s.header_bg||'#1B3A5C');
  set('header-txt',       s.header_text_color||'#ffffff');
  set('footer-bg',        s.footer_bg||'#1B3A5C');
  set('footer-txt-color', s.footer_text_color||'#AABCD0');
  set('box-bg',           s.box_bg||'#ffffff');
  set('accent-color',     s.accent||'#1B3A5C');
  set('footer-text',      s.footer_text||'');
  set('global-size',      s.global_font_size||15);
  chk('hide-subject',     !s.show_subject);
  chk('hide-footer-txt',  !s.show_footer_text);
  const ff = document.getElementById('global-font');
  if (ff) [...ff.options].forEach(o => { if(o.value===s.global_font_family) ff.value=o.value; });
}
window.syncSettingsToUI = syncSettingsToUI;

// ── Temizle ──────────────────────────────────────────────────────────────────
document.getElementById('btn-clear-all').addEventListener('click', () => {
  if (!confirm(PM.lang==='EN'?'Delete all blocks?':'Tüm bloklar silinsin mi?')) return;
  PM.blocks = [];
  if (typeof window.renderBlocks==='function') window.renderBlocks();
  refreshPreview();
});
document.getElementById('btn-clear-content').addEventListener('click', () => {
  if (!confirm(PM.lang==='EN'?'Clear content blocks?':'İçerik blokları silinsin mi?')) return;
  PM.blocks = [];
  if (typeof window.renderBlocks==='function') window.renderBlocks();
  refreshPreview();
});

// ── İlk yükleme (DOM hazır, diğer JS'ler yüklendi) ─────────────────────────
window.addEventListener('load', () => {
  applyLang();
  refreshPreview();
});
