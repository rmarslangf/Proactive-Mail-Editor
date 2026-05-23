/* editor.js — Blok editörü */
'use strict';

const BLOCK_TYPES = [
  {type:'heading',      label:'📌 Başlık'},
  {type:'paragraph',    label:'📝 Paragraf'},
  {type:'quote',        label:'❝ Alıntı'},
  {type:'bullet_list',  label:'• Madde'},
  {type:'numbered_list',label:'1. Numaralı'},
  {type:'divider',      label:'─ Ayraç'},
  {type:'button',       label:'🔗 Buton'},
  {type:'image_url',    label:'🖼 Görsel URL'},
  {type:'image_file',   label:'🖼 Görsel Dosya'},
  {type:'spacer',       label:'↕ Boşluk'},
  {type:'section',      label:'🎨 Bölüm'},
  {type:'toc',          label:'📋 İçindekiler'},
  {type:'highlight',    label:'💡 Highlight'},
  {type:'table',        label:'📊 Tablo'},
  {type:'cards',        label:'👤 Kişi Kartları'},
  {type:'emoji_row',    label:'😊 Emoji'},
];

window.addEventListener('DOMContentLoaded', function() {


// ── Blok ekle butonları ───────────────────────────────────────────────────────
const grid = document.getElementById('add-block-grid');
BLOCK_TYPES.forEach(({type, label}) => {
  const btn = document.createElement('button');
  btn.className = 'add-block-btn';
  btn.dataset.btype = type;          // dil değişiminde güncellenir
  btn.textContent = (window.t && window.t(type) !== type) ? window.t(type) : label;
  btn.addEventListener('click', () => addBlock(type));
  grid.appendChild(btn);
});

function addBlock(type, data={}) {
  const blk = { type, ...defaultData(type), ...data };
  PM.blocks.push(blk);
  renderBlocks();
  markDirty();
}
window.addBlock = addBlock;

function defaultData(type) {
  const d = {
    heading:      {content:'', font_size:22},
    paragraph:    {content:'', font_size:15, inline_links:[]},
    quote:        {content:'', font_size:15},
    bullet_list:  {items:[], font_size:15, two_col:false},
    numbered_list:{items:[], font_size:15},
    divider:      {},
    button:       {text:'', url:''},
    image_url:    {url:'', alt:''},
    image_file:   {path:'', alt:''},
    spacer:       {height:24},
    section:      {bg:'#2C3E6B', lbl_clr:'#aaaaaa', ttl_clr:'#ffffff',
                   label:'', title:'', sec_items:[]},
    toc:          {items:[], cols:2, toc_txt:'#1B3A5C',
                   toc_bg:'#EAF2FB', toc_border:'#1B3A5C'},
    highlight:    {htype:'success', title:'', body:''},
    table:        {columns:'', rows:''},
    cards:        {items_raw:'', cols:2,
                   card_bg:'#f8fafc', card_border:'#dde3ea',
                   card_avatar:'#1B3A5C', card_name:'#1a1a2e',
                   card_role:'#6b7280', card_email:'#1B3A5C'},
    emoji_row:    {emojis:''},
  };
  return d[type] || {};
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderBlocks() {
  const list = document.getElementById('blocks-list');
  list.innerHTML = '';
  if (!PM.blocks.length) {
    list.innerHTML = '<div id="empty-lbl" style="color:#2a2a4a;font-size:13px;text-align:center;padding:20px">Henüz blok yok. Yukarıdan ekleyin ↑</div>';
    return;
  }
  PM.blocks.forEach((blk, idx) => {
    list.appendChild(buildBlockCard(blk, idx));
  });
  initDragDrop();
}
window.renderBlocks = renderBlocks;

// ── Blok kartı ────────────────────────────────────────────────────────────────
function buildBlockCard(blk, idx) {
  const card = document.createElement('div');
  card.className = 'block-card';
  card.dataset.idx = idx;

  const typeMeta = BLOCK_TYPES.find(b => b.type === blk.type) || {label: blk.type};
  const typeLabel = (window.t && window.t(blk.type) !== blk.type) ? window.t(blk.type) : typeMeta.label;

  card.innerHTML = `
    <div class="block-header">
      <span class="block-type-label">${typeLabel}</span>
      <button class="block-ctrl" data-action="up">▲</button>
      <button class="block-ctrl" data-action="dn">▼</button>
      <button class="block-ctrl del" data-action="del">✕</button>
    </div>
    <div class="block-body">${buildBlockBody(blk, idx)}</div>
  `;

  // Kontroller
  card.querySelector('[data-action=up]').addEventListener('click', () => moveBlock(idx, -1));
  card.querySelector('[data-action=dn]').addEventListener('click', () => moveBlock(idx, +1));
  card.querySelector('[data-action=del]').addEventListener('click', () => {
    PM.blocks.splice(idx, 1); renderBlocks(); markDirty();
  });

  // Input değişince → state güncelle
  card.querySelectorAll('input,textarea,select').forEach(el => {
    el.addEventListener('input', () => { syncBlockFromCard(card, idx); markDirty(); });
    el.addEventListener('change', () => { syncBlockFromCard(card, idx); markDirty(); });
  });

  return card;
}

function buildBlockBody(blk, idx) {
  const sp = (key, val, min=8, max=72) =>
    `<input type="number" data-key="${key}" value="${val||15}" min="${min}" max="${max}"
      style="width:52px;padding:3px" title="Punto">`;
  const col = (key, val) =>
    `<input type="color" data-key="${key}" value="${val||'#333333'}">`;
  const ti = (key, val, ph='') =>
    `<input type="text" data-key="${key}" value="${escH(val||'')}" placeholder="${ph}">`;
  const ta = (key, val, ph='', h=70) =>
    `<textarea data-key="${key}" style="height:${h}px;resize:vertical" placeholder="${ph}">${escH(val||'')}</textarea>`;

  switch(blk.type) {
    case 'heading':
    case 'paragraph':
    case 'quote': {
      const phMap = {heading:'Başlık...', paragraph:'Metin...', quote:'Alıntı...'};
      let html = `
        <div class="block-row">
          <label>Punto:</label>${sp('font_size', blk.font_size||15)}
          <label>Renk:</label>${col('text_color', blk.text_color||'#333333')}
        </div>
        ${ta('content', blk.content, phMap[blk.type], blk.type==='heading'?48:80)}
      `;
      if (blk.type === 'paragraph') {
        html += `<div class="block-row" style="margin-top:4px">
          <label style="font-size:10px;color:var(--muted)">🔗 Link metni:</label>
          ${ti('hl_text_0', (blk.inline_links||[])[0]?.text, 'Bu metni linkle...')}
          <label>→</label>
          ${ti('hl_url_0', (blk.inline_links||[])[0]?.url, 'https://')}
        </div>`;
      }
      if (blk.type === 'heading') {
        html += `<div class="block-row"><label>URL:</label>
          ${ti('block_url', blk.block_url, 'https://')}</div>`;
      }
      return html;
    }
    case 'bullet_list':
    case 'numbered_list': {
      let html = `
        <div class="block-row">
          <label>Punto:</label>${sp('font_size', blk.font_size||15)}
          <label>Renk:</label>${col('text_color', blk.text_color||'#333333')}
          ${blk.type==='bullet_list' ? `<label><input type="checkbox" data-key="two_col" ${blk.two_col?'checked':''}> 2 Sütun</label>` : ''}
        </div>
        ${ta('items_raw', (blk.items||[]).join('\n'), 'Her satır bir madde', 80)}
      `;
      return html;
    }
    case 'divider':
      return `<div style="border-top:1px solid #0f3460;margin:4px 0"></div>`;
    case 'button':
      return `<div class="block-row"><label>Metin:</label>${ti('text', blk.text, 'Buton metni')}</div>
        <div class="block-row"><label>URL:</label>${ti('url', blk.url, 'https://')}</div>`;
    case 'image_url':
      return `${ti('url', blk.url, 'https://domain.com/resim.jpg')}
        ${ti('alt', blk.alt, 'Açıklama')}`;
    case 'image_file':
      return `<div class="block-row"><label>Dosya:</label>
        <input type="file" data-key="file_pick" accept=".png,.jpg,.jpeg,.webp" style="flex:1">
        </div>${ti('alt', blk.alt, 'Açıklama')}`;
    case 'spacer':
      return `<div class="block-row"><label>Yükseklik (px):</label>
        ${sp('height', blk.height||24, 4, 200)}</div>`;
    case 'section':
      return `
        <div class="block-row"><label>Arkaplan:</label>${col('bg', blk.bg)}</div>
        <div class="block-row">
          ${col('lbl_clr', blk.lbl_clr)}<label>Etiket punto:</label>${sp('lbl_fs', blk.lbl_fs||11)}
          ${ti('label', blk.label, 'Küçük etiket...')}
        </div>
        <div class="block-row">
          ${col('ttl_clr', blk.ttl_clr)}<label>Başlık punto:</label>${sp('ttl_fs', blk.ttl_fs||26)}
          ${ti('title', blk.title, 'Büyük başlık...')}
        </div>
        <div id="sec-items-${idx}" class="sec-items-wrap"></div>
        <div class="block-row" style="margin-top:4px">
          <button class="add-block-btn" data-sec-add="para" data-sec-idx="${idx}">+ Paragraf</button>
          <button class="add-block-btn" data-sec-add="link" data-sec-idx="${idx}">+ Link</button>
        </div>`;
    case 'toc':
      return `
        <div class="block-row">
          <label>Sütun:</label><input type="number" data-key="cols" value="${blk.cols||2}" min="1" max="4" style="width:52px">
          <label>Yazı:</label>${col('toc_txt', blk.toc_txt)}
          <label>Zemin:</label>${col('toc_bg', blk.toc_bg)}
          <label>Kenarlık:</label>${col('toc_border', blk.toc_border)}
        </div>
        ${ta('items_raw', (blk.items||[]).join('\n'), 'Her satır bir başlık', 70)}`;
    case 'highlight':
      return `
        <div class="block-row"><label>Tür:</label>
          <select data-key="htype">
            <option value="success" ${blk.htype==='success'?'selected':''}>✅ Başarı</option>
            <option value="warning" ${blk.htype==='warning'?'selected':''}>⚠️ Uyarı</option>
            <option value="info"    ${blk.htype==='info'   ?'selected':''}>ℹ️ Bilgi</option>
            <option value="neutral" ${blk.htype==='neutral'?'selected':''}>◻️ Nötr</option>
          </select>
        </div>
        ${ti('title', blk.title, 'Başlık...')}
        ${ta('body', blk.body, 'Açıklama...', 60)}`;
    case 'table':
      return `
        ${ti('columns', blk.columns, 'Sütun1,Sütun2,Sütun3')}
        ${ta('rows', blk.rows, 'Satır1Col1,Satır1Col2\nSatır2Col1,...', 80)}`;
    case 'cards':
      return `
        <div class="block-row">
          <label>Sütun:</label><input type="number" data-key="cols" value="${blk.cols||2}" min="1" max="4" style="width:52px">
          <label>Zemin:</label>${col('card_bg',blk.card_bg)}
          <label>Kenarlık:</label>${col('card_border',blk.card_border)}
          <label>Avatar:</label>${col('card_avatar',blk.card_avatar)}
        </div>
        <div class="block-row">
          <label>İsim:</label>${col('card_name',blk.card_name)}
          <label>Unvan:</label>${col('card_role',blk.card_role)}
          <label>Email:</label>${col('card_email',blk.card_email)}
        </div>
        ${ta('items_raw', blk.items_raw||'', 'Ad|Unvan|email@ornek.com', 80)}`;
    case 'emoji_row':
      return ti('emojis', blk.emojis, '😊 👍 🎉 💡');
    default:
      return `<span style="color:var(--muted);font-size:11px">${blk.type}</span>`;
  }
}

function syncBlockFromCard(card, idx) {
  const blk = PM.blocks[idx];
  if (!blk) return;
  card.querySelectorAll('[data-key]').forEach(el => {
    const key = el.dataset.key;
    if (el.type === 'checkbox') blk[key] = el.checked;
    else if (el.type === 'number') blk[key] = parseFloat(el.value)||0;
    else if (el.type === 'file') {
      if (el.files[0]) {
        const r = new FileReader();
        r.onload = e => { blk.path = e.target.result; markDirty(); };
        r.readAsDataURL(el.files[0]);
      }
    }
    else blk[key] = el.value;
  });
  // items_raw → items
  if ('items_raw' in blk) {
    blk.items = blk.items_raw.split('\n').map(s=>s.trim()).filter(Boolean);
  }
  // inline link
  const ht0 = card.querySelector('[data-key=hl_text_0]');
  const hu0 = card.querySelector('[data-key=hl_url_0]');
  if (ht0 && hu0) {
    blk.inline_links = [{text: ht0.value, url: hu0.value}];
  }
}

// Section + / Link butonları (event delegation)
document.getElementById('blocks-list').addEventListener('click', e => {
  const addBtn = e.target.closest('[data-sec-add]');
  if (!addBtn) return;
  const itype = addBtn.dataset.secAdd;
  const idx   = parseInt(addBtn.dataset.secIdx);
  const blk   = PM.blocks[idx];
  if (!blk) return;
  blk.sec_items = blk.sec_items || [];
  blk.sec_items.push({type: itype, text:'', color: itype==='para'?'#cccccc':'#88bbdd', url:'', fs:14});
  renderBlocks();
  markDirty();
});

function moveBlock(idx, dir) {
  const ni = idx + dir;
  if (ni < 0 || ni >= PM.blocks.length) return;
  [PM.blocks[idx], PM.blocks[ni]] = [PM.blocks[ni], PM.blocks[idx]];
  renderBlocks(); markDirty();
}

function escH(s) {
  return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
}

// ── Drag & Drop ───────────────────────────────────────────────────────────────
function initDragDrop() {
  const cards = document.querySelectorAll('.block-card');
  let dragIdx = null;

  cards.forEach(card => {
    card.setAttribute('draggable', 'true');
    card.addEventListener('dragstart', e => {
      dragIdx = parseInt(card.dataset.idx);
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      document.querySelectorAll('.block-card').forEach(c => c.classList.remove('drag-over'));
    });
    card.addEventListener('dragover', e => {
      e.preventDefault(); card.classList.add('drag-over');
    });
    card.addEventListener('dragleave', () => card.classList.remove('drag-over'));
    card.addEventListener('drop', e => {
      e.preventDefault();
      const dstIdx = parseInt(card.dataset.idx);
      if (dragIdx === null || dragIdx === dstIdx) return;
      const moved = PM.blocks.splice(dragIdx, 1)[0];
      PM.blocks.splice(dstIdx, 0, moved);
      renderBlocks(); markDirty();
    });
  });
}

}); // DOMContentLoaded
