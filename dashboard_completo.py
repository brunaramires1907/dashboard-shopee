import streamlit as st
import pandas as pd
import unicodedata
from io import BytesIO
from datetime import date
import gc
import traceback
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="AfiliaMetrics", layout="wide", page_icon="📊")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif !important; color: #1e293b !important; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
    [data-testid="stSidebar"] * { color: #334155 !important; }
    div[data-testid="metric-container"] { background: #ffffff !important; border: 1px solid #e2e8f0 !important; padding: 16px 20px !important; border-radius: 12px !important; box-shadow: 0 1px 4px rgba(15,23,42,0.07) !important; }
    [data-testid="stMetricValue"] { color: #6366f1 !important; font-size: 1.05rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.78rem !important; font-weight: 500 !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; }
    span[data-baseweb="tag"] { background-color: #ede9fe !important; border: 1px solid #c4b5fd !important; border-radius: 6px !important; }
    span[data-baseweb="tag"] span { color: #6366f1 !important; font-weight: 500 !important; font-size: 0.78rem !important; }
    .stDataFrame { border: 1px solid #e2e8f0 !important; border-radius: 12px !important; overflow: hidden !important; background: white !important; }
    hr { border-color: #e2e8f0 !important; }
    .stDownloadButton button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; border-radius: 9px !important; border: none !important; padding: 10px 22px !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:#6366f1; border-radius:16px; padding:24px 32px; margin-bottom:24px;">
    <div style="font-size:2rem; font-weight:800; color:white; letter-spacing:-1px; font-family:Inter,sans-serif;">
        Afilia<span style="color:#c4b5fd;">Metrics</span>
    </div>
    <div style="font-size:0.82rem; color:rgba(255,255,255,0.6); margin-top:6px; font-family:Inter,sans-serif;">
        Dashboard de Afiliados &nbsp;·&nbsp; {date.today().strftime('%d/%m/%Y')}
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""<div style="padding:4px 0 12px 0;">
    <div style="font-size:1.1rem; font-weight:800; color:#0f172a; font-family:Inter,sans-serif;">Afilia<span style="color:#6366f1;">Metrics</span></div>
    <div style="font-size:0.72rem; color:#94a3b8;">Painel de Controle</div>
</div>""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown("**🎯 Configurações**")
roi_minimo  = st.sidebar.slider("ROI mínimo aceitável", min_value=-1.0, max_value=5.0, value=0.5, step=0.05)
meta_mensal = st.sidebar.number_input("Meta mensal de faturamento (R$)", min_value=0.0, value=10000.0, step=500.0)

st.sidebar.divider()
st.sidebar.markdown("**🧾 Impostos**")
imposto_meta = st.sidebar.number_input("Imposto Meta Ads (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
imposto_nf   = st.sidebar.number_input("Imposto Nota Fiscal (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)

st.sidebar.divider()
st.sidebar.markdown("**📂 Importação de Arquivos**")
pinterest_files       = st.sidebar.file_uploader("📌 Pinterest (CSV)",         type="csv",  accept_multiple_files=True)
meta_files            = st.sidebar.file_uploader("🔵 Meta Ads (XLSX)",          type="xlsx", accept_multiple_files=True)
shopee_comissao_files = st.sidebar.file_uploader("🛍️ Shopee – Comissões (CSV)", type="csv",  accept_multiple_files=True)
shopee_cliques_files  = st.sidebar.file_uploader("🛍️ Shopee – Cliques (CSV)",   type="csv",  accept_multiple_files=True)

st.sidebar.markdown("**📋 Status dos arquivos**")
def status_badge(files, nome, emoji):
    cor = "#16a34a" if files else "#94a3b8"
    txt = f"✅ {nome} — {len(files)} arquivo(s)" if files else f"⏳ {nome} — não importado"
    st.sidebar.markdown(f'<span style="color:{cor}; font-size:0.82rem;">{emoji} {txt}</span>', unsafe_allow_html=True)

status_badge(pinterest_files,       "Pinterest",        "📌")
status_badge(meta_files,            "Meta Ads",         "🔵")
status_badge(shopee_comissao_files, "Shopee Comissões", "🛍️")
status_badge(shopee_cliques_files,  "Shopee Cliques",   "🛍️")

def normalizar_texto(txt):
    if pd.isna(txt): return ""
    return unicodedata.normalize("NFKD", str(txt).lower().strip()).encode("ascii","ignore").decode("utf-8")

def normalizar_coluna(col):
    col = unicodedata.normalize("NFKD", str(col).lower()).encode("ascii","ignore").decode("utf-8")
    return col.replace(" ","_").replace("(","").replace(")","").replace("$","")

def limpar_subid(valor):
    if pd.isna(valor): return ""
    return str(valor).replace("-","").strip().lower()

def converter_valor(valor):
    if pd.isna(valor): return 0.0
    valor = str(valor).replace("R$","").strip()
    if "." in valor and "," in valor: valor = valor.replace(".","").replace(",",".")
    elif "," in valor: valor = valor.replace(",",".")
    try: return float(valor)
    except: return 0.0

@st.cache_data(show_spinner=False, max_entries=20)
def ler_csv(file_bytes):
    for enc in ["utf-8-sig","utf-8","latin-1"]:
        for sep in [",",";"]:
            try:
                df = pd.read_csv(BytesIO(file_bytes), sep=sep, encoding=enc)
                if len(df.columns) > 1: return df
            except: continue
    return pd.read_csv(BytesIO(file_bytes), sep=",", encoding="latin-1", engine="python")

@st.cache_data(show_spinner=False, max_entries=20)
def ler_excel(file_bytes):
    return pd.read_excel(BytesIO(file_bytes), engine="openpyxl")

@st.cache_data(show_spinner=False, max_entries=10)
def gerar_excel(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w: df.to_excel(w, index=False, sheet_name="Dashboard")
    return out.getvalue()

def formatar_valor(v): return f"R$ {v:,.2f}"

def titulo(icone, texto, cor="#6366f1"):
    st.markdown(f"""<div style="display:flex;align-items:center;gap:12px;margin:28px 0 16px 0;">
        <div style="width:4px;height:32px;background:{cor};border-radius:4px;"></div>
        <span style="font-size:1.25rem;font-weight:700;color:#0f172a;font-family:Inter,sans-serif;">{icone}&nbsp;{texto}</span>
    </div>""", unsafe_allow_html=True)

# PROCESSAMENTO
ads            = pd.DataFrame(columns=["subid","gasto","cliques_anuncio"])
vendas         = pd.DataFrame(columns=["subid","comissoes","faturamento","vendas_diretas","vendas_indiretas","qtd_itens"])
cliques_shopee = pd.DataFrame(columns=["subid","cliques_shopee"])
faturamento_bruto_total = 0.0
erros_carregamento = []
df_shopee_raw  = pd.DataFrame()
lista_ads = []; lista_ads_raw = []

if pinterest_files:
    for f in pinterest_files:
        try:
            dfp = ler_csv(f.getvalue())
            dfp.columns = [normalizar_coluna(c) for c in dfp.columns]
            col_sub   = next((c for c in dfp.columns if "ad_name" in c), None)
            col_gasto = next((c for c in dfp.columns if "spend" in c), None)
            col_cli   = next((c for c in dfp.columns if "pin_clicks" in c), None)
            col_data  = next((c for c in dfp.columns if c == "date"), None)
            if col_sub and col_gasto:
                dfp["subid"] = dfp[col_sub].apply(limpar_subid)
                dfp["gasto"] = dfp[col_gasto].apply(converter_valor)
                dfp["cliques_anuncio"] = pd.to_numeric(dfp[col_cli], errors="coerce").fillna(0) if col_cli else 0
                dfp["_data"] = pd.to_datetime(dfp[col_data], errors="coerce") if col_data else pd.NaT
                lista_ads.append(dfp[["subid","gasto","cliques_anuncio"]])
                lista_ads_raw.append(dfp[["subid","gasto","cliques_anuncio","_data"]])
        except Exception as e: erros_carregamento.append(f"Pinterest '{f.name}': {e}")

if meta_files:
    for f in meta_files:
        try:
            meta = ler_excel(f.getvalue())
            meta.columns = [normalizar_coluna(c) for c in meta.columns]
            col_nome  = next((c for c in meta.columns if "nome_do_anuncio" in c), None)
            col_gasto = next((c for c in meta.columns if "valor_usado_brl" in c or "valor_usado" in c), None)
            col_cli   = next((c for c in meta.columns if "cliques_no_link" in c or "resultados" in c), None)
            col_data  = next((c for c in meta.columns if "inicio_dos_relatorios" in c), None)
            if col_nome and col_gasto:
                meta["subid"] = meta[col_nome].apply(lambda x: limpar_subid(x)[:50] if not pd.isna(x) else "")
                meta["gasto"] = meta[col_gasto].apply(converter_valor)
                meta["cliques_anuncio"] = pd.to_numeric(meta[col_cli], errors="coerce").fillna(0) if col_cli else 0
                meta["_data"] = pd.to_datetime(meta[col_data], errors="coerce") if col_data else pd.NaT
                lista_ads.append(meta[["subid","gasto","cliques_anuncio"]])
                lista_ads_raw.append(meta[["subid","gasto","cliques_anuncio","_data"]])
        except Exception as e: erros_carregamento.append(f"Meta '{f.name}': {e}")

if lista_ads: ads = pd.concat(lista_ads).groupby("subid", as_index=False).sum()
df_ads_raw = pd.concat(lista_ads_raw, ignore_index=True) if lista_ads_raw else pd.DataFrame()
del lista_ads, lista_ads_raw

lista_vendas = []; lista_shopee_raw = []

if shopee_comissao_files:
    for f in shopee_comissao_files:
        try:
            shp = ler_csv(f.getvalue())
            shp.columns = [normalizar_coluna(c) for c in shp.columns]
            col_valor  = next((c for c in shp.columns if "valor_de_compra" in c), None)
            col_status = next((c for c in shp.columns if "status_do_pedido" in c), None)
            col_notas  = next((c for c in shp.columns if "notas" in c or "status_do_item" in c), None)
            col_comis  = next((c for c in shp.columns if "comissao_liquida" in c), None) or \
                         next((c for c in shp.columns if "comissao_total_do_item" in c), None) or \
                         next((c for c in shp.columns if "comissao_total" in c), shp.columns[-1])
            col_sub    = next((c for c in shp.columns if "sub_id1" in c), None)
            col_sub2   = next((c for c in shp.columns if "sub_id2" in c), None)
            col_atrib  = next((c for c in shp.columns if "tipo_de_atribuicao" in c), None)
            col_data   = next((c for c in shp.columns if "horario_do_pedido" in c or "data_do_pedido" in c), None)
            col_qtd    = next((c for c in shp.columns if "qtd" in c), None)
            col_canal  = next((c for c in shp.columns if c == "canal"), None)
            if not col_valor:
                erros_carregamento.append(f"Shopee '{f.name}': coluna valor não encontrada."); continue
            status_limpo = shp[col_status].apply(normalizar_texto) if col_status else pd.Series([""]*len(shp))
            notas_limpas = shp[col_notas].apply(normalizar_texto) if col_notas else pd.Series([""]*len(shp))
            mask = ~(status_limpo.str.contains("cancelado|incompleto", na=False) |
                     notas_limpas.str.contains("cancelado|incompleto|nao pago", na=False))
            shp_v = shp[mask].copy(); del shp
            shp_v["_valor"]    = shp_v[col_valor].apply(converter_valor).astype("float32")
            shp_v["_comissao"] = shp_v[col_comis].apply(converter_valor).astype("float32")
            shp_v["_qtd"]      = pd.to_numeric(shp_v[col_qtd], errors="coerce").fillna(1).astype("int16") if col_qtd else 1
            faturamento_bruto_total += float(shp_v["_valor"].sum())
            if col_sub:
                shp_v["subid"] = shp_v[col_sub].apply(limpar_subid)
                if col_sub2:
                    sub2 = shp_v[col_sub2].apply(limpar_subid)
                    shp_v.loc[shp_v["subid"]=="", "subid"] = sub2[shp_v["subid"]==""]
                    mask2 = (shp_v["subid"]!="") & (sub2!="") & (sub2!=shp_v["subid"])
                    if mask2.any():
                        l2 = shp_v[mask2].copy(); l2["subid"] = sub2[mask2].values
                        shp_v = pd.concat([shp_v, l2], ignore_index=True); del l2
                if col_atrib:
                    at = shp_v[col_atrib].apply(normalizar_texto)
                    shp_v["_direta"]   = at.str.contains("mesma", na=False).astype("int8")
                    shp_v["_indireta"] = at.str.contains("diferente", na=False).astype("int8")
                else:
                    shp_v["_direta"] = 0; shp_v["_indireta"] = 1
                shp_v["_data"]  = pd.to_datetime(shp_v[col_data], errors="coerce").dt.date if col_data else date.today()
                shp_v["_canal"] = shp_v[col_canal].fillna("Others").str.strip() if col_canal else "Others"
                lista_shopee_raw.append(shp_v[["subid","_valor","_comissao","_qtd","_direta","_indireta","_data","_canal"]].copy())
                lista_vendas.append(shp_v.groupby("subid", as_index=False).agg(
                    comissoes=("_comissao","sum"), faturamento=("_valor","sum"),
                    vendas_diretas=("_direta","sum"), vendas_indiretas=("_indireta","sum"), qtd_itens=("_qtd","sum")))
                del shp_v; gc.collect()
        except Exception as e: erros_carregamento.append(f"Shopee '{f.name}': {e}")

if lista_vendas:
    vendas = pd.concat(lista_vendas).groupby("subid", as_index=False).agg(
        {"comissoes":"sum","faturamento":"sum","vendas_diretas":"sum","vendas_indiretas":"sum","qtd_itens":"sum"})
if lista_shopee_raw:
    df_shopee_raw = pd.concat(lista_shopee_raw, ignore_index=True)
del lista_vendas, lista_shopee_raw; gc.collect()

# FILTROS
if not df_shopee_raw.empty and "_data" in df_shopee_raw.columns:
    df_shopee_raw["_data"] = pd.to_datetime(df_shopee_raw["_data"], errors="coerce")
    data_min = df_shopee_raw["_data"].min().date()
    data_max = df_shopee_raw["_data"].max().date()
    st.sidebar.divider()
    st.sidebar.markdown("**🔍 Filtros**")
    st.sidebar.markdown("<span style='font-size:0.8rem;color:#64748b;'>📅 Período</span>", unsafe_allow_html=True)
    col_d1, col_d2 = st.sidebar.columns(2)
    with col_d1: data_ini = st.date_input("Início:", value=data_min, min_value=data_min, max_value=data_max, format="DD/MM/YYYY")
    with col_d2: data_fim = st.date_input("Fim:", value=data_max, min_value=data_min, max_value=data_max, format="DD/MM/YYYY")
    st.sidebar.markdown("<span style='font-size:0.8rem;color:#64748b;'>🏷️ SubID(s)</span>", unsafe_allow_html=True)
    subids_shopee  = df_shopee_raw["subid"].dropna().unique().tolist()
    subids_ads_lst = list(df_ads_raw["subid"].unique()) if not df_ads_raw.empty else []
    subids_todos   = sorted(set(subids_shopee + subids_ads_lst))
    subids_sel     = st.sidebar.multiselect("SubIDs", subids_todos, default=subids_todos, label_visibility="collapsed")
    if not subids_sel: subids_sel = subids_todos
    canais_disp = sorted(df_shopee_raw["_canal"].dropna().unique().tolist()) if "_canal" in df_shopee_raw.columns else []
    if canais_disp:
        st.sidebar.markdown("<span style='font-size:0.8rem;color:#64748b;'>📡 Canal</span>", unsafe_allow_html=True)
        canais_sel = st.sidebar.multiselect("Canais", canais_disp, default=canais_disp, label_visibility="collapsed")
        if not canais_sel: canais_sel = canais_disp
    else: canais_sel = []
    st.sidebar.markdown("<span style='font-size:0.8rem;color:#64748b;'>🔀 Tipo de venda</span>", unsafe_allow_html=True)
    tipo_venda = st.sidebar.radio("Tipo", ["Todas","Somente Diretas","Somente Indiretas"], horizontal=True, label_visibility="collapsed")
    st.sidebar.markdown("")
    comparar = st.sidebar.toggle("📊 Comparar dois períodos")
    if comparar:
        col_c1, col_c2 = st.sidebar.columns(2)
        with col_c1: data_ini_b = st.date_input("Início:", value=data_min, min_value=data_min, max_value=data_max, key="db1", format="DD/MM/YYYY")
        with col_c2: data_fim_b = st.date_input("Fim:", value=data_max, min_value=data_min, max_value=data_max, key="db2", format="DD/MM/YYYY")
    mask = ((df_shopee_raw["_data"].dt.date >= data_ini) & (df_shopee_raw["_data"].dt.date <= data_fim) & (df_shopee_raw["subid"].isin(subids_sel)))
    if canais_sel and "_canal" in df_shopee_raw.columns: mask &= df_shopee_raw["_canal"].isin(canais_sel)
    if tipo_venda == "Somente Diretas": mask &= df_shopee_raw["_direta"] == 1
    elif tipo_venda == "Somente Indiretas": mask &= df_shopee_raw["_indireta"] == 1
    df_shopee_filtrado = df_shopee_raw[mask].copy()
    faturamento_bruto_total = float(df_shopee_filtrado["_valor"].sum())
    if not df_shopee_filtrado.empty:
        vendas = df_shopee_filtrado.groupby("subid", as_index=False).agg(
            comissoes=("_comissao","sum"), faturamento=("_valor","sum"),
            vendas_diretas=("_direta","sum"), vendas_indiretas=("_indireta","sum"), qtd_itens=("_qtd","sum"))
    else:
        vendas = pd.DataFrame(columns=["subid","comissoes","faturamento","vendas_diretas","vendas_indiretas","qtd_itens"])
    if not df_ads_raw.empty:
        df_ads_raw["_data"] = pd.to_datetime(df_ads_raw["_data"], errors="coerce")
        ads_filtrado = df_ads_raw.groupby("subid", as_index=False).agg(gasto=("gasto","sum"), cliques_anuncio=("cliques_anuncio","sum"))
    else: ads_filtrado = ads.copy()
    if comparar:
        mask_b = ((df_shopee_raw["_data"].dt.date >= data_ini_b) & (df_shopee_raw["_data"].dt.date <= data_fim_b) & (df_shopee_raw["subid"].isin(subids_sel)))
        df_raw_b = df_shopee_raw[mask_b].copy()
        vendas_b = df_raw_b.groupby("subid", as_index=False).agg(comissoes=("_comissao","sum"), faturamento=("_valor","sum"),
            vendas_diretas=("_direta","sum"), vendas_indiretas=("_indireta","sum"), qtd_itens=("_qtd","sum")) if not df_raw_b.empty else pd.DataFrame()
else:
    df_shopee_filtrado = df_shopee_raw.copy(); ads_filtrado = ads.copy(); comparar = False
    subids_todos = sorted(set(list(df_ads_raw["subid"].unique()) if not df_ads_raw.empty else []))
    subids_sel = subids_todos

lista_cliques = []
if shopee_cliques_files:
    for f in shopee_cliques_files:
        try:
            clk = ler_csv(f.getvalue()); clk.columns = [normalizar_coluna(c) for c in clk.columns]
            sub = next((c for c in clk.columns if "sub" in c), None)
            if sub: clk["subid"] = clk[sub].apply(limpar_subid); lista_cliques.append(clk[["subid"]])
        except Exception as e: erros_carregamento.append(f"Cliques '{f.name}': {e}")
if lista_cliques: cliques_shopee = pd.concat(lista_cliques).groupby("subid").size().reset_index(name="cliques_shopee")

df = ads_filtrado.merge(vendas, on="subid", how="outer").merge(cliques_shopee, on="subid", how="outer")
del ads_filtrado, vendas, cliques_shopee; gc.collect()
df["subid"] = df["subid"].fillna("").str.strip()
df = df.fillna(0)
df["subid"] = df["subid"].replace(0, "")
for col in ["comissoes","faturamento","gasto","vendas_diretas","vendas_indiretas","qtd_itens","cliques_anuncio","cliques_shopee"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if not df_shopee_raw.empty or not df_ads_raw.empty:
    filtro_ativo = set(subids_sel) != set(subids_todos)
    if filtro_ativo: df = df[df["subid"].isin(subids_sel)]
    else: df = df[~((df["gasto"]==0)&(df["comissoes"]==0)&(df["cliques_anuncio"]==0)&(df["cliques_shopee"]==0))]
else: df = df[df["gasto"] > 0]

df["imposto_total"] = (df["gasto"]*imposto_meta/100) + (df["comissoes"]*imposto_nf/100)
df["lucro"]   = df["comissoes"] - df["gasto"] - df["imposto_total"]
df["roi"]     = df.apply(lambda x: x["lucro"]/x["gasto"] if x["gasto"]>0 else 0, axis=1)
df["%_bat"]   = df.apply(lambda x: (x["cliques_shopee"]/x["cliques_anuncio"]*100) if x["cliques_anuncio"]>0 else 0, axis=1)
df["total_vendas"] = df["vendas_diretas"] + df["vendas_indiretas"]
df["ticket_medio"] = df.apply(lambda x: x["faturamento"]/x["total_vendas"] if x["total_vendas"]>0 else 0, axis=1)
for c in ["subid","comissoes","faturamento","gasto","lucro","roi","total_vendas","vendas_diretas","vendas_indiretas","qtd_itens","ticket_medio","cliques_anuncio","cliques_shopee","%_bat"]:
    if c not in df.columns: df[c] = 0
df = df[["subid","comissoes","faturamento","gasto","lucro","roi","total_vendas","vendas_diretas","vendas_indiretas","qtd_itens","ticket_medio","cliques_anuncio","cliques_shopee","%_bat"]]

total_gasto    = df["gasto"].sum(); total_comissao = df["comissoes"].sum()
total_lucro    = df["lucro"].sum(); total_roi = total_lucro/total_gasto if total_gasto>0 else 0
ticket_medio_geral = df["faturamento"].sum()/df["total_vendas"].sum() if df["total_vendas"].sum()>0 else 0

if erros_carregamento:
    with st.expander("⚠️ Avisos", expanded=False):
        for e in erros_carregamento: st.warning(e)

if not df.empty and (total_gasto>0 or total_comissao>0):
    st.success("✅ Análise gerada com sucesso!")
    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    c1.metric("Comissão",    formatar_valor(total_comissao))
    c2.metric("Fat. Bruto",  formatar_valor(faturamento_bruto_total))
    c3.metric("Gasto",       formatar_valor(total_gasto))
    c4.metric("Lucro",       formatar_valor(total_lucro), delta=f"{'▲' if total_lucro>=0 else '▼'} {formatar_valor(abs(total_lucro))}")
    c5.metric("ROI Geral",   f"{total_roi:.2%}")
    c6.metric("Vendas",      f"{int(df['total_vendas'].sum())}", delta=f"{int(df['vendas_diretas'].sum())}D / {int(df['vendas_indiretas'].sum())}I")
    c7.metric("Ticket Médio", formatar_valor(ticket_medio_geral))

    if imposto_meta>0 or imposto_nf>0:
        st.markdown(f"""<div style="background:#fef9ec;border:1px solid #fde68a;border-radius:12px;padding:12px 20px;margin-bottom:12px;">
            🧾 Meta Ads {imposto_meta:.1f}% sobre gasto: <strong>R$ {total_gasto*imposto_meta/100:,.2f}</strong> &nbsp;|&nbsp;
            NF {imposto_nf:.1f}% sobre comissão: <strong>R$ {total_comissao*imposto_nf/100:,.2f}</strong>
        </div>""", unsafe_allow_html=True)

    pct_meta = min(faturamento_bruto_total/meta_mensal,1.0) if meta_mensal else 0
    st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;margin:16px 0 8px 0;">
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span style="font-size:0.85rem;font-weight:600;color:#475569;">🎯 Meta Mensal — R$ {meta_mensal:,.2f}</span>
            <span style="font-size:0.85rem;font-weight:700;color:#6366f1;">{pct_meta*100:.1f}% atingido</span>
        </div>
        <div style="background:#e2e8f0;border-radius:99px;height:8px;overflow:hidden;">
            <div style="background:linear-gradient(90deg,#6366f1,#8b5cf6);width:{min(pct_meta*100,100):.1f}%;height:100%;border-radius:99px;"></div>
        </div>
        <div style="font-size:0.78rem;color:#94a3b8;margin-top:6px;">Faltam: R$ {max(meta_mensal-faturamento_bruto_total,0):,.2f}</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    # DETALHAMENTO POR SUBID
    titulo("📊", "Detalhamento por SubID")
    col_ord, col_filt = st.columns([2,1])
    with col_ord:
        lbl = st.selectbox("Ordenar por:", ["ROI","Lucro","Faturamento","Comissão","Gasto","Total Vendas"])
        mp  = {"ROI":"roi","Lucro":"lucro","Faturamento":"faturamento","Comissão":"comissoes","Gasto":"gasto","Total Vendas":"total_vendas"}
        op  = mp[lbl]
    with col_filt:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        so_prej = st.toggle("🔴 Só prejuízo")
        so_lucr = st.toggle("🟢 Só lucro")

    df_t = df.copy()
    if so_prej:
        df_t = df_t[df_t["lucro"]<0]
        st.error(f"🚨 **{len(df_t)} campanha(s) em prejuízo** — R$ {abs(df_t['lucro'].sum()):,.2f}")
    elif so_lucr:
        df_t = df_t[df_t["lucro"]>0]
        st.markdown(f"""<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px 16px;margin-bottom:8px;">
            ✅ <strong>{len(df_t)} campanha(s) com lucro</strong> — R$ {df_t['lucro'].sum():,.2f}</div>""", unsafe_allow_html=True)
    df_t = df_t.sort_values(op, ascending=False).reset_index(drop=True)

    dd = df_t.copy()
    for c in ["comissoes","faturamento","gasto","lucro"]: dd[c] = dd[c].apply(lambda x: f"R$ {x:,.2f}")
    dd["roi"]  = dd["roi"].apply(lambda x: f"{x:.2%}")
    dd["%_bat"]= dd["%_bat"].apply(lambda x: f"{x:.2f}%")
    dd["ticket_medio"] = dd["ticket_medio"].apply(lambda x: f"R$ {x:,.2f}" if x>0 else "—")
    for c in ["total_vendas","vendas_diretas","vendas_indiretas","qtd_itens","cliques_anuncio","cliques_shopee"]: dd[c] = dd[c].astype(int)

    def fmt_roi(row):
        try:
            v = float(str(row["roi"]).replace("%","").replace(",",".").strip())/100
            return f"↑ {v:.0%}" if v>0 else (f"↓ {v:.0%}" if v<0 else "0%")
        except: return str(row["roi"])

    dd["ROI_fmt"] = dd.apply(fmt_roi, axis=1)
    dd = dd.rename(columns={"subid":"SubID","comissoes":"Comissão","gasto":"Gasto","lucro":"Lucro","faturamento":"Faturamento",
        "ticket_medio":"Ticket Médio","total_vendas":"Vendas","vendas_diretas":"Diretas","vendas_indiretas":"Indiretas",
        "qtd_itens":"Prods","cliques_anuncio":"Cli. Anúncio","cliques_shopee":"Cli. Shopee","%_bat":"% Bat."})
    dd["ROI"] = dd["ROI_fmt"]
    cols = ["SubID","Comissão","Gasto","Lucro","ROI","Faturamento","Ticket Médio","Vendas","Diretas","Indiretas","Prods","Cli. Anúncio","Cli. Shopee","% Bat."]
    dd = dd[[c for c in cols if c in dd.columns]]

    tl = df_t["lucro"].sum(); tg = df_t["gasto"].sum()
    tr = tl/tg if tg>0 else 0
    rs = f"↑ {tr:.0%}" if tr>0 else (f"↓ {tr:.0%}" if tr<0 else "0%")

    def cor_tab(df):
        s = pd.DataFrame("", index=df.index, columns=df.columns)
        for i,row in df.iterrows():
            try:
                v = float(str(row["Lucro"]).replace("R$","").replace(",","").strip())
                s.at[i,"Lucro"] = "color:#16a34a;font-weight:bold;" if v>0 else "color:#dc2626;font-weight:bold;"
            except: pass
            try:
                v = float(str(row["ROI"]).replace("↑","").replace("↓","").replace("%","").replace(",",".").strip())/100
                s.at[i,"ROI"] = "color:#16a34a;font-weight:bold;" if v>=roi_minimo else ("color:#d97706;font-weight:bold;" if v>=0 else "color:#dc2626;font-weight:bold;")
            except: pass
        return s

    st.dataframe(dd.style.apply(cor_tab, axis=None), use_container_width=True, hide_index=True)
    rc = "#16a34a" if tr>=roi_minimo else ("#d97706" if tr>=0 else "#dc2626")
    lc = "#16a34a" if tl>=0 else "#dc2626"
    st.markdown(f"""<div style="background:#f1f5f9;border:1px solid #e2e8f0;border-radius:0 0 10px 10px;padding:10px 14px;margin-top:-8px;display:flex;font-family:Inter,sans-serif;font-size:12px;font-weight:700;">
        <div style="min-width:130px;">TOTAL</div>
        <div style="min-width:110px;">R$ {df_t['comissoes'].sum():,.2f}</div>
        <div style="min-width:100px;">R$ {tg:,.2f}</div>
        <div style="min-width:110px;color:{lc};">R$ {tl:,.2f}</div>
        <div style="min-width:80px;color:{rc};">{rs}</div>
        <div style="min-width:120px;">R$ {df_t['faturamento'].sum():,.2f}</div>
        <div style="min-width:110px;">R$ {ticket_medio_geral:,.2f}</div>
        <div style="min-width:70px;">{int(df_t['total_vendas'].sum())}</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    # CANAL
    if not df_shopee_filtrado.empty and "_canal" in df_shopee_filtrado.columns:
        titulo("📡", "Canal — Quantidade & Comissão", cor="#8b5cf6")
        ca = df_shopee_filtrado.groupby("_canal", as_index=False).agg(
            pedidos=("_qtd","count"), vendas_brutas=("_valor","sum"), comissao_total=("_comissao","sum")
        ).sort_values("vendas_brutas", ascending=False)
        canal_cfg = {
            "Pinterest":   {"bg":"#fff0f0","cor":"#E60023"},
            "Instagram":   {"bg":"#fff0f8","cor":"#C13584"},
            "Websites":    {"bg":"#f0fdf4","cor":"#16a34a"},
            "Others":      {"bg":"#f8fafc","cor":"#64748b"},
            "Code Sharing":{"bg":"#eff6ff","cor":"#2563eb"},
            "EdgeBrowser": {"bg":"#eff6ff","cor":"#0ea5e9"},
        }
        cols_c = st.columns(len(ca))
        for idx,(_, row) in enumerate(ca.iterrows()):
            nm = str(row["_canal"])
            cfg = canal_cfg.get(nm, {"bg":"#f8fafc","cor":"#64748b"})
            with cols_c[idx]:
                st.markdown(f"""<div style="background:{cfg['bg']};border:1px solid #e2e8f0;border-radius:12px;padding:14px 16px;text-align:center;">
                    <div style="font-size:12px;font-weight:700;color:{cfg['cor']};margin-bottom:6px;">{nm}</div>
                    <div style="font-size:15px;font-weight:700;color:#0f172a;">R$ {row['vendas_brutas']:,.2f}</div>
                    <div style="font-size:11px;color:#64748b;margin-top:2px;">R$ {row['comissao_total']:,.2f} comissão</div>
                    <div style="font-size:11px;color:#94a3b8;">{int(row['pedidos'])} pedidos</div>
                </div>""", unsafe_allow_html=True)
        st.divider()

    # INSIGHTS
    titulo("🤖", "Analista IA — Insights", cor="#0ea5e9")
    if not df.empty and df["roi"].nunique()>0:
        melhor = df.loc[df["roi"].idxmax()]; pior = df.loc[df["lucro"].idxmin()]
        a,b,c,d = st.columns(4)
        with a: st.markdown(f"""<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:16px;height:110px;">
            <div style="font-size:10px;font-weight:700;color:#1d4ed8;text-transform:uppercase;margin-bottom:10px;">💡 Escalar</div>
            <div style="font-size:12px;color:#1e3a5f;"><strong>{melhor['subid']}</strong><br>ROI <strong>{melhor['roi']:.0%}</strong></div></div>""", unsafe_allow_html=True)
        with b:
            if pior["lucro"]<0: st.markdown(f"""<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:16px;height:110px;">
                <div style="font-size:10px;font-weight:700;color:#92400e;text-transform:uppercase;margin-bottom:10px;">⚠️ Revisar</div>
                <div style="font-size:12px;color:#78350f;"><strong>{pior['subid']}</strong><br>Prejuízo R$ {abs(pior['lucro']):.2f}</div></div>""", unsafe_allow_html=True)
        with c: st.markdown(f"""<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:16px;height:110px;">
            <div style="font-size:10px;font-weight:700;color:#14532d;text-transform:uppercase;margin-bottom:10px;">✅ Lucrativas</div>
            <div style="font-size:28px;font-weight:800;color:#16a34a;">{len(df[df['lucro']>0])}</div></div>""", unsafe_allow_html=True)
        with d: st.markdown(f"""<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:16px;height:110px;">
            <div style="font-size:10px;font-weight:700;color:#991b1b;text-transform:uppercase;margin-bottom:10px;">🚨 Prejuízo</div>
            <div style="font-size:28px;font-weight:800;color:#dc2626;">{len(df[df['lucro']<0])}</div></div>""", unsafe_allow_html=True)
    st.divider()

    # PAINEL DIÁRIO
    if not df_shopee_filtrado.empty and "_data" in df_shopee_filtrado.columns:
        titulo("📅", "Painel Diário", cor="#f59e0b")
        import calendar
        hoje = date.today()
        ult_dia = calendar.monthrange(hoje.year, hoje.month)[1]
        dias_rest = max(ult_dia - hoje.day, 0)
        fd = df_shopee_filtrado.copy()
        fd["_data"] = pd.to_datetime(fd["_data"]).dt.date
        fa = fd.groupby("_data", as_index=False).agg(faturado=("_valor","sum"), comissao=("_comissao","sum")).sort_values("_data")
        if not df_ads_raw.empty and "_data" in df_ads_raw.columns:
            gd = df_ads_raw.copy()
            if subids_sel: gd = gd[gd["subid"].isin(subids_sel)]
            gd["_data"] = pd.to_datetime(gd["_data"]).dt.date
            ga = gd.groupby("_data", as_index=False).agg(invest=("gasto","sum"))
            fa = fa.merge(ga, on="_data", how="left").fillna(0)
        else: fa["invest"] = 0
        fa["lucro"] = fa["comissao"] - fa["invest"] - (fa["invest"]*imposto_meta/100) - (fa["comissao"]*imposto_nf/100)
        fa["acum"]  = fa["faturado"].cumsum()
        tf = fa["faturado"].sum(); ti = fa["invest"].sum(); tc = fa["comissao"].sum(); tl2 = fa["lucro"].sum()
        md = tf/max(len(fa),1); proj = md*ult_dia; nd = max((meta_mensal-tf)/max(dias_rest,1),0)
        p1,p2,p3,p4,p5 = st.columns(5)
        p1.metric("📦 Faturado", formatar_valor(tf))
        p2.metric("📉 Gasto", formatar_valor(ti))
        p3.metric("📈 Lucro", formatar_valor(tl2))
        p4.metric("📆 Dias Restantes", f"{dias_rest}")
        p5.metric("⚡ Neces./dia", formatar_valor(nd))
        st.markdown(f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:14px 20px;margin:12px 0;display:flex;">
            <div style="flex:1;text-align:center;border-right:1px solid #e2e8f0;padding:0 16px;"><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;">Meta</div><div style="font-size:16px;font-weight:700;color:#6366f1;">R$ {meta_mensal:,.2f}</div></div>
            <div style="flex:1;text-align:center;border-right:1px solid #e2e8f0;padding:0 16px;"><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;">Projeção</div><div style="font-size:16px;font-weight:700;color:#d97706;">R$ {proj:,.2f}</div></div>
            <div style="flex:1;text-align:center;border-right:1px solid #e2e8f0;padding:0 16px;"><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;">% Atingido</div><div style="font-size:16px;font-weight:700;color:#16a34a;">{min(tf/meta_mensal*100,100):.1f}%</div></div>
            <div style="flex:1;text-align:center;padding:0 16px;"><div style="font-size:10px;color:#94a3b8;text-transform:uppercase;">Média/dia</div><div style="font-size:16px;font-weight:700;">R$ {md:,.2f}</div></div>
        </div>""", unsafe_allow_html=True)
        b1,b2,b3 = st.columns(3)
        with b1: st.markdown(f"""<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:14px 16px;">
            <div style="font-size:10px;font-weight:700;color:#1d4ed8;text-transform:uppercase;">Bônus 1% · R$ {meta_mensal:,.0f}</div>
            <div style="font-size:11px;color:#3b82f6;margin:4px 0;">Faltam R$ {max(meta_mensal-tf,0):,.2f}</div>
            <div style="font-size:20px;font-weight:800;color:#1d4ed8;">R$ {meta_mensal*0.01:,.2f}</div></div>""", unsafe_allow_html=True)
        with b2: st.markdown(f"""<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:14px 16px;">
            <div style="font-size:10px;font-weight:700;color:#14532d;text-transform:uppercase;">Bônus 2% · R$ {meta_mensal*1.25:,.0f}</div>
            <div style="font-size:11px;color:#16a34a;margin:4px 0;">Faltam R$ {max(meta_mensal*1.25-tf,0):,.2f}</div>
            <div style="font-size:20px;font-weight:800;color:#14532d;">R$ {meta_mensal*1.25*0.02:,.2f}</div></div>""", unsafe_allow_html=True)
        with b3: st.markdown(f"""<div style="background:#fdf4ff;border:1px solid #e9d5ff;border-radius:12px;padding:14px 16px;">
            <div style="font-size:10px;font-weight:700;color:#6b21a8;text-transform:uppercase;">Bônus 3% · R$ {meta_mensal*1.5:,.0f}</div>
            <div style="font-size:11px;color:#9333ea;margin:4px 0;">Faltam R$ {max(meta_mensal*1.5-tf,0):,.2f}</div>
            <div style="font-size:20px;font-weight:800;color:#6b21a8;">R$ {meta_mensal*1.5*0.03:,.2f}</div></div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        fe = fa.copy()
        fe["_data"]   = pd.to_datetime(fe["_data"]).dt.strftime("%d/%m/%Y")
        fe["comissao"]= fe["comissao"].apply(lambda x: f"R$ {x:,.2f}")
        fe["invest"]  = fe["invest"].apply(lambda x: f"R$ {x:,.2f}")
        fe["faturado"]= fe["faturado"].apply(lambda x: f"R$ {x:,.2f}")
        fe["lucro_s"] = fa["lucro"].apply(lambda x: f"R$ {x:,.2f}")
        fe["roi_s"]   = fa.apply(lambda x: f"{(x['lucro']/x['invest']*100):.0f}%" if x['invest']>0 else "—", axis=1)
        fe["acum_s"]  = fa["acum"].apply(lambda x: f"R$ {x:,.2f}")
        ex = fe[["_data","comissao","invest","lucro_s","roi_s","faturado","acum_s"]].copy()
        ex.columns = ["Dia","Comissão","Gasto","Lucro","ROI","Faturado","Faturado Acum."]
        rt = f"{(tl2/ti*100):.0f}%" if ti>0 else "—"
        ex = pd.concat([ex, pd.DataFrame([{"Dia":"TOTAL","Comissão":f"R$ {tc:,.2f}","Gasto":f"R$ {ti:,.2f}","Lucro":f"R$ {tl2:,.2f}","ROI":rt,"Faturado":f"R$ {tf:,.2f}","Faturado Acum.":"—"}])], ignore_index=True)
        def cor_dia(df):
            s = pd.DataFrame("", index=df.index, columns=df.columns)
            for i,row in df.iterrows():
                if row["Dia"]=="TOTAL":
                    for col in df.columns: s.at[i,col]="font-weight:bold;background-color:#f1f5f9;"
                    continue
                try:
                    v = float(str(row["Lucro"]).replace("R$","").replace(",","").strip())
                    s.at[i,"Lucro"] = "color:#16a34a;font-weight:bold;" if v>=0 else "color:#dc2626;font-weight:bold;"
                except: pass
            return s
        st.dataframe(ex.style.apply(cor_dia, axis=None), use_container_width=True, hide_index=True)
        st.divider()

    # ANÁLISE VISUAL
    titulo("📈", "Análise Visual", cor="#10b981")
    if not df_shopee_filtrado.empty and "_data" in df_shopee_filtrado.columns:
        sv = ["Todos"] + sorted(df_shopee_filtrado["subid"].dropna().unique().tolist())
        sv_sel = st.selectbox("Filtrar por SubID:", sv, key="vis_sub")
        rv = df_shopee_filtrado if sv_sel=="Todos" else df_shopee_filtrado[df_shopee_filtrado["subid"]==sv_sel]
        fv = rv.groupby("_data", as_index=False).agg(faturamento=("_valor","sum"), comissao=("_comissao","sum"),
            vendas=("_qtd","sum"), diretas=("_direta","sum"), indiretas=("_indireta","sum")).sort_values("_data")
        fv["_data"] = pd.to_datetime(fv["_data"]).dt.strftime("%d/%m/%Y")
        gv = df["gasto"].sum() if sv_sel=="Todos" else (df[df["subid"]==sv_sel]["gasto"].values[0] if not df[df["subid"]==sv_sel].empty else 0.0)
        ft2 = fv["faturamento"].sum()
        fv["gasto"] = fv["faturamento"]/ft2*gv if ft2>0 else 0.0
        fv["lucro"] = fv["comissao"] - fv["gasto"]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=fv["_data"], y=fv["faturamento"], name="Faturamento", marker_color="#6366f1"))
        fig.add_trace(go.Bar(x=fv["_data"], y=fv["comissao"],    name="Comissão",    marker_color="#8b5cf6"))
        fig.add_trace(go.Bar(x=fv["_data"], y=fv["gasto"],       name="Gasto",       marker_color="#f87171"))
        fig.update_layout(barmode="group", paper_bgcolor="#ffffff", plot_bgcolor="#f8fafc",
            font_color="#1e293b", font_family="Inter", xaxis_title="Data", yaxis_title="R$")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Carregue os arquivos da Shopee para ver a análise visual.")

    st.divider()
    c1,c2 = st.columns(2)
    with c1: st.download_button("📥 Baixar Excel", data=gerar_excel(df), file_name=f"afiliametrics_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with c2: st.download_button("📄 Baixar CSV", data=df.to_csv(index=False).encode("utf-8"), file_name=f"afiliametrics_{date.today()}.csv", mime="text/csv")

else:
    st.info("👈 Carregue seus arquivos na sidebar para começar a análise.")
    st.markdown("""
    ### Como usar:
    1. **Configure** o ROI mínimo e sua meta mensal
    2. **Importe** os arquivos (Pinterest, Meta, Shopee)
    3. **Analise** os resultados
    4. **Baixe** o relatório
    """)
