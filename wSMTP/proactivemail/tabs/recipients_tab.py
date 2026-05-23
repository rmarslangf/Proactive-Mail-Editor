"""
tabs/recipients_tab.py — Alıcı yönetimi sekmesi.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QDialog, QFormLayout, QComboBox,
    QDialogButtonBox, QCheckBox, QListWidget,
    QListWidgetItem, QColorDialog, QAbstractItemView,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from ..db import Database


# Alıcı ekle/düzenle diyaloğu

class RecipientDialog(QDialog):
    def __init__(self, db: Database, parent=None,
                 data: dict = None):
        super().__init__(parent)
        self.db   = db
        self.data = data or {}
        self.setWindowTitle("Alıcı" if not data else "Alıcıyı Düzenle")
        self.setMinimumWidth(400)
        self._build()

    def _build(self):
        lay = QFormLayout(self)
        lay.setSpacing(10)

        self.name_e    = QLineEdit(self.data.get("name", ""))
        self.email_e   = QLineEdit(self.data.get("email", ""))
        self.company_e = QLineEdit(self.data.get("company", ""))
        self.notes_e   = QLineEdit(self.data.get("notes", ""))

        self.group_cb = QComboBox()
        self.group_cb.addItem("— Grup yok —", None)
        groups = self.db.get_groups()
        self._group_ids = [None]
        for g in groups:
            self.group_cb.addItem(g["name"], g["id"])
            self._group_ids.append(g["id"])
        cur_gid = self.data.get("group_id")
        if cur_gid:
            idx = next((i for i, gid in enumerate(self._group_ids)
                        if gid == cur_gid), 0)
            self.group_cb.setCurrentIndex(idx)

        self.active_cb = QCheckBox("Aktif")
        self.active_cb.setChecked(bool(self.data.get("active", 1)))
        self.sub_cb = QCheckBox("Abone")
        self.sub_cb.setChecked(bool(self.data.get("subscribed", 1)))

        lay.addRow("Ad Soyad *", self.name_e)
        lay.addRow("E-posta *",  self.email_e)
        lay.addRow("Şirket",     self.company_e)
        lay.addRow("Grup",       self.group_cb)
        lay.addRow("Notlar",     self.notes_e)

        flags_row = QHBoxLayout()
        flags_row.addWidget(self.active_cb)
        flags_row.addWidget(self.sub_cb)
        flags_row.addStretch()
        lay.addRow("Durum", flags_row)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addRow(btns)

    def _validate(self):
        if not self.email_e.text().strip() or "@" not in self.email_e.text():
            QMessageBox.warning(self, "Hata", "Geçerli bir e-posta girin.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name":      self.name_e.text().strip(),
            "email":     self.email_e.text().strip().lower(),
            "company":   self.company_e.text().strip(),
            "notes":     self.notes_e.text().strip(),
            "group_id":  self.group_cb.currentData(),
            "active":    int(self.active_cb.isChecked()),
            "subscribed":int(self.sub_cb.isChecked()),
        }


#Grup diyaloğu

class GroupDialog(QDialog):
    def __init__(self, parent=None, name="", color="#1B3A5C"):
        super().__init__(parent)
        self.setWindowTitle("Grup")
        self.setFixedWidth(300)
        self._color = color
        lay = QFormLayout(self)
        self.name_e = QLineEdit(name)
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(36, 28)
        self._refresh_color()
        self.color_btn.clicked.connect(self._pick_color)
        lay.addRow("Grup adı *", self.name_e)
        lay.addRow("Renk",       self.color_btn)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lay.addRow(btns)

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self)
        if c.isValid():
            self._color = c.name()
            self._refresh_color()

    def _refresh_color(self):
        self.color_btn.setStyleSheet(
            f"background:{self._color};border:1px solid #ccc;border-radius:4px;")

    def _validate(self):
        if not self.name_e.text().strip():
            QMessageBox.warning(self, "Hata", "Grup adı boş olamaz.")
            return
        self.accept()

    def get_data(self):
        return {"name": self.name_e.text().strip(), "color": self._color}


#Ana sekme

STYLE_DARK = """
QWidget { background:#16213e; color:#e8e4d9; }
QTableWidget { background:#0d1b2a; gridline-color:#1a3050;
               border:1px solid #1a3050; border-radius:6px; color:#e8e4d9; }
QTableWidget::item:selected { background:#e9456040; color:#fff; }
QHeaderView::section { background:#0f3460; color:#e8e4d9; padding:6px;
                        border:none; font-weight:700; }
QPushButton { background:#0f3460; color:#e8e4d9; border:none;
              border-radius:6px; padding:6px 14px; font-size:12px; }
QPushButton:hover { background:#e94560; }
QPushButton#danger { background:#7b1a1a; }
QPushButton#danger:hover { background:#e94560; }
QPushButton#success { background:#1a5c35; }
QPushButton#success:hover { background:#2ecc71; }
QLineEdit, QComboBox { background:#0d1b2a; border:1px solid #0f3460;
                        border-radius:5px; color:#e8e4d9; padding:5px 8px; }
QLineEdit:focus { border-color:#e94560; }
QListWidget { background:#0d1b2a; border:1px solid #1a3050;
              border-radius:6px; color:#e8e4d9; }
QListWidget::item:selected { background:#e9456040; }
QLabel#title { font-size:15px; font-weight:700; color:#e94560; }
QLabel#count { font-size:11px; color:#5a5a8a; }
"""


class RecipientsTab(QWidget):
    recipients_changed = pyqtSignal()   # Diğer sekmelere haber ver

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setStyleSheet(STYLE_DARK)
        self._build()
        self.refresh()

    #UI

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)
        splitter = QSplitter(Qt.Horizontal)
        outer.addWidget(splitter)

        #grup paneli
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0); lv.setSpacing(8)

        grp_lbl = QLabel("GRUPLAR"); grp_lbl.setObjectName("title")
        lv.addWidget(grp_lbl)

        self.group_list = QListWidget()
        self.group_list.currentRowChanged.connect(self._on_group_select)
        lv.addWidget(self.group_list, 1)

        gbtn = QHBoxLayout()
        btn_add_g  = QPushButton("+ Grup")
        btn_edit_g = QPushButton("✏")
        btn_del_g  = QPushButton("🗑")
        btn_del_g.setObjectName("danger")
        btn_add_g.clicked.connect(self._add_group)
        btn_edit_g.clicked.connect(self._edit_group)
        btn_del_g.clicked.connect(self._del_group)
        for b in [btn_add_g, btn_edit_g, btn_del_g]:
            b.setFixedHeight(28); gbtn.addWidget(b)
        lv.addLayout(gbtn)
        left.setFixedWidth(180)
        splitter.addWidget(left)

        # alıcı tablosu
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(8)

        # Üst araç çubuğu
        top = QHBoxLayout()
        rec_lbl = QLabel("ALICILAR"); rec_lbl.setObjectName("title")
        top.addWidget(rec_lbl)
        top.addStretch()

        self.search_e = QLineEdit()
        self.search_e.setPlaceholderText("🔍 Ara...")
        self.search_e.setFixedWidth(180)
        self.search_e.textChanged.connect(self._filter_table)
        top.addWidget(self.search_e)

        self.sub_filter = QComboBox()
        self.sub_filter.addItems(["Tümü", "Abone", "İptal"])
        self.sub_filter.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.sub_filter)

        btn_add  = QPushButton("+ Alıcı")
        btn_edit = QPushButton("✏ Düzenle")
        btn_del  = QPushButton("🗑 Sil"); btn_del.setObjectName("danger")
        btn_unsub  = QPushButton("⛔ İptal"); btn_unsub.setObjectName("danger")
        btn_resub  = QPushButton("✅ Abone"); btn_resub.setObjectName("success")
        btn_import = QPushButton("📂 CSV")

        btn_add.clicked.connect(self._add_recipient)
        btn_edit.clicked.connect(self._edit_recipient)
        btn_del.clicked.connect(self._del_recipient)
        btn_unsub.clicked.connect(self._unsub)
        btn_resub.clicked.connect(self._resub)
        btn_import.clicked.connect(self._import_csv)

        for b in [btn_add, btn_edit, btn_del, btn_unsub, btn_resub, btn_import]:
            b.setFixedHeight(28); top.addWidget(b)
        rv.addLayout(top)

        # Sayım etiketi
        self.count_lbl = QLabel("0 alıcı")
        self.count_lbl.setObjectName("count")
        rv.addWidget(self.count_lbl)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Ad Soyad", "E-posta", "Şirket", "Grup", "Aktif", "Abone"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        self.table.doubleClicked.connect(self._edit_recipient)
        rv.addWidget(self.table, 1)

        splitter.addWidget(right)
        splitter.setSizes([180, 700])

    # Veri

    def _current_group_id(self):
        row = self.group_list.currentRow()
        if row <= 0:
            return None
        item = self.group_list.item(row)
        return item.data(Qt.UserRole) if item else None

    def refresh(self):
        # Grupları yenile
        self.group_list.blockSignals(True)
        cur_gid = self._current_group_id()
        self.group_list.clear()
        all_item = QListWidgetItem("📋  Tüm Alıcılar")
        all_item.setData(Qt.UserRole, None)
        self.group_list.addItem(all_item)
        for g in self.db.get_groups():
            item = QListWidgetItem(f"  {g['name']}")
            item.setData(Qt.UserRole, g["id"])
            item.setForeground(QColor(g["color"]))
            self.group_list.addItem(item)
        # Seçimi geri yükle
        for i in range(self.group_list.count()):
            if self.group_list.item(i).data(Qt.UserRole) == cur_gid:
                self.group_list.setCurrentRow(i)
                break
        else:
            self.group_list.setCurrentRow(0)
        self.group_list.blockSignals(False)

        self._load_recipients()

    def _load_recipients(self):
        sub_idx = self.sub_filter.currentIndex()
        sub_only = sub_idx == 1
        unsub_only = sub_idx == 2

        gid = self._current_group_id()
        active_only = True
        subscribed_only = sub_only

        # Aboneliği iptal edilenleri de göster
        rows = self.db.get_recipients(
            group_id=gid,
            active_only=active_only,
            subscribed_only=False   # filtre aşağıda
        )

        # Manuel filtre
        if sub_idx == 1:
            rows = [r for r in rows if r["subscribed"]]
        elif sub_idx == 2:
            rows = [r for r in rows if not r["subscribed"]]

        self._populate(rows)

    def _populate(self, rows):
        self.table.setRowCount(0)
        for ri, r in enumerate(rows):
            self.table.insertRow(ri)
            self.table.setItem(ri, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(ri, 1, QTableWidgetItem(r["name"] or ""))
            self.table.setItem(ri, 2, QTableWidgetItem(r["email"]))
            self.table.setItem(ri, 3, QTableWidgetItem(r["company"] or ""))
            grp = r["group_name"] or "—"
            grp_item = QTableWidgetItem(grp)
            if r["group_color"]:
                grp_item.setForeground(QColor(r["group_color"]))
            self.table.setItem(ri, 4, grp_item)
            self.table.setItem(ri, 5, QTableWidgetItem("✅" if r["active"] else "❌"))
            sub_item = QTableWidgetItem("✅" if r["subscribed"] else "⛔")
            if not r["subscribed"]:
                sub_item.setForeground(QColor("#e94560"))
            self.table.setItem(ri, 6, sub_item)

        self.count_lbl.setText(f"{self.table.rowCount()} alıcı")
        self.recipients_changed.emit()

    def _filter_table(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(row, c).text().lower()
                         if self.table.item(row, c) else "")
                for c in [1, 2, 3, 4]
            )
            self.table.setRowHidden(row, not match)

    def _on_group_select(self):
        self._load_recipients()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    # Grup CRUD 

    def _add_group(self):
        dlg = GroupDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            try:
                self.db.add_group(d["name"], d["color"])
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _edit_group(self):
        gid = self._current_group_id()
        if not gid:
            return
        groups = {g["id"]: g for g in self.db.get_groups()}
        g = groups.get(gid)
        if not g:
            return
        dlg = GroupDialog(self, g["name"], g["color"])
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            self.db.update_group(gid, d["name"], d["color"])
            self.refresh()

    def _del_group(self):
        gid = self._current_group_id()
        if not gid:
            return
        if QMessageBox.question(self, "Sil",
            "Grup silinsin mi? (Alıcılar korunur, gruptan çıkarılır)",
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_group(gid)
            self.refresh()

    # Alıcı CRUD

    def _add_recipient(self):
        dlg = RecipientDialog(self.db, self)
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            try:
                self.db.add_recipient(
                    d["name"], d["email"], d["company"],
                    d["group_id"], d["notes"]
                )
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Eklenemedi: {e}")

    def _edit_recipient(self):
        rid = self._selected_id()
        if not rid:
            QMessageBox.information(self, "Seçim", "Lütfen bir alıcı seçin.")
            return
        rows = self.db.get_recipients(active_only=False, subscribed_only=False)
        rec = next((r for r in rows if r["id"] == rid), None)
        if not rec:
            return
        dlg = RecipientDialog(self.db, self, dict(rec))
        if dlg.exec_() == QDialog.Accepted:
            d = dlg.get_data()
            self.db.update_recipient(
                rid, d["name"], d["email"], d["company"],
                d["group_id"], d["notes"], d["active"], d["subscribed"]
            )
            self.refresh()

    def _del_recipient(self):
        rid = self._selected_id()
        if not rid:
            return
        if QMessageBox.question(self, "Sil", "Alıcı silinsin mi?",
           QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_recipient(rid)
            self.refresh()

    def _unsub(self):
        rid = self._selected_id()
        if not rid:
            return
        self.db.unsubscribe(rid)
        self.refresh()

    def _resub(self):
        rid = self._selected_id()
        if not rid:
            return
        self.db.resubscribe(rid)
        self.refresh()

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "CSV Seç", "", "CSV (*.csv)")
        if not path:
            return
        gid = self._current_group_id()
        result = self.db.import_csv(path, gid)
        self.refresh()
        msg = (f"✅ {result['added']} alıcı eklendi.\n"
               f"⏭ {result['skipped']} atlandı (zaten var).\n"
               f"❌ {result['errors']} hata.")
        if result["error_list"]:
            msg += "\n\nHatalar:\n" + "\n".join(result["error_list"][:10])
        QMessageBox.information(self, "İçe Aktarma Tamamlandı", msg)
