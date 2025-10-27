"""
Utilitaire pour sauvegarder des documents générés (cours, exercices) en Markdown et PDF.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional
import markdown
from io import BytesIO
from xhtml2pdf import pisa
from fastapi.responses import Response
import re

from src.models.cours_models import CourseOutput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemin vers le logo Pixia
ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"


def course_output_to_markdown(course: CourseOutput) -> str:
    """
    Convertit un CourseOutput en format Markdown.
    
    Args:
        course: CourseOutput contenant le titre et les parties du cours
        
    Returns:
        str: Contenu Markdown formaté
    """
    md_content = f"# {course.title}\n\n"
    
    for idx, part in enumerate(course.parts, 1):
        # Titre de la partie
        md_content += f"## {idx}. {part.title}\n\n"
        
        # Contenu de la partie
        md_content += f"{part.content}\n\n"
        
        # Si un diagramme est présent
        if part.img_base64:
            md_content += f"### Diagramme - {part.title}\n\n"
            if part.schema_description:
                md_content += f"*{part.schema_description}*\n\n"
            # Référence à l'image (sera gérée lors de la conversion en PDF)
            md_content += f"![Diagramme {idx}](data:image/png;base64,{part.img_base64})\n\n"
        
        # Séparateur entre les parties
        if idx < len(course.parts):
            md_content += "---\n\n"
    
    return md_content


def save_markdown_to_file(markdown_content: str, output_path: Optional[str] = None) -> str:
    """
    Sauvegarde le contenu Markdown dans un fichier.
    
    Args:
        markdown_content: Contenu Markdown à sauvegarder
        output_path: Chemin du fichier de sortie (optionnel, sinon crée un fichier temporaire)
        
    Returns:
        str: Chemin du fichier créé
    """
    if output_path is None:
        # Créer un fichier temporaire
        fd, output_path = tempfile.mkstemp(suffix=".md", prefix="course_")
        os.close(fd)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    logger.info(f"[SAVE_FILES] ✅ Markdown sauvegardé: {output_path}")
    return output_path


def markdown_to_pdf(
    markdown_content: str,
    output_pdf_path: Optional[str] = None,
    add_logo: bool = True
) -> str:
    """
    Convertit du contenu Markdown en PDF avec le logo Pixia en haut à droite de chaque page.
    
    Args:
        markdown_content: Contenu Markdown à convertir
        output_pdf_path: Chemin du fichier PDF de sortie (optionnel, sinon crée un fichier temporaire)
        add_logo: Si True, ajoute le logo Pixia en haut à droite de chaque page
        
    Returns:
        str: Chemin du fichier PDF créé
    """
    if output_pdf_path is None:
        # Créer un fichier temporaire
        fd, output_pdf_path = tempfile.mkstemp(suffix=".pdf", prefix="course_")
        os.close(fd)
    
    # Obtenir la date et l'heure de génération
    from datetime import datetime
    generation_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
    
    # Convertir Markdown en HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['extra', 'tables', 'fenced_code', 'nl2br']
    )
    
    # Construire le HTML complet avec style CSS
    logo_base64 = ""
    generation_info = f"""
    <div class="generation-info" style="text-align: center; margin-bottom: 30px;">
        <p style="color: #7f8c8d; font-size: 9pt; font-style: italic; margin: 0;">
            Généré le {generation_date}
        </p>
    </div>
    """
    
    if add_logo and LOGO_PATH.exists():
        # Encoder le logo en base64 pour l'inclure dans le HTML
        import base64
        with open(LOGO_PATH, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')
    
    # Créer un template de page avec logo (sera répété sur chaque page)
    page_template = ""
    if logo_base64:
        page_template = f"""
        <div id="header_content" style="position: absolute; top: 0; right: 0; width: 100%; text-align: right; padding: 10px 20px;">
            <img src="data:image/png;base64,{logo_base64}" alt="Pixia" style="width: 100px; height: auto; opacity: 0.5;" />
        </div>
        """
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 2.5cm 2cm 2cm 2cm;
                
                @frame header {{
                    -pdf-frame-content: header_content;
                    top: 0.5cm;
                    margin-left: 2cm;
                    margin-right: 2cm;
                    height: 1.5cm;
                }}
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                font-size: 11pt;
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                font-size: 24pt;
                font-weight: 700;
                margin-top: 20px;
                page-break-after: avoid;
            }}
            
            h2 {{
                color: #34495e;
                margin-top: 30px;
                font-size: 18pt;
                font-weight: 600;
                page-break-after: avoid;
            }}
            
            h3 {{
                color: #7f8c8d;
                font-size: 14pt;
                font-weight: 600;
                page-break-after: avoid;
            }}
            
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }}
            
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                overflow-x: auto;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
                page-break-inside: avoid;
            }}
            
            hr {{
                border: none;
                border-top: 2px solid #ecf0f1;
                margin: 30px 0;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                page-break-inside: avoid;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: #3498db;
                color: white;
                font-weight: 600;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 20px;
                margin-left: 0;
                color: #555;
                font-style: italic;
            }}
            
            p {{
                margin: 10px 0;
                text-align: justify;
            }}
            
            ul, ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}
            
            li {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        {page_template}
        {generation_info}
        {html_content}
    </body>
    </html>
    """
    
    # Générer le PDF avec xhtml2pdf
    with open(output_pdf_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(
            src=full_html,
            dest=pdf_file,
            encoding='utf-8'
        )
        
        if hasattr(pisa_status, 'err') and pisa_status.err:
            logger.error(f"[SAVE_FILES] ❌ Erreur lors de la génération du PDF")
            raise Exception(f"Erreur PDF: {pisa_status.err}")
    
    logger.info(f"[SAVE_FILES] ✅ PDF généré: {output_pdf_path}")
    return output_pdf_path


def save_course_as_pdf(
    course: CourseOutput,
    output_pdf_path: Optional[str] = None,
    keep_markdown: bool = False
) -> tuple[str, Optional[str]]:
    """
    Convertit un CourseOutput en PDF complet avec logo Pixia.
    
    Args:
        course: CourseOutput à convertir
        output_pdf_path: Chemin du fichier PDF de sortie (optionnel)
        keep_markdown: Si True, conserve aussi le fichier Markdown temporaire
        
    Returns:
        tuple: (chemin_pdf, chemin_markdown_optionnel)
    """
    logger.info(f"[SAVE_FILES] 📄 Génération du PDF pour le cours: {course.title}")
    
    # 1. Convertir CourseOutput en Markdown
    markdown_content = course_output_to_markdown(course)
    
    # 2. Sauvegarder le Markdown (temporaire)
    md_path = save_markdown_to_file(markdown_content)
    
    # 3. Convertir en PDF
    pdf_path = markdown_to_pdf(markdown_content, output_pdf_path)
    
    # 4. Nettoyer le fichier Markdown si non demandé
    if not keep_markdown:
        try:
            os.unlink(md_path)
            md_path = None
        except Exception as e:
            logger.warning(f"[SAVE_FILES] ⚠️ Impossible de supprimer le Markdown temporaire: {e}")
    
    return pdf_path, md_path


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour le rendre valide sur tous les systèmes.
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        str: Nom de fichier nettoyé
    """
    # Remplacer les caractères invalides par des underscores
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limiter la longueur
    filename = filename[:200]
    # Supprimer les espaces en début et fin
    filename = filename.strip()
    return filename


def generate_course_pdf_response(course: CourseOutput) -> Response:
    """
    Génère un PDF à partir d'un CourseOutput et renvoie une Response FastAPI.
    Le PDF est généré en mémoire, aucun fichier n'est sauvegardé sur le disque.
    
    Args:
        course: CourseOutput à convertir en PDF
        
    Returns:
        Response: Response FastAPI avec le PDF et les headers de téléchargement
    """
    logger.info(f"[SAVE_FILES] 📄 Génération du PDF pour le front: {course.title}")
    
    # 1. Convertir CourseOutput en Markdown
    markdown_content = course_output_to_markdown(course)
    
    # 2. Obtenir la date et l'heure de génération
    from datetime import datetime
    generation_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
    
    # 3. Convertir Markdown en HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['extra', 'tables', 'fenced_code', 'nl2br']
    )
    
    # 4. Construire le HTML complet avec logo
    logo_base64 = ""
    generation_info = f"""
    <div class="generation-info" style="text-align: center; margin-bottom: 30px;">
        <p style="color: #7f8c8d; font-size: 9pt; font-style: italic; margin: 0;">
            Généré le {generation_date}
        </p>
    </div>
    """
    
    if LOGO_PATH.exists():
        import base64
        with open(LOGO_PATH, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')
    
    page_template = ""
    if logo_base64:
        page_template = f"""
        <div id="header_content" style="position: absolute; top: 0; right: 0; width: 100%; text-align: right; padding: 10px 20px;">
            <img src="data:image/png;base64,{logo_base64}" alt="Pixia" style="width: 100px; height: auto; opacity: 0.5;" />
        </div>
        """
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 2.5cm 2cm 2cm 2cm;
                
                @frame header {{
                    -pdf-frame-content: header_content;
                    top: 0.5cm;
                    margin-left: 2cm;
                    margin-right: 2cm;
                    height: 1.5cm;
                }}
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                font-size: 11pt;
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                font-size: 24pt;
                font-weight: 700;
                margin-top: 20px;
                page-break-after: avoid;
            }}
            
            h2 {{
                color: #34495e;
                margin-top: 30px;
                font-size: 18pt;
                font-weight: 600;
                page-break-after: avoid;
            }}
            
            h3 {{
                color: #7f8c8d;
                font-size: 14pt;
                font-weight: 600;
                page-break-after: avoid;
            }}
            
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }}
            
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                overflow-x: auto;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
                page-break-inside: avoid;
            }}
            
            hr {{
                border: none;
                border-top: 2px solid #ecf0f1;
                margin: 30px 0;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                page-break-inside: avoid;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: #3498db;
                color: white;
                font-weight: 600;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 20px;
                margin-left: 0;
                color: #555;
                font-style: italic;
            }}
            
            p {{
                margin: 10px 0;
                text-align: justify;
            }}
            
            ul, ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}
            
            li {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        {page_template}
        {generation_info}
        {html_content}
    </body>
    </html>
    """
    
    # 5. Générer le PDF en mémoire
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(
        src=full_html,
        dest=pdf_buffer,
        encoding='utf-8'
    )
    
    if hasattr(pisa_status, 'err') and pisa_status.err:
        logger.error(f"[SAVE_FILES] ❌ Erreur lors de la génération du PDF")
        raise Exception(f"Erreur PDF: {pisa_status.err}")
    
    # 6. Récupérer les bytes du PDF
    pdf_bytes = pdf_buffer.getvalue()
    
    # 7. Créer un nom de fichier valide à partir du titre du cours
    filename = sanitize_filename(course.title) + ".pdf"
    
    logger.info(f"[SAVE_FILES] ✅ PDF généré en mémoire: {filename} ({len(pdf_bytes)} bytes)")
    
    # 8. Retourner la Response FastAPI
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
