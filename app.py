import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from pathlib import Path

st.set_page_config(
    page_title="Corrida do Policial Civil 2026",
    page_icon="🏃",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f, #0d2137);
        border: 1px solid #2e6da4;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 8px 0;
    }
    .metric-card .number { font-size: 2.5rem; font-weight: 700; color: #4db8ff; }
    .metric-card .label  { font-size: 0.9rem; color: #aac8e4; margin-top: 4px; }
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #4db8ff;
        border-left: 4px solid #2e6da4;
        padding-left: 12px;
        margin: 24px 0 12px 0;
    }
</style>
""", unsafe_allow_html=True)

CORES = {
    "16 a 19 anos":    "#FF6B6B",
    "20 a 29 anos":    "#4ECDC4",
    "30 a 39 anos":    "#45B7D1",
    "40 a 49 anos":    "#96CEB4",
    "50 a 59 anos":    "#FFEAA7",
    "60 anos ou mais": "#DDA0DD",
    "Sem informação":  "#888888",
}

GRUPOS_ORDEM = [
    "16 a 19 anos", "20 a 29 anos", "30 a 39 anos",
    "40 a 49 anos", "50 a 59 anos", "60 anos ou mais", "Sem informação",
]

DB_PATH = Path(__file__).parent / "corrida.db"

# ── Carrega dados do banco ───────────────────────────────────────────────────
@st.cache_data
def carregar_dados():
    if not DB_PATH.exists():
        return None
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM participantes ORDER BY nome", con)
    con.close()
    return df

df = carregar_dados()

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 30px 0 10px 0;'>
    <span style='font-size:3rem;'>🏃‍♂️</span>
    <h1 style='margin:0; font-size:2rem;'>Corrida do Policial Civil 2026</h1>
    <p style='color:#aac8e4; margin-top:6px;'>Análise de Grupos Etários — Treino Oficial</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Banco não encontrado ─────────────────────────────────────────────────────
if df is None:
    st.error("❌ Banco de dados `corrida.db` não encontrado na pasta do app.")
    st.info("""
**Para gerar o banco, rode no seu computador:**
```bash
python criar_banco.py
```
Depois copie o arquivo `corrida.db` para a mesma pasta deste app.
    """)
    st.stop()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Grupos etários")
    for g in GRUPOS_ORDEM[:-1]:
        qtd = len(df[df["grupo_etario"] == g])
        st.markdown(
            f"<span style='color:{CORES[g]}; font-weight:600;'>● {g}</span>"
            f"<span style='color:#aac8e4; float:right;'>{qtd}</span>",
            unsafe_allow_html=True
        )
    st.markdown("---")
    st.caption(f"Total: {len(df)} inscritos")

# ── Métricas ─────────────────────────────────────────────────────────────────
total     = len(df)
com_info  = df["grupo_etario"].ne("Sem informação").sum()
sem_info  = total - com_info
idade_med = df["idade"].mean()

cols = st.columns(4)
metricas = [
    ("👥", total,                               "Total de inscritos"),
    ("📊", com_info,                            "Com data de nascimento"),
    ("❓", sem_info,                            "Sem informação"),
    ("📅", f"{idade_med:.0f}" if pd.notna(idade_med) else "—", "Idade média"),
]
for col, (icon, val, lbl) in zip(cols, metricas):
    with col:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size:1.6rem;'>{icon}</div>
            <div class='number'>{val}</div>
            <div class='label'>{lbl}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Resumo por grupo ─────────────────────────────────────────────────────────
resumo = (
    df.groupby("grupo_etario")
    .agg(Quantidade=("nome", "count"))
    .reindex([g for g in GRUPOS_ORDEM if g in df["grupo_etario"].unique()])
    .fillna(0).astype(int).reset_index()
    .rename(columns={"grupo_etario": "Grupo Etário"})
)
resumo["Percentual"] = (resumo["Quantidade"] / total * 100).round(1)

tab1, tab2, tab3 = st.tabs(["📊 Gráficos", "🗂️ Listagem por Grupo", "📋 Tabela Completa"])

# ─── Gráficos ─────────────────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        fig_bar = go.Figure()
        for _, row in resumo.iterrows():
            g = row["Grupo Etário"]
            fig_bar.add_trace(go.Bar(
                x=[g], y=[row["Quantidade"]],
                marker_color=CORES.get(g, "#888"),
                text=[row["Quantidade"]], textposition="outside",
                showlegend=False,
            ))
        fig_bar.update_layout(
            title="Participantes por grupo",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            yaxis=dict(gridcolor="#333", title="Pessoas"),
            xaxis=dict(tickangle=-20), bargap=0.3, margin=dict(t=50, b=60),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c2:
        fig_pie = go.Figure(go.Pie(
            labels=resumo["Grupo Etário"], values=resumo["Quantidade"],
            hole=0.45,
            marker=dict(colors=[CORES.get(g, "#888") for g in resumo["Grupo Etário"]]),
            textinfo="label+percent", textfont=dict(size=12),
        ))
        fig_pie.update_layout(
            title="Proporção por grupo",
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
            showlegend=False, margin=dict(t=50, b=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    fig_h = go.Figure()
    for _, row in resumo.sort_values("Quantidade").iterrows():
        g = row["Grupo Etário"]
        fig_h.add_trace(go.Bar(
            y=[g], x=[row["Percentual"]], orientation="h",
            marker_color=CORES.get(g, "#888"),
            text=[f"{row['Percentual']:.1f}% ({int(row['Quantidade'])} pessoas)"],
            textposition="auto", showlegend=False,
        ))
    fig_h.update_layout(
        title="Percentual por grupo",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(gridcolor="#333", title="%"), margin=dict(t=50), height=320,
    )
    st.plotly_chart(fig_h, use_container_width=True)

    df_idades = df[df["idade"].notna()]
    if not df_idades.empty:
        fig_hist = px.histogram(
            df_idades, x="idade", nbins=20,
            color="grupo_etario", color_discrete_map=CORES,
            title="Distribuição de idades",
            labels={"idade": "Idade", "count": "Quantidade", "grupo_etario": "Grupo"},
        )
        fig_hist.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            yaxis=dict(gridcolor="#333"), xaxis=dict(gridcolor="#333"),
            legend=dict(bgcolor="rgba(0,0,0,0.4)"),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

# ─── Listagem por Grupo ───────────────────────────────────────────────────
with tab2:
    grupos_disp = [g for g in GRUPOS_ORDEM if g in df["grupo_etario"].unique()]
    grupo_sel   = st.selectbox("Selecione o grupo:", grupos_disp)
    df_grupo    = df[df["grupo_etario"] == grupo_sel].copy()
    cor         = CORES.get(grupo_sel, "#888")

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,{cor}22,{cor}11);
                border:1px solid {cor}; border-radius:10px;
                padding:16px; margin-bottom:16px;'>
        <span style='color:{cor}; font-size:1.4rem; font-weight:700;'>{grupo_sel}</span>
        &nbsp; <span style='color:#fff;'>{len(df_grupo)} participante{"s" if len(df_grupo) != 1 else ""}</span>
    </div>""", unsafe_allow_html=True)

    busca = st.text_input("🔍 Filtrar por nome:", key="busca_grupo")
    if busca:
        df_grupo = df_grupo[df_grupo["nome"].str.contains(busca, case=False, na=False)]

    exibir = df_grupo[["nome", "nascimento_fmt", "idade"]].copy()
    exibir.columns = ["Nome", "Nascimento", "Idade"]
    exibir.index   = range(1, len(exibir) + 1)
    st.dataframe(exibir, use_container_width=True)

    csv = exibir.to_csv(index=True).encode("utf-8-sig")
    st.download_button(
        f"⬇️ Baixar lista — {grupo_sel}", data=csv,
        file_name=f"grupo_{grupo_sel.replace(' ', '_')}.csv", mime="text/csv",
    )

