import logging
import os
from logging.handlers import RotatingFileHandler as BaseRotatingFileHandler
import sys
from datetime import datetime

class UnicodeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream = sys.stdout if stream is sys.stderr else stream
            stream.buffer.write(msg.encode('utf-8'))
            stream.buffer.write(self.terminator.encode('utf-8'))
            self.flush()
        except Exception:
            self.handleError(record)

class RotatingFileHandler(BaseRotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=5*1024*1024, 
                 backupCount=5, encoding='utf-8', delay=False):
        # Crea la directory se non esiste
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Aggiungi timestamp al nome del file
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        super().__init__(
            filename, mode, maxBytes, backupCount, 
            encoding=encoding, delay=delay
        )

    def rotate(self, source, dest):
        """Comprime i file di log durante la rotazione"""
        import gzip
        with open(source, 'rb') as f_in:
            with gzip.open(f"{dest}.gz", 'wb') as f_out:
                f_out.writelines(f_in)
        if os.path.exists(source):
            os.remove(source) 