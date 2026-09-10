# -*- coding: utf-8 -*-
"""
Собирает Главы/*.md обратно в один docx.

Оригинальный «Том 1.docx» используется как шаблон: из него берутся стили,
шрифты, поля страницы — меняется только содержимое. Поэтому вёрстка
остаётся ровно такой, какой была.

Запуск:  python _служебное/собрать_docx.py
Результат: «Том 1 (сборка).docx» рядом с главами.

Что понимает в markdown:
  # Заголовок      -> заголовок главы (стиль Heading 1)
  *курсив*         -> курсив
  **жирный**       -> жирный
  ![Имя](путь)     -> картинка из Иллюстрации/
  ---              -> горизонтальный разделитель
  одиночный \n     -> перенос строки внутри абзаца
  пустая строка    -> граница абзацев
"""
import os, re, sys, json, shutil, zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL  = os.path.join(BASE, 'Том 1.docx')
CH   = os.path.join(BASE, 'Главы')
ILL  = os.path.join(BASE, 'Иллюстрации')
OUT  = os.path.join(BASE, 'Том 1 (сборка).docx')

SZ   = '<w:sz w:val="28"/><w:szCs w:val="28"/>'
PPR_H = f'<w:pPr><w:pStyle w:val="Heading1"/><w:spacing w:after="0" w:before="0" w:line="360" w:lineRule="auto"/><w:jc w:val="both"/><w:rPr>{SZ}</w:rPr></w:pPr>'
PPR_B = f'<w:pPr><w:spacing w:after="240" w:before="240" w:line="360" w:lineRule="auto"/><w:jc w:val="both"/><w:rPr>{SZ}</w:rPr></w:pPr>'
PPR_I = f'<w:pPr><w:spacing w:after="0" w:before="0" w:line="360" w:lineRule="auto"/><w:jc w:val="center"/><w:rPr>{SZ}</w:rPr></w:pPr>'
EMU_PER_PX = 9525
MAXW = 5731200          # ширина колонки в EMU — по ней ужимаем крупные арты


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def run(text, bold=False, ital=False):
    """Один <w:r>. Переводы строк внутри превращаются в <w:br/>."""
    rpr = SZ + ('<w:b w:val="1"/><w:bCs w:val="1"/>' if bold else '') \
             + ('<w:i w:val="1"/><w:iCs w:val="1"/>' if ital else '') + '<w:rtl w:val="0"/>'
    out = ''
    for k, piece in enumerate(text.split('\n')):
        if k:
            out += '<w:br/>'
        if piece:
            out += f'<w:t xml:space="preserve">{esc(piece)}</w:t>'
    return f'<w:r><w:rPr>{rpr}</w:rPr>{out}</w:r>' if out else ''


INLINE = re.compile(r'(\*\*.+?\*\*|\*[^*]+?\*)', re.S)


def runs(text):
    out = ''
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith('**') and part.endswith('**') and len(part) > 4:
            out += run(part[2:-2], bold=True)
        elif part.startswith('*') and part.endswith('*') and len(part) > 2:
            out += run(part[1:-1], ital=True)
        else:
            out += run(part)
    return out


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] == b'\x89PNG\r\n\x1a\n':
        w = int.from_bytes(head[16:20], 'big')
        h = int.from_bytes(head[20:24], 'big')
        return w, h
    return None


