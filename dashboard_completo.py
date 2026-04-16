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
st.set_page_config(page_title="Dashboard Shopee + Ads", layout="wide", page_icon="📊")

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
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 20px 24px;
        border-radius: 14px;
        box-shadow: 0 1px 4px rgba(15,23,42,0.07);
        transition: box-shadow 0.2s, transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 4px 16px rgba(15,23,42,0.12);
        transform: translateY(-2px);
    }
    [data-testid="stMetricValue"]  { color: #6366f1 !important; font-size: 1.7rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"]  { color: #64748b !important; font-size: 0.82rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.05em; }
    [data-testid="stMetricDelta"]  { font-size: 0.85rem !important; }

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

st.title("📊 Dashboard Shopee + Pinterest + Meta")
st.caption(f"Atualizado em: {date.today().strftime('%d/%m/%Y')}")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("🎯 Configurações")

roi_minimo = st.sidebar.slider("ROI mínimo aceitável", min_value=-1.0, max_value=5.0, value=0.5, step=0.05)
meta_mensal = st.sidebar.number_input("Meta mensal de faturamento (R$)", min_value=0.0, value=10000.0, step=500.0)

st.sidebar.divider()
st.sidebar.header("🤖 IA (Anthropic)")
api_key = st.sidebar.text_input("Chave API Anthropic (opcional)", type="password", help="Obtenha em console.anthropic.com")

st.sidebar.divider()
st.sidebar.header("📂 Importação de Arquivos")

pinterest_files       = st.sidebar.file_uploader("Pinterest (CSV)",           type="csv",  accept_multiple_files=True)
meta_files            = st.sidebar.file_uploader("Meta Ads (XLSX)",            type="xlsx", accept_multiple_files=True)
shopee_comissao_files = st.sidebar.file_uploader("Shopee – Comissões (CSV)",   type="csv",  accept_multiple_files=True)
shopee_cliques_files  = st.sidebar.file_uploader("Shopee – Cliques (CSV)",     type="csv",  accept_multiple_files=True)

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
    estilos = []
    for col in row.index:
        if col in ("lucro", "Lucro"):
            v = converter_valor(row[col])
            estilos.append("color: #16a34a; font-weight:bold;" if v > 0 else "color: #dc2626; font-weight:bold;")
        elif col in ("roi", "ROI"):
            try:
                v = float(str(row[col]).replace("%", "").replace(",", ".")) / 100
            except:
                v = 0
            if v >= roi_minimo:
                estilos.append("color: #16a34a; font-weight:bold;")
            elif v >= roi_minimo * 0.8:
                estilos.append("color: #d97706; font-weight:bold;")
            else:
                estilos.append("color: #dc2626; font-weight:bold;")
        else:
            estilos.append("")
    return estilos

# =========================
# PROCESSAMENTO
# =========================
ads              = pd.DataFrame(columns=["subid", "gasto", "cliques_anuncio"])
vendas           = pd.DataFrame(columns=["subid", "comissoes", "faturamento", "vendas_diretas", "vendas_indiretas", "qtd_itens"])
cliques_shopee   = pd.DataFrame(columns=["subid", "cliques_shopee"])
faturamento_bruto_total = 0.0
erros_carregamento = []
df_shopee_raw    = pd.DataFrame()  # dados brutos para análise por dia

# --- ADS ---
lista_ads = []

if pinterest_files:
    for f in pinterest_files:
        try:
            dfp = ler_csv_inteligente(f)
            dfp.columns = [normalizar_coluna(c) for c in dfp.columns]
            sub     = next((c for c in dfp.columns if "nome" in c), None)
            gasto   = next((c for c in dfp.columns if "gasto" in c), None)
            cliques = next((c for c in dfp.columns if "cliques" in c), None)
            if sub and gasto:
                dfp["subid"]          = dfp[sub].apply(limpar_subid)
                dfp["gasto"]          = dfp[gasto].apply(converter_valor)
                dfp["cliques_anuncio"] = pd.to_numeric(dfp[cliques], errors="coerce").fillna(0) if cliques else 0
                lista_ads.append(dfp[["subid", "gasto", "cliques_anuncio"]])
            else:
                erros_carregamento.append(f"Pinterest '{f.name}': colunas 'nome' ou 'gasto' não encontradas.")
        except Exception as e:
            erros_carregamento.append(f"Pinterest '{f.name}': {e}")

if meta_files:
    for f in meta_files:
        try:
            meta = ler_excel(f)
            meta.columns = [normalizar_coluna(c) for c in meta.columns]
            if "nome_do_anuncio" not in meta.columns or "valor_usado_brl" not in meta.columns:
                erros_carregamento.append(f"Meta '{f.name}': colunas esperadas não encontradas. Verifique o formato.")
                continue
            meta["subid"]           = meta["nome_do_anuncio"].apply(limpar_subid)
            meta["gasto"]           = meta["valor_usado_brl"].apply(converter_valor)
            meta["cliques_anuncio"] = pd.to_numeric(meta.get("resultados", 0), errors="coerce").fillna(0)
            lista_ads.append(meta[["subid", "gasto", "cliques_anuncio"]])
        except Exception as e:
            erros_carregamento.append(f"Meta '{f.name}': {e}")

if lista_ads:
    ads = pd.concat(lista_ads).groupby("subid", as_index=False).sum()

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

                lista_shopee_raw.append(shp_valido[["subid", "_valor", "_comissao", "_qtd", "_direta", "_indireta", "_data"]])

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
    ads
    .merge(vendas,         on="subid", how="outer")
    .merge(cliques_shopee, on="subid", how="outer")
    .fillna(0)
)
df["lucro"] = df["comissoes"] - df["gasto"]
df["roi"]   = df.apply(lambda x: x["lucro"] / x["gasto"] if x["gasto"] > 0 else 0, axis=1)
df["%_batimento_cliques"] = df.apply(
    lambda x: (x["cliques_shopee"] / x["cliques_anuncio"] * 100) if x["cliques_anuncio"] > 0 else 0, axis=1
)
df["total_vendas"] = df["vendas_diretas"] + df["vendas_indiretas"]

