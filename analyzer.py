"""
Moteur d'analyse IA pour les fiches techniques - Utilise Google Gemini Pro
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import asdict

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from config import DocumentTemplate, ControlPoint, CriticityLevel

class TechnicalDocumentAnalyzer:
    """Analyseur de documents techniques basé sur Google Gemini Pro"""
    
    AVAILABLE_MODELS = {
        "gemini-2.0-flash": "Gemini 2.0 Flash (Rapide & Puissant)",
        "gemini-1.5-pro": "Gemini 1.5 Pro (Qualité)",
        "gemini-1.5-flash": "Gemini 1.5 Flash (Rapide)",
        "gemini-1.0-pro": "Gemini 1.0 Pro (Stable)",
    }
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai n'est pas installé. Lancez: pip install google-genai")
        
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Clé API Gemini requise. Définissez GEMINI_API_KEY.")
        
        # New API uses client-based approach
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model
        self.logger = logging.getLogger(__name__)
    
    def generate_prompt(self, template: DocumentTemplate) -> str:
        """Génère le prompt pour l'IA basé sur le template"""
        
        # Construire la liste des points de contrôle
        points_text = []
        for i, point in enumerate(template.control_points, 1):
            synonyms = ", ".join(point.synonyms) if point.synonyms else "Aucun"
            points_text.append(f"""
{i}. **{point.name}** (Criticité: {point.criticity.value})
   - Description: {point.description}
   - Synonymes à rechercher: {synonyms}
   - Requis: {'Oui' if point.required else 'Non'}
""")
        
        prompt = f"""
Tu es un expert en analyse de documents techniques. Tu dois analyser un {template.name} et vérifier la présence et la conformité des informations.

## DOCUMENT À ANALYSER
Catégorie: {template.category}
Description: {template.description}

## POINTS DE CONTRÔLE À VÉRIFIER
{chr(10).join(points_text)}

## INSTRUCTIONS D'ANALYSE

Pour chaque point de contrôle, tu dois fournir:

1. **Statut** (un des trois):
   - ✅ CONFORME: Information présente et conforme
   - ⚠️ DOUTEUX: Information partielle ou ambiguë
   - ❌ NON_CONFORME: Information absente ou non conforme

2. **Valeur trouvée**: Le texte ou la valeur exacte extraite du document

3. **Commentaire**: Brève explication si DOUTEUX ou NON_CONFORME

4. **Criticité**: Reprendre la criticité indiquée (Mineur/Majeur/Critique)

5. **Recommandation**:
   - VALIDER si CONFORME
   - DEMANDER_COMPLEMENT si DOUTEUX ou NON_CONFORME sur point Mineur/Majeur
   - REFUSER si NON_CONFORME sur point Critique

## RÈGLES IMPORTANTES

- Sois exhaustif: vérifie tous les points de contrôle
- Pour chaque point, cherche d'abord les synonymes listés
- Si une information est introuvable même avec les synonymes, marque NON_CONFORME
- Fournis des preuves concrètes (citations du texte) pour chaque statut
- Ne fais pas de suppositions, base-toi uniquement sur le texte fourni

## FORMAT DE RÉPONSE

Réponds en JSON avec cette structure exacte:

{{
    "document_type": "{template.name}",
    "analysis_date": "date du jour",
    "global_status": "CONFORME|PARTIELLEMENT_CONFORME|NON_CONFORME",
    "global_recommendation": "VALIDER|DEMANDER_COMPLEMENT|REFUSER",
    "points": [
        {{
            "name": "nom du point",
            "status": "CONFORME|DOUTEUX|NON_CONFORME",
            "value_found": "valeur extraite ou null",
            "comment": "explication ou null",
            "criticity": "Mineur|Majeur|Critique",
            "recommendation": "VALIDER|DEMANDER_COMPLEMENT|REFUSER"
        }}
    ],
    "summary": {{
        "total_points": nombre,
        "conforme": nombre,
        "douteux": nombre,
        "non_conforme": nombre,
        "critical_issues": ["liste des problèmes critiques"],
        "recommendations": "recommandation globale détaillée"
    }}
}}

## TEXTE DU DOCUMENT À ANALYSER

"""
        return prompt
    
    def analyze(self, text: str, template: DocumentTemplate) -> Dict[str, Any]:
        """Analyse un texte selon le template fourni avec Gemini"""
        
        prompt = self.generate_prompt(template)
        full_prompt = f"Tu es un système d'analyse documentaire expert. Tu réponds uniquement en JSON valide, sans texte additionnel.\n\n{prompt}\n\n{text}"
        
        try:
            # New API uses client.models.generate_content()
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4000,
                    response_mime_type="application/json"
                )
            )
            
            result_text = response.text
            result = json.loads(result_text)
            
            self.logger.info(f"Analyse terminée: {result['summary']['total_points']} points analysés")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Erreur parsing JSON: {e}")
            return {"error": "Format de réponse invalide", "raw_response": result_text if 'result_text' in locals() else "N/A"}
        except Exception as e:
            self.logger.error(f"Erreur analyse: {e}")
            return {"error": str(e)}
    
    @classmethod
    def list_available_models(cls) -> Dict[str, str]:
        """Liste les modèles Gemini disponibles"""
        return cls.AVAILABLE_MODELS
    
    def compare_documents(self, text1: str, text2: str, template: DocumentTemplate) -> Dict[str, Any]:
        """Compare deux versions d'un document"""
        
        analysis1 = self.analyze(text1, template)
        analysis2 = self.analyze(text2, template)
        
        # Comparer les résultats
        comparison = {
            "document_1": analysis1,
            "document_2": analysis2,
            "differences": []
        }
        
        if "points" in analysis1 and "points" in analysis2:
            for p1, p2 in zip(analysis1["points"], analysis2["points"]):
                if p1["status"] != p2["status"] or p1["value_found"] != p2["value_found"]:
                    comparison["differences"].append({
                        "point": p1["name"],
                        "doc1_status": p1["status"],
                        "doc1_value": p1["value_found"],
                        "doc2_status": p2["status"],
                        "doc2_value": p2["value_found"]
                    })
        
        return comparison

