"""Paleta e tipografia comuns da interface desktop."""

from PySide6.QtGui import QColor, QFont, QPalette


CORES = {
    "fundo": "#f4f6f5",
    "superficie": "#ffffff",
    "texto": "#20352e",
    "texto_placeholder": "#667770",
    "selecao": "#17634f",
    "texto_selecao": "#ffffff",
}


def aplicar_tema(aplicacao):
    """Define cores legíveis sem depender do tema do sistema operacional."""
    paleta = aplicacao.palette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(CORES["fundo"]))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(CORES["texto"]))
    paleta.setColor(QPalette.ColorRole.Base, QColor(CORES["superficie"]))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor("#f0f4f1"))
    paleta.setColor(QPalette.ColorRole.Text, QColor(CORES["texto"]))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor(CORES["texto_placeholder"]))
    paleta.setColor(QPalette.ColorRole.Button, QColor(CORES["superficie"]))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(CORES["texto"]))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(CORES["selecao"]))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(CORES["texto_selecao"]))
    aplicacao.setPalette(paleta)
    aplicacao.setFont(QFont("Segoe UI", 10))
    aplicacao.setStyleSheet("""
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit,
        QPlainTextEdit, QTableWidget, QTableView {
            color: #20352e;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit,
        QPlainTextEdit {
            selection-background-color: #17634f;
            selection-color: #ffffff;
        }
        QComboBox QAbstractItemView {
            color: #20352e;
            background: #ffffff;
            selection-background-color: #17634f;
            selection-color: #ffffff;
        }
        QHeaderView::section {
            min-height: 30px;
            padding: 0 8px;
            color: #20352e;
            background: #e8efeb;
            border: 0;
            border-bottom: 1px solid #bdcbc5;
        }
    """)