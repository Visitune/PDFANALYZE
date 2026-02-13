"""
Moteur OCR modulaire avec prétraitement configurable.
"""

import io
import logging
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image, ImageEnhance, ImageOps
from pdf2image import convert_from_bytes
import pytesseract


def get_poppler_path() -> Optional[str]:
    """
    Détecte automatiquement le chemin de Poppler.
    Cherche d'abord dans le dossier du projet, puis dans le PATH système.
    """
    # Chercher dans le dossier du projet (où se trouve ce fichier)
    current_dir = Path(__file__).parent.resolve()
    
    # Chercher un dossier poppler-* dans le projet
    for item in current_dir.iterdir():
        if item.is_dir() and item.name.startswith('poppler'):
            # Vérifier si le sous-dossier Library/bin existe
            poppler_bin = item / 'Library' / 'bin'
            if poppler_bin.exists():
                return str(poppler_bin)
            # ou directement bin
            poppler_bin2 = item / 'bin'
            if poppler_bin2.exists():
                return str(poppler_bin2)
    
    # Chercher aussi dans les sous-dossiers (pour les versions comme poppler-25.12.0)
    for pattern in ['**/poppler*/Library/bin', '**/poppler*/bin']:
        matches = list(current_dir.glob(pattern))
        if matches:
            return str(matches[0])
    
    return None


class PopplerNotFoundError(RuntimeError):
    """Exception raised when Poppler is not installed or not in PATH."""
    
    MESSAGE = (
        "POPPLER NOT FOUND: pdf2image requires Poppler to be installed.\n\n"
        "Option 1 - Auto-détection (recommandé):\n"
        "Placez le dossier Poppler dans le même dossier que l'application:\n"
        "  pdf_analyzer_v2/\n"
        "    ├── poppler-25.12.0/\n"
        "    │   └── Library/bin/\n"
        "    ├── ocr_engine.py\n"
        "    └── ...\n\n"
        "Option 2 - Installation système:\n"
        "Windows:\n"
        "1. Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases\n"
        "2. Extract to C:\\Program Files\\poppler\n"
        "3. Add C:\\Program Files\\poppler\\Library\\bin to your PATH\n"
        "4. Restart VS Code/Terminal\n\n"
        "Ubuntu/Debian:\n"
        "  sudo apt-get install poppler-utils\n\n"
        "macOS:\n"
        "  brew install poppler"
    )
    
    def __init__(self, original_error=None):
        super().__init__(self.MESSAGE)
        self.original_error = original_error


def convert_pdf_to_images(pdf_data: bytes, dpi: int = 300) -> List[Image.Image]:
    """
    Convertit un PDF en images en utilisant Poppler.
    Tente d'abord l'auto-détection, sinon utilise le PATH système.
    """
    poppler_path = get_poppler_path()
    
    # Si Poppler est trouvé dans le projet, l'ajouter au PATH système
    # pour que les DLLs soient trouvées sur Windows
    if poppler_path:
        import os
        current_path = os.environ.get('PATH', '')
        if poppler_path not in current_path:
            os.environ['PATH'] = poppler_path + os.pathsep + current_path
    
    try:
        if poppler_path:
            # Utiliser le Poppler trouvé dans le projet
            return convert_from_bytes(
                pdf_data,
                dpi=dpi,
                poppler_path=poppler_path
            )
        else:
            # Essayer avec le PATH système
            return convert_from_bytes(pdf_data, dpi=dpi)
    except Exception as e:
        error_msg = str(e).lower()
        if "poppler" in error_msg or "unable to get page count" in error_msg:
            raise PopplerNotFoundError(e) from e
        raise


class OCREngine:
    """Moteur OCR configurable"""
    
    DEFAULT_CONFIG = {
        'dpi': 300,
        'contrast': 2.0,
        'sharpness': 1.0,
        'brightness': 1.0,
        'threshold': 160,
        'lang': 'fra',
        'preprocess': True,
        'grayscale': True,
        'autocontrast': True,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.logger = logging.getLogger(__name__)
    
    def preprocess_image(self, img: Image.Image) -> Image.Image:
        """Applique le prétraitement d'image configuré"""
        config = self.config
        
        # Contraste
        if config['contrast'] != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(config['contrast'])
        
        # Netteté
        if config['sharpness'] != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(config['sharpness'])
        
        # Luminosité
        if config['brightness'] != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(config['brightness'])
        
        # Niveaux de gris
        if config['grayscale']:
            img = img.convert('L')
        
        # Autocontraste
        if config['autocontrast']:
            img = ImageOps.autocontrast(img)
        
        # Binarisation
        if config['threshold'] > 0:
            img = img.point(lambda x: 0 if x < config['threshold'] else 255, '1')
        
        return img
    
    def extract_text(self, pdf_data: bytes) -> str:
        """Extrait le texte d'un PDF via OCR"""
        text_parts = []
        
        # Conversion PDF -> Images (avec auto-détection Poppler)
        images = convert_pdf_to_images(pdf_data, dpi=self.config['dpi'])
        
        try:
            for idx, img in enumerate(images):
                self.logger.info(f"Traitement de la page {idx + 1}/{len(images)}")
                
                # Prétraitement
                if self.config['preprocess']:
                    img = self.preprocess_image(img)
                
                # OCR
                ocr_text = pytesseract.image_to_string(
                    img, 
                    lang=self.config['lang']
                )
                
                text_parts.append(ocr_text)
                self.logger.debug(f"Page {idx + 1}: {len(ocr_text)} caractères extraits")
                
        except Exception as e:
            self.logger.error(f"Erreur OCR: {e}")
            raise
        
        # Nettoyage
        text = "\n".join(text_parts)
        text = self.clean_text(text)
        
        return text
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Nettoie le texte OCR"""
        # Espaces multiples
        text = re.sub(r' +', ' ', text)
        # Lignes multiples
        text = re.sub(r'\n+', '\n', text)
        # Caractères spéciaux parasites
        text = re.sub(r'[^\w\s\-\(\)\[\]/\\.,:;@&%€$°\'\"]+', ' ', text)
        return text.strip()
    
    def extract_text_with_layout(self, pdf_data: bytes) -> List[Dict[str, Any]]:
        """Extrait le texte avec informations de mise en page"""
        pages = []
        
        # Conversion PDF -> Images (avec auto-détection Poppler)
        images = convert_pdf_to_images(pdf_data, dpi=self.config['dpi'])
        
        try:
            for idx, img in enumerate(images):
                if self.config['preprocess']:
                    img = self.preprocess_image(img)
                
                # OCR avec données de structure
                data = pytesseract.image_to_data(
                    img, 
                    lang=self.config['lang'],
                    output_type=pytesseract.Output.DICT
                )
                
                pages.append({
                    'page_num': idx + 1,
                    'ocr_data': data
                })
                
        except Exception as e:
            self.logger.error(f"Erreur OCR avec layout: {e}")
            raise
        
        return pages


class OCRLanguageManager:
    """Gestionnaire des langues OCR"""
    
    SUPPORTED_LANGS = {
        'fra': 'Français',
        'eng': 'Anglais',
        'deu': 'Allemand',
        'spa': 'Espagnol',
        'ita': 'Italien',
        'por': 'Portugais',
        'nld': 'Néerlandais',
        'eng+fra': 'Anglais + Français',
    }
    
    @classmethod
    def get_language_name(cls, code: str) -> str:
        return cls.SUPPORTED_LANGS.get(code, code)
    
    @classmethod
    def list_languages(cls) -> Dict[str, str]:
        return cls.SUPPORTED_LANGS
