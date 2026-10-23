from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor
import os
from pathlib import Path
from src.core.workers import LoginWorker

class LoginScreen(QWidget):
    login_successful = pyqtSignal()

    def __init__(self, supabase_client):
        super().__init__()
        self.supabase = supabase_client
        self.init_ui()

    def init_ui(self):
        # Layout principal centrado
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Contenedor del login tipo "Card"
        container = QWidget()
        container.setFixedWidth(400)
        container.setObjectName("LoginContainer")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setSpacing(20)
        
        title = QLabel()
        title.setObjectName("TitleLabel")
        local_assets = Path(__file__).resolve().parents[2] / "assets"
        info_logos = Path(__file__).resolve().parents[3] / "INFO PROYECTO" / "LOGOS"
        logo_path = None
        for d in [local_assets, info_logos]:
            for fname in ["logo_gryphus_nombre_sf.png", "logo_gryphus_nombre_sf.png", "logo_gryphus_circular_sf.png"]:
                p = d / fname
                if p.exists():
                    logo_path = str(p)
                    break
            if logo_path:
                break
            
        if logo_path:
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaledToWidth(250, Qt.TransformationMode.SmoothTransformation)
            title.setPixmap(scaled_pixmap)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("GryPhus Conect — Gerencia\nInicia sesión en tu cuenta corporativa")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        from PyQt6.QtCore import QSettings
        settings = QSettings("GryphusSystems", "GryPhusConectGerencia")
        saved_email = settings.value("auth/saved_email", "")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Correo electrónico")
        if saved_email:
            self.email_input.setText(saved_email)
        self.email_input.returnPressed.connect(self.handle_login)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.handle_login)
        
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.hide()
        
        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.setObjectName("PrimaryButton")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        
        from src.version import __version__
        footer_ver = QLabel(f"GryPhus Conect Gerencia v{__version__} • Gryphus Systems")
        footer_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_ver.setStyleSheet("font-size: 11px; color: #4A524E; padding-top: 10px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.error_label)
        layout.addSpacing(10)
        layout.addWidget(self.login_btn)
        layout.addWidget(footer_ver)
        
        main_layout.addWidget(container)
        if saved_email:
            self.password_input.setFocus()
        else:
            self.email_input.setFocus()

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            self.show_error("Por favor ingresa correo y contraseña.")
            return
            
        if not self.supabase:
            # Fallback para pruebas sin credenciales de Supabase
            if email == "test@accuratek.cl" and password == "test1234":
                self.login_successful.emit()
            else:
                self.show_error("Error: Cliente Supabase no configurado.")
            return
            
        self.error_label.hide()
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Iniciando...")
        
        self.worker = LoginWorker(self.supabase, email, password)
        self.worker.success.connect(self.on_login_success)
        self.worker.error.connect(self.on_login_error)
        self.worker.start()

    def on_login_success(self):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Iniciar Sesión")
        self.login_successful.emit()

    def on_login_error(self, message):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Iniciar Sesión")
        self.show_error(message)
            
    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()
