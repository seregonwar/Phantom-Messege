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
        min-width: 80px;
    }}
    
    QPushButton:hover {{
        background-color: {theme['button']['hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {theme['button']['pressed']};
    }}
    
    QPushButton:disabled {{
        background-color: {theme['input']['border']};
        color: {theme['input']['text']};
        opacity: 0.7;
    }}
    
    QTextEdit, QSpinBox, QComboBox, QLineEdit {{
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
        min-height: 20px;
    }}
    
    QProgressBar::chunk {{
        background-color: {theme['progress']['chunk']};
        border-radius: 3px;
    }}
    
    QGroupBox {{
        border: 1px solid {theme['group']['border']};
        border-radius: 6px;
        margin-top: 6px;
        padding-top: 10px;
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px;
        color: {theme['group']['title']};
    }}
    
    QTabWidget::pane {{
        border: 1px solid {theme['input']['border']};
        border-radius: 4px;
        top: -1px;
    }}
    
    QTabBar::tab {{
        background-color: {theme['tab']['inactive']};
        color: {theme['foreground']};
        padding: 8px 16px;
        margin: 2px;
        border: 1px solid {theme['input']['border']};
        border-radius: 4px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {theme['tab']['active']};
        color: {theme['button']['text']};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {theme['tab']['hover']};
    }}
    
    QSlider::groove:horizontal {{
        border: 1px solid {theme['input']['border']};
        height: 8px;
        background: {theme['progress']['background']};
        margin: 2px 0;
        border-radius: 4px;
    }}
    
    QSlider::handle:horizontal {{
        background: {theme['button']['background']};
        border: 1px solid {theme['button']['background']};
        width: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }}
    
    QSlider::handle:horizontal:hover {{
        background: {theme['button']['hover']};
        border: 1px solid {theme['button']['hover']};
    }}
    
    QMenuBar {{
        background-color: {theme['background']};
        color: {theme['foreground']};
        border-bottom: 1px solid {theme['input']['border']};
    }}
    
    QMenuBar::item:selected {{
        background-color: {theme['tab']['hover']};
    }}
    
    QMenu {{
        background-color: {theme['background']};
        color: {theme['foreground']};
        border: 1px solid {theme['input']['border']};
    }}
    
    QMenu::item:selected {{
        background-color: {theme['tab']['hover']};
    }}
    
    QStatusBar {{
        background-color: {theme['background']};
        color: {theme['foreground']};
        border-top: 1px solid {theme['input']['border']};
    }}
    """ 