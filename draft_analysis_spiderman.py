
# draft_analysis_spiderman.py
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from collections import Counter
import re

st.set_page_config(page_title="Draft Analysis – Spider‑Man (SPM)", layout="wide")

@st.cache_data(show_spinner=True)
def fetch_spiderman_cards():
    url = "https://api.scryfall.com/cards/search"
    params = {"q": "set:spm"}
    all_cards = []
    while url:
        r = requests.get(url, params=params if not all_cards else None, timeout=30)
        r.raise_for_status()
        data = r.json()
        all_cards.extend(data.get("data", []))
        url = data.get("next_page")
        params = None
    return all_cards

def cards_to_dataframe(cards):
    rows = []
    for c in cards:
        rows.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "mana_cost": c.get("mana_cost"),
            "cmc": c.get("cmc"),
            "colors": tuple(c.get("colors") or []),
            "color_identity": tuple(c.get("color_identity") or []),
            "type_line": c.get("type_line"),
            "rarity": c.get("rarity"),
            "power": c.get("power"),
            "toughness": c.get("toughness"),
            "oracle_text": c.get("oracle_text") or "",
            "image": (c.get("image_uris") or {}).get("normal"),
            "collector_number": c.get("collector_number"),
        })
    df = pd.DataFrame(rows)
    def to_num(x):
        try:
            return float(x)
        except Exception:
            return None
    df["cmc_num"] = df["cmc"].apply(to_num)
    df["is_creature"] = df["type_line"].fillna("").str.contains("Creature", case=False)
    def color_label(colors):
        if not colors:
            return "Colorless"
        if len(colors) == 1:
            mapping = {"W":"White","U":"Blue","B":"Black","R":"Red","G":"Green"}
            return mapping.get(colors[0], colors[0])
        return "Multicolor"
    df["color_label"] = df["colors"].apply(color_label)
    return df

def extract_keywords(text):
    keywords = [
        "flying","trample","haste","lifelink","vigilance","menace","reach",
        "deathtouch","hexproof","ward","prowess","scry","draw","discard",
        "destroy","exile","fight","damage","counter","token","equip","aura",
        "flash","first strike","double strike"
    ]
    t = text.lower()
    found = []
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", t):
            found.append(kw)
    return found

def keyword_counts(df):
    counts = Counter()
    for t in df["oracle_text"].fillna(""):
        for kw in extract_keywords(t):
            counts[kw] += 1
    if not counts:
        return pd.DataFrame(columns=["keyword","count"])
    return pd.DataFrame({"keyword": list(counts.keys()), "count": list(counts.values())}).sort_values("count", ascending=False)

# Load
cards = fetch_spiderman_cards()
df = cards_to_dataframe(cards)

# Sidebar filters
with st.sidebar:
    st.header("Filtres")
    rarity_options = sorted(df["rarity"].dropna().unique().tolist())
    rarity_sel = st.multiselect("Rareté", options=rarity_options, default=rarity_options)
    color_options = ["White","Blue","Black","Red","Green","Multicolor","Colorless"]
    color_sel = st.multiselect("Couleurs", options=color_options, default=color_options)
    type_filter = st.text_input("Filtre type (contient)", value="")
    name_search = st.text_input("Recherche nom/texte", value="")
    cmc_min, cmc_max = int((df["cmc_num"].min() or 0)), int((df["cmc_num"].max() or 10))
    cmc_range = st.slider("Plage CMC", min_value=0, max_value=max(10, cmc_max), value=(0, max(5, cmc_max)))

mask = (
    df["rarity"].isin(rarity_sel)
    & df["color_label"].isin(color_sel)
    & df["cmc_num"].fillna(-1).between(cmc_range[0], cmc_range[1])
)
if type_filter.strip():
    mask &= df["type_line"].fillna("").str.contains(type_filter, case=False)
if name_search.strip():
    query = name_search.strip().lower()
    mask &= (
        df["name"].fillna("").str.lower().str.contains(query)
        | df["oracle_text"].fillna("").str.lower().str.contains(query)
    )
df_f = df[mask].copy()

st.title("Draft Analysis – Spider‑Man (SPM)")

st.subheader("Aperçu des cartes filtrées")
st.dataframe(
    df_f[["name","mana_cost","cmc","color_label","type_line","rarity","power","toughness","oracle_text"]],
    use_container_width=True,
    hide_index=True
)

# Graphs
st.subheader("Courbe de mana (global)")
fig1, ax1 = plt.subplots()
df_f["cmc_num"].dropna().astype(int).value_counts().sort_index().plot(kind="bar", ax=ax1)
ax1.set_xlabel("CMC")
ax1.set_ylabel("Nombre de cartes")
ax1.set_title("Mana Curve (global)")
st.pyplot(fig1, clear_figure=True)

st.subheader("Courbe de mana – Créatures")
fig2, ax2 = plt.subplots()
df_f[df_f["is_creature"]]["cmc_num"].dropna().astype(int).value_counts().sort_index().plot(kind="bar", ax=ax2)
ax2.set_xlabel("CMC")
ax2.set_ylabel("Nombre de créatures")
ax2.set_title("Mana Curve (créatures)")
st.pyplot(fig2, clear_figure=True)

st.subheader("Répartition par couleur")
fig3, ax3 = plt.subplots()
df_f["color_label"].value_counts().sort_index().plot(kind="bar", ax=ax3)
ax3.set_xlabel("Couleur")
ax3.set_ylabel("Nombre de cartes")
ax3.set_title("Cartes par couleur")
st.pyplot(fig3, clear_figure=True)

st.subheader("Répartition par rareté")
fig4, ax4 = plt.subplots()
order_rarity = [r for r in ["common","uncommon","rare","mythic"] if r in df_f["rarity"].unique()]
df_f["rarity"].value_counts().reindex(order_rarity).fillna(0).plot(kind="bar", ax=ax4)
ax4.set_xlabel("Rareté")
ax4.set_ylabel("Nombre de cartes")
ax4.set_title("Cartes par rareté")
st.pyplot(fig4, clear_figure=True)

st.subheader("Mots-clés (oracle_text)")
kw_df = keyword_counts(df_f)
if not kw_df.empty:
    fig5, ax5 = plt.subplots()
    kw_df.head(20).set_index("keyword")["count"].plot(kind="bar", ax=ax5)
    ax5.set_xlabel("Mot-clé")
    ax5.set_ylabel("Occurrences")
    ax5.set_title("Top 20 mots-clés")
    st.pyplot(fig5, clear_figure=True)
else:
    st.info("Aucun mot-clé détecté avec les filtres actuels.")
