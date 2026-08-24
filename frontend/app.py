import streamlit as st
import requests
import pandas as pd

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="Vala Bleu Ops Copilot", page_icon="🛰️", layout="wide")

# --- CSS custom (thème sombre pro) ---
st.markdown("""
<style>
#MainMenu, footer {visibility:hidden;}
.block-container {padding-top:2.2rem;}
.hero-title{
  font-size:2.3rem;font-weight:800;letter-spacing:-.02em;margin-bottom:0;
  background:linear-gradient(90deg,#12B5B0,#4F8BF9);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.hero-sub{color:#93A0AE;margin-top:2px;font-size:.95rem;}
.stButton>button{
  background:#12B5B0;color:#04211f;font-weight:700;border:none;
  border-radius:10px;padding:.5rem 1.4rem;transition:.15s;
}
.stButton>button:hover{background:#0FA3A3;color:#04211f;transform:translateY(-1px);}
div[data-testid="stMetric"]{
  background:#161B22;border:1px solid #26303A;border-radius:14px;padding:14px 18px;
}
div[data-testid="stMetricValue"]{color:#12B5B0;}
.stTabs [data-baseweb="tab-list"]{gap:6px;}
.stTabs [data-baseweb="tab"]{border-radius:10px 10px 0 0;padding:8px 16px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="hero-title">🛰️ Vala Bleu Ops Copilot</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Assistant agentique RAG + détection d\'anomalies · inférence 100% locale</p>',
            unsafe_allow_html=True)
st.write("")

tab_chat, tab_mon, tab_qual = st.tabs(["💬 Chat", "📊 Monitoring", "✅ Qualité"])

# --- Onglet 1 : Chat ---
with tab_chat:
    st.subheader("Assistant technique")
    question = st.text_input("Ta question :", "Comment activer un certificat SSL ?")
    if st.button("Envoyer", key="chat"):
        try:
            with st.spinner("Routage + génération (inférence locale)..."):
                r = requests.post(f"{API}/chat", json={"question": question}, timeout=120).json()
            st.markdown(f"🧭 Intention détectée : **{r['intent']}**")
            with st.container(border=True):
                st.markdown(r["answer"] or "_(pas de réponse textuelle)_")
            if r.get("sources"):
                st.caption("Sources :")
                for s in r["sources"]:
                    st.caption(f"📄 {s['titre']} — {s['source_url']}")
            if r.get("logs"):
                st.dataframe(pd.DataFrame(r["logs"]["anomalies"]), use_container_width=True)
        except requests.exceptions.RequestException:
            st.error("⚠️ Impossible de joindre l'API (port 8000). Lance `python backend\\app\\main.py` dans un autre terminal.")

# --- Onglet 2 : Monitoring ---
with tab_mon:
    st.subheader("Détection d'anomalies de trafic")
    if st.button("🔍 Analyser les logs", key="mon"):
        try:
            with st.spinner("Analyse des logs..."):
                r = requests.post(f"{API}/logs/analyze", timeout=60).json()
            c1, c2, c3 = st.columns(3)
            c1.metric("IP analysées", r["total_ips"])
            c2.metric("Anomalies détectées", r["n_anomalies"])
            taux = r["n_anomalies"] / r["total_ips"] * 100 if r["total_ips"] else 0
            c3.metric("Taux d'anomalies", f"{taux:.1f}%")
            df = pd.DataFrame(r["anomalies"])
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.markdown("**Requêtes par IP anormale**")
                st.bar_chart(df.set_index("ip")["n_requests"])
        except requests.exceptions.RequestException:
            st.error("⚠️ Impossible de joindre l'API (port 8000).")

# --- Onglet 3 : Qualité ---
with tab_qual:
    st.subheader("Qualité du RAG (RAGAS)")
    st.info("📊 Scores RAGAS — à venir après l'évaluation (Étape 15).")
