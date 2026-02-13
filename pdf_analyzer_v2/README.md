# 🔍 Analyseur de Fiches Techniques v2.0

Version améliorée et générique de l'analyseur de documents techniques avec interface Streamlit et **Google Gemini Pro**.

## ✨ Nouvelles fonctionnalités

- **🎨 Interface utilisateur Streamlit** - Interface web moderne et intuitive
- **📋 Templates configurables** - Supporte différents types de fiches techniques
- **🔍 OCR amélioré** - Configuration avancée du prétraitement d'image
- **📊 Exports multi-format** - PDF, Excel, JSON, CSV, Markdown
- **📁 Analyse par lot** - Traitement multiple de documents
- **🤖 Google Gemini Pro** - IA performante et économique

## 🚀 Installation

### Prérequis système

Installez Tesseract OCR sur votre système :

**Windows:**
```bash
# Téléchargez et installez depuis:
# https://github.com/UB-Mannheim/tesseract/wiki

# Ajoutez au PATH:
C:\Program Files\Tesseract-OCR
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-fra poppler-utils
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

### Installation Python

```bash
cd pdf_analyzer_v2
pip install -r requirements.txt
```

## 🎯 Utilisation

### 1. Lancer l'interface Streamlit

```bash
streamlit run app.py
```

L'interface sera accessible à l'adresse : `http://localhost:8501`

### 2. Configuration

