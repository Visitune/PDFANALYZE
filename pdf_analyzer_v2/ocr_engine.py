"""
Moteur OCR modulaire avec prétraitement configurable.
"""

import io
import logging
import re
from typing import Optional, List, Dict, Any
from PIL import Image, ImageEnhance, ImageOps
from pdf2image import convert_from_bytes
import pytesseract


class PopplerNotFoundError(RuntimeError):
    """Exception raised when Poppler is not installed or not in PATH."""
    
    MESSAGE = (
        "POPPLER NOT FOUND: pdf2image requires Poppler to be installed and in PATH.\n\n"
        "Windows Installation:\n"
        "1. Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases\n"
        "2. Extract to C:\\Program Files\\poppler (or any folder)\n"
        "3. Add the 'bin' folder to your PATH (e.g., C:\\Program Files\\poppler\\Library\\bin)\n"
        "4. Restart VS Code/Terminal\n\n"
        "Ubuntu/Debian:\n"
        "  sudo apt-get install poppler-utils\n\n"
        "macOS:\n"
        "  brew install poppler"
    )
    
    def __init__(self, original_error=None):
        super().__init__(self.MESSAGE)
        self.original_error = original_error


def _handle_pdf2image_error(e: Exception) -> None:
    """Convertit les erreurs pdf2image en erreurs plus explicites."""
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
        images = []
        
        try:
            images = convert_from_bytes(
                pdf_data, 
                dpi=self.config['dpi']
            )
        except Exception as e:
            _handle_pdf2image_error(e)
        
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
        images = []
        
        try:
            images = convert_from_bytes(pdf_data, dpi=self.config['dpi'])
        except Exception as e:
            _handle_pdf2image_error(e)
        
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
