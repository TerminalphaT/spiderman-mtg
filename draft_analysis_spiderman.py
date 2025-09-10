
# draft_analysis_spiderman.py
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from collections import Counter
import re

st.set_page_config(page_title="Draft Analysis – Spider-Man (SPM)", layout="wide")

# ---------------------------
# Data
# ---------------------------
@st.cache_data(show_spinner=True)
def fetch_spiderman_cards():
    url = "https://api.scryfall.com/cards/search"
    params = {"q": "set:spm"}   # change "spm" for another set code if needed
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
    t = (text or "").lower()
    found = []
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", t):
            found.append(kw)
    return found

def keyword_counts(df_in):
    counts = Counter()
    for t in df_in["oracle_text"].fillna(""):
        for kw in extract_keywords(t):
            counts[kw] += 1
    if not counts:
        return pd.DataFrame(columns=["keyword","count"])
    return (
        pd.DataFrame({"keyword": list(counts.keys()), "count": list(counts.values())})
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )

# ---------------------------
# Load
# ---------------------------
cards = fetch_spiderman_cards()
df = cards_to_dataframe(cards)

# ---------------------------
# Sidebar / Filters
# ---------------------------
with st.sidebar:
    st.header("Filtres")
    rarity_options = sorted(df["rarity"].dropna().unique().tolist())
    rarity_sel = st.multiselect("Rareté", options=rarity_options, default=rarity_options)

    color_options = ["White","Blue","Black","Red","Green","Multicolor","Colorless"]
    color_sel = st.multiselect("Couleurs", options=color_options, default=color_options)

    type_filter = st.text_input("Filtre type (contient)", value="")
    name_search = st.text_input("Recherche nom/texte", value="")

    cmc_min = int((df["cmc_num"].min() or 0))
    cmc_max = int((df["cmc_num"].max() or 10))
    cmc_range = st.slider("Plage CMC", min_value=0, max_value=max(10, cmc_max), value=(0, max(5, cmc_max)))

    show_table = st.checkbox("Afficher le tableau des cartes filtrées", value=False)

# Apply filters
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

# ---------------------------
# Header
# ---------------------------
st.title("Draft Analysis – Marvel’s Spider-Man (SPM)")
st.caption("Card data & images © Scryfall — https://scryfall.com/ — used under their API guidelines.")

# Optional table
if show_table:
    st.subheader("Cartes filtrées")
    st.dataframe(
        df_f[["name","mana_cost","cmc","color_label","type_line","rarity","power","toughness","oracle_text"]],
        use_container_width=True,
        hide_index=True
    )

# ---------------------------
# Small helper to render bar charts quickly
# ---------------------------
def bar_count(series, title, xlabel, ylabel):
    counts = series.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(4, 3))   # SMALL FIG
    counts.plot(kind="bar", ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis='x', labelrotation=0)
    fig.tight_layout()
    return fig

# ---------------------------
# Row 1: 3 small charts side-by-side
# ---------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Mana curve (global)")
    cmc_counts = df_f["cmc_num"].dropna().astype(int)
    if cmc_counts.empty:
        st.info("Aucune donnée à afficher.")
    else:
        fig1, ax1 = plt.subplots(figsize=(4, 3))
        cmc_counts.value_counts().sort_index().plot(kind="bar", ax=ax1)
        ax1.set_xlabel("CMC")
        ax1.set_ylabel("Nombre de cartes")
        ax1.set_title("Mana Curve (global)")
        ax1.tick_params(axis='x', labelrotation=0)
        fig1.tight_layout()
        st.pyplot(fig1, clear_figure=True)

with col2:
    st.subheader("Raretés")
    if df_f.empty:
        st.info("Aucune donnée.")
    else:
        order_rarity = [r for r in ["common","uncommon","rare","mythic"] if r in df_f["rarity"].unique()]
        fig2, ax2 = plt.subplots(figsize=(4, 3))
        df_f["rarity"].value_counts().reindex(order_rarity).fillna(0).plot(kind="bar", ax=ax2)
        ax2.set_xlabel("Rareté")
        ax2.set_ylabel("Nombre")
        ax2.set_title("Répartition par rareté")
        ax2.tick_params(axis='x', labelrotation=0)
        fig2.tight_layout()
        st.pyplot(fig2, clear_figure=True)

with col3:
    st.subheader("Couleurs")
    if df_f.empty:
        st.info("Aucune donnée.")
    else:
        fig3 = bar_count(df_f["color_label"], "Cartes par couleur", "Couleur", "Nombre")
        st.pyplot(fig3, clear_figure=True)

# ---------------------------
# Row 2: 2 small charts side-by-side
# ---------------------------
col4, col5 = st.columns(2)

with col4:
    st.subheader("Mana curve – Créatures")
    creatures = df_f[df_f["is_creature"]]
    cmc_crea = creatures["cmc_num"].dropna().astype(int)
    if cmc_crea.empty:
        st.info("Aucune créature dans le filtre actuel.")
    else:
        fig4, ax4 = plt.subplots(figsize=(5, 3.5))  # slightly wider for readability
        cmc_crea.value_counts().sort_index().plot(kind="bar", ax=ax4)
        ax4.set_xlabel("CMC")
        ax4.set_ylabel("Nombre de créatures")
        ax4.set_title("Mana Curve (créatures)")
        ax4.tick_params(axis='x', labelrotation=0)
        fig4.tight_layout()
        st.pyplot(fig4, clear_figure=True)

with col5:
    st.subheader("Mots-clés (Top 12)")
    kw_df = keyword_counts(df_f)
    if kw_df.empty:
        st.info("Aucun mot-clé détecté avec les filtres actuels.")
    else:
        fig5, ax5 = plt.subplots(figsize=(5, 3.5))
        kw_df.head(12).set_index("keyword")["count"].plot(kind="bar", ax=ax5)
        ax5.set_xlabel("Mot-clé")
        ax5.set_ylabel("Occurrences")
        ax5.set_title("Capacités / effets (Top 12)")
        ax5.tick_params(axis='x', labelrotation=45)
        fig5.tight_layout()
        st.pyplot(fig5, clear_figure=True)
