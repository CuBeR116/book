# -*- coding: utf-8 -*-
"""
Проверка главы на следы нейросети и на ровность ритма.
Нормы сняты с человеческой прозы (Чехов «Степь», «Дама с собачкой»; Кинг «История Лизи»,
«Позже» в переводах) и с непереписанных черновиков этой же книги. Подробности и порядок
проверки — в «ПРОВЕРКА — следы нейросети.md».

Запуск из корня репозитория:
  python3 -I "Манхва/Книга/_служебное/проверить_следы.py"                 # все главы, таблица
  python3 -I "Манхва/Книга/_служебное/проверить_следы.py" Главы/01*.md     # выбранные главы
  python3 -I "Манхва/Книга/_служебное/проверить_следы.py" --где Главы/01*.md   # где именно править
Ничего не меняет, только печатает.
"""
import sys, os, re, glob, zlib, statistics as st, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(BASE, 'Главы')

# --- словари штампов -------------------------------------------------------
КАНЦЕЛЯРИТ = ["таким образом", "в современном мире", "подводя итог", "важно отметить", "стоит отметить",
    "следует отметить", "в заключение", "в конечном итоге", "тем не менее", "более того", "кроме того",
    "в свою очередь", "играет важную роль", "представляет собой", "является", "данный", "ключев",
    "уникальн", "эффективн", "в рамках", "безусловно", "несомненно", "действительно", "по-настоящему",
    "в целом", "так или иначе", "однако", "впрочем", "и всё же", "и все же"]
ШТАМПЫ_ПРОЗЫ = ["на мгновение", "в тот же миг", "повисла тишина", "тишина повисла", "воцарил", "нечто",
    "что-то внутри", "внутри что-то", "по спине", "холодок", "мурашки", "сердце пропустило",
    "перехватило дыхание", "дыхание перехватило", "уголки губ", "едва заметн", "лёгкая улыбка",
    "легкая улыбка", "мир сузился", "время остановилось", "не просто", "это было не", "это был не",
    "осознание", "понимание", "ощущение", "присутствие", "пронзительн", "ледян", "атмосфер",
    "в глубине души", "где-то внутри", "что-то изменилось", "что-то сместилось", "не в силах",
    "невозможно было", "невидим", "бездн", "эхо", "пауза."]
РЕФРЕНЫ = {"Значит/Выходит/Похоже": r'\b(Значит|Выходит|Похоже)\b', "сам/сама/сами/само": r'\b(сам|сама|сами|само)\b(?=[.,;: ])',
    "не сходилось": r'не сходил|не сходит', "стоило запомнить": r'стоило запомнить', "соль (запах страха)": r'\bсол[ьи]\b',
    "вручную": r'вручную', "три шага": r'тр[иех]х? шаг'}

# --- нормы: (нижняя, верхняя) человеческой прозы; None = нет нормы, смотреть на динамику ----
НОРМЫ = {
    'слов_в_предл': (12, 22), 'длинных_%': (10, 30), 'коротких_%': (0, 12), 'cv': (0.70, 1.0), 'ровных_%': (0, 15),
    'mattr': (0.63, 1.0), 'тире': (30, 60), 'двоеточий': (0, 10), 'что_то': (0, 2.5), 'будто': (0, 3.5),
    'казалось': (0, 3), 'штампы': (0, 4), 'канцелярит': (0, 0.5), 'не_просто': (0, 0.3), 'не_а': (0, 5),
    'вопросов': (0, 5), 'триад': (0, 1), 'приговоров_%': (0, 6), 'цепочек': (0, 0.3), 'без_длинного': (0, 20),
    'дублей': (0, 0), 'тех': (0, 0), 'Значит/Выходит/Похоже': (0, 4), 'не сходилось': (0, 1), 'стоило запомнить': (0, 1),
}

def load(path):
    t = open(path, encoding='utf-8').read()
    return re.sub(r'^#.*$', '', t, flags=re.M)

def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?…])\s+', text) if s.strip()]

