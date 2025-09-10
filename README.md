# Draft Analysis – Spider-Man (SPM)

Tableau de bord **Streamlit** pour analyser le set *Spider-Man* (SPM).  
Les données proviennent de l'API **Scryfall**.

---

## 🚀 Déploiement (Option A – Streamlit Community Cloud)

1. Créez un dépôt GitHub (par ex. `draft-spiderman-analysis`).
2. Ajoutez ces fichiers :
   - `draft_analysis_spiderman.py`
   - `requirements.txt`
   - `.streamlit/config.toml` (optionnel)
   - `README.md`
3. Allez sur [Streamlit Cloud](https://share.streamlit.io/).
4. Connectez votre dépôt GitHub.
5. Choisissez le fichier principal : `draft_analysis_spiderman.py`.
6. Déployez → une URL publique est générée automatiquement 🎉

---

## ✅ Bonnes pratiques

- Ajoutez une attribution en bas de page :
  ```python
  st.caption("Card data & images © Scryfall — https://scryfall.com/ — used under their API guidelines.")
  ```
- Utilisez le cache (`@st.cache_data`) pour éviter trop d’appels API.
- Pour analyser un autre set, modifiez la requête dans `draft_analysis_spiderman.py` :
  ```python
  params = {"q": "set:spm"}  # remplacez spm par le code du set
  ```

---

## 📦 Installation locale (optionnel)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run draft_analysis_spiderman.py
```
