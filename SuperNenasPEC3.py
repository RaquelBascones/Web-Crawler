import re
import sqlite3
import requests
import trafilatura
from googletrans import Translator
translator = Translator()
from pathlib import Path
from html import escape
from urllib.parse import urljoin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB


# =============== 1) REGEX PARA ENLACES (expresiones regulares) ===============

LINK_REGEX = re.compile(
    r'<a[^>]+href=["\'](?P<url>[^"\']+)["\'][^>]*>(?P<text>.*?)</a>',
    re.IGNORECASE | re.DOTALL
)


def limpiar_html(texto_html: str) -> str:
    if not texto_html:
        return ""
    texto = re.sub(r"<.*?>", " ", texto_html)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def descargar_html(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[ERROR] No se pudo descargar {url}: {e}")
        return ""


# =============== 2) RESUMEN LOCAL (SIN API, GRATIS) ==========================
def generar_resumen_desde_url(url: str, fallback_text: str = "") -> str:
    """
    Genera un resumen del contenido real de la URL usando trafilatura,
    y lo traduce automáticamente al español con googletrans.
    """
    texto = ""

    # --- EXTRAER TEXTO REAL DE LA PÁGINA ---
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            texto = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
                favor_recall=False
            ) or ""
    except Exception as e:
        print(f"[TRAFILATURA] Error con {url}: {e}")
        texto = ""

    texto = (texto or "").strip()

    # Fallback si no hay texto
    if not texto:
        if fallback_text:
            texto = fallback_text
        else:
            return "Contenido no accesible automáticamente para esta URL."

    # --- RESUMIR (2 frases) ---
    frases = re.split(r'(?<=[.!?])\s+', texto)
    frases_buenas = [f.strip() for f in frases if len(f.strip()) > 40]

    if frases_buenas:
        resumen = " ".join(frases_buenas[:2])
    else:
        resumen = " ".join(frases[:2])

    if len(resumen) > 320:
        resumen = resumen[:317] + "..."

    # --- ⚠️ TRADUCIR AL ESPAÑOL ⚠️ ---
    try:
        resumen_es = translator.translate(resumen, dest="es").text
    except Exception:
        resumen_es = resumen  # fallback en caso de error

    return resumen_es




# =============== 3) BASE DE DATOS SQLITE =====================================

DB_PATH = "crawler.db"


def inicializar_db():
    """
    Crea la tabla si no existe.
    Incluye columna 'summary' para guardar el resumen del enlace.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            link_url   TEXT NOT NULL,
            link_text  TEXT,
            summary    TEXT
        );
        """
    )
    # Por si la tabla existía antes sin la columna 'summary'
    cur.execute("PRAGMA table_info(links);")
    columnas = [c[1] for c in cur.fetchall()]
    if "summary" not in columnas:
        cur.execute("ALTER TABLE links ADD COLUMN summary TEXT;")
    conn.commit()
    conn.close()