# ─── Tabela Completa ──────────────────────────────────────────────────────
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        busca_geral = st.text_input("🔍 Buscar por nome:")
    with c2:
        grupos_filtro = st.multiselect("Filtrar por grupo:", grupos_disp, default=grupos_disp)

    df_filtrado = df.copy()
    if busca_geral:
        df_filtrado = df_filtrado[df_filtrado["nome"].str.contains(busca_geral, case=False, na=False)]
    if grupos_filtro:
        df_filtrado = df_filtrado[df_filtrado["grupo_etario"].isin(grupos_filtro)]

    df_filtrado = df_filtrado.sort_values(["grupo_etario", "nome"])
    exibir_g    = df_filtrado[["nome","idade", "grupo_etario"]].copy()
    exibir_g.columns = ["Nome","Idade", "Grupo Etário"]
    exibir_g.index   = range(1, len(exibir_g) + 1)
    st.dataframe(exibir_g, use_container_width=True)

    csv_g = exibir_g.to_csv(index=True).encode("utf-8-sig")
    st.download_button(
        "⬇️ Baixar tabela completa (.csv)", data=csv_g,
        file_name="participantes_completo.csv", mime="text/csv",
    )

st.divider()
st.markdown(
    "<p style='text-align:center;color:#555;font-size:0.8rem;'>"
    "Corrida do Policial Civil 2026 · Análise de Grupos Etários</p>",
    unsafe_allow_html=True
)