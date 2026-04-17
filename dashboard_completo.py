import streamlit as st
import pandas as pd
import unicodedata
from io import BytesIO
from datetime import date
import os
import requests
import plotly.express as px
import plotly.graph_objects as go

# =========================
# CONFIGURAÇÃO E DESIGN
# =========================
st.set_page_config(page_title="AfiliaMetrics", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Reset geral — fundo branco limpo */
    html, body, .stApp {
        background-color: #f8fafc !important;
        font-family: 'Inter', sans-serif !important;
        color: #1e293b !important;
    }

    /* Sidebar branca com borda suave */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    [data-testid="stSidebar"] * { color: #334155 !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #0f172a !important; font-weight: 600 !important; }

    /* Cards de Métrica — estilo SaaS moderno */
    div[data-testid="metric-container"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        padding: 16px 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 4px rgba(15,23,42,0.07) !important;
        transition: box-shadow 0.2s, transform 0.2s !important;
        outline: none !important;
    }
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 4px 16px rgba(15,23,42,0.12) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricValue"]  { color: #6366f1 !important; font-size: 1.05rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"]  { color: #64748b !important; font-size: 0.78rem !important; font-weight: 500 !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; }
    [data-testid="stMetricDelta"]  { font-size: 0.78rem !important; }

    /* Tags do multiselect — roxo no lugar do vermelho */
    span[data-baseweb="tag"] {
        background-color: #ede9fe !important;
        border: 1px solid #c4b5fd !important;
        border-radius: 6px !important;
    }
    span[data-baseweb="tag"] span {
        color: #6366f1 !important;
        font-weight: 500 !important;
        font-size: 0.78rem !important;
    }
    span[data-baseweb="tag"] button { color: #6366f1 !important; }

    /* Radio buttons mais compactos */
    div[data-testid="stRadio"] > div { gap: 6px !important; }

    /* Toggle */
    div[data-testid="stToggle"] label { font-weight: 500 !important; }

    /* Títulos */
    h1 { color: #0f172a !important; font-size: 1.8rem !important; font-weight: 700 !important; }
    h2, h3 { color: #1e293b !important; font-weight: 600 !important; }

    /* Tabelas */
    .stDataFrame {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background: white !important;
    }

    /* Divider */
    hr { border-color: #e2e8f0 !important; }

    /* Alertas */
    .stAlert { border-radius: 10px !important; }

    /* Botões de download */
    .stDownloadButton button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border-radius: 9px !important;
        border: none !important;
        padding: 10px 22px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important;
        transition: opacity 0.2s !important;
    }
    .stDownloadButton button:hover { opacity: 0.88 !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #f1f5f9 !important;
        border-radius: 10px !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        color: #64748b !important;
        font-weight: 500 !important;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #6366f1 !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
    }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
        border-radius: 99px !important;
    }

    /* Inputs e selects */
    .stSelectbox > div, .stNumberInput > div {
        border-radius: 8px !important;
    }

    /* Caption / subtexto */
    .stCaption { color: #94a3b8 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:#6366f1; border-radius:16px; padding:24px 32px; margin-bottom:24px;">
    <div style="font-size:2rem; font-weight:800; color:white; letter-spacing:-1px; font-family:Inter,sans-serif; line-height:1.1;">
        Afilia<span style="color:#c4b5fd;">Metrics</span>
    </div>
    <div style="font-size:0.82rem; color:rgba(255,255,255,0.6); margin-top:6px; font-family:Inter,sans-serif;">
        Dashboard de Afiliados &nbsp;·&nbsp; {date.today().strftime('%d/%m/%Y')}
    </div>
</div>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("""
<div style="padding:4px 0 12px 0;">
    <div style="font-size:1.1rem; font-weight:800; color:#0f172a; font-family:Inter,sans-serif; letter-spacing:-0.3px;">
        Afilia<span style="color:#6366f1;">Metrics</span>
    </div>
    <div style="font-size:0.72rem; color:#94a3b8; font-family:Inter,sans-serif;">Painel de Controle</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown("**🎯 Configurações**")
roi_minimo   = st.sidebar.slider("ROI mínimo aceitável", min_value=-1.0, max_value=5.0, value=0.5, step=0.05)
meta_mensal  = st.sidebar.number_input("Meta mensal de faturamento (R$)", min_value=0.0, value=10000.0, step=500.0)

st.sidebar.divider()
st.sidebar.markdown("**📂 Importação de Arquivos**")

pinterest_files       = st.sidebar.file_uploader("📌 Pinterest (CSV)",         type="csv",  accept_multiple_files=True, help="Exporte o relatório de métricas do Pinterest Ads em CSV")
meta_files            = st.sidebar.file_uploader("🔵 Meta Ads (XLSX)",          type="xlsx", accept_multiple_files=True, help="Exporte o relatório de campanhas do Meta Ads em XLSX")
shopee_comissao_files = st.sidebar.file_uploader("🛍️ Shopee – Comissões (CSV)", type="csv",  accept_multiple_files=True, help="Exporte o relatório de comissões do painel de afiliados Shopee")
shopee_cliques_files  = st.sidebar.file_uploader("🛍️ Shopee – Cliques (CSV)",   type="csv",  accept_multiple_files=True, help="Exporte o relatório de cliques do painel de afiliados Shopee")

# Status dos uploads
st.sidebar.markdown("**📋 Status dos arquivos**")
def status_badge(files, nome, emoji):
    if files:
        st.sidebar.markdown(f'<span style="color:#16a34a; font-size:0.82rem;">{emoji} ✅ {nome} — {len(files)} arquivo(s)</span>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown(f'<span style="color:#94a3b8; font-size:0.82rem;">{emoji} ⏳ {nome} — não importado</span>', unsafe_allow_html=True)

status_badge(pinterest_files,       "Pinterest",        "📌")
status_badge(meta_files,            "Meta Ads",         "🔵")
status_badge(shopee_comissao_files, "Shopee Comissões", "🛍️")
status_badge(shopee_cliques_files,  "Shopee Cliques",   "🛍️")

# =========================
# FUNÇÕES UTILITÁRIAS
# =========================

def normalizar_texto(txt):
    if pd.isna(txt): return ""
    txt = str(txt).lower().strip()
    return unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("utf-8")

def normalizar_coluna(col):
    col = str(col).lower()
    col = unicodedata.normalize("NFKD", col).encode("ascii", "ignore").decode("utf-8")
    return col.replace(" ", "_").replace("(", "").replace(")", "").replace("$", "")

def limpar_subid(valor):
    if pd.isna(valor): return ""
    return str(valor).replace("-", "").strip()

def converter_valor(valor):
    if pd.isna(valor): return 0.0
    valor = str(valor).replace("R$", "").strip()
    if "." in valor and "," in valor:
        valor = valor.replace(".", "").replace(",", ".")
    elif "," in valor:
        valor = valor.replace(",", ".")
    try: return float(valor)
    except: return 0.0

def ler_csv_inteligente(file):
    file.seek(0)
    for enc in ["utf-8-sig", "utf-8", "latin-1"]:
        for sep in [",", ";"]:
            try:
                file.seek(0)
                df = pd.read_csv(file, sep=sep, encoding=enc, engine="python")
                if len(df.columns) > 1:
                    return df
            except:
                continue
    file.seek(0)
    return pd.read_csv(file, sep=",", encoding="latin-1", engine="python")

def ler_excel(file):
    file.seek(0)
    return pd.read_excel(file, engine="openpyxl")

def gerar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dashboard")
    output.seek(0)
    return output

def formatar_valor(v):
    return f"R$ {v:,.2f}"

def titulo(icone, texto, cor="#6366f1"):
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin: 28px 0 16px 0;">
        <div style="width:4px; height:32px; background:{cor}; border-radius:4px;"></div>
        <span style="font-size:1.25rem; font-weight:700; color:#0f172a; font-family:Inter,sans-serif; letter-spacing:-0.3px;">
            {icone}&nbsp; {texto}
        </span>
    </div>
    """, unsafe_allow_html=True)


# =========================
# PROCESSAMENTO
# =========================
ads              = pd.DataFrame(columns=["subid", "gasto", "cliques_anuncio"])
vendas           = pd.DataFrame(columns=["subid", "comissoes", "faturamento", "vendas_diretas", "vendas_indiretas", "qtd_itens"])
cliques_shopee   = pd.DataFrame(columns=["subid", "cliques_shopee"])
faturamento_bruto_total = 0.0
erros_carregamento = []
df_shopee_raw    = pd.DataFrame()  # dados brutos para análise por dia

# --- ADS COM DATA ---
lista_ads     = []  # agregado por subid (total)
lista_ads_raw = []  # raw com data por dia

if pinterest_files:
    for f in pinterest_files:
        try:
            dfp = ler_csv_inteligente(f)
            dfp.columns = [normalizar_coluna(c) for c in dfp.columns]

            # Colunas do Pinterest com data
            col_sub     = next((c for c in dfp.columns if "ad_name" in c or "nome" in c), None)
            col_gasto   = next((c for c in dfp.columns if "spend" in c or "gasto" in c), None)
            col_cliques = next((c for c in dfp.columns if "pin_clicks" in c or "cliques" in c), None)
            col_data    = next((c for c in dfp.columns if c == "date" or "data" in c), None)

            if col_sub and col_gasto:
                dfp["subid"]           = dfp[col_sub].apply(limpar_subid)
                dfp["gasto"]           = dfp[col_gasto].apply(converter_valor)
                dfp["cliques_anuncio"] = pd.to_numeric(dfp[col_cliques], errors="coerce").fillna(0) if col_cliques else 0
                dfp["_data"]           = pd.to_datetime(dfp[col_data], errors="coerce") if col_data else pd.NaT
                dfp["_plataforma"]     = "Pinterest"
                lista_ads.append(dfp[["subid", "gasto", "cliques_anuncio"]])
                lista_ads_raw.append(dfp[["subid", "gasto", "cliques_anuncio", "_data", "_plataforma"]])
            else:
                erros_carregamento.append(f"Pinterest '{f.name}': colunas não encontradas.")
        except Exception as e:
            erros_carregamento.append(f"Pinterest '{f.name}': {e}")

if meta_files:
    for f in meta_files:
        try:
            meta = ler_excel(f)
            meta.columns = [normalizar_coluna(c) for c in meta.columns]

            col_nome    = next((c for c in meta.columns if "nome_do_anuncio" in c), None)
            col_gasto   = next((c for c in meta.columns if "valor_usado_brl" in c or "valor_usado" in c), None)
            col_cliques = next((c for c in meta.columns if "resultados" in c), None)
            col_data    = next((c for c in meta.columns if "inicio_dos_relatorios" in c or "inicio" in c), None)

            if not col_nome or not col_gasto:
                erros_carregamento.append(f"Meta '{f.name}': colunas esperadas não encontradas.")
                continue

            meta["subid"]           = meta[col_nome].apply(limpar_subid)
            meta["gasto"]           = meta[col_gasto].apply(converter_valor)
            meta["cliques_anuncio"] = pd.to_numeric(meta[col_cliques], errors="coerce").fillna(0) if col_cliques else 0
            meta["_data"]           = pd.to_datetime(meta[col_data], errors="coerce") if col_data else pd.NaT
            meta["_plataforma"]     = "Meta"
            lista_ads.append(meta[["subid", "gasto", "cliques_anuncio"]])
            lista_ads_raw.append(meta[["subid", "gasto", "cliques_anuncio", "_data", "_plataforma"]])
        except Exception as e:
            erros_carregamento.append(f"Meta '{f.name}': {e}")

if lista_ads:
    ads = pd.concat(lista_ads).groupby("subid", as_index=False).sum()

# Raw de ads com data para filtro
df_ads_raw = pd.concat(lista_ads_raw, ignore_index=True) if lista_ads_raw else pd.DataFrame()

# --- SHOPEE COMISSÕES ---
lista_vendas = []
lista_shopee_raw = []

if shopee_comissao_files:
    for f in shopee_comissao_files:
        try:
            shp = ler_csv_inteligente(f)
            shp.columns = [normalizar_coluna(c) for c in shp.columns]

            col_valor     = next((c for c in shp.columns if "valor_de_compra" in c), None)
            col_status    = next((c for c in shp.columns if "status_do_pedido" in c), None)
            col_notas     = next((c for c in shp.columns if "notas" in c or "status_do_item" in c), None)
            col_comis     = next((c for c in shp.columns if "comissao_liquida" in c), None) or \
                            next((c for c in shp.columns if "comissao_total_do_item" in c), None) or \
                            next((c for c in shp.columns if "comissao_total" in c), shp.columns[-1])
            col_sub       = next((c for c in shp.columns if "sub_id1" in c), None)
            col_atrib     = next((c for c in shp.columns if "tipo_de_atribuicao" in c or "atribuicao" in c), None)
            col_data      = next((c for c in shp.columns if "horario_do_pedido" in c or "data_do_pedido" in c), None)
            col_qtd       = next((c for c in shp.columns if "qtd" in c), None)
            col_canal     = next((c for c in shp.columns if c == "canal"), None)

            if not col_valor:
                erros_carregamento.append(f"Shopee '{f.name}': coluna 'valor_de_compra' não encontrada.")
                continue

            status_limpo = shp[col_status].apply(normalizar_texto) if col_status else pd.Series([""] * len(shp))
            notas_limpas = shp[col_notas].apply(normalizar_texto)  if col_notas  else pd.Series([""] * len(shp))

            termos_excluir = "cancelado|incompleto|nao pago|ainda nao pagou|nao pagou"
            mask_validas   = ~(
                status_limpo.str.contains("cancelado|incompleto", na=False) |
                notas_limpas.str.contains(termos_excluir, na=False)
            )

            shp_valido = shp[mask_validas].copy()
            shp_valido["_valor"]    = shp_valido[col_valor].apply(converter_valor)
            shp_valido["_comissao"] = shp_valido[col_comis].apply(converter_valor)
            shp_valido["_qtd"]      = pd.to_numeric(shp_valido[col_qtd], errors="coerce").fillna(1) if col_qtd else 1
            faturamento_bruto_total += shp_valido["_valor"].sum()

            if col_sub:
                shp_valido["subid"] = shp_valido[col_sub].apply(limpar_subid)

                # Tipo de venda: direta (mesma loja) ou indireta (loja diferente)
                if col_atrib:
                    atrib_limpo = shp_valido[col_atrib].apply(normalizar_texto)
                    shp_valido["_direta"]   = atrib_limpo.str.contains("mesma", na=False).astype(int)
                    shp_valido["_indireta"] = atrib_limpo.str.contains("diferente", na=False).astype(int)
                else:
                    shp_valido["_direta"]   = 0
                    shp_valido["_indireta"] = 1

                # Data do pedido para análise diária
                if col_data:
                    shp_valido["_data"] = pd.to_datetime(shp_valido[col_data], errors="coerce").dt.date
                else:
                    shp_valido["_data"] = date.today()

                shp_valido["_canal"] = shp_valido[col_canal].fillna("Others").str.strip() if col_canal else "Others"

                lista_shopee_raw.append(shp_valido[["subid", "_valor", "_comissao", "_qtd", "_direta", "_indireta", "_data", "_canal"]])

                agg = shp_valido.groupby("subid", as_index=False).agg(
                    comissoes=("_comissao", "sum"),
                    faturamento=("_valor", "sum"),
                    vendas_diretas=("_direta", "sum"),
                    vendas_indiretas=("_indireta", "sum"),
                    qtd_itens=("_qtd", "sum")
                )
                lista_vendas.append(agg)

        except Exception as e:
            erros_carregamento.append(f"Shopee Comissões '{f.name}': {e}")

if lista_vendas:
    vendas = pd.concat(lista_vendas).groupby("subid", as_index=False).agg({
        "comissoes": "sum", "faturamento": "sum",
        "vendas_diretas": "sum", "vendas_indiretas": "sum", "qtd_itens": "sum"
    })

if lista_shopee_raw:
    df_shopee_raw = pd.concat(lista_shopee_raw, ignore_index=True)

# =========================
# FILTROS GLOBAIS
# =========================
if not df_shopee_raw.empty and "_data" in df_shopee_raw.columns:
    df_shopee_raw["_data"] = pd.to_datetime(df_shopee_raw["_data"], errors="coerce")
    data_min = df_shopee_raw["_data"].min().date()
    data_max = df_shopee_raw["_data"].max().date()

    st.sidebar.divider()
    st.sidebar.markdown("**🔍 Filtros**")

    # --- Filtro de período ---
    st.sidebar.markdown("<span style='font-size:0.8rem; color:#64748b;'>📅 Período principal (análise)</span>", unsafe_allow_html=True)
    col_d1, col_d2 = st.sidebar.columns(2)
    with col_d1:
        data_ini = st.date_input("Início:", value=data_min, min_value=data_min, max_value=data_max, format="DD/MM/YYYY")
    with col_d2:
        data_fim = st.date_input("Fim:", value=data_max, min_value=data_min, max_value=data_max, format="DD/MM/YYYY")

    # --- Filtro por SubID ---
    st.sidebar.markdown("<span style='font-size:0.8rem; color:#64748b;'>🏷️ SubID(s)</span>", unsafe_allow_html=True)
    subids_todos = sorted(df_shopee_raw["subid"].dropna().unique().tolist())
    subids_sel   = st.sidebar.multiselect("", subids_todos, default=subids_todos, label_visibility="collapsed")

    # --- Filtro por canal ---
    canais_disponiveis = sorted(df_shopee_raw["_canal"].dropna().unique().tolist()) if "_canal" in df_shopee_raw.columns else []
    if canais_disponiveis:
        st.sidebar.markdown("<span style='font-size:0.8rem; color:#64748b;'>📡 Canal</span>", unsafe_allow_html=True)
        canais_sel = st.sidebar.multiselect("", canais_disponiveis, default=canais_disponiveis, label_visibility="collapsed")
    else:
        canais_sel = []

    # --- Filtro por tipo de venda ---
    st.sidebar.markdown("<span style='font-size:0.8rem; color:#64748b;'>🔀 Tipo de venda</span>", unsafe_allow_html=True)
    tipo_venda = st.sidebar.radio("", ["Todas", "Somente Diretas", "Somente Indiretas"],
                                   horizontal=True, label_visibility="collapsed")

    # --- Comparativo de períodos ---
    st.sidebar.markdown("")
    comparar = st.sidebar.toggle("📊 Comparar dois períodos")
    if comparar:
        st.sidebar.markdown("<span style='font-size:0.8rem; color:#f59e0b;'>📅 Período de comparação</span>", unsafe_allow_html=True)
        st.sidebar.caption("Selecione outro intervalo para comparar com o período principal")
        col_c1, col_c2 = st.sidebar.columns(2)
        with col_c1:
            data_ini_b = st.date_input("Início:", value=data_min, min_value=data_min, max_value=data_max, key="db1", format="DD/MM/YYYY")
        with col_c2:
            data_fim_b = st.date_input("Fim:", value=data_max, min_value=data_min, max_value=data_max, key="db2", format="DD/MM/YYYY")

    # --- Aplicar filtros no raw ---
    mask = (
        (df_shopee_raw["_data"].dt.date >= data_ini) &
        (df_shopee_raw["_data"].dt.date <= data_fim) &
        (df_shopee_raw["subid"].isin(subids_sel))
    )
    if canais_sel and "_canal" in df_shopee_raw.columns:
        mask &= df_shopee_raw["_canal"].isin(canais_sel)
    if tipo_venda == "Somente Diretas":
        mask &= df_shopee_raw["_direta"] == 1
    elif tipo_venda == "Somente Indiretas":
        mask &= df_shopee_raw["_indireta"] == 1

    df_shopee_filtrado = df_shopee_raw[mask].copy()

    # Recalcula faturamento bruto com filtro
    faturamento_bruto_total = df_shopee_filtrado["_valor"].sum()

    # Recalcula vendas agregadas com filtro
    if not df_shopee_filtrado.empty:
        vendas = df_shopee_filtrado.groupby("subid", as_index=False).agg(
            comissoes=("_comissao", "sum"),
            faturamento=("_valor", "sum"),
            vendas_diretas=("_direta", "sum"),
            vendas_indiretas=("_indireta", "sum"),
            qtd_itens=("_qtd", "sum")
        )
    else:
        vendas = pd.DataFrame(columns=["subid", "comissoes", "faturamento", "vendas_diretas", "vendas_indiretas", "qtd_itens"])

    # Filtra ads por data se disponível
    if not df_ads_raw.empty and "_data" in df_ads_raw.columns:
        df_ads_raw["_data"] = pd.to_datetime(df_ads_raw["_data"], errors="coerce")
        data_ini_dt = pd.Timestamp(data_ini)
        data_fim_dt = pd.Timestamp(data_fim)
        mask_ads = (
            (df_ads_raw["_data"] >= data_ini_dt) &
            (df_ads_raw["_data"] <= data_fim_dt)
        )
        ads_filtrado = df_ads_raw[mask_ads].groupby("subid", as_index=False).agg(
            gasto=("gasto", "sum"),
            cliques_anuncio=("cliques_anuncio", "sum")
        )
    else:
        ads_filtrado = ads.copy()

    # Período B para comparativo
    if comparar:
        mask_b = (
            (df_shopee_raw["_data"].dt.date >= data_ini_b) &
            (df_shopee_raw["_data"].dt.date <= data_fim_b) &
            (df_shopee_raw["subid"].isin(subids_sel))
        )
        df_raw_b = df_shopee_raw[mask_b].copy()
        vendas_b = df_raw_b.groupby("subid", as_index=False).agg(
            comissoes=("_comissao", "sum"),
            faturamento=("_valor", "sum"),
            vendas_diretas=("_direta", "sum"),
            vendas_indiretas=("_indireta", "sum"),
            qtd_itens=("_qtd", "sum")
        ) if not df_raw_b.empty else pd.DataFrame()
else:
    df_shopee_filtrado = df_shopee_raw.copy()
    ads_filtrado = ads.copy()
    comparar = False

# --- SHOPEE CLIQUES ---
lista_cliques = []
if shopee_cliques_files:
    for f in shopee_cliques_files:
        try:
            clk = ler_csv_inteligente(f)
            clk.columns = [normalizar_coluna(c) for c in clk.columns]
            sub = next((c for c in clk.columns if "sub" in c), None)
            if sub:
                clk["subid"] = clk[sub].apply(limpar_subid)
                lista_cliques.append(clk[["subid"]])
            else:
                erros_carregamento.append(f"Cliques '{f.name}': coluna 'sub' não encontrada.")
        except Exception as e:
            erros_carregamento.append(f"Cliques '{f.name}': {e}")

if lista_cliques:
    cliques_shopee = pd.concat(lista_cliques).groupby("subid").size().reset_index(name="cliques_shopee")

# --- MERGE E CÁLCULOS ---
df = (
    ads_filtrado
    .merge(vendas,         on="subid", how="outer")
    .merge(cliques_shopee, on="subid", how="outer")
    .fillna(0)
)
for col in ["comissoes", "faturamento", "gasto", "vendas_diretas", "vendas_indiretas", "qtd_itens", "cliques_anuncio", "cliques_shopee"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
df["lucro"] = df["comissoes"] - df["gasto"]
df["roi"]   = df.apply(lambda x: x["lucro"] / x["gasto"] if x["gasto"] > 0 else 0, axis=1)
df["%_batimento_cliques"] = df.apply(
    lambda x: (x["cliques_shopee"] / x["cliques_anuncio"] * 100) if x["cliques_anuncio"] > 0 else 0, axis=1
)
df["total_vendas"]  = df["vendas_diretas"] + df["vendas_indiretas"]
df["ticket_medio"]  = df.apply(lambda x: x["faturamento"] / x["total_vendas"] if x["total_vendas"] > 0 else 0, axis=1)

# Ordem das colunas
colunas_ordem = ["subid", "comissoes", "faturamento", "gasto", "lucro", "roi",
                 "total_vendas", "vendas_diretas", "vendas_indiretas", "qtd_itens",
                 "ticket_medio", "cliques_anuncio", "cliques_shopee", "%_batimento_cliques"]
for c in colunas_ordem:
    if c not in df.columns:
        df[c] = 0
df = df[colunas_ordem]

total_gasto      = df["gasto"].sum()
total_comissao   = df["comissoes"].sum()
total_lucro      = df["lucro"].sum()
total_roi        = total_lucro / total_gasto if total_gasto > 0 else 0
total_vendas_num = df["total_vendas"].sum()
ticket_medio_geral = df["faturamento"].sum() / total_vendas_num if total_vendas_num > 0 else 0

# =========================
# EXIBIÇÃO DE ERROS
# =========================
if erros_carregamento:
    with st.expander("⚠️ Avisos de carregamento", expanded=False):
        for e in erros_carregamento:
            st.warning(e)

# =========================
# MÉTRICAS
# =========================
if not df.empty and (total_gasto > 0 or total_comissao > 0):
    st.success("✅ Análise gerada com sucesso!")

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("Comissão",    formatar_valor(total_comissao))
    c2.metric("Fat. Bruto",  formatar_valor(faturamento_bruto_total))
    c3.metric("Gasto",       formatar_valor(total_gasto))
    c4.metric("Lucro",       formatar_valor(total_lucro), delta=f"{'▲' if total_lucro >= 0 else '▼'} {formatar_valor(abs(total_lucro))}")
    c5.metric("ROI Geral",   f"{total_roi:.2%}")
    total_vendas_geral = int(df["total_vendas"].sum())
    c6.metric("Vendas",      f"{total_vendas_geral}", delta=f"{int(df['vendas_diretas'].sum())}D / {int(df['vendas_indiretas'].sum())}I")
    c7.metric("Ticket Médio", formatar_valor(ticket_medio_geral))

    # Progresso da Meta
    percentual_meta = min(faturamento_bruto_total / meta_mensal, 1.0) if meta_mensal else 0
    st.markdown(f"""
    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:16px 20px; margin:16px 0 8px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:0.85rem; font-weight:600; color:#475569; font-family:Inter,sans-serif;">
                🎯 Meta Mensal — R$ {meta_mensal:,.2f}
            </span>
            <span style="font-size:0.85rem; font-weight:700; color:#6366f1; font-family:Inter,sans-serif;">
                {percentual_meta*100:.1f}% atingido
            </span>
        </div>
        <div style="background:#e2e8f0; border-radius:99px; height:8px; overflow:hidden;">
            <div style="background:linear-gradient(90deg,#6366f1,#8b5cf6); width:{min(percentual_meta*100,100):.1f}%; height:100%; border-radius:99px; transition:width 0.5s;"></div>
        </div>
        <div style="font-size:0.78rem; color:#94a3b8; margin-top:6px; font-family:Inter,sans-serif;">
            Faltam: R$ {max(meta_mensal - faturamento_bruto_total, 0):,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # =========================
    # 1. DETALHAMENTO POR SubID (PRIMEIRO)
    # =========================
    titulo("📊", "Detalhamento por SubID")
    col_ord, col_filt = st.columns([2, 1])
    with col_ord:
        ordenar_por = st.selectbox("Ordenar por:", ["roi", "lucro", "faturamento", "comissoes", "gasto", "total_vendas", "%_batimento_cliques"])
    with col_filt:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        mostrar_apenas_prejuizo = st.toggle("🔴 Só prejuízo")

    df_tabela = df.copy()
    if mostrar_apenas_prejuizo:
        df_tabela = df_tabela[df_tabela["lucro"] < 0]
        total_prejuizo = df_tabela["lucro"].sum()
        qtd_prejuizo   = len(df_tabela)
        st.error(f"🚨 **{qtd_prejuizo} campanha(s) em prejuízo** — Prejuízo total: **R$ {abs(total_prejuizo):,.2f}**")
    df_tabela = df_tabela.sort_values(ordenar_por, ascending=False)

    df_display = df_tabela.copy()
    for col in ["comissoes", "faturamento", "gasto", "lucro"]:
        df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}")
    df_display["roi"]                 = df_display["roi"].apply(lambda x: f"{x:.2%}")
    df_display["%_batimento_cliques"] = df_display["%_batimento_cliques"].apply(lambda x: f"{x:.2f}%")
    df_display["ticket_medio"]        = df_display["ticket_medio"].apply(lambda x: f"R$ {x:,.2f}" if x > 0 else "—")
    for col in ["total_vendas", "vendas_diretas", "vendas_indiretas", "qtd_itens", "cliques_anuncio", "cliques_shopee"]:
        df_display[col] = df_display[col].astype(int)

    # Tendência por texto compacto
    def gerar_spark(subid):
        if df_shopee_filtrado.empty or "_data" not in df_shopee_filtrado.columns:
            return "—"
        dados = df_shopee_filtrado[df_shopee_filtrado["subid"] == subid].copy()
        if dados.empty: return "—"
        dados["_data"] = pd.to_datetime(dados["_data"], errors="coerce")
        por_dia = dados.groupby("_data")["_valor"].sum().sort_index().tail(7)
        if len(por_dia) < 2: return "—"
        vals = por_dia.values
        var = ((vals[-1] - vals[0]) / vals[0] * 100) if vals[0] > 0 else 0
        if var > 0:   return f"↑ +{var:.0f}%"
        elif var < 0: return f"↓ {var:.0f}%"
        else:         return "→"

    df_display["tendencia"] = df_tabela["subid"].apply(gerar_spark)

    df_display.columns = [
        "SubID", "Comissão", "Faturamento", "Gasto", "Lucro", "_roi_num",
        "Vendas", "Diretas", "Indiretas", "Prods",
        "Ticket Médio", "Cliques Anúncio", "Cliques Shopee", "% Bat.", "_tend"
    ]

    # ROI com seta baseada no valor (positivo ↑ / negativo ↓)
    def formatar_roi(row):
        roi_str = str(row["_roi_num"])
        try:
            v = float(roi_str.replace("%","").replace(",",".").strip()) / 100
            if v > 0:   return f"↑ {v:.0%}"
            elif v < 0: return f"↓ {v:.0%}"
            else:       return "0%"
        except:
            return roi_str

    df_display["ROI"] = df_display.apply(formatar_roi, axis=1)
    df_display = df_display.drop(columns=["_roi_num", "_tend"])

    cols_ordem = ["SubID", "Comissão", "Gasto", "Lucro", "ROI", "Faturamento",
                  "Ticket Médio", "Vendas", "Diretas", "Indiretas", "Prods",
                  "Cliques Anúncio", "Cliques Shopee", "% Bat."]
    df_display = df_display[cols_ordem]

    # Linha de total
    total_row = {
        "SubID":           "TOTAL",
        "Comissão":        f"R$ {df_tabela['comissoes'].sum():,.2f}",
        "Gasto":           f"R$ {df_tabela['gasto'].sum():,.2f}",
        "Lucro":           f"R$ {df_tabela['lucro'].sum():,.2f}",
        "ROI":             f"{(df_tabela['lucro'].sum()/df_tabela['gasto'].sum()) if df_tabela['gasto'].sum() > 0 else 0:.0%}",
        "Faturamento":     f"R$ {df_tabela['faturamento'].sum():,.2f}",
        "Ticket Médio":    f"R$ {ticket_medio_geral:,.2f}",
        "Vendas":          int(df_tabela["total_vendas"].sum()),
        "Diretas":         int(df_tabela["vendas_diretas"].sum()),
        "Indiretas":       int(df_tabela["vendas_indiretas"].sum()),
        "Prods":           int(df_tabela["qtd_itens"].sum()),
        "Cliques Anúncio": int(df_tabela["cliques_anuncio"].sum()),
        "Cliques Shopee":  int(df_tabela["cliques_shopee"].sum()),
        "% Bat.":          "—",
    }
    df_display = pd.concat([df_display, pd.DataFrame([total_row])], ignore_index=True)

    def colorir_tabela(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for i, row in df.iterrows():
            if row["SubID"] == "TOTAL":
                for col in df.columns:
                    styles.at[i, col] = "font-weight:bold; background-color:#f1f5f9;"
                continue
            try:
                v = float(str(row["Lucro"]).replace("R$","").replace(",","").strip())
                styles.at[i, "Lucro"] = "color: #16a34a; font-weight:bold;" if v > 0 else "color: #dc2626; font-weight:bold;"
            except: pass
            try:
                roi_str = str(row["ROI"])
                v = float(roi_str.replace("↑","").replace("↓","").replace("%","").replace(",",".").strip()) / 100
                if v >= roi_minimo:
                    styles.at[i, "ROI"] = "color: #16a34a; font-weight:bold;"
                elif v >= 0:
                    styles.at[i, "ROI"] = "color: #d97706; font-weight:bold;"
                else:
                    styles.at[i, "ROI"] = "color: #dc2626; font-weight:bold;"
            except: pass
        return styles

    st.dataframe(df_display.style.apply(colorir_tabela, axis=None), use_container_width=True, hide_index=True)

    st.divider()

    # =========================
    # 2. CANAL
    # =========================
    if not df_shopee_filtrado.empty and "_canal" in df_shopee_filtrado.columns:
        titulo("📡", "Canal — Quantidade & Comissão", cor="#8b5cf6")
        canal_agg = df_shopee_filtrado.groupby("_canal", as_index=False).agg(
            pedidos=("_qtd", "count"),
            vendas_brutas=("_valor", "sum"),
            comissao_total=("_comissao", "sum")
        ).sort_values("vendas_brutas", ascending=False)

        # Ícones e cores por canal
        canal_config = {
            "Pinterest":    {"bg": "#fff0f0", "cor": "#E60023", "svg": '<svg width="20" height="20" viewBox="0 0 24 24"><path fill="#E60023" d="M12 0C5.373 0 0 5.373 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.632-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/></svg>'},
            "Instagram":    {"bg": "#fff0f8", "cor": "#C13584", "svg": '<svg width="20" height="20" viewBox="0 0 24 24"><path fill="#C13584" d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/></svg>'},
            "Websites":     {"bg": "#f0fdf4", "cor": "#16a34a", "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'},
            "Others":       {"bg": "#f8fafc", "cor": "#64748b", "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>'},
            "Code Sharing": {"bg": "#eff6ff", "cor": "#2563eb", "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>'},
            "EdgeBrowser":  {"bg": "#eff6ff", "cor": "#0ea5e9", "svg": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8.56 2.75c4.37 6.03 6.02 9.42 8.03 17.72m2.54-15.38c-3.72 4.35-8.94 5.66-16.88 5.85m19.5 1.9c-3.5-.93-6.63-.82-8.94 0-2.58.92-5.01 2.86-7.44 6.32"/></svg>'},
        }

        # Renderiza cards por canal
        cols_canal = st.columns(len(canal_agg))
        for idx, (_, row) in enumerate(canal_agg.iterrows()):
            nome = str(row["_canal"]) if "_canal" in canal_agg.columns else str(row.iloc[0])
            cfg = canal_config.get(nome, {"bg": "#f8fafc", "cor": "#64748b", "svg": "📦"})
            fat = f"R$ {row['vendas_brutas']:,.2f}"
            com = f"R$ {row['comissao_total']:,.2f}"
            ped = int(row['pedidos'])
            with cols_canal[idx]:
                st.markdown(f"""
                <div style="background:{cfg['bg']}; border:1px solid #e2e8f0; border-radius:12px; padding:14px 16px; text-align:center;">
                    <div style="display:flex; justify-content:center; margin-bottom:8px;">{cfg['svg']}</div>
                    <div style="font-size:12px; font-weight:700; color:{cfg['cor']}; margin-bottom:6px;">{nome}</div>
                    <div style="font-size:15px; font-weight:700; color:#0f172a;">{fat}</div>
                    <div style="font-size:11px; color:#64748b; margin-top:2px;">{com} comissão</div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:2px;">{ped} pedidos</div>
                </div>
                """, unsafe_allow_html=True)
        st.divider()

    # =========================
    # 3. IA — INSIGHTS
    # =========================
    titulo("🤖", "Analista IA — Insights", cor="#0ea5e9")
    if not df.empty and df["roi"].nunique() > 0:
        melhor             = df.loc[df["roi"].idxmax()]
        pior               = df.loc[df["lucro"].idxmin()]
        campanhas_lucro    = len(df[df["lucro"] > 0])
        campanhas_prejuizo = len(df[df["lucro"] < 0])

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.markdown(f"""<div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px; padding:16px; height:110px;">
                <div style="font-size:10px; font-weight:700; color:#1d4ed8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">💡 Escalar</div>
                <div style="font-size:12px; color:#1e3a5f; line-height:1.6;"><strong>{melhor['subid']}</strong><br>ROI de <strong>{melhor['roi']:.0%}</strong> — melhor performance</div>
            </div>""", unsafe_allow_html=True)
        with col_b:
            if pior["lucro"] < 0:
                st.markdown(f"""<div style="background:#fffbeb; border:1px solid #fde68a; border-radius:12px; padding:16px; height:110px;">
                    <div style="font-size:10px; font-weight:700; color:#92400e; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">⚠️ Revisar</div>
                    <div style="font-size:12px; color:#78350f; line-height:1.6;"><strong>{pior['subid']}</strong><br>Prejuízo de <strong>R$ {abs(pior['lucro']):.2f}</strong></div>
                </div>""", unsafe_allow_html=True)
        with col_c:
            st.markdown(f"""<div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px; padding:16px; height:110px;">
                <div style="font-size:10px; font-weight:700; color:#14532d; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">✅ Lucrativas</div>
                <div style="font-size:28px; font-weight:800; color:#16a34a; line-height:1;">{campanhas_lucro}</div>
                <div style="font-size:11px; color:#4ade80; margin-top:6px;">campanhas no positivo</div>
            </div>""", unsafe_allow_html=True)
        with col_d:
            st.markdown(f"""<div style="background:#fef2f2; border:1px solid #fecaca; border-radius:12px; padding:16px; height:110px;">
                <div style="font-size:10px; font-weight:700; color:#991b1b; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px;">🚨 Em Prejuízo</div>
                <div style="font-size:28px; font-weight:800; color:#dc2626; line-height:1;">{campanhas_prejuizo}</div>
                <div style="font-size:11px; color:#f87171; margin-top:6px;">campanhas no negativo</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # =========================
    # 4. COMPARATIVO DE PERÍODOS
    # =========================
    if comparar and not df_shopee_raw.empty and not vendas_b.empty:
        titulo("📊", "Comparativo de Períodos", cor="#f59e0b")
        st.caption(f"**Período A:** {data_ini} → {data_fim}  |  **Período B:** {data_ini_b} → {data_fim_b}")
        fat_a = df_shopee_filtrado["_valor"].sum()
        com_a = df_shopee_filtrado["_comissao"].sum()
        ven_a = len(df_shopee_filtrado)
        fat_b = df_raw_b["_valor"].sum()
        com_b = df_raw_b["_comissao"].sum()
        ven_b = len(df_raw_b)

        def delta_str(a, b):
            if b == 0: return ""
            d = ((a - b) / b) * 100
            return f"{'▲' if d >= 0 else '▼'} {abs(d):.1f}% vs B"

        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("🧾 Faturamento", f"R$ {fat_a:,.2f}", delta=delta_str(fat_a, fat_b))
        cc2.metric("💰 Comissão",    f"R$ {com_a:,.2f}", delta=delta_str(com_a, com_b))
        cc3.metric("🛒 Vendas",      f"{ven_a}",          delta=delta_str(ven_a, ven_b))

        st.markdown(f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px 16px; margin:12px 0; font-size:0.82rem; color:#64748b; font-family:Inter,sans-serif;">
            📅 <b>Período A:</b> {data_ini.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')}
            &nbsp;&nbsp;|&nbsp;&nbsp;
            📅 <b>Período B:</b> {data_ini_b.strftime('%d/%m/%Y')} → {data_fim_b.strftime('%d/%m/%Y')}
        </div>
        """, unsafe_allow_html=True)

        # Top 10 SubIDs por faturamento no período A
        df_comp = vendas[["subid", "faturamento", "comissoes"]].rename(
            columns={"faturamento": "Fat A (R$)", "comissoes": "Com A (R$)"}
        ).merge(
            vendas_b[["subid", "faturamento", "comissoes"]].rename(
                columns={"faturamento": "Fat B (R$)", "comissoes": "Com B (R$)"}
            ), on="subid", how="outer"
        ).fillna(0).nlargest(10, "Fat A (R$)")

        df_comp["Δ Fat (%)"] = df_comp.apply(
            lambda r: f"{'▲' if r['Fat A (R$)'] >= r['Fat B (R$)'] else '▼'} {abs((r['Fat A (R$)']-r['Fat B (R$)'])/(r['Fat B (R$)']+0.01)*100):.1f}%", axis=1
        )
        for col in ["Fat A (R$)", "Fat B (R$)", "Com A (R$)", "Com B (R$)"]:
            df_comp[col] = df_comp[col].apply(lambda x: f"R$ {x:,.2f}")

        st.dataframe(df_comp[["subid","Fat A (R$)","Fat B (R$)","Δ Fat (%)","Com A (R$)","Com B (R$)"]].rename(
            columns={"subid":"SubID"}), use_container_width=True, hide_index=True)
        st.divider()

    # =========================
    # 5. ANÁLISE VISUAL (ÚLTIMO)
    # =========================
    titulo("📈", "Análise Visual", cor="#10b981")
    tab1, tab2 = st.tabs(["ROI por Campanha", "📅 Faturamento por Dia"])

    with tab1:
        df_sorted = df[df["subid"] != ""].sort_values("roi", ascending=False).head(20)
        if df_sorted.empty:
            st.info("Nenhum dado disponível para exibir.")
        else:
            fig_roi = px.bar(
                df_sorted, x="subid", y="roi",
                color="roi",
                color_continuous_scale=["#f87171", "#fbbf24", "#4ade80"],
                labels={"roi": "ROI", "subid": "Campanha"},
                title="ROI por SubID (Top 20)"
            )
            fig_roi.add_hline(y=roi_minimo, line_dash="dash", line_color="#6366f1",
                              annotation_text=f"Meta ROI: {roi_minimo:.0%}", annotation_position="top right")
            fig_roi.update_layout(
                paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
                font_color="#1e293b", coloraxis_showscale=False, font_family="Inter"
            )
            fig_roi.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_roi, use_container_width=True)

    with tab2:
        if not df_shopee_filtrado.empty and "_data" in df_shopee_filtrado.columns:
            subids_disponiveis = ["Todos"] + sorted(df_shopee_filtrado["subid"].dropna().unique().tolist())
            subid_sel = st.selectbox("Filtrar por SubID:", subids_disponiveis, key="fat_dia_subid")
            raw_filtrado = df_shopee_filtrado if subid_sel == "Todos" else df_shopee_filtrado[df_shopee_filtrado["subid"] == subid_sel]

            fat_dia = raw_filtrado.groupby("_data", as_index=False).agg(
                faturamento=("_valor", "sum"),
                comissao=("_comissao", "sum"),
                vendas=("_qtd", "sum"),
                diretas=("_direta", "sum"),
                indiretas=("_indireta", "sum")
            ).sort_values("_data")

            # Formata data corretamente
            fat_dia["_data"] = pd.to_datetime(fat_dia["_data"]).dt.strftime("%d/%m/%Y")

            # Adicionar gasto do df principal (por SubID selecionado)
            if subid_sel == "Todos":
                gasto_subid = df["gasto"].sum()
            else:
                gasto_row = df[df["subid"] == subid_sel]
                gasto_subid = gasto_row["gasto"].values[0] if not gasto_row.empty else 0.0

            # Distribui o gasto proporcionalmente por dia (pelo faturamento)
            fat_total = fat_dia["faturamento"].sum()
            if fat_total > 0:
                fat_dia["gasto"] = fat_dia["faturamento"] / fat_total * gasto_subid
            else:
                fat_dia["gasto"] = 0.0
            fat_dia["lucro"] = fat_dia["comissao"] - fat_dia["gasto"]

            fig_dia = go.Figure()
            fig_dia.add_trace(go.Bar(x=fat_dia["_data"], y=fat_dia["faturamento"], name="Faturamento", marker_color="#6366f1"))
            fig_dia.add_trace(go.Bar(x=fat_dia["_data"], y=fat_dia["comissao"],    name="Comissão",    marker_color="#8b5cf6"))
            fig_dia.add_trace(go.Bar(x=fat_dia["_data"], y=fat_dia["gasto"],       name="Gasto",       marker_color="#f87171"))
            fig_dia.update_layout(
                barmode="group", title="Faturamento, Comissão e Gasto por Dia",
                paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
                font_color="#1e293b", font_family="Inter", xaxis_title="Data", yaxis_title="R$"
            )
            st.plotly_chart(fig_dia, use_container_width=True)

            fat_dia_display = fat_dia.copy()

            # Linha de totais
            totais = {
                "_data":       "TOTAL",
                "faturamento": fat_dia["faturamento"].sum(),
                "comissao":    fat_dia["comissao"].sum(),
                "gasto":       fat_dia["gasto"].sum(),
                "lucro":       fat_dia["lucro"].sum(),
                "vendas":      fat_dia["vendas"].sum(),
                "diretas":     fat_dia["diretas"].sum(),
                "indiretas":   fat_dia["indiretas"].sum(),
            }
            fat_dia_display = pd.concat([fat_dia_display, pd.DataFrame([totais])], ignore_index=True)

            # Formata colunas monetárias
            for col in ["faturamento", "comissao", "gasto", "lucro"]:
                fat_dia_display[col] = fat_dia_display[col].apply(lambda x: f"R$ {float(x):,.2f}" if str(x) != "**TOTAL**" else x)
            for col in ["vendas", "diretas", "indiretas"]:
                fat_dia_display[col] = fat_dia_display[col].apply(lambda x: int(float(x)))

            fat_dia_display = fat_dia_display[["_data", "faturamento", "comissao", "gasto", "lucro", "vendas", "diretas", "indiretas"]]
            fat_dia_display.columns = ["Data", "Faturamento", "Comissão", "Gasto", "Lucro", "Qtd Vendas", "Diretas", "Indiretas"]

            if gasto_subid == 0:
                st.caption("ℹ️ Gasto zerado — importe o arquivo de ads para ver o gasto por dia.")
            st.dataframe(fat_dia_display, use_container_width=True, hide_index=True)
        else:
            st.info("Carregue os arquivos de comissão da Shopee para ver o faturamento por dia.")

    # =========================
    # DOWNLOADS
    # =========================
    st.divider()
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "📥 Baixar Relatório Excel",
            data=gerar_excel(df),
            file_name=f"analise_campanhas_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col_dl2:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📄 Baixar CSV completo",
            data=csv_bytes,
            file_name=f"analise_campanhas_{date.today()}.csv",
            mime="text/csv"
        )

else:
    st.info("👈 Carregue seus arquivos na sidebar para começar a análise.")
    st.markdown("""
    ### Como usar:
    1. **Configure** o ROI mínimo e sua meta mensal
    2. **Importe** os arquivos de cada plataforma (Pinterest, Meta, Shopee)
    3. **Analise** os resultados nos cards, gráficos e tabela
    4. **Baixe** o relatório em Excel ou CSV
    """)
