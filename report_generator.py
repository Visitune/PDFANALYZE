"""
Générateur de rapports multi-format.
"""

import io
import json
from typing import Dict, Any, List
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ReportGenerator:
    """Générateur de rapports d'analyse"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_pdf(self, analysis_result: Dict[str, Any], output_buffer: io.BytesIO = None) -> io.BytesIO:
        """Génère un rapport PDF"""
        
        if output_buffer is None:
            output_buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(output_buffer, pagesize=A4)
        elements = []
        
        # Titre
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("Rapport d'Analyse Documentaire", title_style))
        elements.append(Spacer(1, 20))
        
        # Informations générales
        info_data = [
            ["Type de document:", analysis_result.get("document_type", "N/A")],
            ["Date d'analyse:", analysis_result.get("analysis_date", datetime.now().strftime("%d/%m/%Y"))],
            ["Statut global:", analysis_result.get("global_status", "N/A")],
            ["Recommandation:", analysis_result.get("global_recommendation", "N/A")],
        ]
        info_table = Table(info_data, colWidths=[2.5*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 30))
        
        # Points de contrôle
        elements.append(Paragraph("Détail des points de contrôle", self.styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        if "points" in analysis_result:
            points_data = [["Point", "Statut", "Valeur", "Criticité", "Recommandation"]]
            
            for point in analysis_result["points"]:
                status = point.get("status", "N/A")
                status_color = self._get_status_color(status)
                
                points_data.append([
                    point.get("name", ""),
                    status,
                    point.get("value_found", "")[:100] + "..." if point.get("value_found") and len(point.get("value_found")) > 100 else (point.get("value_found") or ""),
                    point.get("criticity", ""),
                    point.get("recommendation", "")
                ])
            
            points_table = Table(points_data, colWidths=[1.5*inch, 0.9*inch, 2*inch, 0.9*inch, 1.2*inch])
            points_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]))
            elements.append(points_table)
        
        elements.append(Spacer(1, 30))
        
        # Résumé
        if "summary" in analysis_result:
            elements.append(Paragraph("Résumé", self.styles['Heading2']))
            summary = analysis_result["summary"]
            summary_text = f"""
            <b>Total des points:</b> {summary.get('total_points', 0)}<br/>
            <b>Conformes:</b> {summary.get('conforme', 0)}<br/>
            <b>Douteux:</b> {summary.get('douteux', 0)}<br/>
            <b>Non conformes:</b> {summary.get('non_conforme', 0)}<br/>
            """
            elements.append(Paragraph(summary_text, self.styles['Normal']))
            
            if summary.get('recommendations'):
                elements.append(Spacer(1, 10))
                elements.append(Paragraph("<b>Recommandations:</b>", self.styles['Normal']))
                elements.append(Paragraph(summary['recommendations'], self.styles['Normal']))
        
        doc.build(elements)
        output_buffer.seek(0)
        return output_buffer
    
    def generate_excel(self, analysis_result: Dict[str, Any]) -> io.BytesIO:
        """Génère un rapport Excel"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas est requis pour générer des fichiers Excel")
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille résumé
            summary_data = {
                'Type de document': [analysis_result.get('document_type', 'N/A')],
                'Date': [analysis_result.get('analysis_date', datetime.now().strftime("%d/%m/%Y"))],
                'Statut global': [analysis_result.get('global_status', 'N/A')],
                'Recommandation': [analysis_result.get('global_recommendation', 'N/A')],
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Résumé', index=False)
            
            # Feuille points de contrôle
            if 'points' in analysis_result:
                points_data = []
                for point in analysis_result['points']:
                    points_data.append({
                        'Point': point.get('name', ''),
                        'Statut': point.get('status', ''),
                        'Valeur trouvée': point.get('value_found', ''),
                        'Commentaire': point.get('comment', ''),
                        'Criticité': point.get('criticity', ''),
                        'Recommandation': point.get('recommendation', '')
                    })
                df_points = pd.DataFrame(points_data)
                df_points.to_excel(writer, sheet_name='Points de contrôle', index=False)
            
            # Feuille statistiques
            if 'summary' in analysis_result:
                stats = analysis_result['summary']
                stats_data = {
                    'Métrique': ['Total points', 'Conformes', 'Douteux', 'Non conformes'],
                    'Valeur': [
                        stats.get('total_points', 0),
                        stats.get('conforme', 0),
                        stats.get('douteux', 0),
                        stats.get('non_conforme', 0)
                    ]
                }
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='Statistiques', index=False)
        
        output.seek(0)
        return output
    
    def generate_json(self, analysis_result: Dict[str, Any]) -> str:
        """Génère un rapport JSON"""
        return json.dumps(analysis_result, indent=2, ensure_ascii=False)
    
    def generate_csv(self, analysis_result: Dict[str, Any]) -> str:
        """Génère un rapport CSV"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas est requis pour générer des fichiers CSV")
        
        if 'points' not in analysis_result:
            return ""
        
        points_data = []
        for point in analysis_result['points']:
            points_data.append({
                'document_type': analysis_result.get('document_type', ''),
                'analysis_date': analysis_result.get('analysis_date', ''),
                'global_status': analysis_result.get('global_status', ''),
                'point_name': point.get('name', ''),
                'status': point.get('status', ''),
                'value_found': point.get('value_found', ''),
                'criticity': point.get('criticity', ''),
                'recommendation': point.get('recommendation', '')
            })
        
        df = pd.DataFrame(points_data)
        return df.to_csv(index=False)
    
    def generate_markdown(self, analysis_result: Dict[str, Any]) -> str:
        """Génère un rapport Markdown"""
        lines = []
        
        lines.append("# Rapport d'Analyse Documentaire\n")
        lines.append(f"**Type:** {analysis_result.get('document_type', 'N/A')}\n")
        lines.append(f"**Date:** {analysis_result.get('analysis_date', datetime.now().strftime('%d/%m/%Y'))}\n")
        lines.append(f"**Statut global:** {analysis_result.get('global_status', 'N/A')}\n")
        lines.append(f"**Recommandation:** {analysis_result.get('global_recommendation', 'N/A')}\n")
        
        lines.append("\n## Points de contrôle\n")
        lines.append("| Point | Statut | Valeur | Criticité | Recommandation |")
        lines.append("|-------|--------|--------|-----------|----------------|")
        
        if 'points' in analysis_result:
            for point in analysis_result['points']:
                lines.append(
                    f"| {point.get('name', '')} | "
                    f"{point.get('status', '')} | "
                    f"{point.get('value_found', '') or '-'} | "
                    f"{point.get('criticity', '')} | "
                    f"{point.get('recommendation', '')} |"
                )
        
        if 'summary' in analysis_result:
            summary = analysis_result['summary']
            lines.append("\n## Résumé\n")
            lines.append(f"- **Total:** {summary.get('total_points', 0)}")
            lines.append(f"- **Conformes:** {summary.get('conforme', 0)}")
            lines.append(f"- **Douteux:** {summary.get('douteux', 0)}")
            lines.append(f"- **Non conformes:** {summary.get('non_conforme', 0)}")
            
            if summary.get('recommendations'):
                lines.append(f"\n### Recommandations\n{summary['recommendations']}")
        
        return "\n".join(lines)
    
    def _get_status_color(self, status: str) -> colors.Color:
        """Retourne la couleur associée à un statut"""
        status_colors = {
            "CONFORME": colors.green,
            "DOUTEUX": colors.orange,
            "NON_CONFORME": colors.red,
        }
        return status_colors.get(status, colors.black)


class BatchReportGenerator:
    """Générateur de rapports pour analyses par lot"""
    
    def __init__(self):
        self.generator = ReportGenerator()
    
    def generate_consolidated_pdf(self, batch_results: Dict[str, Any]) -> io.BytesIO:
        """Génère un rapport PDF consolidé pour un lot"""
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1f4788'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph("Rapport d'Analyse - Lot de Documents", title_style))
        elements.append(Spacer(1, 30))
        
        # Résumé du lot
        if 'batch_summary' in batch_results:
            summary = batch_results['batch_summary']
            elements.append(Paragraph("Résumé du lot", styles['Heading2']))
            
            summary_data = [
                ["Métrique", "Valeur"],
                ["Documents analysés", str(summary.get('total_documents', 0))],
                ["Conformes", str(summary.get('conforme', 0))],
                ["Partiellement conformes", str(summary.get('partiellement_conforme', 0))],
                ["Non conformes", str(summary.get('non_conforme', 0))],
                ["Taux de conformité", f"{summary.get('conformity_rate', 0):.1f}%"],
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
        
        # Liste des documents
        if 'documents' in batch_results:
            elements.append(Paragraph("Détail par document", styles['Heading2']))
            
            doc_data = [["Document", "Statut", "Points conformes", "Points douteux", "Points non conformes"]]
            
            for doc in batch_results['documents']:
                summary = doc.get('summary', {})
                doc_data.append([
                    doc.get('filename', 'Sans nom'),
                    doc.get('global_status', 'N/A'),
                    str(summary.get('conforme', 0)),
                    str(summary.get('douteux', 0)),
                    str(summary.get('non_conforme', 0))
                ])
            
            doc_table = Table(doc_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            doc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(doc_table)
        
        doc.build(elements)
        output.seek(0)
        return output