def analyze(t):
    k = len(t) / 10000
    lines = t.split('\n')
    paras = [p.strip() for p in re.split(r'\n\s*\n', t) if p.strip()]
    dial = [p for p in paras if p.startswith(('—', '–'))]
    narr = [p for p in paras if p not in dial]
    sents = sentences(' '.join(narr))
    wl = [len(s.split()) for s in sents]
    m = st.mean(wl) if wl else 0
    words = re.findall(r'[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)?', t.lower())
    W = 500
    mattr = st.mean([len(set(words[i:i + W])) / W for i in range(0, len(words) - W, 250)]) if len(words) > W else 0
    low = t.lower()
    chains = 0; run = 0
    for w in wl:
        run = run + 1 if w <= 3 else 0
        if run == 3: chains += 1
    without_long = sum(1 for p in narr if len(sentences(p)) >= 4 and max(len(s.split()) for s in sentences(p)) < 20)
    long_paras = sum(1 for p in narr if len(sentences(p)) >= 4)
    seen = set(); dups = 0
    for p in narr:
        key = re.sub(r'\s+', ' ', p)
        if len(key) > 60:
            if key in seen: dups += 1
            seen.add(key)
    tech = len(re.findall(r'[А-Яа-яЁё][A-Za-z]|[A-Za-z][А-Яа-яЁё]', t)) + sum(t.count(c) for c in '​‌‍﻿ ') \
        + len(re.findall(r'[^\s]  +[^\s]', t)) + sum(t.count(x) for x in ['contentReference', 'oaicite', 'utm_source'])
    r = {
        'тыс_зн': len(t) / 1000, 'слов_в_предл': m, 'длинных_%': 100 * sum(1 for w in wl if w >= 25) / len(wl),
        'коротких_%': 100 * sum(1 for w in wl if w <= 3) / len(wl), 'cv': st.pstdev(wl) / m if m else 0,
        'ровных_%': 100 * sum(1 for w in wl if abs(w - m) <= 2) / len(wl), 'mattr': mattr,
        'тире': (t.count('—') + t.count('–')) / k, 'двоеточий': t.count(':') / k,
        'что_то': len(re.findall(r'[Чч]то-то', t)) / k, 'будто': (low.count('будто') + low.count('словно')) / k,
        'казалось': low.count('казалось') / k, 'штампы': sum(low.count(x) for x in ШТАМПЫ_ПРОЗЫ) / k,
        'канцелярит': sum(low.count(x) for x in КАНЦЕЛЯРИТ) / k, 'не_просто': low.count('не просто') / k,
        'не_а': len(re.findall(r'\b[Нн]е\s[^.!?;]{1,40},\s(?:а|но)\s', t)) / k,
        'вопросов': sum(1 for s in sents if s.endswith('?')) / k,
        'триад': len(re.findall(r'(?:^|[.!?…]\s+)(Ни|Не|Без)\s[^.!?]{1,25}[.,;]\s(?:Ни|Не|без)\s[^.!?]{1,25}[.,;]\s(?:Ни|Не|без|и|а|А|И)\b', t)) / k,
        'приговоров_%': 100 * sum(1 for p in narr if len(p.split()) > 12 and len(sentences(p)[-1].split()) <= 3) / max(1, len(narr)),
        'цепочек': chains / (len(t) / 1000), 'без_длинного': 100 * without_long / max(1, long_paras), 'дублей': dups, 'тех': tech,
        'реплик_%': 100 * len(dial) / max(1, len(paras)),
    }
    for name, rx in РЕФРЕНЫ.items():
        r[name] = len(re.findall(rx, t))
    return r

СТОЛБЦЫ = [('тыс_зн', 'тыс.зн', '{:.0f}'), ('слов_в_предл', 'слов/пр', '{:.1f}'), ('длинных_%', '%≥25сл', '{:.0f}'),
    ('коротких_%', '%≤3сл', '{:.0f}'), ('cv', 'CV', '{:.2f}'), ('ровных_%', '%±2', '{:.0f}'), ('mattr', 'MATTR', '{:.3f}'),
    ('тире', 'тире', '{:.0f}'), ('двоеточий', 'двоет', '{:.0f}'), ('что_то', 'что-то', '{:.1f}'), ('будто', 'будто', '{:.1f}'),
    ('штампы', 'штамп', '{:.1f}'), ('канцелярит', 'канц', '{:.1f}'), ('не_а', 'не..,а', '{:.1f}'), ('вопросов', 'вопр', '{:.1f}'),
    ('приговоров_%', '%приг', '{:.0f}'), ('цепочек', 'цеп', '{:.2f}'), ('без_длинного', '%безДл', '{:.0f}'),
    ('дублей', 'дубл', '{}'), ('тех', 'тех', '{}'), ('Значит/Выходит/Похоже', 'Знач', '{}'), ('не сходилось', 'несх', '{}')]

def flag(key, val):
    n = НОРМЫ.get(key)
    if not n: return ' '
    lo, hi = n
    return '!' if (val < lo or val > hi) else ' '

