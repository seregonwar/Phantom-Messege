from PyQt6.QtGui import QColor

class Themes:
    DARK = {
        'background': '#2b2b2b',
        'foreground': '#ffffff',
        'accent': '#007acc',
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'button': {
            'background': '#007acc',
            'hover': '#0069d9',
            'pressed': '#0062cc',
            'text': '#ffffff'
        },
        'input': {
            'background': '#3c3c3c',
            'border': '#555555',
            'text': '#ffffff'
        },
        'progress': {
            'background': '#3c3c3c',
            'chunk': '#007acc'
        }
    }
    
    LIGHT = {
        'background': '#ffffff',
        'foreground': '#000000',
        'accent': '#0056b3',
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'button': {
            'background': '#0056b3',
            'hover': '#004494',
            'pressed': '#003d87',
            'text': '#ffffff'
        },
        'input': {
            'background': '#f8f9fa',
            'border': '#ced4da',
            'text': '#000000'
        },
        'progress': {
            'background': '#e9ecef',
            'chunk': '#0056b3'
        }
    }

def get_stylesheet(theme):
    return f"""
    QMainWindow {{
        background-color: {theme['background']};
        color: {theme['foreground']};
    }}
    
    QWidget {{
        background-color: {theme['background']};
        color: {theme['foreground']};
    }}
    
    QPushButton {{
        background-color: {theme['button']['background']};
        color: {theme['button']['text']};
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        background-color: {theme['button']['hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {theme['button']['pressed']};
    }}
    
    QTextEdit, QSpinBox, QComboBox {{
        background-color: {theme['input']['background']};
        color: {theme['input']['text']};
        border: 1px solid {theme['input']['border']};
        border-radius: 4px;
        padding: 4px;
    }}
    
    QProgressBar {{
        border: 1px solid {theme['input']['border']};
        border-radius: 4px;
        text-align: center;
        background-color: {theme['progress']['background']};
    }}
    
    QProgressBar::chunk {{
        background-color: {theme['progress']['chunk']};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {theme['input']['border']};
        border-radius: 4px;
    }}
    
    QTabBar::tab {{
        background-color: {theme['background']};
        color: {theme['foreground']};
        padding: 8px 16px;
        margin: 2px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {theme['button']['background']};
        color: {theme['button']['text']};
    }}
    """ 