# Ordem das colunas conforme solicitado
colunas_ordem = ["subid", "comissoes", "faturamento", "gasto", "lucro", "roi",
                 "total_vendas", "vendas_diretas", "vendas_indiretas", "qtd_itens",
                 "cliques_anuncio", "cliques_shopee", "%_batimento_cliques"]
for c in colunas_ordem:
    if c not in df.columns:
        df[c] = 0
df = df[colunas_ordem]

total_gasto    = df["gasto"].sum()
total_comissao = df["comissoes"].sum()
total_lucro    = df["lucro"].sum()
total_roi      = total_lucro / total_gasto if total_gasto > 0 else 0

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

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("💰 Comissão",    formatar_valor(total_comissao))
    c2.metric("🧾 Fat. Bruto",  formatar_valor(faturamento_bruto_total))
    c3.metric("📉 Gasto",       formatar_valor(total_gasto))
    c4.metric("📈 Lucro",       formatar_valor(total_lucro), delta=f"{'▲' if total_lucro >= 0 else '▼'} {formatar_valor(abs(total_lucro))}")
    c5.metric("🚀 ROI Geral",   f"{total_roi:.2%}")
    total_vendas_geral = int(df["total_vendas"].sum())
    c6.metric("🛒 Vendas",      f"{total_vendas_geral}", delta=f"{int(df['vendas_diretas'].sum())}D / {int(df['vendas_indiretas'].sum())}I")

    # Progresso da Meta
    st.write(f"**Progresso da Meta Mensal (R$ {meta_mensal:,.2f})**")
    percentual_meta = min(faturamento_bruto_total / meta_mensal, 1.0) if meta_mensal else 0
    st.progress(percentual_meta)
    st.caption(f"Atingido: {percentual_meta * 100:.2f}%  |  Faltam: R$ {max(meta_mensal - faturamento_bruto_total, 0):,.2f}")

    st.divider()

    # =========================
    # GRÁFICOS
    # =========================
    st.subheader("📈 Análise Visual")

    tab1, tab2, tab3, tab4 = st.tabs(["ROI por Campanha", "Lucro vs Gasto", "Funil de Cliques", "📅 Faturamento por Dia"])

    with tab1:
        df_sorted = df[df["subid"] != ""].sort_values("roi", ascending=False).head(20)
        fig_roi = px.bar(
            df_sorted,
            x="subid", y="roi",
            color="roi",
            color_continuous_scale=["#f87171", "#fbbf24", "#4ade80"],
            labels={"roi": "ROI", "subid": "Campanha"},
            title="ROI por SubID (Top 20)"
        )
        fig_roi.add_hline(y=roi_minimo, line_dash="dash", line_color="#38bdf8",
                          annotation_text=f"Meta ROI: {roi_minimo:.0%}", annotation_position="top right")
        fig_roi.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
            font_color="#1e293b", coloraxis_showscale=False,
            font_family="Inter"
        )
        fig_roi.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig_roi, use_container_width=True)

    with tab2:
        df_plot = df[df["subid"] != ""].copy()
        fig_lv = px.scatter(
            df_plot,
            x="gasto", y="comissoes",
            size=df_plot["lucro"].clip(lower=0) + 1,
            color="lucro",
            color_continuous_scale=["#f87171", "#4ade80"],
            hover_name="subid",
            labels={"gasto": "Gasto (R$)", "comissoes": "Comissão (R$)", "lucro": "Lucro"},
            title="Comissão vs Gasto por SubID"
        )
        max_val = max(df_plot["gasto"].max(), df_plot["comissoes"].max()) * 1.1
        fig_lv.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val,
                         line=dict(color="#64748b", dash="dot"))
        fig_lv.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc", font_color="#1e293b", font_family="Inter")
        st.plotly_chart(fig_lv, use_container_width=True)

    with tab3:
        df_funil = df[df["subid"] != ""].nlargest(10, "cliques_anuncio")
        if df_funil["cliques_anuncio"].sum() > 0:
            fig_funil = go.Figure()
            fig_funil.add_trace(go.Bar(
                name="Cliques Anúncio", x=df_funil["subid"],
                y=df_funil["cliques_anuncio"], marker_color="#38bdf8"
            ))
            fig_funil.add_trace(go.Bar(
                name="Cliques Shopee", x=df_funil["subid"],
                y=df_funil["cliques_shopee"], marker_color="#4ade80"
            ))
            fig_funil.update_layout(
                barmode="group", title="Funil de Cliques: Anúncio → Shopee (Top 10)",
                paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc", font_color="#1e293b", font_family="Inter"
            )
            st.plotly_chart(fig_funil, use_container_width=True)
        else:
            st.info("Carregue os arquivos de cliques da Shopee para ver o funil.")

    with tab4:
        if not df_shopee_raw.empty and "_data" in df_shopee_raw.columns:
            # Filtro por SubID
            subids_disponiveis = ["Todos"] + sorted(df_shopee_raw["subid"].dropna().unique().tolist())
            subid_sel = st.selectbox("Filtrar por SubID:", subids_disponiveis, key="fat_dia_subid")

            raw_filtrado = df_shopee_raw if subid_sel == "Todos" else df_shopee_raw[df_shopee_raw["subid"] == subid_sel]

            fat_dia = raw_filtrado.groupby("_data", as_index=False).agg(
                faturamento=("_valor", "sum"),
                comissao=("_comissao", "sum"),
                vendas=("_qtd", "sum"),
                diretas=("_direta", "sum"),
                indiretas=("_indireta", "sum")
            ).sort_values("_data")

            fig_dia = go.Figure()
            fig_dia.add_trace(go.Bar(
                x=fat_dia["_data"].astype(str), y=fat_dia["faturamento"],
                name="Faturamento", marker_color="#6366f1"
            ))
            fig_dia.add_trace(go.Bar(
                x=fat_dia["_data"].astype(str), y=fat_dia["comissao"],
                name="Comissão", marker_color="#8b5cf6"
            ))
            fig_dia.update_layout(
                barmode="group", title="Faturamento e Comissão por Dia",
                paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
                font_color="#1e293b", font_family="Inter",
                xaxis_title="Data", yaxis_title="R$"
            )
            st.plotly_chart(fig_dia, use_container_width=True)

            # Tabela diária
            fat_dia_display = fat_dia.copy()
            fat_dia_display["faturamento"] = fat_dia_display["faturamento"].apply(lambda x: f"R$ {x:,.2f}")
            fat_dia_display["comissao"]    = fat_dia_display["comissao"].apply(lambda x: f"R$ {x:,.2f}")
            fat_dia_display["vendas"]      = fat_dia_display["vendas"].astype(int)
            fat_dia_display["diretas"]     = fat_dia_display["diretas"].astype(int)
            fat_dia_display["indiretas"]   = fat_dia_display["indiretas"].astype(int)
            fat_dia_display.columns        = ["Data", "Faturamento", "Comissão", "Qtd Vendas", "Diretas", "Indiretas"]
            st.dataframe(fat_dia_display, use_container_width=True, hide_index=True)
        else:
            st.info("Carregue os arquivos de comissão da Shopee para ver o faturamento por dia.")

    st.divider()

    # =========================
    # TABELA DETALHADA
    # =========================
    st.subheader("📊 Detalhamento por SubID")

    col_ord, col_filt = st.columns([2, 1])
    with col_ord:
        ordenar_por = st.selectbox("Ordenar por:", ["roi", "lucro", "faturamento", "comissoes", "gasto", "total_vendas", "%_batimento_cliques"])
    with col_filt:
        mostrar_apenas_prejuizo = st.checkbox("Mostrar apenas prejuízo")

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
    for col in ["total_vendas", "vendas_diretas", "vendas_indiretas", "qtd_itens", "cliques_anuncio", "cliques_shopee"]:
        df_display[col] = df_display[col].astype(int)

    df_display.columns = [
        "SubID", "Comissão", "Faturamento", "Gasto", "Lucro", "ROI",
        "Total Vendas", "Diretas", "Indiretas", "Qtd Itens",
        "Cliques Anúncio", "Cliques Shopee", "% Batimento"
    ]

    # Colorização segura via HTML — sem depender de versão do pandas
    def colorir_tabela(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for i, row in df.iterrows():
            try:
                v = float(str(row["Lucro"]).replace("R$","").replace(",","").strip())
                styles.at[i, "Lucro"] = "color: #16a34a; font-weight:bold;" if v > 0 else "color: #dc2626; font-weight:bold;"
            except: pass
            try:
                v = float(str(row["ROI"]).replace("%","").replace(",",".").strip()) / 100
                if v >= roi_minimo:  styles.at[i, "ROI"] = "color: #16a34a; font-weight:bold;"
                elif v >= 0:         styles.at[i, "ROI"] = "color: #d97706; font-weight:bold;"
                else:                styles.at[i, "ROI"] = "color: #dc2626; font-weight:bold;"
            except: pass
        return styles

    st.dataframe(
        df_display.style.apply(colorir_tabela, axis=None),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =========================
    # IA — INSIGHTS
    # =========================
    st.subheader("🤖 Analista IA — Insights")

    melhor = df.loc[df["roi"].idxmax()]
    pior   = df.loc[df["lucro"].idxmin()]
    batimento_avg = df["%_batimento_cliques"].mean()
    campanhas_lucro    = len(df[df["lucro"] > 0])
    campanhas_prejuizo = len(df[df["lucro"] < 0])

    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"💡 **Escalar:** `{melhor['subid']}` tem ROI de **{melhor['roi']:.2%}** — sua melhor performance.")
    with col_b:
        if pior["lucro"] < 0:
            st.warning(f"⚠️ **Revisar:** `{pior['subid']}` gerou prejuízo de **R$ {abs(pior['lucro']):.2f}**.")

    col_c, col_d = st.columns(2)
    with col_c:
        if batimento_avg < 75:
            st.error(f"📉 **Funil fraco:** Batimento médio de **{batimento_avg:.1f}%**. Muitos cliques se perdem antes da Shopee.")
        else:
            st.success(f"✅ **Funil saudável:** Batimento médio de **{batimento_avg:.1f}%**.")
    with col_d:
        st.metric("Campanhas lucrativas", f"{campanhas_lucro}", delta=f"-{campanhas_prejuizo} em prejuízo")

    # IA Real via Anthropic
    if api_key:
        st.markdown("---")
        st.markdown("**🧠 Análise profunda via Claude (Anthropic)**")

        resumo_dados = f"""
        Dados do dashboard de afiliados:
        - Faturamento bruto: R$ {faturamento_bruto_total:,.2f}
        - Total gasto em ads: R$ {total_gasto:,.2f}
        - Total comissões: R$ {total_comissao:,.2f}
        - Lucro líquido: R$ {total_lucro:,.2f}
        - ROI geral: {total_roi:.2%}
        - Meta mensal: R$ {meta_mensal:,.2f} ({percentual_meta*100:.1f}% atingida)
        - Total de vendas: {int(df['total_vendas'].sum())} ({int(df['vendas_diretas'].sum())} diretas / {int(df['vendas_indiretas'].sum())} indiretas)
        - Campanhas lucrativas: {campanhas_lucro}
        - Campanhas em prejuízo: {campanhas_prejuizo}
        - Melhor campanha: {melhor['subid']} com ROI {melhor['roi']:.2%}
        - Pior campanha: {pior['subid']} com lucro R$ {pior['lucro']:,.2f}
        - Batimento médio de cliques: {batimento_avg:.1f}%
        Top 5 por ROI:
        {df.nlargest(5, 'roi')[['subid','gasto','comissoes','faturamento','lucro','roi','total_vendas']].to_string(index=False)}
        """

        if st.button("🔍 Gerar análise detalhada com IA"):
            with st.spinner("Consultando Claude..."):
                try:
                    response = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": "claude-sonnet-4-20250514",
                            "max_tokens": 1024,
                            "messages": [{
                                "role": "user",
                                "content": f"""Você é um especialista em marketing de afiliados e tráfego pago.
                                Analise os dados abaixo e forneça:
                                1. Diagnóstico geral da operação
                                2. Top 3 ações prioritárias para aumentar o lucro
                                3. Alertas importantes
                                4. Previsão se vai bater a meta mensal com base no ritmo atual
                                Seja direto, use bullet points e linguagem prática.
                                
                                {resumo_dados}"""
                            }]
                        },
                        timeout=30
                    )
                    resultado = response.json()
                    texto_ia = resultado["content"][0]["text"]
                    st.markdown(texto_ia)
                except Exception as e:
                    st.error(f"Erro ao consultar a IA: {e}")
    else:
        st.caption("💡 Adicione sua chave API da Anthropic na sidebar para ativar a análise profunda com IA.")

    st.divider()

    # =========================
    # HISTÓRICO
    # =========================
    historico_path = "historico_dashboard.csv"
    registro_hoje = {
        "data":        date.today().strftime("%Y-%m-%d"),
        "faturamento": faturamento_bruto_total,
        "gasto":       total_gasto,
        "lucro":       total_lucro,
        "roi":         total_roi
    }

    if faturamento_bruto_total > 0:
        if os.path.exists(historico_path):
            hist = pd.read_csv(historico_path)
            hist = hist[hist["data"] != registro_hoje["data"]]
            hist = pd.concat([hist, pd.DataFrame([registro_hoje])], ignore_index=True)
        else:
            hist = pd.DataFrame([registro_hoje])
        hist.to_csv(historico_path, index=False)

        if len(hist) > 1:
            st.subheader("📅 Evolução Histórica")
            hist["data"] = pd.to_datetime(hist["data"])
            hist_sorted  = hist.sort_values("data")

            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=hist_sorted["data"], y=hist_sorted["faturamento"],
                name="Faturamento", line=dict(color="#38bdf8", width=2)
            ))
            fig_hist.add_trace(go.Scatter(
                x=hist_sorted["data"], y=hist_sorted["lucro"],
                name="Lucro", line=dict(color="#4ade80", width=2)
            ))
            fig_hist.add_trace(go.Scatter(
                x=hist_sorted["data"], y=hist_sorted["gasto"],
                name="Gasto", line=dict(color="#f87171", width=2)
            ))
            fig_hist.update_layout(
                title="Evolução Diária — Faturamento / Lucro / Gasto",
                paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
                font_color="#1e293b", font_family="Inter", xaxis_title="Data", yaxis_title="R$"
            )
            st.plotly_chart(fig_hist, use_container_width=True)

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
    # Estado inicial — nenhum arquivo carregado
    st.info("👈 Carregue seus arquivos na sidebar para começar a análise.")
    st.markdown("""
    ### Como usar:
    1. **Configure** o ROI mínimo e sua meta mensal
    2. **Importe** os arquivos de cada plataforma (Pinterest, Meta, Shopee)
    3. **Analise** os resultados nos cards, gráficos e tabela
    4. **(Opcional)** Adicione sua chave da Anthropic para análise profunda com IA
    5. **Baixe** o relatório em Excel ou CSV
    """)