def table(paths):
    print('Единицы: на 10 тыс. знаков, кроме %, CV, MATTR и счётчиков (Знач, несх, дубл, тех). «!» = вне человеческой нормы.')
    print(f"{'глава':<24}" + ''.join(f"{h:>8}" for _, h, _ in СТОЛБЦЫ))
    print(f"{'норма':<24}" + ''.join(f"{(('%g–%g' % НОРМЫ[k]) if k in НОРМЫ else ''):>8}" for k, _, _ in СТОЛБЦЫ))
    for p in paths:
        r = analyze(load(p))
        print(f"{os.path.basename(p)[:22]:<24}" + ''.join(f"{(fmt.format(r[k]) + flag(k, r[k])):>8}" for k, _, fmt in СТОЛБЦЫ))

def where(path):
    t = load(path); lines = t.split('\n')
    print(f"=== {os.path.basename(path)} — где править (номера строк файла) ===")
    def show(title, rx, limit=40, flags=0):
        hits = [(i + 1, l) for i, l in enumerate(lines) if re.search(rx, l, flags)]
        if hits:
            print(f"\n-- {title}: {len(hits)}")
            for n, l in hits[:limit]: print(f"{n:>5}  {l[:110]}")
    show('Значит / Выходит / Похоже', r'\b(Значит|Выходит|Похоже)\b')
    show('«что-то»', r'[Чч]то-то')
    show('будто / словно / казалось', r'будто|словно|казалось')
    show('штампы прозы', '|'.join(re.escape(x) for x in ШТАМПЫ_ПРОЗЫ), flags=re.I)
    show('канцелярит', '|'.join(re.escape(x) for x in КАНЦЕЛЯРИТ), flags=re.I)
    show('«не X, а Y»', r'\b[Нн]е\s[^.!?;]{1,40},\s(?:а|но)\s')
    show('триада Не…/Ни…/Без…', r'(?:^|[.!?…]\s+)(Ни|Не|Без)\s[^.!?]{1,25}[.,;]\s(?:Ни|Не|без)\s[^.!?]{1,25}[.,;]\s(?:Ни|Не|без|и|а|А|И)\b')
    show('«Пауза.», «В итоге», «И всё же», «это был(о) не»', r'Пауза\.|В итоге|И вс[её] же|[Ээ]то был[ао]? не')
    show('латиница в кириллице / неразрывные / двойные пробелы', r'[А-Яа-яЁё][A-Za-z]|[A-Za-z][А-Яа-яЁё]| |[^\s]  +[^\s]')
    # абзацы без длинного предложения
    hits = []
    for i, l in enumerate(lines):
        if l.startswith(('—', '–', '#')) or not l.strip(): continue
        ss = sentences(l)
        if len(ss) >= 4 and max(len(s.split()) for s in ss) < 20: hits.append((i + 1, l))
    if hits:
        print(f"\n-- абзацы из 4+ предложений без единого длинного (≥20 слов): {len(hits)} — добавить по одному длинному")
        for n, l in hits[:40]: print(f"{n:>5}  {l[:110]}")
    hits = []
    for i, l in enumerate(lines):
        if l.startswith(('—', '–', '#')) or not l.strip(): continue
        wl = [len(s.split()) for s in sentences(l)]; run = 0
        for w in wl:
            run = run + 1 if w <= 3 else 0
            if run == 3: hits.append((i + 1, l)); break
    if hits:
        print(f"\n-- цепочки из 3+ обрывков подряд: {len(hits)} — склеить половину")
        for n, l in hits[:40]: print(f"{n:>5}  {l[:110]}")
    hits = [(i + 1, l) for i, l in enumerate(lines) if not l.startswith(('—', '–', '#')) and len(l.split()) > 12 and len(sentences(l)[-1].split()) <= 3]
    if hits:
        print(f"\n-- абзацы с приговором в хвосте (≤3 слов): {len(hits)} — каждый третий закончить на образе")
        for n, l in hits[:40]: print(f"{n:>5}  …{l[-90:]}")
    seen = {}
    for i, l in enumerate(lines):
        key = re.sub(r'\s+', ' ', l.strip())
        if len(key) > 60:
            if key in seen: print(f"\n-- ДУБЛЬ абзаца: строки {seen[key]} и {i + 1}: {key[:80]}")
            seen.setdefault(key, i + 1)
    cols = [(i + 1, l.count(':')) for i, l in enumerate(lines) if l.count(':') >= 2]
    if cols:
        print(f"\n-- абзацы с двумя и более двоеточиями: {len(cols)} (строки {', '.join(str(n) for n, _ in cols[:30])})")

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--где']
    paths = args or sorted(p for p in glob.glob(os.path.join(CH, '*.md')) if not os.path.basename(p).startswith('00'))
    if '--где' in sys.argv:
        for p in paths: where(p)
    else:
        table(paths)
