"""
Interface Streamlit pour l'analyseur de fiches techniques.
"""

import os
import sys
import io
import base64
import json
from datetime import datetime

import streamlit as st
from PIL import Image

# Importer nos modules
from config import TEMPLATES, get_template, DocumentTemplate, ControlPoint, CriticityLevel
from ocr_engine import OCREngine, OCRLanguageManager
from analyzer import (
    TechnicalDocumentAnalyzer, GroqDocumentAnalyzer, BatchAnalyzer,
    GEMINI_AVAILABLE, GROQ_AVAILABLE, create_analyzer
)
from report_generator import ReportGenerator, BatchReportGenerator

# Configuration de la page
st.set_page_config(
    page_title="Analyseur de Fiches Techniques",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stStatusConforme {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .stStatusDouteux {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .stStatusNonConforme {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialise les variables de session"""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'ocr_text' not in st.session_state:
        st.session_state.ocr_text = None
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = None


def sidebar_config():
    """Configuration dans la barre latérale"""
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Sélection du provider AI
        st.subheader("🔌 Provider AI")
        
        available_providers = []
        if GEMINI_AVAILABLE:
            available_providers.append("Gemini")
        if GROQ_AVAILABLE:
            available_providers.append("Groq (Gratuit)")
        
        if not available_providers:
            st.error("❌ Aucun provider AI n'est installé. Installez google-genai ou groq.")
            return None, None, None, None
        
        provider = st.selectbox(
            "Provider",
            options=available_providers,
            index=1 if "Groq" in available_providers else 0,
            help="Choisissez le provider AI. Groq est gratuit avec 1M tokens/jour!"
        )
        
        provider_key = "groq" if "Groq" in provider else "gemini"
        
        # Configuration selon le provider
        if provider_key == "groq":
            api_key = st.text_input(
                "🔑 Clé API Groq (Gratuite)",
                type="password",
                value=os.environ.get("GROQ_API_KEY", ""),
                help="Obtenez une clé gratuite sur https://console.groq.com - 1M tokens/jour!"
            )
            
            models = GroqDocumentAnalyzer.list_available_models()
            model = st.selectbox(
                "🤖 Modèle Groq",
                options=list(models.keys()),
                format_func=lambda k: models[k],
                index=0,
                help="Llama 3.3 70B recommandé pour la qualité"
            )
            
            if api_key:
                st.success("✅ Clé API Groq configurée")
                st.info("🎉 Gratuit: 1M tokens/jour!")
            else:
                st.warning("⚠️ Entrez votre clé API Groq (gratuite sur console.groq.com)")
        
        else:  # Gemini
            api_key = st.text_input(
                "🔑 Clé API Google Gemini",
                type="password",
                value=os.environ.get("GEMINI_API_KEY", ""),
                help="Votre clé API Gemini (obtenez-la sur https://makersuite.google.com/app/apikey)"
            )
            
            models = TechnicalDocumentAnalyzer.list_available_models()
            model = st.selectbox(
                "🤖 Modèle Gemini",
                options=list(models.keys()),
                format_func=lambda k: models[k],
                index=0,
                help="Modèle Gemini à utiliser pour l'analyse"
            )
            
            if api_key:
                st.success("✅ Clé API Gemini configurée")
            else:
                st.warning("⚠️ Entrez votre clé API Gemini")
        
        st.divider()
        
        # Configuration OCR
        st.subheader("🔍 Configuration OCR")
        
        ocr_language = st.selectbox(
            "Langue OCR",
            options=list(OCRLanguageManager.list_languages().keys()),
            format_func=OCRLanguageManager.get_language_name,
            index=0
        )
        
        ocr_dpi = st.slider("DPI", 150, 600, 300, 50, help="Résolution OCR (plus haut = plus précis mais plus lent)")
        ocr_contrast = st.slider("Contraste", 1.0, 3.0, 2.0, 0.1)
        ocr_threshold = st.slider("Seuil de binarisation", 100, 200, 160, 5)
        
        ocr_config = {
            'lang': ocr_language,
            'dpi': ocr_dpi,
            'contrast': ocr_contrast,
            'threshold': ocr_threshold,
            'preprocess': True,
            'grayscale': True
        }
        
        st.divider()
        
        # À propos
        st.markdown("---")
        st.markdown("**Version 2.0** - Analyseur modulaire")
        st.markdown("Développé pour l'analyse de fiches techniques")
    
    return api_key, model, ocr_config, provider_key


def render_template_selector():
    """Sélection du template"""
    st.header("📋 Sélection du type de document")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        template_key = st.selectbox(
            "Type de fiche technique",
            options=list(TEMPLATES.keys()),
            format_func=lambda k: f"{TEMPLATES[k].name} ({TEMPLATES[k].category})",
            help="Choisissez le type de document à analyser"
        )
        
        template = get_template(template_key)
        
        st.info(f"**{template.name}**\n\n{template.description}")
    
    with col2:
        with st.expander("Voir les points de contrôle"):
            for i, point in enumerate(template.control_points, 1):
                criticity_color = {
                    CriticityLevel.CRITIQUE: "🔴",
                    CriticityLevel.MAJEUR: "🟠",
                    CriticityLevel.MINEUR: "🟡"
                }.get(point.criticity, "⚪")
                
                st.markdown(f"{criticity_color} **{i}. {point.name}** ({point.criticity.value})")
                st.caption(f"_{point.description}_")
    
    return template


def render_single_analysis(template: DocumentTemplate, api_key: str, model: str, ocr_config: dict, provider: str):
    """Analyse d'un seul document"""
    st.header("📄 Analyse d'un document")
    
    uploaded_file = st.file_uploader(
        "Charger un PDF",
        type=['pdf'],
        help="Sélectionnez la fiche technique au format PDF"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"📁 Fichier: **{uploaded_file.name}**")
            st.caption(f"Taille: {uploaded_file.size / 1024:.1f} KB")
        
        with col2:
            if st.button("🚀 Lancer l'analyse", type="primary", use_container_width=True):
                if not api_key:
                    st.error("⚠️ Veuillez entrer votre clé API dans la barre latérale")
                    return
                
                with st.spinner("Extraction du texte (OCR)..."):
                    try:
                        ocr_engine = OCREngine(ocr_config)
                        pdf_bytes = uploaded_file.read()
                        ocr_text = ocr_engine.extract_text(pdf_bytes)
                        st.session_state.ocr_text = ocr_text
                        
                        with st.expander("Texte OCR extrait"):
                            st.text_area("", ocr_text[:3000] + "..." if len(ocr_text) > 3000 else ocr_text, height=200)
                    
                    except Exception as e:
                        st.error(f"Erreur OCR: {e}")
                        return
                
                with st.spinner("Analyse IA en cours..."):
                    try:
                        analyzer = create_analyzer(provider=provider, api_key=api_key, model=model)
                        result = analyzer.analyze(ocr_text, template)
                        
                        # Check for errors in result
                        if "error" in result:
                            st.error(f"❌ Erreur lors de l'analyse: {result['error']}")
                            if "raw_response" in result:
                                with st.expander("Voir la réponse brute"):
                                    st.code(result["raw_response"])
                            return
                        
                        st.session_state.analysis_result = result
                        st.success(f"✅ Analyse terminée! {result.get('summary', {}).get('total_points', 0)} points analysés")
                    
                    except Exception as e:
                        st.error(f"Erreur analyse: {e}")
                        import traceback
                        with st.expander("Détails de l'erreur"):
                            st.code(traceback.format_exc())
                        return
        
        # Afficher les résultats
        if st.session_state.analysis_result:
            render_analysis_results(st.session_state.analysis_result)


def render_analysis_results(result: dict):
    """Affiche les résultats d'analyse"""
    st.divider()
    st.header("📊 Résultats de l'analyse")
    
    # En-tête avec statut global
    status = result.get("global_status", "N/A")
    status_color = {
        "CONFORME": "green",
        "PARTIELLEMENT_CONFORME": "orange",
        "NON_CONFORME": "red"
    }.get(status, "gray")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Statut global", status)
    
    with col2:
        st.metric("Recommandation", result.get("global_recommendation", "N/A"))
    
    with col3:
        if "summary" in result:
            conformite_rate = result["summary"].get("conforme", 0) / result["summary"].get("total_points", 1) * 100
            st.metric("Taux de conformité", f"{conformite_rate:.1f}%")
    
    # Tableau des points de contrôle
    st.subheader("Points de contrôle détaillés")
    
    if "points" in result:
        # Créer un DataFrame pour l'affichage
        import pandas as pd
        
        df_data = []
        for point in result["points"]:
            df_data.append({
                "Point": point.get("name", ""),
                "Statut": point.get("status", ""),
                "Valeur trouvée": point.get("value_found", "") or "-",
                "Criticité": point.get("criticity", ""),
                "Recommandation": point.get("recommendation", "")
            })
        
        df = pd.DataFrame(df_data)
        
        # Appliquer des couleurs selon le statut
        def color_status(val):
            if val == "CONFORME":
                return 'background-color: #d4edda'
            elif val == "DOUTEUX":
                return 'background-color: #fff3cd'
            elif val == "NON_CONFORME":
                return 'background-color: #f8d7da'
            return ''
        
        styled_df = df.style.applymap(color_status, subset=['Statut'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Résumé
    if "summary" in result:
        st.subheader("Résumé")
        summary = result["summary"]
        
        cols = st.columns(4)
        cols[0].metric("Total points", summary.get("total_points", 0))
        cols[1].metric("✅ Conformes", summary.get("conforme", 0))
        cols[2].metric("⚠️ Douteux", summary.get("douteux", 0))
        cols[3].metric("❌ Non conformes", summary.get("non_conforme", 0))
        
        if summary.get("recommendations"):
            st.info(f"**Recommandations:** {summary['recommendations']}")
        
        if summary.get("critical_issues"):
            st.error("**Problèmes critiques:** " + ", ".join(summary["critical_issues"]))
    
    # Export des résultats
    st.divider()
    st.subheader("📥 Exporter le rapport")
    
    report_gen = ReportGenerator()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        pdf_buffer = report_gen.generate_pdf(result)
        st.download_button(
            label="📄 Télécharger PDF",
            data=pdf_buffer,
            file_name=f"rapport_analyse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        try:
            excel_buffer = report_gen.generate_excel(result)
            st.download_button(
                label="📊 Télécharger Excel",
                data=excel_buffer,
                file_name=f"rapport_analyse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except ImportError:
            st.button("📊 Excel (non disponible)", disabled=True, use_container_width=True)
    
    with col3:
        json_str = report_gen.generate_json(result)
        st.download_button(
            label="📋 Télécharger JSON",
            data=json_str,
            file_name=f"rapport_analyse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col4:
        markdown_str = report_gen.generate_markdown(result)
        st.download_button(
            label="📝 Télécharger Markdown",
            data=markdown_str,
            file_name=f"rapport_analyse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )


def render_batch_analysis(template: DocumentTemplate, api_key: str, model: str, ocr_config: dict, provider: str):
    """Analyse par lot de documents"""
    st.header("📁 Analyse par lot")
    
    uploaded_files = st.file_uploader(
        "Charger plusieurs PDFs",
        type=['pdf'],
        accept_multiple_files=True,
        help="Sélectionnez plusieurs fiches techniques"
    )
    
    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} fichier(s) sélectionné(s)")
        
        if st.button("🚀 Lancer l'analyse du lot", type="primary", use_container_width=True):
            if not api_key:
                st.error("⚠️ Veuillez entrer votre clé API")
                return
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            documents = []
            
            # Phase 1: OCR
            ocr_engine = OCREngine(ocr_config)
            
            for i, file in enumerate(uploaded_files):
                status_text.text(f"Extraction OCR: {file.name} ({i+1}/{len(uploaded_files)})")
                try:
                    pdf_bytes = file.read()
                    text = ocr_engine.extract_text(pdf_bytes)
                    documents.append({
                        "filename": file.name,
                        "text": text,
                        "metadata": {"size": file.size}
                    })
                except Exception as e:
                    st.error(f"Erreur OCR pour {file.name}: {e}")
                
                progress_bar.progress((i + 1) / (len(uploaded_files) * 2))
            
            # Phase 2: Analyse IA
            analyzer = create_analyzer(provider=provider, api_key=api_key, model=model)
            batch_analyzer = BatchAnalyzer(analyzer)
            
            results = batch_analyzer.analyze_multiple(documents, template)
            batch_results = batch_analyzer.generate_batch_report(results)
            
            st.session_state.batch_results = batch_results
            progress_bar.progress(1.0)
            status_text.text("Analyse terminée!")
            st.success("✅ Analyse du lot terminée!")
        
        # Afficher les résultats du lot
        if st.session_state.batch_results:
            render_batch_results(st.session_state.batch_results)


def render_batch_results(batch_results: dict):
    """Affiche les résultats d'analyse par lot"""
    st.divider()
    st.header("📊 Résultats du lot")
    
    if "batch_summary" in batch_results:
        summary = batch_results["batch_summary"]
        
        cols = st.columns(5)
        cols[0].metric("Documents", summary.get("total_documents", 0))
        cols[1].metric("✅ Conformes", summary.get("conforme", 0))
        cols[2].metric("⚠️ Partiels", summary.get("partiellement_conforme", 0))
        cols[3].metric("❌ Non conformes", summary.get("non_conforme", 0))
        cols[4].metric("Taux conformité", f"{summary.get('conformity_rate', 0):.1f}%")
    
    # Tableau détaillé
    if "documents" in batch_results:
        st.subheader("Détail par document")
        
        import pandas as pd
        
        df_data = []
        for doc in batch_results["documents"]:
            s = doc.get("summary", {})
            df_data.append({
                "Document": doc.get("filename", ""),
                "Statut": doc.get("global_status", ""),
                "Conformes": s.get("conforme", 0),
                "Douteux": s.get("douteux", 0),
                "Non conformes": s.get("non_conforme", 0)
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Export du rapport consolidé
    st.subheader("📥 Exporter le rapport consolidé")
    
    batch_gen = BatchReportGenerator()
    
    pdf_buffer = batch_gen.generate_consolidated_pdf(batch_results)
    st.download_button(
        label="📄 Télécharger rapport PDF consolidé",
        data=pdf_buffer,
        file_name=f"rapport_lot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )


def main():
    """Fonction principale"""
    init_session_state()
    
    # En-tête
    st.title("📄 Analyseur de Fiches Techniques")
    st.markdown("**Analysez vos documents techniques avec Google Gemini ou Groq AI** ✨")
    st.divider()
    
    # Configuration
    config_result = sidebar_config()
    if config_result is None:
        st.error("❌ Impossible de démarrer: aucun provider AI n'est installé")
        st.code("pip install groq", language="bash")
        return
    
    api_key, model, ocr_config, provider = config_result
    
    # Sélection du template
    template = render_template_selector()
    
    st.divider()
    
    # Onglets pour les différents modes
    tab1, tab2 = st.tabs(["📄 Analyse unique", "📁 Analyse par lot"])
    
    with tab1:
        render_single_analysis(template, api_key, model, ocr_config, provider)
    
    with tab2:
        render_batch_analysis(template, api_key, model, ocr_config, provider)
    
    # Pied de page
    st.divider()
    st.caption("Analyseur de Fiches Techniques v2.0 - Propulsé par Google Gemini & Groq AI")


if __name__ == "__main__":
    main()