def guardar_enlace(source_url: str, link_url: str, link_text: str, summary: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO links (source_url, link_url, link_text, summary)
        VALUES (?, ?, ?, ?);
        """,
        (source_url, link_url, link_text, summary),
    )
    conn.commit()
    conn.close()


def obtener_enlaces(limit: int = 200):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_url, link_url, summary
        FROM links
        ORDER BY id DESC
        LIMIT ?;
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# =============== 4) VISTA HTML (ESTILO MÁS PROFESIONAL) ======================

def generar_vista_html(output_file: str = "resultado.html", limit: int = 200):
    filas = obtener_enlaces(limit=limit)
    path = Path(output_file)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Resultados Web Crawler</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    :root {{
        --bg-body: #F59E72;
        --bg-card: #C25A24;
        --bg-table-header: #FFD0AA;
        --bg-table-row-odd: #FFF1E3;
        --bg-table-row-even: #FFE5CF;

        --border-subtle: #F7C7A6;

        --accent: #F59E72;               /* salmón principal */
        --accent-soft: rgba(245, 158, 114, 0.25);
        --accent-strong: #E2763D;        /* naranja fuerte */
        --accent-focus: #C25A24;         /* naranja quemado para hover */

        --text-main: #0F172A;            /* azul muy oscuro */
        --text-muted: #1F2937;           /* azul oscuro suave */

        --pill-bg: rgba(245, 158, 114, 0.18);
        --shadow-soft: 0 8px 30px rgba(245, 158, 114, 0.35);

        --radius-xl: 20px;
    }}

    * {{
        box-sizing: border-box;
    }}

    body {{
        margin: 0;
        padding: 32px;
        background: radial-gradient(circle at top, #FFE6D3 0, #FFF5EC 45%, #FFD7B8 100%);
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--text-main);
    }}

    @media (max-width: 768px) {{
        body {{
            padding: 16px;
        }}
    }}

    .container {{
        max-width: 1200px;
        margin: 0 auto;
    }}

    .card {{
        background: linear-gradient(145deg, #FFFDF9 0%, #FFF5EC 55%, #FFE2C7 100%);
        padding: 28px 28px 24px 28px;
        border-radius: var(--radius-xl);
        border: 1px solid var(--border-subtle);
        box-shadow: var(--shadow-soft);
        position: relative;
        overflow: hidden;
    }}

    .card::before {{
        content: "";
        position: absolute;
        inset: -40%;
        background:
            radial-gradient(circle at 0% 0%, rgba(245, 158, 114, 0.25), transparent 60%),
            radial-gradient(circle at 100% 100%, rgba(226, 118, 61, 0.22), transparent 65%);
        opacity: 0.9;
        pointer-events: none;
    }}

    .card-inner {{
        position: relative;
        z-index: 1;
    }}

    .header {{
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 16px;
        align-items: center;
        margin-bottom: 20px;
    }}

    .title-block {{
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}

    .pill {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: var(--pill-bg);
        color: var(--accent-strong);
        border-radius: 999px;
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        border: 1px solid var(--accent-soft);
        backdrop-filter: blur(12px);
    }}

    .pill-dot {{
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: var(--accent-strong);
        box-shadow: 0 0 10px rgba(226, 118, 61, 0.8);
    }}

    h1 {{
        margin: 0;
        font-size: 26px;
        letter-spacing: 0.02em;
        display: flex;
        align-items: center;
        gap: 8px;
        color: var(--text-main);
    }}

    h1 span.highlight {{
        color: var(--accent-strong);
    }}

    .subtitle {{
        margin: 2px 0 0 0;
        font-size: 13px;
        color: var(--text-muted);
    }}

    .badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 10px;
        border-radius: 999px;
        background: #FFEFE0;
        border: 1px solid var(--border-subtle);
        font-size: 12px;
        color: var(--text-muted);
    }}

    .badge strong {{
        color: var(--accent-focus);
        font-weight: 600;
    }}

    .badge-dot {{
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: var(--accent-strong);
    }}

    .stats {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 18px;
        font-size: 13px;
        color: var(--text-muted);
    }}

    .stat-chip {{
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px solid #F9C49F;
        background: #FFF7EF;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }}

    .stat-chip span.value {{
        color: var(--accent-focus);
        font-weight: 600;
        font-feature-settings: "tnum" 1, "lnum" 1;
    }}

    .table-wrapper {{
        margin-top: 12px;
        border-radius: 16px;
        border: 1px solid #F3B98E;
        background: #FFF7EF;
        overflow: hidden;
        backdrop-filter: blur(8px);
    }}

    .table-scroller {{
        max-height: 540px;
        overflow: auto;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        min-width: 720px;
    }}

    thead {{
        position: sticky;
        top: 0;
        z-index: 2;
        background: linear-gradient(180deg, #FFD7B8 0%, #FFCBA1 60%, #FFBE8B 100%);
        box-shadow: 0 1px 0 rgba(243, 185, 140, 0.9);
    }}

    th, td {{
        padding: 10px 14px;
        text-align: left;
        border-bottom: 1px solid #F3B98E;
        vertical-align: top;
    }}

    th {{
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-size: 11px;
        color: var(--text-main);
    }}

    tbody tr:nth-child(odd) {{
        background: var(--bg-table-row-odd);
    }}

    tbody tr:nth-child(even) {{
        background: var(--bg-table-row-even);
    }}

    tbody tr:hover {{
        background: rgba(245, 158, 114, 0.24);
    }}

    td.url {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 12px;
        max-width: 360px;
        word-break: break-all;
        color: var(--text-main);
    }}

    td.source {{
        max-width: 260px;
        word-break: break-all;
        color: var(--text-main);
        opacity: 0.95;
    }}

    td.summary {{
        max-width: 420px;
        color: var(--text-muted);
    }}

    a:link,
    a:visited {{
        color: var(--accent-strong);
        text-decoration: none;
        font-weight: 600;
    }}

    a:hover,
    a:active {{
        color: var(--accent-focus);
        text-decoration: underline;
    }}

    .empty-state {{
        padding: 32px 24px;
        text-align: center;
        color: var(--text-muted);
        font-size: 14px;
    }}

    .empty-state strong {{
        color: var(--accent-focus);
    }}

    .footer {{
        margin-top: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
        color: var(--text-muted);
        border-top: 1px solid #F3B98E;
        padding-top: 10px;
    }}

    .footer span.brand {{
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-size: 10px;
        color: #1F2937;
    }}

    .footer span.brand strong {{
        color: var(--accent-strong);
    }}
</style>
</head>
<body>
<div class="container">
  <div class="card">
    <div class="card-inner">
      <div class="header">
        <div class="title-block">
          <span class="pill"><span class="pill-dot"></span> Creado por grupo de Guillermo, Raquel e Ingrid.</span>
          <h1>Enlaces <span class="highlight">indexados</span></h1>
          <p class="subtitle">
            Registros desde la base de datos SQLite:
          </p>
        </div>
        <div class="badge">
            <span class="badge-dot"></span>
            Última generación:
            <strong>sesión actual</strong>
        </div>
      </div>

      <div class="stats">
        <div class="stat-chip">
          Total enlaces <span class="value">{len(filas)}</span>
        </div>
      </div>

      <div class="table-wrapper">
        <div class="table-scroller">
"""

    if filas:
        html += """
          <table>
            <thead>
              <tr>
                <th>Fuente</th>
                <th>URL</th>
                <th>Resumen</th>
              </tr>
            </thead>
            <tbody>
"""
        for source, url, summary in filas:
            html += (
                "<tr>"
                f"<td class='source'>{escape(source)}</td>"
                f"<td class='url'><a href='{escape(url)}' target='_blank' rel='noopener noreferrer'>{escape(url)}</a></td>"
                f"<td class='summary'>{escape(summary or '')}</td>"
                "</tr>\n"
            )

        html += """
            </tbody>
          </table>
"""
    else:
        html += """
          <div class="empty-state">
            No hay enlaces almacenados todavía.<br>
            <br>
            Ejecuta el crawler con una URL válida y vuelve a generar este informe.<br><br>
            <strong>Tip:</strong> puedes aumentar el límite en <code>generar_vista_html(limit=...)</code>.
          </div>
"""

    html += """
        </div>
      </div>

      <div class="footer">
        <span>Creado por Guillermo, Raquel e Ingrid.</span>
        <span class="brand"><strong>Grupo:  </strong>Super nenas</span>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""

    with path.open("w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] Vista HTML generada en: {path.resolve()}")



# =============== 5) MODELO DE IA (un poco más “serio”) =======================

def entrenar_modelo_ia():
    """
    Entrena un modelo muy sencillo de clasificación de texto:
    - Usamos TF-IDF con unigrams + bigrams.
    - Filtrado de palabras demasiado frecuentes.
    - Stopwords en inglés (para los ejemplos que ponemos).
    """

    documentos = [
        # NOTICIAS / GENERAL
        "breaking news politics world government economy finance market crisis",
        "latest news headlines international conflict policy election campaign",
        "global news live coverage and political analysis",
        "economía mundial bolsa política internacional actualidad",

        # DEPORTE
        "football results live match sports news premier league champions",
        "sports news basketball tennis football scores highlights",
        "resultados de fútbol liga jornada clasificación gol partido",
        "crónica deportiva análisis del partido y estadísticas",

        # TIENDA / ECOMMERCE
        "buy now product offer cart checkout payment secure online shop",
        "online shop discount sale price marketplace ecommerce platform",
        "añadir al carrito oferta especial compra ahora envío gratis",
        "tienda online rebajas descuentos stock pedido factura",

        # TECNOLOGÍA / DESARROLLO
        "software programming code tutorial api developer technology cloud",
        "machine learning artificial intelligence data science model training",
        "backend frontend microservices devops docker kubernetes cloud native",
        "guía de programación en python código ejemplo librería framework",
    ]

    etiquetas = [
        "noticias",
        "noticias",
        "noticias",
        "noticias",

        "deportes",
        "deportes",
        "deportes",
        "deportes",

        "tienda",
        "tienda",
        "tienda",
        "tienda",

        "tecnologia",
        "tecnologia",
        "tecnologia",
        "tecnologia",
    ]

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),      # unigrams + bigrams
        max_df=0.85,             # ignora términos demasiado frecuentes
        min_df=1,
        sublinear_tf=True,
        stop_words="english",    # muchos términos de ejemplo están en inglés
    )
    X = vectorizer.fit_transform(documentos)

    modelo = MultinomialNB(alpha=0.5)  # alpha más fino que el default
    modelo.fit(X, etiquetas)

    return vectorizer, modelo


def clasificar_contenido_html(html: str, vectorizer, modelo) -> str:
    texto = limpiar_html(html).lower()
    if not texto:
        return "desconocido"
    X_new = vectorizer.transform([texto])
    return modelo.predict(X_new)[0]


# =============== 6) PROGRAMA PRINCIPAL ========================================

def main():
    print("=== Mini Web Crawler con BBDD + HTML + IA (Python) ===\n")
    
    url = input("Introduce la URL inicial (ej: https://example.com): ").strip()

    if not url.startswith("http"):
        print("❌ Debes poner una URL REAL que empiece por http o https.")
        return

    # Descargar la página
    html = descargar_html(url)
    if not html:
        print("No se pudo descargar la página. Saliendo.")
        return

    # Extraer enlaces
    matches = list(LINK_REGEX.finditer(html))[:50]
    print(f"\nSe encontraron {len(matches)} enlaces.\n")

    # BBDD
    inicializar_db()

    for m in matches:
        link_url = m.group("url")
        link_text = limpiar_html(m.group("text"))

        # Normalizar URLs relativas
        if link_url.startswith("/"):
            link_url_abs = urljoin(url, link_url)
        else:
            link_url_abs = link_url

        # Aquí usamos el resumen nuevo basado en trafilatura
        resumen = generar_resumen_desde_url(link_url_abs, fallback_text=link_text)

        print(f"[RESUMEN] {link_url_abs} -> {resumen[:80]}")

        guardar_enlace(url, link_url_abs, link_text, resumen)


    # Vista HTML
    generar_vista_html("supernenas.html")

    # IA
    vectorizer, modelo = entrenar_modelo_ia()
    categoria = clasificar_contenido_html(html, vectorizer, modelo)
    print(f"\n[IA] La página se ha clasificado como: {categoria}")

    print("\nListo. Abre 'supernenas.html' para ver la vista HTML con resúmenes.")


if __name__ == "__main__":
    main()
