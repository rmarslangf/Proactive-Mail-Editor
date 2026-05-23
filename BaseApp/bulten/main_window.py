"""
main_window.py — Ana uygulama penceresi 

Sağ panel: Canlı HTML önizleme (QWebEngineView)
"""
import sys, json, os, re
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLineEdit, QLabel, QScrollArea, QGroupBox,
    QSpinBox, QSizePolicy, QCheckBox, QTabWidget, QFileDialog,
    QMessageBox, QComboBox, QToolButton
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView

from .config import AUTO_SAVE_PATH, CORP_COLORS, CORP_NAMES_TR, CORP_NAMES_EN, FONT_LIST
from .lang import LANG
from .style import APP_STYLE
from .utils import make_color_btn, set_color_btn
from .html_builder import build_html
from .block_widget import BlockWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = "TR"
        self._init_state()
        self._build_ui()
        self._auto_preview_timer()
        self._load_autosave()     # son projeyi yükle

    def _t(self, key):
        return LANG[self.lang].get(key, key)

    def _init_state(self):
        self.blocks            = []
        self.header_path       = ""
        self.footer_path       = ""
        self.box_bg            = "#ffffff"
        self.accent_color      = "#1B3A5C"
        self.header_bg         = "#1B3A5C"
        self.header_text_color = "#FFFFFF"
        self.footer_text       = LANG[self.lang]["footer_default"]
        self.footer_bg         = "#1B3A5C"
        self.footer_text_color = "#AABCD0"
        self.show_subject      = True
        self.show_footer_text  = True
        self.global_font_size   = 15
        self.global_font_family = "Georgia, serif"

    # ─────────────────────────────────────────────────
    #  UI İNŞA
    # ─────────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle(self._t("app_title"))
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(APP_STYLE)

        central = QWidget(); central.setObjectName("root")
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self._splitter)
        self._editor_panel  = self._build_editor()
        self._preview_panel = self._build_preview()
        self._splitter.addWidget(self._editor_panel)
        self._splitter.addWidget(self._preview_panel)
        self._splitter.setSizes([600, 680])

    def _build_editor(self):
        from PyQt5.QtWidgets import QTabWidget, QCheckBox, QScrollArea as QSA
        panel = QWidget(); panel.setObjectName("panel"); panel.setMinimumWidth(520)
        v = QVBoxLayout(panel); v.setContentsMargins(12,12,12,10); v.setSpacing(8)

        # ── Üst: başlık + dil butonu + Uygula
        top_row = QHBoxLayout()
        self._title_lbl = QLabel(self._t("editor_title")); self._title_lbl.setObjectName("title")
        top_row.addWidget(self._title_lbl); top_row.addStretch()
        self._lang_btn = QPushButton(self._t("lang_btn")); self._lang_btn.setObjectName("lang_btn")
        self._lang_btn.clicked.connect(self._toggle_lang)
        top_row.addWidget(self._lang_btn)
        self._btn_apply = QPushButton(self._t("btn_apply"))
        self._btn_apply.setObjectName("accent"); self._btn_apply.setFixedWidth(100)
        self._btn_apply.clicked.connect(self._apply_changes)
        top_row.addWidget(self._btn_apply)
        v.addLayout(top_row)

        #  Konu satırı (her zaman görünür)
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText(self._t("subject_ph"))
        v.addWidget(self.subject_edit)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane { border:none; background:#16213e; }
            QTabBar::tab { background:#0d1b2a; color:#7070a0; padding:7px 16px;
                           border:none; border-radius:6px 6px 0 0; margin-right:2px; font-size:12px; }
            QTabBar::tab:selected { background:#e94560; color:#fff; font-weight:700; }
        """)
        v.addWidget(self._tabs, 1)

        # ════ AYARLAR ════════════════════════════════════
        settings_scroll = QSA(); settings_scroll.setWidgetResizable(True)
        settings_w = QWidget()
        sv = QVBoxLayout(settings_w); sv.setContentsMargins(8,8,8,8); sv.setSpacing(8)

        # Gizle checkboxları
        chk_row = QHBoxLayout()
        self._chk_hide_subj = QCheckBox(self._t("hide_subject"))
        self._chk_hide_subj.setStyleSheet("color:#a0a0c0;font-size:12px;")
        self._chk_hide_subj.setChecked(not self.show_subject)
        self._chk_hide_subj.stateChanged.connect(self._on_hide_subject)
        self._chk_hide_ftxt = QCheckBox(self._t("hide_footer_txt"))
        self._chk_hide_ftxt.setStyleSheet("color:#a0a0c0;font-size:12px;")
        self._chk_hide_ftxt.setChecked(not self.show_footer_text)
        self._chk_hide_ftxt.stateChanged.connect(self._on_hide_footer_txt)
        chk_row.addWidget(self._chk_hide_subj); chk_row.addSpacing(16)
        chk_row.addWidget(self._chk_hide_ftxt); chk_row.addStretch()
        sv.addLayout(chk_row)

        # Header
        self._hdr_box = QGroupBox(self._t("header_grp"))
        hf = QVBoxLayout(self._hdr_box); hf.setContentsMargins(10,16,10,10); hf.setSpacing(6)
        hrow = QHBoxLayout()
        self.header_lbl = QLabel(self._t("no_img")); self.header_lbl.setObjectName("subtitle")
        self._btn_hdr     = QPushButton(self._t("img_sel")); self._btn_hdr.setObjectName("ghost"); self._btn_hdr.setFixedWidth(100)
        self._btn_hdr_clr = QPushButton(self._t("img_clr")); self._btn_hdr_clr.setObjectName("ghost"); self._btn_hdr_clr.setFixedWidth(75)
        self._btn_hdr.clicked.connect(self.pick_header); self._btn_hdr_clr.clicked.connect(self.clear_header)
        hrow.addWidget(self.header_lbl,1); hrow.addWidget(self._btn_hdr); hrow.addWidget(self._btn_hdr_clr)
        hf.addLayout(hrow)
        crow = QHBoxLayout()
        self._hdr_bg_lbl  = QLabel(self._t("header_bg_lbl"))
        self._hdr_txt_lbl = QLabel(self._t("header_txt_lbl"))
        self._hdr_bg_btn  = make_color_btn(self.header_bg,         self._on_hdr_bg)
        self._hdr_txt_btn = make_color_btn(self.header_text_color, self._on_hdr_txt)
        crow.addWidget(self._hdr_bg_lbl); crow.addWidget(self._hdr_bg_btn)
        crow.addSpacing(12); crow.addWidget(self._hdr_txt_lbl); crow.addWidget(self._hdr_txt_btn); crow.addStretch()
        hf.addLayout(crow)
        sv.addWidget(self._hdr_box)

        # Footer
        self._ftr_box = QGroupBox(self._t("footer_grp"))
        ff = QVBoxLayout(self._ftr_box); ff.setContentsMargins(10,16,10,10); ff.setSpacing(6)
        self.footer_edit = QLineEdit(self.footer_text)
        self.footer_edit.setPlaceholderText(self._t("footer_text_ph"))
        self.footer_edit.textChanged.connect(self._on_footer_text)
        ff.addWidget(self.footer_edit)
        fimg_row = QHBoxLayout()
        self.footer_img_lbl = QLabel(self._t("no_img")); self.footer_img_lbl.setObjectName("subtitle")
        self._btn_ftr     = QPushButton(self._t("img_sel")); self._btn_ftr.setObjectName("ghost"); self._btn_ftr.setFixedWidth(100)
        self._btn_ftr_clr = QPushButton(self._t("img_clr")); self._btn_ftr_clr.setObjectName("ghost"); self._btn_ftr_clr.setFixedWidth(75)
        self._btn_ftr.clicked.connect(self.pick_footer); self._btn_ftr_clr.clicked.connect(self.clear_footer)
        fimg_row.addWidget(self.footer_img_lbl,1); fimg_row.addWidget(self._btn_ftr); fimg_row.addWidget(self._btn_ftr_clr)
        ff.addLayout(fimg_row)
        frow = QHBoxLayout()
        self._ftr_bg_lbl  = QLabel(self._t("footer_bg_lbl"))
        self._ftr_txt_lbl = QLabel(self._t("footer_txt_lbl"))
        self._ftr_bg_btn  = make_color_btn(self.footer_bg,         self._on_ftr_bg)
        self._ftr_txt_btn = make_color_btn(self.footer_text_color, self._on_ftr_txt)
        frow.addWidget(self._ftr_bg_lbl); frow.addWidget(self._ftr_bg_btn)
        frow.addSpacing(12); frow.addWidget(self._ftr_txt_lbl); frow.addWidget(self._ftr_txt_btn); frow.addStretch()
        ff.addLayout(frow)
        sv.addWidget(self._ftr_box)

        # Renkler
        self._clr_box = QGroupBox(self._t("colors_grp"))
        cf = QVBoxLayout(self._clr_box); cf.setContentsMargins(10,16,10,10); cf.setSpacing(6)
        self._bg_lbl = QLabel(self._t("bg_color_lbl")); cf.addWidget(self._bg_lbl)
        pal_row = QHBoxLayout(); self._palette_btns = []
        names = CORP_NAMES_TR if self.lang == "TR" else CORP_NAMES_EN
        for hex_c, name in zip(CORP_COLORS, names):
            pb = QPushButton(); pb.setFixedSize(26,26)
            pb.setToolTip(f"{name}\n{hex_c}")
            pb.setStyleSheet(f"QPushButton{{background:{hex_c};border:2px solid #0f3460;border-radius:5px;}}QPushButton:hover{{border-color:#e94560;}}")
            pb.clicked.connect(lambda _, h=hex_c: self._set_box_bg(h))
            pal_row.addWidget(pb); self._palette_btns.append(pb)
        self._bg_custom_btn = make_color_btn(self.box_bg, self._set_box_bg)
        self._custom_lbl = QLabel(self._t("custom_color"))
        pal_row.addSpacing(6); pal_row.addWidget(self._custom_lbl); pal_row.addWidget(self._bg_custom_btn); pal_row.addStretch()
        cf.addLayout(pal_row)
        arow = QHBoxLayout()
        self._acc_lbl = QLabel(self._t("accent_lbl"))
        self._acc_btn = make_color_btn(self.accent_color, self._set_accent)
        arow.addWidget(self._acc_lbl); arow.addWidget(self._acc_btn); arow.addStretch()
        cf.addLayout(arow)
        sv.addWidget(self._clr_box)

        # ── Global Font & Punto
        from PyQt5.QtWidgets import QComboBox as _QCB2
        self._GFONTS = ["Georgia, serif","Arial, sans-serif","Helvetica, sans-serif",
                        "Times New Roman, serif","Trebuchet MS, sans-serif",
                        "Verdana, sans-serif","Tahoma, sans-serif",
                        "Courier New, monospace","Palatino, serif"]
        self._fonts_box = QGroupBox(self._t("fonts_grp"))
        fboxv = QVBoxLayout(self._fonts_box); fboxv.setContentsMargins(10,16,10,10); fboxv.setSpacing(6)
        fr1 = QHBoxLayout()
        self._gfont_lbl = QLabel(self._t("font_family_lbl"))
        self._gfont_cb  = _QCB2()
        self._gfont_cb.addItems([f.split(",")[0] for f in self._GFONTS])
        _gi = next((i for i,f in enumerate(self._GFONTS) if f == self.global_font_family), 0)
        self._gfont_cb.setCurrentIndex(_gi)
        self._gfont_cb.currentIndexChanged.connect(self._on_global_font)
        fr1.addWidget(self._gfont_lbl); fr1.addWidget(self._gfont_cb, 1)
        fboxv.addLayout(fr1)
        fr2 = QHBoxLayout()
        self._gsize_lbl = QLabel(self._t("font_size_lbl"))
        self._gsize_sp  = QSpinBox(); self._gsize_sp.setRange(8,48)
        self._gsize_sp.setValue(self.global_font_size)
        self._gsize_sp.setFixedWidth(70)
        self._gsize_sp.setStyleSheet("background:#0d1b2a;color:#e8e4d9;border:1px solid #0f3460;border-radius:6px;padding:4px;")
        self._gsize_sp.valueChanged.connect(self._on_global_size)
        fr2.addWidget(self._gsize_lbl); fr2.addWidget(self._gsize_sp); fr2.addStretch()
        fboxv.addLayout(fr2)
        sv.addWidget(self._fonts_box)

        sv.addStretch()

        settings_scroll.setWidget(settings_w)
        self._tabs.addTab(settings_scroll, "⚙️  Ayarlar")

        # ════ SİÇERİK ════════════════════════════════════
        content_w = QWidget()
        cv = QVBoxLayout(content_w); cv.setContentsMargins(8,8,8,8); cv.setSpacing(6)

        # Blok ekle butonları
        self._add_box = QGroupBox(self._t("add_block_grp"))
        ag = QVBoxLayout(self._add_box); ag.setContentsMargins(8,16,8,8); ag.setSpacing(4)
        block_rows_keys = [
            [("heading","block_heading"),("paragraph","block_paragraph"),("quote","block_quote")],
            [("bullet_list","block_bullet"),("numbered_list","block_numbered"),("divider","block_divider")],
            [("button","block_button"),("image_url","block_image_url"),("image_file","block_image_file"),("spacer","block_spacer")],
            [("section","block_section"),("toc","block_toc"),("highlight","block_highlight")],
            [("table","block_table"),("cards","block_cards"),("emoji_row","block_emoji_row")],
        ]
        self._block_btns = {}
        for pairs in block_rows_keys:
            row = QHBoxLayout(); row.setSpacing(4)
            for btype, lkey in pairs:
                b = QPushButton(self._t(lkey)); b.setObjectName("ghost")
                b.setFixedHeight(28)
                b.setStyleSheet("QPushButton{font-size:11px;padding:4px 6px;}")
                b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                b.clicked.connect(lambda _, bt=btype: self.add_block(bt))
                row.addWidget(b); self._block_btns[btype] = b
            ag.addLayout(row)
        cv.addWidget(self._add_box)

        # Blok listesi 
        self._content_lbl = QLabel(self._t("content_lbl")); self._content_lbl.setObjectName("section")
        cv.addWidget(self._content_lbl)
        scroll = QSA(); scroll.setWidgetResizable(True)
        self.blocks_container = QWidget()
        self.blocks_container.setAcceptDrops(True)
        self.blocks_layout = QVBoxLayout(self.blocks_container)
        self.blocks_layout.setAlignment(Qt.AlignTop); self.blocks_layout.setSpacing(6)
        scroll.setWidget(self.blocks_container)
        cv.addWidget(scroll, 1)
        self.empty_lbl = QLabel(self._t("no_block_lbl"))
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.empty_lbl.setStyleSheet("color:#2a2a4a;font-size:13px;")
        self.blocks_layout.addWidget(self.empty_lbl)

        self._tabs.addTab(content_w, "✍️  İçerik")

        # Alt butonlar
        bot = QHBoxLayout()
        self._btn_clear       = QPushButton(self._t("btn_clear")); self._btn_clear.setObjectName("ghost")
        self._btn_clear_cont  = QPushButton(self._t("btn_clear_content")); self._btn_clear_cont.setObjectName("ghost")
        self._btn_load        = QPushButton(self._t("btn_load"));  self._btn_load.setObjectName("ghost")
        self._btn_save_proj   = QPushButton(self._t("btn_save_proj")); self._btn_save_proj.setObjectName("ghost")
        self._btn_export      = QPushButton(self._t("btn_export")); self._btn_export.setObjectName("save_btn")
        self._btn_clear.clicked.connect(self.clear_all)
        self._btn_clear_cont.clicked.connect(self.clear_content_only)
        self._btn_load.clicked.connect(self.load_project)
        self._btn_save_proj.clicked.connect(self.save_project)
        self._btn_export.clicked.connect(self.export_html)
        for b in [self._btn_clear, self._btn_clear_cont, self._btn_load, self._btn_save_proj]:
            bot.addWidget(b)
        bot.addStretch(); bot.addWidget(self._btn_export)
        v.addLayout(bot)
        return panel

    def _build_preview(self):
        panel = QWidget(); panel.setObjectName("preview_panel")
        v = QVBoxLayout(panel); v.setContentsMargins(12,18,18,14); v.setSpacing(10)
        top = QHBoxLayout()
        self._prev_lbl = QLabel(self._t("preview_lbl")); self._prev_lbl.setObjectName("section")
        top.addWidget(self._prev_lbl); top.addStretch()
        self._btn_copy = QPushButton(self._t("btn_copy")); self._btn_copy.setObjectName("accent")
        self._btn_copy.clicked.connect(self.copy_html); top.addWidget(self._btn_copy)
        btn_ref = QPushButton(self._t("btn_refresh")); btn_ref.setObjectName("ghost"); btn_ref.setFixedWidth(36)
        btn_ref.clicked.connect(self.refresh_preview); top.addWidget(btn_ref)
        v.addLayout(top)
        self.web = QWebEngineView()
        v.addWidget(self.web, 1)
        return panel
    #  DİL 
    def _toggle_lang(self):
        self.lang = "EN" if self.lang == "TR" else "TR"
        self._apply_lang()
        self._mark_dirty()

    def _apply_lang(self):
        t = self._t
        self.setWindowTitle(t("app_title"))
        self._title_lbl.setText(t("editor_title"))
        self._lang_btn.setText(t("lang_btn"))
        self.subject_edit.setPlaceholderText(t("subject_ph"))
        # Sekme başlıkları
        self._tabs.setTabText(0, ("⚙️  Ayarlar" if self.lang=="TR" else "⚙️  Settings"))
        self._tabs.setTabText(1, ("✍️  İçerik"  if self.lang=="TR" else "✍️  Content"))
        if hasattr(self,"_hdr_box"): self._hdr_box.setTitle(t("header_grp"))
        if hasattr(self,"_btn_hdr"): self._btn_hdr.setText(t("img_sel")); self._btn_hdr_clr.setText(t("img_clr"))
        if hasattr(self,"_hdr_bg_lbl"): self._hdr_bg_lbl.setText(t("header_bg_lbl")); self._hdr_txt_lbl.setText(t("header_txt_lbl"))
        if hasattr(self,"_ftr_box"): self._ftr_box.setTitle(t("footer_grp"))
        if hasattr(self,"footer_edit"): self.footer_edit.setPlaceholderText(t("footer_text_ph"))
        if hasattr(self,"_btn_ftr"): self._btn_ftr.setText(t("img_sel")); self._btn_ftr_clr.setText(t("img_clr"))
        if hasattr(self,"_ftr_bg_lbl"): self._ftr_bg_lbl.setText(t("footer_bg_lbl")); self._ftr_txt_lbl.setText(t("footer_txt_lbl"))
        if hasattr(self,"_clr_box"): self._clr_box.setTitle(t("colors_grp"))
        if hasattr(self,"_bg_lbl"): self._bg_lbl.setText(t("bg_color_lbl"))
        if hasattr(self,"_custom_lbl"): self._custom_lbl.setText(t("custom_color"))
        if hasattr(self,"_acc_lbl"): self._acc_lbl.setText(t("accent_lbl"))
        if hasattr(self,"_add_box"): self._add_box.setTitle(t("add_block_grp"))
        if hasattr(self,"_content_lbl"): self._content_lbl.setText(t("content_lbl"))
        if hasattr(self,"_btn_clear"): self._btn_clear.setText(t("btn_clear")); self._btn_load.setText(t("btn_load"))
        if hasattr(self,"_btn_save_proj"): self._btn_save_proj.setText(t("btn_save_proj")); self._btn_export.setText(t("btn_export"))
        if hasattr(self,"_btn_copy"): self._btn_copy.setText(t("btn_copy"))
        if hasattr(self,"_prev_lbl"): self._prev_lbl.setText(t("preview_lbl"))
        if hasattr(self,"empty_lbl"): self.empty_lbl.setText(t("no_block_lbl"))
        if hasattr(self,"_btn_apply"): self._btn_apply.setText(t("btn_apply"))
        if hasattr(self,"_chk_hide_subj"): self._chk_hide_subj.setText(t("hide_subject"))
        if hasattr(self,"_chk_hide_ftxt"): self._chk_hide_ftxt.setText(t("hide_footer_txt"))
        if hasattr(self,"_btn_clear_cont"): self._btn_clear_cont.setText(t("btn_clear_content"))
        if hasattr(self, "_fonts_box"):
            self._fonts_box.setTitle(t("fonts_grp"))
            self._gfont_lbl.setText(t("font_family_lbl"))
            self._gsize_lbl.setText(t("font_size_lbl"))
        # palette buton tooltipleri
        names = CORP_NAMES_TR if self.lang == "TR" else CORP_NAMES_EN
        for btn, name, hex_c in zip(self._palette_btns, names, CORP_COLORS):
            btn.setToolTip(f"{name}\n{hex_c}")
        # blok butonları
        bkeys = {
            "heading":"block_heading","paragraph":"block_paragraph","quote":"block_quote",
            "bullet_list":"block_bullet","numbered_list":"block_numbered","divider":"block_divider",
            "button":"block_button","image_url":"block_image_url",
            "image_file":"block_image_file","spacer":"block_spacer",
            "section":"block_section","toc":"block_toc","highlight":"block_highlight",
            "table":"block_table","cards":"block_cards","emoji_row":"block_emoji_row",
        }
        for btype, lkey in bkeys.items():
            if btype in self._block_btns:
                self._block_btns[btype].setText(t(lkey))

    # ─────────────────────────────────────────────────
    #  RENK CALLBACK
    # ─────────────────────────────────────────────────
    def _on_global_font(self, idx):
        self.global_font_family = self._GFONTS[idx] if idx < len(self._GFONTS) else self._GFONTS[0]
        self._mark_dirty()

    def _on_global_size(self, val):
        self.global_font_size = val
        self._mark_dirty()

    def _on_hdr_bg(self, c):    self.header_bg = c;          self._schedule_preview()
    def _on_hdr_txt(self, c):   self.header_text_color = c;  self._schedule_preview()
    def _on_footer_text(self,t):self.footer_text = t;         self._schedule_preview()
    def _on_ftr_bg(self, c):    self.footer_bg = c;          self._schedule_preview()
    def _on_ftr_txt(self, c):   self.footer_text_color = c;  self._schedule_preview()
    def _on_hide_subject(self, state):
        self.show_subject = not bool(state)
        self._schedule_preview()
    def _on_hide_footer_txt(self, state):
        self.show_footer_text = not bool(state)
        self._schedule_preview()
    def _set_box_bg(self, c):
        self.box_bg = c
        set_color_btn(self._bg_custom_btn, c)
        self._schedule_preview()
    def _set_accent(self, c):
        self.accent_color = c
        self._schedule_preview()

    # ─────────────────────────────────────────────────
    #  BLOK YÖNETİMİ
    # ─────────────────────────────────────────────────
    def add_block(self, block_type, data=None):
        try:
            bw = BlockWidget(block_type, data, lang=self.lang)
            bw.sig_delete  = self.remove_block
            bw.sig_move_up = self.move_up
            bw.sig_move_dn = self.move_dn
            self.blocks.append(bw)
            self.blocks_layout.addWidget(bw)
            self.empty_lbl.setVisible(False)
            self._mark_dirty()
        except Exception as e:
            QMessageBox.critical(self, self._t("error_title"), self._t("block_add_err").format(e))

    def remove_block(self, bw):
        self.blocks.remove(bw)
        self.blocks_layout.removeWidget(bw); bw.deleteLater()
        if not self.blocks: self.empty_lbl.setVisible(True)
        self._mark_dirty()

    def move_up(self, bw):
        i = self.blocks.index(bw)
        if i == 0: return
        self.blocks[i], self.blocks[i-1] = self.blocks[i-1], self.blocks[i]
        self._rebuild_layout()

    def move_dn(self, bw):
        i = self.blocks.index(bw)
        if i >= len(self.blocks)-1: return
        self.blocks[i], self.blocks[i+1] = self.blocks[i+1], self.blocks[i]
        self._rebuild_layout()

    def _rebuild_layout(self):
        for bw in self.blocks: self.blocks_layout.removeWidget(bw)
        for bw in self.blocks: self.blocks_layout.addWidget(bw)
        self.blocks_layout.update()
        self._mark_dirty()

    def clear_content_only(self):
        """Sadece bloklar silinir — header/footer/renkler/konu korunur."""
        if not self.blocks: return
        if QMessageBox.question(self, self._t("clear_title"), self._t("clear_confirm"),
                QMessageBox.Yes|QMessageBox.No) != QMessageBox.Yes: return
        for bw in self.blocks[:]:
            self.blocks_layout.removeWidget(bw); bw.deleteLater()
        self.blocks.clear()
        self.empty_lbl.setVisible(True)
        self._mark_dirty()

    def clear_all(self):
        if self.blocks and QMessageBox.question(
            self, self._t("clear_title"), self._t("clear_confirm"),
            QMessageBox.Yes|QMessageBox.No) != QMessageBox.Yes: return
        for bw in self.blocks[:]:
            self.blocks_layout.removeWidget(bw); bw.deleteLater()
        self.blocks.clear(); self.empty_lbl.setVisible(True)
        self.web.setHtml("")

 
    #  HEADER / FOOTER GÖRSEL SEÇİMİ

    def pick_header(self):
        path, _ = QFileDialog.getOpenFileName(
            self,"","","Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.header_path = path
            self.header_lbl.setText(f"✅  {os.path.basename(path)}")
            self.header_lbl.setStyleSheet("color:#27ae60;font-size:12px;")
            self._schedule_preview()

    def clear_header(self):
        self.header_path = ""
        self.header_lbl.setText(self._t("no_img"))
        self.header_lbl.setStyleSheet("color:#7070a0;font-size:12px;")
        self._schedule_preview()

    def pick_footer(self):
        path, _ = QFileDialog.getOpenFileName(
            self,"","","Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.footer_path = path
            self.footer_img_lbl.setText(f"✅  {os.path.basename(path)}")
            self.footer_img_lbl.setStyleSheet("color:#27ae60;font-size:12px;")
            self._schedule_preview()

    def clear_footer(self):
        self.footer_path = ""
        self.footer_img_lbl.setText(self._t("no_img"))
        self.footer_img_lbl.setStyleSheet("color:#7070a0;font-size:12px;")
        self._schedule_preview()


    #  HTML ÜRETİMİ & ÖNİZLEME

    def _get_html(self):
        try:
            return build_html(
                subject            = self.subject_edit.text().strip() or "Newsletter",
                blocks             = [b.get_data() for b in self.blocks],
                header_image_path  = self.header_path or None,
                header_bg          = self.header_bg,
                header_text_color  = self.header_text_color,
                footer_text        = self.footer_text,
                footer_image_path  = self.footer_path or None,
                footer_bg          = self.footer_bg,
                footer_text_color  = self.footer_text_color,
                box_bg             = self.box_bg,
                accent             = self.accent_color,
                show_subject       = self.show_subject,
                show_footer_text   = self.show_footer_text,
                global_font_size   = self.global_font_size,
                global_font_family = self.global_font_family,
            )
        except Exception as e:
            return (f"<html><body><p style='color:red;font-family:monospace;padding:20px'>"
                    f"{self._t('html_err').format(e)}</p></body></html>")

    def _auto_preview_timer(self):
        self._dirty = False
        self._auto_timer = QTimer()
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._apply_changes)

    def _mark_dirty(self, *_):
        self._dirty = True
        # Buton vurgu — değişiklik var
        self._btn_apply.setStyleSheet(
            "QPushButton{background:#e94560;color:#fff;border-radius:8px;"
            "padding:8px 18px;font-size:13px;font-weight:700;"
            "border:2px solid #ff6b81;}"
        )
        # 600ms sonra otomatik uygula
        self._auto_timer.start(600)

    def _schedule_preview(self, *_):
        self._mark_dirty()

    def _apply_changes(self):
        self.refresh_preview()
        self._dirty = False
        self._btn_apply.setStyleSheet("")
        QTimer.singleShot(1500, self._autosave)

    def refresh_preview(self):
        try:
            self.web.setHtml(self._get_html())
            QTimer.singleShot(200, self._fit_preview)
        except Exception as e:
            print(f"[preview] {e}")

    def _fit_preview(self):
        js = (
            "(function(){"
            "var t=document.querySelector('table[width]')||document.querySelector('table table');"
            "if(!t)return;"
            "var vw=window.innerWidth-32;"
            "var tw=t.offsetWidth||600;"
            "if(tw<1)tw=600;"
            "var s=vw/tw;"
            "if(s>1)s=1;"
            "document.body.style.transformOrigin='top center';"
            "document.body.style.transform='scale('+s+')';"
            "document.body.style.width=(100/s)+'%';"
            "document.body.style.margin='0';"
            "})()"
        )
        try: self.web.page().runJavaScript(js)
        except Exception as e: print(f"[fit] {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(100, self._fit_preview)


    #  DIŞA AKTARMA

    def export_html(self):
        try:
            subject = self.subject_edit.text().strip() or "newsletter"
            safe = re.sub(r'[^\w\s-]','',subject).strip().replace(' ','_')
            path, _ = QFileDialog.getSaveFileName(self,"",f"{safe}.html","HTML (*.html)")
            if not path: return
            # Büyük resim varken donmayı önle — thread kullan
            html = self._get_html()
            from PyQt5.QtCore import QThread, pyqtSignal
            class _SaveThread(QThread):
                done  = pyqtSignal(str)   # başarı: boş string
                error = pyqtSignal(str)   # hata mesajı
                def __init__(self, p, h):
                    super().__init__(); self._p = p; self._h = h
                def run(self):
                    try:
                        with open(self._p,"w",encoding="utf-8") as f: f.write(self._h)
                        self.done.emit(self._p)
                    except Exception as ex:
                        self.error.emit(str(ex))
            self._save_thread = _SaveThread(path, html)
            self._save_thread.done.connect(
                lambda p: QMessageBox.information(self, self._t("saved_title"), self._t("saved_msg").format(p)))
            self._save_thread.error.connect(
                lambda e: QMessageBox.critical(self, self._t("error_title"), self._t("export_err").format(e)))
            self._save_thread.start()
        except Exception as e:
            QMessageBox.critical(self, self._t("error_title"), self._t("export_err").format(e))

    def copy_html(self):
        QApplication.clipboard().setText(self._get_html())
        QMessageBox.information(self, self._t("copied_title"), self._t("copied_msg"))


    #  PROJE KAYDET / YÜKLE

    def _project_data(self):
        return {
            "lang":              self.lang,
            "subject":           self.subject_edit.text(),
            "header_path":       self.header_path,
            "header_bg":         self.header_bg,
            "header_text_color": self.header_text_color,
            "footer_text":       self.footer_text,
            "footer_path":       self.footer_path,
            "footer_bg":         self.footer_bg,
            "footer_text_color": self.footer_text_color,
            "box_bg":            self.box_bg,
            "accent_color":      self.accent_color,
            "show_subject":      self.show_subject,
            "show_footer_text":  self.show_footer_text,
            "global_font_size":   self.global_font_size,
            "global_font_family": self.global_font_family,
            "blocks":            [b.get_data() for b in self.blocks],
        }

    def _apply_project_data(self, data):
        # Dil
        lang = data.get("lang", "TR")
        if lang != self.lang:
            self.lang = lang
            self._apply_lang()

        self.subject_edit.setText(data.get("subject",""))

        # Header
        hp = data.get("header_path","")
        self.header_path = hp if (hp and os.path.exists(hp)) else ""
        if hasattr(self, "header_lbl"):
            if self.header_path:
                self.header_lbl.setText(f"✅  {os.path.basename(self.header_path)}")
                self.header_lbl.setStyleSheet("color:#27ae60;font-size:12px;")
            else:
                self.header_lbl.setText(self._t("no_img"))

        # Footer resim
        fp = data.get("footer_path","")
        self.footer_path = fp if (fp and os.path.exists(fp)) else ""
        if hasattr(self, "footer_img_lbl"):
            if self.footer_path:
                self.footer_img_lbl.setText(f"✅  {os.path.basename(self.footer_path)}")
                self.footer_img_lbl.setStyleSheet("color:#27ae60;font-size:12px;")
            else:
                self.footer_img_lbl.setText(self._t("no_img"))

        # Footer metin
        ft = data.get("footer_text", self.footer_text)
        self.footer_text = ft
        if hasattr(self, "footer_edit"): self.footer_edit.setText(ft)

        # Renkler
        def _lc(key, attr, btn, setter):
            val = data.get(key, getattr(self, attr))
            setattr(self, attr, val)
            set_color_btn(btn, val)
            setter(val)

        if hasattr(self, "_hdr_bg_btn"):
            _lc("header_bg",         "header_bg",         self._hdr_bg_btn,  self._on_hdr_bg)
            _lc("header_text_color", "header_text_color", self._hdr_txt_btn, self._on_hdr_txt)
            _lc("footer_bg",         "footer_bg",         self._ftr_bg_btn,  self._on_ftr_bg)
            _lc("footer_text_color", "footer_text_color", self._ftr_txt_btn, self._on_ftr_txt)
            _lc("box_bg",            "box_bg",            self._bg_custom_btn, self._set_box_bg)
            _lc("accent_color",      "accent_color",      self._acc_btn,     self._set_accent)
        else:
            for key, attr in [("header_bg","header_bg"),("header_text_color","header_text_color"),
                               ("footer_bg","footer_bg"),("footer_text_color","footer_text_color"),
                               ("box_bg","box_bg"),("accent_color","accent_color")]:
                setattr(self, attr, data.get(key, getattr(self, attr)))

        self.show_subject     = data.get("show_subject", True)
        self.show_footer_text = data.get("show_footer_text", True)
        if hasattr(self, "_chk_hide_subj"):
            self._chk_hide_subj.setChecked(not self.show_subject)
        if hasattr(self, "_chk_hide_ftxt"):
            self._chk_hide_ftxt.setChecked(not self.show_footer_text)
        self.global_font_size   = data.get("global_font_size", 15)
        self.global_font_family = data.get("global_font_family", "Georgia, serif")
        if hasattr(self, "_gsize_sp"):
            self._gsize_sp.setValue(self.global_font_size)
        if hasattr(self, "_gfont_cb") and hasattr(self, "_GFONTS"):
            _gi2 = next((i for i,f in enumerate(self._GFONTS) if f == self.global_font_family), 0)
            self._gfont_cb.setCurrentIndex(_gi2)

        # Bloklar
        for bw in self.blocks[:]:
            self.blocks_layout.removeWidget(bw); bw.deleteLater()
        self.blocks.clear(); self.empty_lbl.setVisible(True)

        for blk in data.get("blocks",[]):
            self.add_block(blk["type"], blk)

        if hasattr(self, "web"):
            self.refresh_preview()

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self,"","bulten.json","JSON (*.json)")
        if not path: return
        with open(path,"w",encoding="utf-8") as f:
            json.dump(self._project_data(), f, ensure_ascii=False, indent=2)
        self._autosave()
        QMessageBox.information(self, self._t("saved_title"), self._t("proj_saved"))

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self,"","","JSON (*.json)")
        if not path: return
        with open(path,encoding="utf-8") as f: data = json.load(f)
        self._apply_project_data(data)

    # ─────────────────────────────────────────────────
    #  OTOMATİK KAYIT
    # ─────────────────────────────────────────────────
    def _autosave(self):
        try:
            with open(AUTO_SAVE_PATH,"w",encoding="utf-8") as f:
                json.dump(self._project_data(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[autosave] {e}")

    def _load_autosave(self):
        if os.path.exists(AUTO_SAVE_PATH):
            try:
                with open(AUTO_SAVE_PATH,encoding="utf-8") as f:
                    data = json.load(f)
                self._apply_project_data(data)
            except Exception as e:
                print(f"[autosave load] {e}")

    def closeEvent(self, event):
        self._autosave()
        super().closeEvent(event)



