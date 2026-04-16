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
    /* Fundo escuro geral */
    .stApp { background-color: #0f172a; }

    /* Cards de Métrica */
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover { transform: translateY(-2px); }

    [data-testid="stMetricValue"]  { color: #38bdf8 !important; font-size: 1.6rem !important; }
    [data-testid="stMetricLabel"]  { color: #94a3b8 !important; }
    [data-testid="stMetricDelta"]  { font-size: 0.85rem !important; }

    /* Tabelas */
    .stDataFrame { border: 1px solid #334155; border-radius: 12px; overflow: hidden; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1e293b; }

    /* Títulos */
    h1, h2, h3 { color: #f1f5f9 !important; }

    /* Alertas */
    .stAlert { border-radius: 10px; }

    /* Botão de download */
    .stDownloadButton button {
        background-color: #0284c7;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stDownloadButton button:hover { background-color: #0369a1; }
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
    try:
        df = pd.read_csv(file, sep=";", encoding="latin-1", engine="python")
        if len(df.columns) <= 1:
            file.seek(0)
            df = pd.read_csv(file, sep=",", encoding="latin-1", engine="python")
        return df
    except:
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

def estilo_linha(row):
    estilos = []
    for col in row.index:
        if col == "lucro":
            v = converter_valor(row[col])
            estilos.append("color: #4ade80; font-weight:bold;" if v > 0 else "color: #f87171; font-weight:bold;")
        elif col == "roi":
            v = float(str(row[col]).replace("%", "")) / 100
            if v >= roi_minimo:
                estilos.append("color: #4ade80; font-weight:bold;")
            elif v >= roi_minimo * 0.8:
                estilos.append("color: #fbbf24; font-weight:bold;")
            else:
                estilos.append("color: #f87171; font-weight:bold;")
        else:
            estilos.append("")
    return estilos

# =========================
# PROCESSAMENTO
# =========================
ads              = pd.DataFrame(columns=["subid", "gasto", "cliques_anuncio"])
vendas           = pd.DataFrame(columns=["subid", "comissoes"])
cliques_shopee   = pd.DataFrame(columns=["subid", "cliques_shopee"])
faturamento_bruto_total = 0.0
erros_carregamento = []

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
if shopee_comissao_files:
    for f in shopee_comissao_files:
        try:
            shp = ler_csv_inteligente(f)
            shp.columns = [normalizar_coluna(c) for c in shp.columns]

            col_valor  = next((c for c in shp.columns if "valor_de_compra" in c), None)
            col_status = next((c for c in shp.columns if "status_do_pedido" in c), None)
            col_notas  = next((c for c in shp.columns if "notas" in c or "status_do_item" in c), None)
            col_comis  = next((c for c in shp.columns if "comissao_liquida" in c or "comissao_total" in c), shp.columns[-1])
            col_sub    = next((c for c in shp.columns if "sub_id1" in c), None)

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
            faturamento_bruto_total += shp_valido[col_valor].apply(converter_valor).sum()

            if col_sub:
                shp_valido["subid"]     = shp_valido[col_sub].apply(limpar_subid)
                shp_valido["comissoes"] = shp_valido[col_comis].apply(converter_valor)
                lista_vendas.append(shp_valido[["subid", "comissoes"]])
        except Exception as e:
            erros_carregamento.append(f"Shopee Comissões '{f.name}': {e}")

if lista_vendas:
    vendas = pd.concat(lista_vendas).groupby("subid", as_index=False).sum()

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

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Comissão",   f"R$ {total_comissao:,.2f}")
    c2.metric("📉 Gasto",      f"R$ {total_gasto:,.2f}")
    c3.metric("📈 Lucro",      f"R$ {total_lucro:,.2f}", delta=f"{'▲' if total_lucro >= 0 else '▼'} {abs(total_lucro):,.2f}")
    c4.metric("🚀 ROI Geral",  f"{total_roi:.2%}")
    c5.metric("🧾 Fat. Bruto", f"R$ {faturamento_bruto_total:,.2f}")

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

    tab1, tab2, tab3 = st.tabs(["ROI por Campanha", "Lucro vs Gasto", "Funil de Cliques"])

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
            paper_bgcolor="#1e293b", plot_bgcolor="#0f172a",
            font_color="#f1f5f9", coloraxis_showscale=False
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
        fig_lv.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#0f172a", font_color="#f1f5f9")
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
                paper_bgcolor="#1e293b", plot_bgcolor="#0f172a", font_color="#f1f5f9"
            )
            st.plotly_chart(fig_funil, use_container_width=True)
        else:
            st.info("Carregue os arquivos de cliques da Shopee para ver o funil.")

    st.divider()

    # =========================
    # TABELA DETALHADA
    # =========================
    st.subheader("📊 Detalhamento por SubID")

    col_ord, col_filt = st.columns([2, 1])
    with col_ord:
        ordenar_por = st.selectbox("Ordenar por:", ["roi", "lucro", "comissoes", "gasto", "%_batimento_cliques"])
    with col_filt:
        mostrar_apenas_prejuizo = st.checkbox("Mostrar apenas prejuízo")

    df_tabela = df.copy()
    if mostrar_apenas_prejuizo:
        df_tabela = df_tabela[df_tabela["lucro"] < 0]
    df_tabela = df_tabela.sort_values(ordenar_por, ascending=False)

    df_display = df_tabela.copy()
    for col in ["comissoes", "gasto", "lucro"]:
        df_display[col] = df_display[col].apply(lambda x: f"R$ {x:,.2f}")
    df_display["roi"]                  = df_display["roi"].apply(lambda x: f"{x:.2%}")
    df_display["%_batimento_cliques"]  = df_display["%_batimento_cliques"].apply(lambda x: f"{x:.2f}%")

    st.dataframe(df_display.style.apply(estilo_linha, axis=1), use_container_width=True)

    # Alertas
    if not df[df["lucro"] < 0].empty:
        st.error(f"🚨 {len(df[df['lucro'] < 0])} campanha(s) em prejuízo! Revise os criativos.")

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
        - Campanhas lucrativas: {campanhas_lucro}
        - Campanhas em prejuízo: {campanhas_prejuizo}
        - Melhor campanha: {melhor['subid']} com ROI {melhor['roi']:.2%}
        - Pior campanha: {pior['subid']} com lucro R$ {pior['lucro']:,.2f}
        - Batimento médio de cliques: {batimento_avg:.1f}%
        Top 5 por ROI:
        {df.nlargest(5, 'roi')[['subid','gasto','comissoes','lucro','roi']].to_string(index=False)}
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
                paper_bgcolor="#1e293b", plot_bgcolor="#0f172a",
                font_color="#f1f5f9", xaxis_title="Data", yaxis_title="R$"
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