Dans la barre latérale, configurez :
- **Clé API Gemini** : Votre clé API (obtenez-la gratuitement sur https://makersuite.google.com/app/apikey)
- **Modèle IA** : 
  - 🌟 **Gemini 3 Pro** (meilleur modèle multimodal, recommandé)
  - Gemini 2.0 Flash (rapide & puissant)
  - Gemini 1.5 Pro (qualité)
- **Paramètres OCR** : Langue, DPI, contraste, etc.

**Avantage Gemini** : L'API Gemini offre un généreux quota gratuit !

### 3. Analyser un document

1. **Sélectionnez le type de document** :
   - 🍽️ Agro-alimentaire
   - 🔌 Électronique
   - 🧪 Chimie (FDS)

2. **Chargez votre PDF**

3. **Cliquez sur "Lancer l'analyse"**

4. **Consultez les résultats** et exportez au format souhaité

## 📁 Structure du projet

```
pdf_analyzer_v2/
├── app.py                 # Interface Streamlit
├── config.py              # Templates et configuration
├── ocr_engine.py          # Moteur OCR
├── analyzer.py            # Analyseur IA
├── report_generator.py    # Générateur de rapports
├── requirements.txt       # Dépendances
└── README.md             # Documentation
```

## 🧩 Architecture modulaire

### Templates de documents

Le système utilise des templates configurables définis dans [`config.py`](config.py:1) :

```python
# Template agro-alimentaire existant
TEMPLATE_AGRO_ALIMENTAIRE

# Template électronique
TEMPLATE_ELECTRONIQUE

# Template chimie (FDS)
TEMPLATE_CHIMIE
```

### Créer un template personnalisé

```python
from config import DocumentTemplate, ControlPoint, CriticityLevel

mon_template = DocumentTemplate(
    name="Mon Type de Document",
    description="Description du document",
    category="ma_categorie",
    control_points=[
        ControlPoint(
            name="Nom du point",
            description="Description",
            criticity=CriticityLevel.CRITIQUE,
            synonyms=["synonyme1", "synonyme2"]
        ),
        # ... autres points
    ]
)
```

## 🔧 Configuration OCR

L'OCR est entièrement configurable via l'interface ou programmatiquement :

```python
from ocr_engine import OCREngine

config = {
    'dpi': 300,           # Résolution (150-600)
    'contrast': 2.0,      # Contraste (1.0-3.0)
    'sharpness': 1.5,     # Netteté
    'brightness': 1.0,    # Luminosité
    'threshold': 160,     # Seuil binarisation (0-255)
    'lang': 'fra',        # Langue OCR
    'preprocess': True,   # Activer le prétraitement
}

ocr = OCREngine(config)
text = ocr.extract_text(pdf_bytes)
```

## 📊 Formats d'export

| Format | Description | Utilisation |
|--------|-------------|-------------|
| **PDF** | Rapport formaté | Partage, archivage |
| **Excel** | Tableur avec onglets | Analyse, statistiques |
| **JSON** | Données brutes | Intégration API |
| **CSV** | Format tableur simple | Import dans d'autres outils |
| **Markdown** | Texte formaté | Documentation |

## 🚀 Analyse par lot

Traitez plusieurs documents simultanément :

1. Allez dans l'onglet **"📁 Analyse par lot"**
2. Sélectionnez plusieurs fichiers PDF
3. Lancez l'analyse
4. Téléchargez le rapport consolidé

## 🔌 API Programmatique

Utilisez les modules directement dans votre code :

```python
from config import get_template
from ocr_engine import OCREngine
from analyzer import TechnicalDocumentAnalyzer
from report_generator import ReportGenerator

# 1. Charger un template
template = get_template("agro")

# 2. Extraire le texte
ocr = OCREngine({'lang': 'fra', 'dpi': 300})
with open('document.pdf', 'rb') as f:
    text = ocr.extract_text(f.read())

# 3. Analyser avec Gemini
analyzer = TechnicalDocumentAnalyzer(
    api_key="votre_clé_gemini",
    model="gemini-1.5-pro"
)
result = analyzer.analyze(text, template)

# 4. Générer un rapport
report_gen = ReportGenerator()
pdf = report_gen.generate_pdf(result)
```

## 🔑 Obtenir une clé API Gemini

1. Allez sur https://makersuite.google.com/app/apikey
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Create API Key"
4. Copiez la clé et collez-la dans l'interface Streamlit

**C'est gratuit et immédiat !**

## ️ Développement

### Ajouter un nouveau template

Éditez [`config.py`](config.py:1) et ajoutez votre template au dictionnaire `TEMPLATES` :

```python
TEMPLATES = {
    "agro": TEMPLATE_AGRO_ALIMENTAIRE,
    "electronique": TEMPLATE_ELECTRONIQUE,
    "chimie": TEMPLATE_CHIMIE,
    "mon_nouveau": MON_NOUVEAU_TEMPLATE,  # Ajoutez ici
}
```

### Personnaliser l'interface

Modifiez [`app.py`](app.py:1) pour adapter l'interface à vos besoins.

## 📋 Comparaison avec v1.0

| Fonctionnalité | v1.0 | v2.0 |
|----------------|------|------|
| Interface | API Flask uniquement | Streamlit + API |
| Templates | Agro uniquement | Multi-domaines |
| OCR | Configuration fixe | Hautement configurable |
| Exports | PDF uniquement | PDF, Excel, JSON, CSV, Markdown |
| Analyse | Unitaire | Unitaire + Lot |
| IA | GPT-3.5 | GPT-4o, GPT-4o-mini, GPT-3.5 |
| Architecture | Monolithique | Modulaire |

## ⚠️ Notes importantes

- **Clé API requise** : Une clé Gemini valide est nécessaire (gratuit avec quota généreux)
- **Quota gratuit** : Gemini Pro offre 1M tokens/jour gratuitement!
- **Tesseract** : L'OCR nécessite Tesseract installé sur le système
- **Confidentialité** : Les documents sont envoyés à l'API Google, ne traitez pas de données sensibles

## 💰 Comparaison des coûts

| Service | Coût | Quota gratuit |
|---------|------|---------------|
| OpenAI GPT-4o | ~$5/M tokens | Très limité |
| **Google Gemini Pro** | **Gratuit** | **1M tokens/jour** |
| Google Gemini Flash | Gratuit | 1M tokens/jour |

## 🆘 Support

Pour toute question ou problème :
1. Vérifiez que Tesseract est correctement installé
2. Vérifiez votre clé API OpenAI
3. Consultez les logs dans le terminal

## 📄 Licence

Ce projet est fourni tel quel pour usage interne.
