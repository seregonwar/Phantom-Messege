from typing import Optional
from .base_parser import BaseSiteParser
from .ngl_parser import NGLParser
from .tellonym_parser import TellonymParser

class ParserFactory:
    _parsers = [NGLParser, TellonymParser]

    @classmethod
    def get_parser(cls, url: str) -> Optional[BaseSiteParser]:
        """Restituisce il parser appropriato per l'URL"""
        for parser_class in cls._parsers:
            if parser_class.can_handle_url(url):
                return parser_class(url)
        return None

    @classmethod
    def get_supported_sites(cls) -> list:
        """Restituisce la lista dei siti supportati"""
        supported_sites = []
        for parser in cls._parsers:
            supported_sites.extend(parser.get_supported_domains()) 