class BatchAnalyzer:
    """Analyse par lot de documents"""
    
    def __init__(self, analyzer: TechnicalDocumentAnalyzer):
        self.analyzer = analyzer
        self.logger = logging.getLogger(__name__)
    
    def analyze_multiple(self, documents: List[Dict[str, Any]], template: DocumentTemplate) -> List[Dict[str, Any]]:
        """Analyse plusieurs documents"""
        results = []
        
        for i, doc in enumerate(documents, 1):
            self.logger.info(f"Analyse du document {i}/{len(documents)}: {doc.get('filename', 'sans nom')}")
            
            result = self.analyzer.analyze(doc["text"], template)
            result["filename"] = doc.get("filename", f"document_{i}")
            result["metadata"] = doc.get("metadata", {})
            
            results.append(result)
        
        return results
    
    def generate_batch_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Génère un rapport consolidé pour un lot"""
        
        total_docs = len(results)
        conforme_count = sum(1 for r in results if r.get("global_status") == "CONFORME")
        non_conforme_count = sum(1 for r in results if r.get("global_status") == "NON_CONFORME")
        partial_count = total_docs - conforme_count - non_conforme_count
        
        # Collecter tous les problèmes critiques
        all_critical_issues = []
        for r in results:
            if "summary" in r and "critical_issues" in r["summary"]:
                all_critical_issues.extend(r["summary"]["critical_issues"])
        
        return {
            "batch_summary": {
                "total_documents": total_docs,
                "conforme": conforme_count,
                "partiellement_conforme": partial_count,
                "non_conforme": non_conforme_count,
                "conformity_rate": (conforme_count / total_docs * 100) if total_docs > 0 else 0
            },
            "critical_issues_summary": list(set(all_critical_issues)),
            "documents": results
        }
