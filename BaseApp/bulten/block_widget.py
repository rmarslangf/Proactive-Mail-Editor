"""
block_widget.py — İçerik bloğu widget'ı (BlockWidget).
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QSpinBox, QToolButton, QPushButton, QFileDialog,
    QComboBox, QCheckBox, QMainWindow
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDrag, QPixmap
from PyQt5.QtCore import QMimeData

from .lang import LANG
from .utils import make_color_btn

class BlockWidget(QFrame):
    def __init__(self, block_type, data=None, lang="TR", parent=None):
        super().__init__(parent)
        self.block_type  = block_type
        self.lang        = lang
        self.inputs      = {}
        self.sig_delete  = None
        self.sig_move_up = None
        self.sig_move_dn = None
        self.setObjectName("block_card")
        self.setAcceptDrops(True)
        self._drag_start = None
        self._build(data or {})

    def mousePressEvent(self, event):
        from PyQt5.QtCore import Qt as _Qt
        if event.button() == _Qt.LeftButton:
            self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        from PyQt5.QtCore import Qt as _Qt, QMimeData
        from PyQt5.QtGui import QDrag, QPixmap
        if not (event.buttons() & _Qt.LeftButton): return
        if self._drag_start is None: return
        if (event.pos() - self._drag_start).manhattanLength() < 10: return
        drag = QDrag(self)
        mime = QMimeData()
        # Blok index'ini mime'a yaz
        parent_win = self._find_main_window()
        if parent_win and self in parent_win.blocks:
            mime.setText(str(parent_win.blocks.index(self)))
        drag.setMimeData(mime)
        # Küçük önizleme
        pix = QPixmap(self.size())
        pix.fill()
        self.render(pix)
        drag.setPixmap(pix.scaled(200, 60))
        drag.setHotSpot(event.pos())
        drag.exec_()

    def _find_main_window(self):
        w = self.parent()
        while w:
            if isinstance(w, QMainWindow): return w
            w = w.parent() if hasattr(w,"parent") else None
        return None

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()

    def dropEvent(self, event):
        parent_win = self._find_main_window()
        if not parent_win: return
        try:
            src_idx = int(event.mimeData().text())
            dst_idx = parent_win.blocks.index(self)
            if src_idx == dst_idx: return
            # Swap
            blk = parent_win.blocks.pop(src_idx)
            parent_win.blocks.insert(dst_idx, blk)
            parent_win._rebuild_layout()
        except Exception:
            pass

    def _t(self, key):
        return LANG[self.lang].get(key, key)

    def _build(self, data):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # başlık çubuğu
        bar = QHBoxLayout()
        type_labels = {
            "heading":      self._t("block_heading"),
            "paragraph":    self._t("block_paragraph"),
            "quote":        self._t("block_quote"),
            "bullet_list":  self._t("block_bullet"),
            "numbered_list":self._t("block_numbered"),
            "divider":      self._t("block_divider"),
            "button":       self._t("block_button"),
            "image_url":    self._t("block_image_url"),
            "image_file":   self._t("block_image_file"),
            "spacer":       self._t("block_spacer"),
            "section":      self._t("block_section"),
            "toc":          self._t("block_toc"),
            "highlight":    self._t("block_highlight"),
            "table":        self._t("block_table"),
            "cards":        self._t("block_cards"),
            "emoji_row":    self._t("block_emoji_row"),
        }
        lbl = QLabel(type_labels.get(self.block_type, self.block_type))
        lbl.setStyleSheet("font-weight:700;font-size:12px;color:#e94560;letter-spacing:1px;")
        bar.addWidget(lbl); bar.addStretch()

        for txt, attr in [("▲","sig_move_up"),("▼","sig_move_dn"),("✕","sig_delete")]:
            b = QToolButton(); b.setText(txt); b.setFixedSize(22,22)
            if txt == "✕":
                b.setStyleSheet("color:#e94560;border-color:#e9456040;")
            _attr = attr
            b.clicked.connect(lambda _, a=_attr: getattr(self, a) and getattr(self, a)(self))
            bar.addWidget(b)
        root.addLayout(bar)

        # ── Font & Punto satırı (metin içeren bloklar)
        _TEXT_TYPES = ("heading","paragraph","quote","bullet_list","numbered_list",
                       "button","section","toc","highlight","table","cards","emoji_row")
        if self.block_type in _TEXT_TYPES:
            from PyQt5.QtWidgets import QComboBox as _QCB
            frow = QHBoxLayout(); frow.setSpacing(6)
            # Font ailesi
            frow.addWidget(QLabel(self._t("font_family_lbl")))
            _ff_cb = _QCB()
            _FONTS = ["Georgia, serif","Arial, sans-serif","Helvetica, sans-serif",
                      "Times New Roman, serif","Trebuchet MS, sans-serif",
                      "Verdana, sans-serif","Tahoma, sans-serif",
                      "Courier New, monospace","Palatino, serif"]
            _ff_cb.addItems([f.split(",")[0] for f in _FONTS])
            _ff_cb.setFixedWidth(150)
            _saved_ff = data.get("font_family", "")
            if _saved_ff:
                _idx = next((i for i,f in enumerate(_FONTS) if f == _saved_ff), 0)
                _ff_cb.setCurrentIndex(_idx)
            _mw2 = self._find_main_window()
            if _mw2: _ff_cb.currentIndexChanged.connect(lambda _: _mw2._mark_dirty())
            frow.addWidget(_ff_cb)
            self.inputs["_font_list"] = _FONTS
            self.inputs["font_family_cb"] = _ff_cb
            # Punto
            frow.addSpacing(8)
            frow.addWidget(QLabel(self._t("font_size_lbl")))
            _default_fs = {"heading":22,"quote":15}.get(self.block_type, 15)
            _fs_sp = QSpinBox(); _fs_sp.setRange(8, 48); _fs_sp.setValue(data.get("font_size", _default_fs))
            _fs_sp.setFixedWidth(60)
            _fs_sp.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:6px;padding:3px;")
            # Değişince _mark_dirty tetikle
            _mw = self._find_main_window()
            if _mw: _fs_sp.valueChanged.connect(lambda _: _mw._mark_dirty())
            frow.addWidget(_fs_sp)
            self.inputs["font_size_sp"] = _fs_sp
            # Renk seçici
            _COLOR_TYPES = ("heading","paragraph","quote","bullet_list","numbered_list")
            if self.block_type in _COLOR_TYPES:
                frow.addSpacing(8)
                frow.addWidget(QLabel(self._t("text_color_lbl")))
                _saved_color = data.get("text_color", "#333333")
                _inp_ref = self.inputs
                _col_btn = make_color_btn(_saved_color,
                    lambda v, _r=_inp_ref: _r.__setitem__("text_color", v))
                self.inputs["text_color"] = _saved_color
                frow.addWidget(_col_btn)
            frow.addStretch()
            root.addLayout(frow)
            # URL satırı
            url_row = QHBoxLayout()
            _url_lbl = QLabel(self._t("block_url_lbl"))
            _url_lbl.setFixedWidth(46)
            _url_e = QLineEdit(data.get("block_url", ""))
            _url_e.setPlaceholderText(self._t("block_url_ph"))
            url_row.addWidget(_url_lbl); url_row.addWidget(_url_e)
            root.addLayout(url_row)
            self.inputs["block_url"] = _url_e

        t = self.block_type
        if t in ("heading","paragraph","quote"):
            ph = {"heading": self._t("ph_heading"),
                  "paragraph": self._t("ph_paragraph"),
                  "quote": self._t("ph_quote")}[t]
            te = QTextEdit(); te.setPlaceholderText(ph)
            te.setFixedHeight(52 if t == "heading" else 80)
            te.setAcceptRichText(False)  # enter = gerçek newline
            te.setPlainText(data.get("content",""))
            root.addWidget(te)
            self.inputs["content"] = te
            # Çoklu inline hyperlink sistemi (sadece paragraph için)
            if t == "paragraph":
                # Paragraf mesafesi
                _mr = QHBoxLayout()
                _mr.addWidget(QLabel("↕ Üst (px):"))
                _mt = QSpinBox(); _mt.setRange(0,80); _mt.setValue(data.get("para_margin_top",12))
                _mt.setFixedWidth(52)
                _mt.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:6px;padding:3px;")
                _mww = self._find_main_window()
                if _mww: _mt.valueChanged.connect(lambda _: _mww._mark_dirty())
                _mr.addWidget(_mt)
                _mr.addSpacing(10)
                _mr.addWidget(QLabel("Alt (px):"))
                _mb = QSpinBox(); _mb.setRange(0,80); _mb.setValue(data.get("para_margin_bottom",12))
                _mb.setFixedWidth(52)
                _mb.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:6px;padding:3px;")
                if _mww: _mb.valueChanged.connect(lambda _: _mww._mark_dirty())
                _mr.addWidget(_mb)
                _mr.addStretch()
                root.addLayout(_mr)
                self.inputs["para_margin_top"]    = _mt
                self.inputs["para_margin_bottom"] = _mb
                _hl_hint = QLabel("🔗 " + self._t("hyperlink_hint"))
                _hl_hint.setStyleSheet("color:#5a5a8a;font-size:11px;")
                root.addWidget(_hl_hint)
                # Mevcut linkleri yükle
                self._inline_links = []        # list of (txt_e, url_e, frame)
                self._inline_links_layout = QVBoxLayout()
                self._inline_links_layout.setSpacing(3)
                root.addLayout(self._inline_links_layout)
                for _lk in data.get("inline_links", []):
                    self._add_inline_link(_lk.get("text",""), _lk.get("url",""))
                # Ekle butonu
                _btn_addlk = QPushButton("+ " + self._t("hyperlink_lbl"))
                _btn_addlk.setObjectName("ghost")
                _btn_addlk.setFixedHeight(24)
                _btn_addlk.setStyleSheet("font-size:11px;padding:2px 8px;")
                _btn_addlk.clicked.connect(lambda: self._add_inline_link())
                root.addWidget(_btn_addlk)

        elif t in ("bullet_list","numbered_list"):
            te = QTextEdit(); te.setPlaceholderText(self._t("ph_list"))
            te.setFixedHeight(90)
            te.setPlainText("\n".join(data.get("items",[])))
            root.addWidget(te); self.inputs["items_text"] = te
            if t == "bullet_list":
                from PyQt5.QtWidgets import QCheckBox
                cb = QCheckBox(self._t("two_col"))
                cb.setChecked(bool(data.get("two_col", False)))
                cb.setStyleSheet("color:#a0a0c0;font-size:12px;")
                root.addWidget(cb)
                self.inputs["two_col"] = cb

        elif t == "divider":
            root.addWidget(QLabel("─ ─ ─ ─ ─ ─ ─ ─ ─"))

        elif t == "button":
            r = QHBoxLayout()
            te = QLineEdit(data.get("text","")); te.setPlaceholderText(self._t("ph_btn_text"))
            ue = QLineEdit(data.get("url",""));  ue.setPlaceholderText(self._t("ph_btn_url"))
            r.addWidget(QLabel(self._t("btn_text_lbl"))); r.addWidget(te)
            r.addWidget(QLabel(self._t("btn_url_lbl")));  r.addWidget(ue)
            root.addLayout(r)
            self.inputs["text"] = te; self.inputs["url"] = ue

        elif t == "image_url":
            ue = QLineEdit(data.get("url","")); ue.setPlaceholderText(self._t("ph_img_url"))
            ae = QLineEdit(data.get("alt","")); ae.setPlaceholderText(self._t("ph_img_alt"))
            root.addWidget(ue); root.addWidget(ae)
            self.inputs["url"] = ue; self.inputs["alt"] = ae

        elif t == "image_file":
            # Dosyadan resim seç
            fr = QHBoxLayout()
            self._img_lbl = QLabel(os.path.basename(data.get("path","")) or self._t("img_file_lbl"))
            self._img_lbl.setObjectName("subtitle")
            self._img_lbl.setWordWrap(True)
            btn_sel = QPushButton(self._t("img_select_btn"))
            btn_sel.setObjectName("ghost"); btn_sel.setFixedWidth(110)
            btn_sel.clicked.connect(self._pick_file)
            fr.addWidget(self._img_lbl,1); fr.addWidget(btn_sel)
            root.addLayout(fr)
            ae = QLineEdit(data.get("alt","")); ae.setPlaceholderText(self._t("ph_img_alt"))
            root.addWidget(ae)
            self.inputs["path"] = data.get("path","")
            self.inputs["alt"]  = ae
            self.inputs["_img_lbl"] = self._img_lbl

        elif t == "spacer":
            r = QHBoxLayout()
            sp = QSpinBox(); sp.setRange(4,200); sp.setValue(data.get("height",24))
            sp.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:6px;padding:4px;")
            r.addWidget(QLabel(self._t("height_lbl"))); r.addWidget(sp); r.addStretch()
            root.addLayout(r); self.inputs["height"] = sp

        elif t == "section":
            # Arkaplan
            r1 = QHBoxLayout()
            r1.addWidget(QLabel(self._t("section_bg_lbl")))
            _sb = make_color_btn(data.get("bg","#2C3E6B"),
                lambda v, r=self.inputs: r.__setitem__("bg", v))
            r1.addWidget(_sb); r1.addStretch()
            self.inputs["bg"] = data.get("bg","#2C3E6B")
            root.addLayout(r1)
            def _mk_sp(val, inp, key):
                _s = QSpinBox(); _s.setRange(8,72); _s.setValue(val)
                _s.setFixedWidth(52)
                _s.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:4px;padding:3px;font-size:11px;")
                _mw = self._find_main_window()
                if _mw: _s.valueChanged.connect(lambda _: _mw._mark_dirty())
                inp[key] = _s; return _s
            # Etiket (küçük başlık)
            _lr = QHBoxLayout()
            lbl_e = QLineEdit(data.get("label","")); lbl_e.setPlaceholderText(self._t("section_label_ph"))
            _lc = make_color_btn(data.get("lbl_clr","#aaaaaa"),
                lambda v, r=self.inputs: r.__setitem__("lbl_clr", v))
            self.inputs["lbl_clr"] = data.get("lbl_clr","#aaaaaa")
            _lsp = _mk_sp(data.get("lbl_fs",11), self.inputs, "lbl_fs")
            _lr.addWidget(QLabel(self._t("section_lbl_clr"))); _lr.addWidget(_lc)
            _lr.addWidget(QLabel("pt")); _lr.addWidget(_lsp)
            _lr.addSpacing(6); _lr.addWidget(lbl_e, 1)
            root.addLayout(_lr)
            # Büyük başlık
            _tr = QHBoxLayout()
            ttl_e = QLineEdit(data.get("title","")); ttl_e.setPlaceholderText(self._t("section_title_ph"))
            _tc = make_color_btn(data.get("ttl_clr","#ffffff"),
                lambda v, r=self.inputs: r.__setitem__("ttl_clr", v))
            self.inputs["ttl_clr"] = data.get("ttl_clr","#ffffff")
            _tsp = _mk_sp(data.get("ttl_fs",26), self.inputs, "ttl_fs")
            _tr.addWidget(QLabel(self._t("section_ttl_clr"))); _tr.addWidget(_tc)
            _tr.addWidget(QLabel("pt")); _tr.addWidget(_tsp)
            _tr.addSpacing(6); _tr.addWidget(ttl_e, 1)
            root.addLayout(_tr)
            # ── Mini içerik editörü
            _hint_lbl = QLabel(self._t("sec_items_hint"))
            _hint_lbl.setStyleSheet("color:#5a5a8a;font-size:11px;font-weight:700;")
            root.addWidget(_hint_lbl)
            # Dinamik içerik listesi container
            self._sec_items_layout = QVBoxLayout()
            self._sec_items_layout.setSpacing(4)
            self._sec_items_data = []   # list of dicts
            root.addLayout(self._sec_items_layout)
            # Mevcut kayıtlı içerikleri yükle
            for _si in data.get("sec_items", []):
                self._add_sec_item(_si)
            # Butonlar
            _sbtn_row = QHBoxLayout()
            _btn_para = QPushButton(self._t("sec_add_para"))
            _btn_para.setObjectName("ghost"); _btn_para.setFixedHeight(26)
            _btn_para.setStyleSheet("font-size:11px;padding:3px 10px;")
            _btn_para.clicked.connect(lambda: self._add_sec_item({"type":"para"}))
            _btn_link = QPushButton(self._t("sec_add_link"))
            _btn_link.setObjectName("ghost"); _btn_link.setFixedHeight(26)
            _btn_link.setStyleSheet("font-size:11px;padding:3px 10px;")
            _btn_link.clicked.connect(lambda: self._add_sec_item({"type":"link"}))
            _sbtn_row.addWidget(_btn_para); _sbtn_row.addWidget(_btn_link); _sbtn_row.addStretch()
            root.addLayout(_sbtn_row)
            self.inputs["label_e"] = lbl_e
            self.inputs["title_e"] = ttl_e

        elif t == "toc":
            hint = QLabel("Her satır = bir içindekiler öğesi")
            hint.setStyleSheet("color:#5a5a8a;font-size:11px;")
            root.addWidget(hint)
            te = QTextEdit(); te.setPlaceholderText(self._t("toc_items_ph")); te.setFixedHeight(80)
            te.setPlainText("\n".join(data.get("items",[])))
            root.addWidget(te); self.inputs["items_text"] = te
            r2 = QHBoxLayout()
            r2.addWidget(QLabel(self._t("toc_cols_lbl")))
            sp2 = QSpinBox(); sp2.setRange(1,4); sp2.setValue(data.get("cols",2))
            sp2.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:6px;padding:4px;")
            r2.addWidget(sp2); r2.addStretch()
            root.addLayout(r2); self.inputs["cols"] = sp2
            # Renk seçiciler
            _tc_row = QHBoxLayout(); _tc_row.setSpacing(6)
            for _ck, _lk, _cd in [
                ("toc_txt",    "toc_txt_lbl",    "#1B3A5C"),
                ("toc_bg",     "toc_bg_lbl",     "#EAF2FB"),
                ("toc_border", "toc_border_lbl", "#1B3A5C"),
            ]:
                _val = data.get(_ck, _cd)
                _inp_r = self.inputs
                _btn_c = make_color_btn(_val,
                    (lambda _k=_ck, _r=_inp_r: lambda v, k=_k, r=_inp_r: r.__setitem__(k, v))())
                self.inputs[_ck] = _val
                _tc_row.addWidget(QLabel(self._t(_lk)))
                _tc_row.addWidget(_btn_c)
                _tc_row.addSpacing(6)
            _tc_row.addStretch()
            root.addLayout(_tc_row)

        elif t == "highlight":
            from PyQt5.QtWidgets import QComboBox as QCB
            r3 = QHBoxLayout()
            r3.addWidget(QLabel(self._t("hl_type_lbl")))
            cb2 = QCB()
            cb2.addItems([self._t("hl_success"), self._t("hl_warning"), self._t("hl_info"), self._t("hl_neutral")])
            htype_map = {"success":0,"warning":1,"info":2,"neutral":3}
            cb2.setCurrentIndex(htype_map.get(data.get("htype","success"),0))
            r3.addWidget(cb2); r3.addStretch()
            root.addLayout(r3)
            ttl2 = QLineEdit(data.get("title","")); ttl2.setPlaceholderText(self._t("hl_title_ph"))
            bdy2 = QTextEdit(); bdy2.setPlaceholderText(self._t("hl_body_ph")); bdy2.setFixedHeight(70)
            bdy2.setPlainText(data.get("body",""))
            root.addWidget(ttl2); root.addWidget(bdy2)
            self.inputs["htype_cb"] = cb2
            self.inputs["title_e"]  = ttl2
            self.inputs["body_e"]   = bdy2

        elif t == "table":
            hint2 = QLabel("Sutunlar: virgülle | Satirlar: her satir ayri")
            hint2.setStyleSheet("color:#5a5a8a;font-size:11px;")
            root.addWidget(hint2)
            cols_e = QLineEdit(data.get("columns","")); cols_e.setPlaceholderText(self._t("tbl_cols_ph"))
            rows_e = QTextEdit(); rows_e.setPlaceholderText(self._t("tbl_rows_ph")); rows_e.setFixedHeight(90)
            rows_e.setPlainText(data.get("rows",""))
            root.addWidget(cols_e); root.addWidget(rows_e)
            self.inputs["columns_e"] = cols_e
            self.inputs["rows_e"]    = rows_e

        elif t == "cards":
            hint3 = QLabel("Her satir: Ad|Unvan|email (| ile ayrilmis)")
            hint3.setStyleSheet("color:#5a5a8a;font-size:11px;")
            root.addWidget(hint3)
            te3 = QTextEdit(); te3.setPlaceholderText(self._t("card_items_ph")); te3.setFixedHeight(90)
            te3.setPlainText(data.get("items_raw",""))
            root.addWidget(te3); self.inputs["items_raw_e"] = te3
            # Sütun sayısı
            r4 = QHBoxLayout()
            r4.addWidget(QLabel(self._t("card_cols_lbl")))
            sp4 = QSpinBox(); sp4.setRange(1,4); sp4.setValue(data.get("cols",2))
            sp4.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:6px;padding:4px;")
            r4.addWidget(sp4); r4.addStretch()
            root.addLayout(r4); self.inputs["cols4"] = sp4
            # Renk seçiciler — satır 1
            _cr1 = QHBoxLayout(); _cr1.setSpacing(6)
            _card_colors = [
                ("card_bg",     "card_bg_lbl",     "#f8fafc"),
                ("card_border", "card_border_lbl", "#dde3ea"),
                ("card_avatar", "card_avatar_lbl", "#1B3A5C"),
            ]
            for _ck, _lk, _cd in _card_colors:
                _val = data.get(_ck, _cd)
                _inp_r = self.inputs
                _btn_c = make_color_btn(_val,
                    (lambda _k=_ck, _r=_inp_r: lambda v, k=_k, r=_inp_r: r.__setitem__(k, v))())
                self.inputs[_ck] = _val
                _cr1.addWidget(QLabel(self._t(_lk)))
                _cr1.addWidget(_btn_c)
                _cr1.addSpacing(6)
            _cr1.addStretch()
            root.addLayout(_cr1)
            # Renk seçiciler — satır 2
            _cr2 = QHBoxLayout(); _cr2.setSpacing(6)
            _card_colors2 = [
                ("card_name",  "card_name_lbl",  "#1a1a2e"),
                ("card_role",  "card_role_lbl",  "#6b7280"),
                ("card_email", "card_email_lbl", "#1B3A5C"),
            ]
            for _ck, _lk, _cd in _card_colors2:
                _val = data.get(_ck, _cd)
                _inp_r = self.inputs
                _btn_c = make_color_btn(_val,
                    (lambda _k=_ck, _r=_inp_r: lambda v, k=_k, r=_inp_r: r.__setitem__(k, v))())
                self.inputs[_ck] = _val
                _cr2.addWidget(QLabel(self._t(_lk)))
                _cr2.addWidget(_btn_c)
                _cr2.addSpacing(6)
            _cr2.addStretch()
            root.addLayout(_cr2)

        elif t == "emoji_row":
            ee = QLineEdit(data.get("emojis","")); ee.setPlaceholderText(self._t("emoji_ph"))
            root.addWidget(ee); self.inputs["emojis_e"] = ee

    def _add_inline_link(self, text="", url=""):
        """Paragraf bloğuna inline link satırı ekler."""
        frame = QFrame()
        frame.setStyleSheet("QFrame{background:#0a1520;border:1px solid #1a3050;border-radius:5px;}")
        fh = QHBoxLayout(frame); fh.setContentsMargins(6,4,6,4); fh.setSpacing(4)
        txt_e = QLineEdit(text); txt_e.setPlaceholderText(self._t("hyperlink_text"))
        txt_e.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:4px;padding:3px;font-size:12px;")
        url_e = QLineEdit(url);  url_e.setPlaceholderText("https://")
        url_e.setStyleSheet("background:#0d1b2a;color:#88bbff;border:1px solid #0f3460;border-radius:4px;padding:3px;font-size:12px;")
        btn_del = QToolButton(); btn_del.setText("✕"); btn_del.setFixedSize(18,18)
        btn_del.setStyleSheet("color:#e94560;background:transparent;border:none;font-size:12px;")
        fh.addWidget(QLabel("Metin:"))
        fh.addWidget(txt_e, 2)
        fh.addWidget(QLabel("→"))
        fh.addWidget(url_e, 3)
        fh.addWidget(btn_del)
        entry = (txt_e, url_e, frame)
        self._inline_links.append(entry)
        self._inline_links_layout.addWidget(frame)
        _eid = id(entry)
        _fref = frame
        def _do_rm(_f=_fref, _id=_eid):
            idx = next((i for i,e in enumerate(self._inline_links) if id(e)==_id), None)
            if idx is not None:
                self._inline_links.pop(idx)
            self._inline_links_layout.removeWidget(_f)
            _f.setParent(None)
            _f.deleteLater()
        btn_del.clicked.connect(lambda _=None: _do_rm())
        _mw = self._find_main_window()
        if _mw: _mw._mark_dirty()

    def _add_sec_item(self, item_data=None):
        """Section içine dinamik paragraf veya link satırı ekler."""
        item_data = item_data or {"type":"para"}
        itype = item_data.get("type","para")

        # Satır frame
        frame = QFrame()
        frame.setStyleSheet("QFrame{background:#0a1520;border:1px solid #1a3050;border-radius:6px;}")
        fv = QVBoxLayout(frame); fv.setContentsMargins(8,6,8,6); fv.setSpacing(4)

        # Üst: tür etiketi + sil butonu
        top = QHBoxLayout()
        icon = "¶ Paragraf" if itype == "para" else "🔗 Link"
        top.addWidget(QLabel(icon))
        top.addStretch()
        btn_del = QToolButton(); btn_del.setText("✕"); btn_del.setFixedSize(18,18)
        btn_del.setStyleSheet("color:#e94560;background:transparent;border:none;")
        fv.addLayout(top)

        item_dict = {"type": itype, "frame": frame}

        if itype == "para":
            # Renk + punto + metin
            crow = QHBoxLayout()
            _col = make_color_btn(item_data.get("color","#cccccc"),
                lambda v, d=item_dict: d.__setitem__("color", v))
            item_dict["color"] = item_data.get("color","#cccccc")
            _psp = QSpinBox(); _psp.setRange(8,48); _psp.setValue(item_data.get("fs",14))
            _psp.setFixedWidth(48)
            _psp.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:4px;padding:2px;")
            _mwp = self._find_main_window()
            if _mwp: _psp.valueChanged.connect(lambda _: _mwp._mark_dirty())
            item_dict["fs_sp"] = _psp
            crow.addWidget(QLabel("🎨")); crow.addWidget(_col)
            crow.addWidget(QLabel("pt")); crow.addWidget(_psp)
            crow.addSpacing(4)
            te = QTextEdit(); te.setFixedHeight(60); te.setAcceptRichText(False)
            te.setPlaceholderText("Paragraf metni... (Enter = yeni satır)")
            te.setPlainText(item_data.get("text",""))
            te.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:5px;font-size:12px;")
            crow.addWidget(te, 1)
            fv.addLayout(crow)
            item_dict["te"] = te

        elif itype == "link":
            # Link metni + URL + renk + punto
            r1 = QHBoxLayout()
            _col = make_color_btn(item_data.get("color","#88bbdd"),
                lambda v, d=item_dict: d.__setitem__("color", v))
            item_dict["color"] = item_data.get("color","#88bbdd")
            _lsp = QSpinBox(); _lsp.setRange(8,48); _lsp.setValue(item_data.get("fs",14))
            _lsp.setFixedWidth(48)
            _lsp.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:4px;padding:2px;")
            _mwl = self._find_main_window()
            if _mwl: _lsp.valueChanged.connect(lambda _: _mwl._mark_dirty())
            item_dict["fs_sp"] = _lsp
            txt_e = QLineEdit(item_data.get("text",""))
            txt_e.setPlaceholderText("Link metni")
            txt_e.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:5px;padding:4px;font-size:12px;")
            url_e = QLineEdit(item_data.get("url",""))
            url_e.setPlaceholderText("https://...")
            url_e.setStyleSheet("background:#0d1b2a;color:#88bbff;border:1px solid #0f3460;border-radius:5px;padding:4px;font-size:12px;")
            r1.addWidget(QLabel("🎨")); r1.addWidget(_col, 0)
            r1.addWidget(QLabel("pt")); r1.addWidget(_lsp, 0)
            r1.addSpacing(4)
            r1.addWidget(QLabel("Metin:")); r1.addWidget(txt_e, 1)
            r1.addWidget(QLabel("URL:"));   r1.addWidget(url_e, 1)
            fv.addLayout(r1)
            item_dict["txt_e"] = txt_e
            item_dict["url_e"] = url_e

        # Sil butonu
        top.addWidget(btn_del)
        _item_id = id(item_dict)
        _frame_ref = frame
        def _do_remove(_f=_frame_ref, _id=_item_id):
            idx = next((i for i,x in enumerate(self._sec_items_data) if id(x)==_id), None)
            if idx is not None:
                self._sec_items_data.pop(idx)
            self._sec_items_layout.removeWidget(_f)
            _f.setParent(None)
            _f.deleteLater()
        btn_del.clicked.connect(lambda _=None: _do_remove())

        self._sec_items_data.append(item_dict)
        self._sec_items_layout.addWidget(frame)

    def _inject_font(self, d):
        """font_family_cb, font_size_sp ve block_url varsa dict'e ekle."""
        if "font_family_cb" in self.inputs:
            fonts = self.inputs["_font_list"]
            idx   = self.inputs["font_family_cb"].currentIndex()
            d["font_family"] = fonts[idx] if idx < len(fonts) else fonts[0]
        if "font_size_sp" in self.inputs:
            d["font_size"] = self.inputs["font_size_sp"].value()
        if "block_url" in self.inputs:
            u = self.inputs["block_url"].text().strip()
            if u: d["block_url"] = u
        if "text_color" in self.inputs:
            col = self.inputs["text_color"]
            if isinstance(col, str): d["text_color"] = col

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "", "", "Images (*.png *.jpg *.jpeg *.webp *.gif)")
        if path:
            self.inputs["path"] = path
            self.inputs["_img_lbl"].setText(os.path.basename(path))
            self.inputs["_img_lbl"].setStyleSheet("color:#27ae60;font-size:12px;")

    def get_data(self):
        t = self.block_type
        if t in ("heading","paragraph","quote"):
            d = {"type":t,"content":self.inputs["content"].toPlainText()}
            if t == "paragraph" and hasattr(self, "_inline_links"):
                d["inline_links"] = [
                    {"text": te.text(), "url": ue.text()}
                    for te, ue, _ in self._inline_links
                ]
            if t == "paragraph":
                if "para_margin_top"    in self.inputs: d["para_margin_top"]    = self.inputs["para_margin_top"].value()
                if "para_margin_bottom" in self.inputs: d["para_margin_bottom"] = self.inputs["para_margin_bottom"].value()
            self._inject_font(d)
            return d
        elif t in ("bullet_list","numbered_list"):
            raw = self.inputs["items_text"].toPlainText()
            d = {"type":t,"items":[l.strip() for l in raw.splitlines() if l.strip()]}
            if t == "bullet_list" and "two_col" in self.inputs:
                d["two_col"] = self.inputs["two_col"].isChecked()
            self._inject_font(d)
            return d
        elif t == "divider":
            return {"type":"divider"}
        elif t == "button":
            return {"type":"button","text":self.inputs["text"].text(),"url":self.inputs["url"].text()}
        elif t == "image_url":
            return {"type":"image_url","url":self.inputs["url"].text(),"alt":self.inputs["alt"].text()}
        elif t == "image_file":
            return {"type":"image_file","path":self.inputs.get("path",""),"alt":self.inputs["alt"].text()}
        elif t == "spacer":
            return {"type":"spacer","height":self.inputs["height"].value()}
        elif t == "section":
            # sec_items topla
            _sitems = []
            for _d in self._sec_items_data:
                if _d["type"] == "para":
                    _sitems.append({"type":"para",
                                    "text":  _d["te"].toPlainText(),
                                    "color": _d.get("color","#cccccc"),
                                    "fs":    _d["fs_sp"].value() if hasattr(_d.get("fs_sp"),"value") else 14})
                elif _d["type"] == "link":
                    _sitems.append({"type":"link",
                                    "text":  _d["txt_e"].text(),
                                    "url":   _d["url_e"].text(),
                                    "color": _d.get("color","#88bbdd"),
                                    "fs":    _d["fs_sp"].value() if hasattr(_d.get("fs_sp"),"value") else 14})
            return {"type":"section",
                    "bg":       self.inputs.get("bg","#2C3E6B"),
                    "lbl_clr":  self.inputs.get("lbl_clr","#aaaaaa"),
                    "ttl_clr":  self.inputs.get("ttl_clr","#ffffff"),
                    "lbl_fs":   self.inputs["lbl_fs"].value() if hasattr(self.inputs.get("lbl_fs"), "value") else 11,
                    "ttl_fs":   self.inputs["ttl_fs"].value() if hasattr(self.inputs.get("ttl_fs"), "value") else 26,
                    "label":    self.inputs["label_e"].text(),
                    "title":    self.inputs["title_e"].text(),
                    "sec_items": _sitems}
        elif t == "toc":
            raw = self.inputs["items_text"].toPlainText()
            d = {"type":"toc",
                 "items": [l.strip() for l in raw.splitlines() if l.strip()],
                 "cols":  self.inputs["cols"].value()}
            for _ck in ("toc_txt","toc_bg","toc_border"):
                if _ck in self.inputs and isinstance(self.inputs[_ck], str):
                    d[_ck] = self.inputs[_ck]
            return d
        elif t == "highlight":
            hmap = {0:"success",1:"warning",2:"info",3:"neutral"}
            return {"type":"highlight",
                    "htype": hmap.get(self.inputs["htype_cb"].currentIndex(),"success"),
                    "title": self.inputs["title_e"].text(),
                    "body":  self.inputs["body_e"].toPlainText()}
        elif t == "table":
            d = {"type":"table","columns":self.inputs["columns_e"].text(),"rows":self.inputs["rows_e"].toPlainText()}
            self._inject_font(d); return d
        elif t == "cards":
            d = {"type":"cards",
                 "items_raw": self.inputs["items_raw_e"].toPlainText(),
                 "cols":      self.inputs["cols4"].value()}
            for _ck in ("card_bg","card_border","card_avatar","card_name","card_role","card_email"):
                if _ck in self.inputs and isinstance(self.inputs[_ck], str):
                    d[_ck] = self.inputs[_ck]
            return d
        elif t == "emoji_row":
            d = {"type":"emoji_row","emojis":self.inputs["emojis_e"].text()}
            self._inject_font(d); return d
        return {}


# ══════════════════════════════════════════════════════════════════
#  ANA PENCERE
# ══════════════════════════════════════════════════════════════════
