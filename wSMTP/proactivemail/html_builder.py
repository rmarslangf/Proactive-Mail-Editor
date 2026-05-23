"""
html_builder.py — Campaign HTML şablon üreticisi.

build_html(subject, blocks, ...) fonksiyonu tüm blok tiplerini
alır ve e-posta istemcileriyle uyumlu tek parça HTML döndürür.

Desteklenen blok tipleri:
  heading, paragraph, bullet_list, numbered_list, quote,
  divider, button, image_url, image_file, spacer,
  section, toc, highlight, table, cards, emoji_row
"""
import os, html as _html_stdlib
from .utils import img_to_b64

def build_html(subject, blocks,
               header_image_path=None, header_bg="#1B3A5C", header_text_color="#ffffff",
               footer_text="", footer_image_path=None,
               footer_bg="#1B3A5C", footer_text_color="#AABCD0",
               box_bg="#ffffff",
               page_bg="#E8EDF2",
               accent="#1B3A5C", font="Georgia, serif",
               show_subject=True, show_footer_text=True,
               global_font_size=15, global_font_family="Georgia, serif"):

    # ── Header
    subj_bar = (
        f'<div style="background:{header_bg};padding:10px 40px 18px;">'
        f'<p style="color:{header_text_color};margin:0;font-family:{font};'
        f'font-size:14px;letter-spacing:1px;text-align:center;">{subject}</p></div>'
    ) if show_subject else ''
    if header_image_path and os.path.exists(header_image_path):
        src = img_to_b64(header_image_path)
        header_html = (
            f'<img src="{src}" alt="Header"'
            f' style="width:100%;max-width:600px;display:block;">'
            + subj_bar
        )
    else:
        if show_subject:
            header_html = (
                f'<div style="background:{header_bg};padding:40px;text-align:center;">'
                f'<h1 style="color:{header_text_color};margin:0;font-family:{font};'
                f'font-size:28px;letter-spacing:2px;">{subject}</h1></div>'
            )
        else:
            header_html = f'<div style="background:{header_bg};height:8px;"></div>'

    # ── İçerik blokları
    # Her blok kendi font/size ayarını taşır; yoksa global kullanılır
    def _wrap_url(html, url):
        if not url: return html
        return (f'<a href="{url}" style="text-decoration:none;color:inherit;">' + html + '</a>')
    body_parts = ""
    for blk in blocks:
        t = blk.get("type", "")
        if t == "heading":
            _ff = blk.get("font_family", global_font_family)
            _fs = blk.get("font_size", global_font_size + 7)
            _tc = blk.get("text_color", accent)
            _html = (f'<h2 style="font-family:{_ff};color:{_tc};font-size:{_fs}px;'
                     f'margin:28px 0 10px;border-bottom:2px solid {_tc}22;'
                     f'padding-bottom:6px;">{blk.get("content","")}</h2>')
            body_parts += _wrap_url(_html, blk.get("block_url",""))
        elif t == "paragraph":
            _ff = blk.get("font_family", global_font_family)
            _fs = blk.get("font_size", global_font_size)
            _tc = blk.get("text_color", "#333333")
            import html as _hm
            _content = blk.get("content","")
            _content_safe = _hm.escape(_content).replace("\n","<br>")
            # Çoklu inline linkler: metindeki geçtiği yeri <a> ile sar
            for _lk in blk.get("inline_links", []):
                _lt = _lk.get("text",""); _lu = _lk.get("url","")
                if _lt and _lu:
                    _tag = (f'<a href="{_lu}" style="color:{accent};'
                            f'text-decoration:underline;font-weight:600;">{_hm.escape(_lt)}</a>')
                    _content_safe = _content_safe.replace(_hm.escape(_lt), _tag, 1)
            _html = (f'<p style="font-family:{_ff};color:{_tc};font-size:{_fs}px;'
                     f'line-height:1.9;margin:12px 0;">{_content_safe}</p>')
            body_parts += _wrap_url(_html, blk.get("block_url",""))
        elif t == "bullet_list":
            _ff = blk.get("font_family", global_font_family)
            _fs = blk.get("font_size", global_font_size)
            _tc = blk.get("text_color", "#333333")
            items = "".join(
                f'<li style="font-family:{_ff};color:{_tc};font-size:{_fs}px;'
                f'line-height:1.8;margin-bottom:6px;">{i}</li>'
                for i in blk.get("items", [])
            )
            if blk.get("two_col"):
                _html = f'<ul style="padding-left:22px;margin:12px 0;columns:2;-webkit-columns:2;column-gap:32px;">{items}</ul>'
            else:
                _html = f'<ul style="padding-left:22px;margin:12px 0;">{items}</ul>'
            body_parts += _wrap_url(_html, blk.get("block_url",""))
        elif t == "numbered_list":
            _ff = blk.get("font_family", global_font_family)
            _fs = blk.get("font_size", global_font_size)
            _tc = blk.get("text_color", "#333333")
            items = "".join(
                f'<li style="font-family:{_ff};color:{_tc};font-size:{_fs}px;'
                f'line-height:1.8;margin-bottom:6px;">{i}</li>'
                for i in blk.get("items", [])
            )
            _html = f'<ol style="padding-left:22px;margin:12px 0;">{items}</ol>'
            body_parts += _wrap_url(_html, blk.get("block_url",""))
        elif t == "divider":
            body_parts += f'<hr style="border:none;border-top:1px solid {accent}30;margin:28px 0;">'
        elif t == "quote":
            _ff = blk.get("font_family", global_font_family)
            _fs = blk.get("font_size", global_font_size)
            _tc = blk.get("text_color", "#555555")
            _html = (f'<blockquote style="border-left:4px solid {accent};margin:20px 0;'
                     f'padding:12px 20px;background:{accent}0a;border-radius:0 8px 8px 0;">'
                     f'<p style="font-family:{_ff};color:{_tc};font-size:{_fs}px;'
                     f'font-style:italic;margin:0;">{blk.get("content","")}</p></blockquote>')
            body_parts += _wrap_url(_html, blk.get("block_url",""))
        elif t == "button":
            body_parts += (
                f'<div style="text-align:center;margin:28px 0;">'
                f'<a href="{blk.get("url","#")}" style="background:{accent};color:#fff;'
                f'padding:13px 36px;border-radius:8px;text-decoration:none;'
                f'font-family:{font};font-size:15px;display:inline-block;">'
                f'{blk.get("text","")}</a></div>'
            )
        elif t == "image_url":
            alt_p = (f'<p style="font-size:12px;color:#888;margin-top:6px;">'
                     f'{blk.get("alt","")}</p>') if blk.get("alt") else ""
            body_parts += (
                f'<div style="text-align:center;margin:20px 0;">'
                f'<img src="{blk.get("url","")}" alt="{blk.get("alt","")}"'
                f' style="max-width:100%;border-radius:8px;">{alt_p}</div>'
            )
        elif t == "image_file":
            # base64 gömülü resim
            path = blk.get("path", "")
            alt  = blk.get("alt", "")
            if path and os.path.exists(path):
                src = img_to_b64(path)
                alt_p = (f'<p style="font-size:12px;color:#888;margin-top:6px;">{alt}</p>'
                         if alt else "")
                body_parts += (
                    f'<div style="text-align:center;margin:20px 0;">'
                    f'<img src="{src}" alt="{alt}"'
                    f' style="max-width:100%;border-radius:8px;">{alt_p}</div>'
                )
        elif t == "spacer":
            body_parts += f'<div style="height:{blk.get("height",24)}px;"></div>'

        elif t == "section":
            import html as _hm
            sbg    = blk.get("bg","#2C3E6B")
            slbl_c = blk.get("lbl_clr","#aaaaaa")
            sttl_c = blk.get("ttl_clr","#ffffff")
            slbl   = blk.get("label","")
            stitl  = blk.get("title","")
            slbl_fs = blk.get("lbl_fs", 11)
            sttl_fs = blk.get("ttl_fs", 26)
            label_html = (f'<p style="font-family:{font};color:{slbl_c};font-size:{slbl_fs}px;'
                           f'letter-spacing:2px;margin:0 0 6px;text-transform:uppercase;">{_hm.escape(slbl)}</p>') if slbl else ""
            title_html = (f'<h2 style="font-family:{font};color:{sttl_c};font-size:{sttl_fs}px;'
                           f'margin:0 0 16px;font-weight:700;">{_hm.escape(stitl)}</h2>') if stitl else ""
            # sec_items → HTML
            items_html = ""
            for _si in blk.get("sec_items", []):
                _itype = _si.get("type","para")
                _iclr  = _si.get("color","#cccccc")
                _ifs   = _si.get("fs", 14)
                if _itype == "para":
                    _txt = _hm.escape(_si.get("text","")).replace("\n","<br>")
                    items_html += (f'<p style="font-family:{font};color:{_iclr};'
                                   f'font-size:{_ifs}px;line-height:1.8;margin:0 0 10px;">{_txt}</p>')
                elif _itype == "link":
                    _ltxt = _hm.escape(_si.get("text",""))
                    _lurl = _si.get("url","#")
                    items_html += (f'<p style="margin:0 0 8px;">'
                                   f'<a href="{_lurl}" style="font-family:{font};color:{_iclr};'
                                   f'font-size:{_ifs}px;text-decoration:underline;">{_ltxt}</a></p>')
            body_parts += (
                f'<div style="background:{sbg};margin:0 -48px;padding:28px 48px;">'
                + label_html + title_html + items_html + '</div>'
            )

        elif t == "toc":
            cols       = int(blk.get("cols", 2))
            toc_txt    = blk.get("toc_txt",    "#1B3A5C")
            toc_bg     = blk.get("toc_bg",     "#EAF2FB")
            toc_border = blk.get("toc_border", "#1B3A5C")
            item_list  = [i for i in blk.get("items", []) if i]
            # Satırlara böl, eksik hücreleri doldur
            row_html = ""
            for i in range(0, max(len(item_list),1), cols):
                chunk = item_list[i:i+cols]
                while len(chunk) < cols: chunk.append("")
                tds = "".join(
                    f'<td style="width:{100//cols}%;padding:6px;">'
                    f'<div style="padding:11px 14px;'
                    f'border:1px solid {toc_border}66;border-radius:8px;'
                    f'font-family:{font};color:{toc_txt};'
                    f'font-size:13px;font-weight:600;text-align:center;'
                    f'background:{toc_bg};">{it}</div></td>'
                    if it else
                    f'<td style="width:{100//cols}%;padding:6px;"></td>'
                    for it in chunk
                )
                row_html += f'<tr>{tds}</tr>'
            body_parts += (
                f'<table width="100%" cellpadding="0" cellspacing="0" '
                f'style="margin:16px 0;border-collapse:separate;border-spacing:6px;">'
                + row_html + '</table>'
            )

        elif t == "highlight":
            htype = blk.get("htype","success")
            htitle = blk.get("title","")
            hbody  = blk.get("body","")
            colors = {
                "success": ("#2ecc71","#1a5c35","#e8f8f0"),
                "warning": ("#e74c3c","#7b1a1a","#fdf0f0"),
                "info":    ("#3498db","#1a3a5c","#eaf4fd"),
                "neutral": ("#95a5a6","#3d4a4b","#f4f6f6"),
            }
            border_c, title_c, bg_c = colors.get(htype, colors["neutral"])
            icon = {"success":"✅","warning":"⚠️","info":"ℹ️","neutral":"◻️"}.get(htype,"•")
            _html = (
                f'<div style="background:{bg_c};border-left:4px solid {border_c};'
                f'border-radius:0 8px 8px 0;padding:14px 18px;margin:14px 0;">'
                f'<p style="font-family:{font};color:{title_c};font-size:13px;'
                f'font-weight:700;margin:0 0 6px;">{icon} {htitle}</p>'
                f'<p style="font-family:{font};color:#444;font-size:13px;'
                f'font-style:italic;margin:0;">{hbody}</p></div>'
            )
            body_parts += _wrap_url(_html, blk.get("block_url",""))

        elif t == "table":
            cols_raw = blk.get("columns","")
            rows_raw = blk.get("rows","")
            cols = [c.strip() for c in cols_raw.split(",") if c.strip()]
            col_pct = f"{100 // len(cols) if cols else 100}%"
            _ff = blk.get("font_family", global_font_family)
            _fs = blk.get("font_size", global_font_size - 2)
            header_row = "".join(
                f'<th style="background:{accent};color:#fff;padding:10px 12px;'
                f'font-family:{_ff};font-size:{_fs}px;text-align:left;font-weight:700;'
                f'width:{col_pct};">{col}</th>'
                for col in cols
            )
            rows_html = ""
            for ri, row_str in enumerate(rows_raw.splitlines()):
                cells_data = [x.strip() for x in row_str.split(",")]
                row_bg = "#f8f9fa" if ri % 2 == 0 else "#ffffff"
                tds = "".join(
                    f'<td style="padding:9px 12px;font-family:{_ff};font-size:{_fs}px;'
                    f'color:#333;border-bottom:1px solid #eee;">{cd}</td>'
                    for cd in cells_data
                )
                rows_html += f'<tr style="background:{row_bg};">{tds}</tr>'
            body_parts += (
                f'<table width="100%" cellpadding="0" cellspacing="0" '
                f'style="border-collapse:collapse;margin:16px 0;border-radius:8px;overflow:hidden;'
                f'border:1px solid #e0e0e0;table-layout:fixed;">'
                f'<thead><tr>{header_row}</tr></thead>'
                f'<tbody>{rows_html}</tbody></table>'
            )

        elif t == "cards":
            cols       = int(blk.get("cols", 2))
            col_w      = f"{100//cols}%"
            c_bg       = blk.get("card_bg",     "#f8fafc")
            c_border   = blk.get("card_border", "#dde3ea")
            c_avatar   = blk.get("card_avatar", accent)
            c_name     = blk.get("card_name",   "#1a1a2e")
            c_role     = blk.get("card_role",   "#6b7280")
            c_email    = blk.get("card_email",  accent)
            all_lines  = [l for l in blk.get("items_raw","").splitlines() if l.strip()]
            rows_html2 = ""
            for i in range(0, len(all_lines), cols):
                chunk = all_lines[i:i+cols]
                while len(chunk) < cols: chunk.append("")
                tds2 = ""
                for line in chunk:
                    if not line.strip():
                        tds2 += f'<td style="width:{col_w};padding:6px;"></td>'
                        continue
                    parts  = [p.strip() for p in line.split("|")]
                    name   = parts[0] if len(parts) > 0 else ""
                    role   = parts[1] if len(parts) > 1 else ""
                    email  = parts[2] if len(parts) > 2 else ""
                    avatar = name[0].upper() if name else "?"
                    email_html = (
                        f'<a href="mailto:{email}" style="display:block;color:{c_email};'
                        f'font-size:12px;font-weight:600;text-decoration:none;margin-top:8px;'
                        f'word-break:break-all;">{email}</a>'
                    ) if email else ""
                    tds2 += (
                        f'<td style="width:{col_w};padding:8px;vertical-align:top;">'
                        f'<div style="border:1px solid {c_border};border-radius:12px;'
                        f'padding:18px 16px;background:{c_bg};'
                        f'box-shadow:0 2px 8px rgba(0,0,0,0.07);height:100%;box-sizing:border-box;">'
                        f'<div style="width:44px;height:44px;border-radius:50%;'
                        f'background:{c_avatar};color:#fff;font-size:18px;font-weight:700;'
                        f'line-height:44px;text-align:center;margin-bottom:12px;">{avatar}</div>'
                        f'<p style="font-family:{font};font-size:14px;font-weight:700;'
                        f'color:{c_name};margin:0 0 4px;line-height:1.3;">{name}</p>'
                        f'<p style="font-family:{font};font-size:12px;color:{c_role};'
                        f'margin:0;line-height:1.4;">{role}</p>'
                        + email_html + '</div></td>'
                    )
                rows_html2 += (
                    f'<tr style="vertical-align:stretch;">{tds2}</tr>'
                )
            body_parts += (
                f'<table width="100%" cellpadding="0" cellspacing="0" '
                f'style="margin:14px 0;border-collapse:separate;border-spacing:8px;">'
                + rows_html2 + '</table>'
            )

        elif t == "emoji_row":
            emojis = blk.get("emojis","")
            body_parts += (
                f'<div style="text-align:center;font-size:28px;letter-spacing:12px;margin:20px 0;">'
                + emojis + '</div>'
            )

    # ── Footer
    if footer_image_path and os.path.exists(footer_image_path):
        fsrc = img_to_b64(footer_image_path)
        # PNG her zaman göster; renkli kutu sadece show_footer_text=True ise
        color_box = (
            f'<div style="background:{footer_bg};padding:12px 48px;text-align:center;">'
            f'<p style="font-family:{font};color:{footer_text_color};font-size:12px;margin:0;">{footer_text}</p>'
            '</div>'
        ) if show_footer_text else ''
        footer_html = (
            f'<td style="padding:0;border-top:1px solid {accent}20;">'
            f'<img src="{fsrc}" alt="Footer"'
            f' style="width:100%;max-width:600px;display:block;">'
            + color_box + '</td>'
        )
    elif not show_footer_text:
        footer_html = ''
    else:
        footer_html = (
            f'<td style="background:{footer_bg};padding:24px 48px;'
            f'border-top:1px solid {accent}20;text-align:center;">'
            f'<p style="font-family:{font};color:{footer_text_color};font-size:12px;margin:0;">{footer_text}</p>'
            '</td>'
        )

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:{page_bg};font-family:{font};">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:{page_bg};padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;width:100%;background:{box_bg};
                    border-radius:12px;overflow:hidden;
                    box-shadow:0 8px 40px rgba(0,0,0,0.12);">
        <tr><td>{header_html}</td></tr>
        <tr><td style="padding:40px 48px;background:{box_bg};">{body_parts}</td></tr>
        {('<tr>'+footer_html+'</tr>') if footer_html else ''}
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════
#  BLOK WIDGET
# ══════════════════════════════════════════════════════════════════