def main():
    if not os.path.exists(TPL):
        sys.exit(f'нет шаблона: {TPL}')
    files = sorted(f for f in os.listdir(CH)
                   if f.lower().endswith('.md') and not f.startswith('00 '))
    if not files:
        sys.exit('в папке Главы нет файлов глав')

    sizes = {}
    man = os.path.join(ILL, 'манифест.json')
    if os.path.exists(man):
        for it in json.load(open(man, encoding='utf-8')).get('иллюстрации', []):
            if it.get('ширина_emu'):
                sizes[it['имя']] = (it['ширина_emu'], it['высота_emu'])

    zin = zipfile.ZipFile(TPL)
    xml = zin.read('word/document.xml').decode('utf-8')
    rels = zin.read('word/_rels/document.xml.rels').decode('utf-8')
    ctypes = zin.read('[Content_Types].xml').decode('utf-8')
    hr_tpl = re.search(r'<w:p(?:\s[^>]*)?>(?:(?!</w:p>).)*?<v:rect.*?</w:p>', xml, re.S)
    hr_xml = hr_tpl.group(0) if hr_tpl else ''

    used, media, body, stats = {}, {}, [], []
    next_rid = max([int(m) for m in re.findall(r'Id="rId(\d+)"', rels)] or [0]) + 1
    docpr = 1000

    for fn in files:
        text = open(os.path.join(CH, fn), encoding='utf-8').read()
        blocks = [b for b in re.split(r'\n[ \t]*\n', text) if b.strip()]
        nimg = 0
        for b in blocks:
            b = b.strip('\n')
            if b.strip() == '---':
                body.append(hr_xml)
                continue
            m = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', b.strip())
            if m:
                name, rel = m.group(1), m.group(2)
                src = os.path.normpath(os.path.join(CH, rel))
                if not os.path.exists(src):
                    print(f'  !! нет картинки: {rel} (в {fn})')
                    continue
                if src not in used:
                    ext = os.path.splitext(src)[1].lower().lstrip('.')
                    target = f'media/{os.path.basename(src)}'
                    used[src] = (f'rId{next_rid}', target, ext)
                    media[target] = src
                    next_rid += 1
                rid, target, ext = used[src]
                if name in sizes:
                    cx, cy = sizes[name]
                else:
                    px = png_size(src)
                    cx, cy = (px[0] * EMU_PER_PX, px[1] * EMU_PER_PX) if px else (MAXW, MAXW)
                    if cx > MAXW:
                        cy = int(cy * MAXW / cx); cx = MAXW
                docpr += 1
                body.append(
                    f'<w:p>{PPR_I}<w:r><w:rPr>{SZ}</w:rPr><w:drawing>'
                    f'<wp:inline distB="114300" distT="114300" distL="114300" distR="114300">'
                    f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent b="0" l="0" r="0" t="0"/>'
                    f'<wp:docPr id="{docpr}" name="{esc(name)}"/><a:graphic>'
                    f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                    f'<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="{esc(name)}"/>'
                    f'<pic:cNvPicPr preferRelativeResize="0"/></pic:nvPicPr><pic:blipFill>'
                    f'<a:blip r:embed="{rid}"/><a:srcRect b="0" l="0" r="0" t="0"/>'
                    f'<a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr>'
                    f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                    f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
                    f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
                nimg += 1
                continue
            if b.lstrip().startswith('# '):
                body.append(f'<w:p>{PPR_H}{runs(b.lstrip()[2:].strip())}</w:p>')
                continue
            body.append(f'<w:p>{PPR_B}{runs(b)}</w:p>')
        stats.append((fn, len(blocks), len(text.split()), nimg))

    sect = re.search(r'<w:sectPr>.*?</w:sectPr>', xml, re.S)
    sect = sect.group(0) if sect else ''
    head = xml[:xml.index('<w:body>') + len('<w:body>')]
    newxml = head + ''.join(body) + sect + '</w:body></w:document>'

    add = ''
    for src, (rid, target, ext) in used.items():
        if f'Target="{target}"' not in rels:
            add += (f'<Relationship Id="{rid}" '
                    f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                    f'Target="{target}"/>')
    if add:
        rels = rels.replace('</Relationships>', add + '</Relationships>')
    for ext in {e for _, _, e in used.values()}:
        mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                'gif': 'image/gif', 'webp': 'image/webp'}.get(ext, 'image/png')
        if f'Extension="{ext}"' not in ctypes:
            ctypes = ctypes.replace('</Types>',
                                    f'<Default Extension="{ext}" ContentType="{mime}"/></Types>')

    skip = {'word/document.xml', 'word/_rels/document.xml.rels', '[Content_Types].xml'}
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
        zo.writestr('[Content_Types].xml', ctypes)
        zo.writestr('word/document.xml', newxml)
        zo.writestr('word/_rels/document.xml.rels', rels)
        for it in zin.infolist():
            if it.filename in skip or it.filename.startswith('word/media/'):
                continue
            zo.writestr(it, zin.read(it.filename))
        for target, src in media.items():
            zo.write(src, 'word/' + target)

    print(f'{"файл":42s} {"абзацев":>8s} {"слов":>7s} {"арт":>4s}')
    for fn, nb, nw, ni in stats:
        print(f'{fn:42s} {nb:8d} {nw:7d} {ni:4d}')
    print(f'\nвсего: {len(stats)} глав, {sum(s[2] for s in stats)} слов, '
          f'{sum(s[3] for s in stats)} иллюстраций')
    print(f'готово: {OUT}')
    print('\nОглавление в Word: Ссылки -> Оглавление (заголовки глав размечены стилем «Заголовок 1»).')


if __name__ == '__main__':
    main()
