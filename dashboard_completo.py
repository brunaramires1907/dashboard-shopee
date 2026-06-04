import streamlit as st
import pandas as pd
import unicodedata
from io import BytesIO
from datetime import date
import gc
import plotly.graph_objects as go

st.set_page_config(page_title="AfiliaMetrics", layout="wide", page_icon="📊")
st.title("AfiliaMetrics - Teste")
st.write("✅ App funcionando!")
st.write(f"Data: {date.today()}")

uploaded = st.file_uploader("Teste de upload", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
    st.dataframe(df.head())
