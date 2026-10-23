import sys
import os
import warnings

# Garantizar que el directorio de gryphus_conect_gerencia esté en sys.path sin importar desde dónde se ejecute
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from src.version import __version__, APP_USER_MODEL_ID
from src.core.updater import CheckUpdateWorker
from src.ui.update_dialog import UpdateDialog

# ── Icono en barra de tareas de Windows ────────────────────────────────────────
# Registrar el AppUserModelID ANTES de crear el QApplication.
# Sin esto, Windows muestra el icono genérico del bootloader de PyInstaller.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass
# ──────────────────────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use('QtAgg')
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QSize, QTimer, qInstallMessageHandler, QtMsgType
from PyQt6.QtGui import QIcon, QPixmap, QMovie
from dotenv import load_dotenv
from supabase import create_client, Client
from src.ui.login_screen import LoginScreen
from src.ui.main_view import MainView
from src.core.workers import SessionCheckWorker, LogoutWorker, FetchInitialBatchWorker

# Silenciar avisos no bloqueantes de Windows Winsock (WSAEWOULDBLOCK / 10035) y WM_DESTROY externos de Qt
warnings.filterwarnings("ignore", message=".*socket.*")
warnings.filterwarnings("ignore", message=".*desbloqueo.*")
warnings.filterwarnings("ignore", message=".*inmediat.*")

def qt_message_handler(mode, context, message):
    msg_lower = message.lower()
    if any(term in msg_lower for term in ["socket", "desbloqueo", "inmediat", "10035", "wsaewouldblock", "wm_destroy"]):
        return
    if mode == QtMsgType.QtWarningMsg:
        print(f"Qt Warning: {message}", file=sys.stderr)
    elif mode == QtMsgType.QtCriticalMsg:
        print(f"Qt Critical: {message}", file=sys.stderr)
    elif mode == QtMsgType.QtFatalMsg:
        print(f"Qt Fatal: {message}", file=sys.stderr)

qInstallMessageHandler(qt_message_handler)

# Load environment variables
env_candidates = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    os.path.join(os.getcwd(), ".env")
]
for env_file in env_candidates:
    if os.path.exists(env_file):
        load_dotenv(env_file)
        break
else:
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xkifhzhqgroemzudzxrf.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_Lbkl0KuLm8h2ZaPQAUM7VQ_PVTjSw7W")

# Initialize Supabase client
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_URL != "your_supabase_url_here" and SUPABASE_KEY and SUPABASE_KEY != "your_supabase_anon_key_here":
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Supabase: {e}")
else:
    print("Warning: Supabase credentials not found or are default placeholders in .env file.")

class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GryPhus Conect Gerencia - Control de Obras")
        
        # Set Window Icon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        possible_dirs = [
            os.path.join(base_dir, "assets"),
            os.path.join(os.path.dirname(base_dir), "INFO PROYECTO", "LOGOS")
        ]
        icon_path = None
        for d in possible_dirs:
            for fname in ["app_icon.ico", "logo_gryphus_circular_sf.png", "logo_gryphus_solo_sf.png", "logo_gryphus_circular_sf.png"]:
                p = os.path.join(d, fname)
                if os.path.exists(p):
                    icon_path = p
                    break
            if icon_path:
                break
                
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        self.resize(1200, 800)
        
        self.central_widget = QWidget()
        self.central_widget.setObjectName("MainCentralWidget")
        self.central_widget.setAutoFillBackground(True)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setAutoFillBackground(True)
        self.main_layout.addWidget(self.stacked_widget)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # ─────────────────────────────────────────────────────────────
        # 1. PANTALLA 1: SPLASH DE INICIO (Animación de Video + Línea Negra)
        # ─────────────────────────────────────────────────────────────
        self.splash_screen = QWidget()
        self.splash_screen.setStyleSheet("background-color: #FFFFFF;")
        splash_layout = QVBoxLayout(self.splash_screen)
        splash_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        splash_layout.setSpacing(16)

        self.anim_label = QLabel()
        self.anim_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        gif_candidates = [
            os.path.join(base_dir, "assets", "animacion_gryphus.gif"),
            os.path.join(base_dir, "assets", "animacion_gryphus.gif"),
            os.path.join(os.path.dirname(base_dir), "INFO PROYECTO", "LOGOS", "animacion_gryphus.gif"),
            os.path.join(base_dir, "assets", "logo_gryphus_nombre_sf.png")
        ]
        
        anim_path = next((p for p in gif_candidates if os.path.exists(p)), None)
        self.movie = None
        if anim_path and anim_path.endswith(".gif"):
            self.movie = QMovie(anim_path)
            self.movie.setScaledSize(QSize(480, 339))
            self.anim_label.setMovie(self.movie)
            self.movie.start()
        elif anim_path:
            pixmap = QPixmap(anim_path).scaledToWidth(260, Qt.TransformationMode.SmoothTransformation)
            self.anim_label.setPixmap(pixmap)
            
        splash_layout.addWidget(self.anim_label)

        # Pequeña línea negra de carga abajo (Splash inicial)
        self.splash_progress_bar = QProgressBar()
        self.splash_progress_bar.setFixedWidth(280)
        self.splash_progress_bar.setFixedHeight(3)
        self.splash_progress_bar.setRange(0, 100)
        self.splash_progress_bar.setValue(0)
        self.splash_progress_bar.setTextVisible(False)
        self.splash_progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #D8D5CD;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #3D523C;
                border-radius: 1px;
            }
        """)
        splash_layout.addWidget(self.splash_progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stacked_widget.addWidget(self.splash_screen)

        # ─────────────────────────────────────────────────────────────
        # 2. PANTALLA 2: CARGA DE DATOS TRAS LOGIN (Logo Estático + Línea Negra)
        # ─────────────────────────────────────────────────────────────
        self.data_pull_screen = QWidget()
        self.data_pull_screen.setStyleSheet("background-color: #F2EFE9;")
        data_pull_layout = QVBoxLayout(self.data_pull_screen)
        data_pull_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        data_pull_layout.setSpacing(20)

        # Logo Estático de Trabs
        self.static_logo_label = QLabel()
        self.static_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        static_logo_candidates = [
            os.path.join(base_dir, "assets", "logo_gryphus_nombre_sf.png"),
            os.path.join(base_dir, "assets", "logo_gryphus_nombre_sf.png"),
            os.path.join(os.path.dirname(base_dir), "INFO PROYECTO", "LOGOS", "logo_gryphus_nombre_sf.png"),
            os.path.join(base_dir, "assets", "logo_gryphus_circular_sf.png")
        ]
        static_logo_path = next((p for p in static_logo_candidates if os.path.exists(p)), None)
        if static_logo_path:
            pix = QPixmap(static_logo_path).scaledToWidth(240, Qt.TransformationMode.SmoothTransformation)
            self.static_logo_label.setPixmap(pix)
        data_pull_layout.addWidget(self.static_logo_label)

        # Pequeña línea negra de carga abajo (Carga de datos)
        self.data_progress_bar = QProgressBar()
        self.data_progress_bar.setFixedWidth(280)
        self.data_progress_bar.setFixedHeight(3)
        self.data_progress_bar.setRange(0, 100)
        self.data_progress_bar.setValue(0)
        self.data_progress_bar.setTextVisible(False)
        self.data_progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #D8D5CD;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #3D523C;
                border-radius: 1px;
            }
        """)
        data_pull_layout.addWidget(self.data_progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Subtítulo sutil de estado
        self.data_status_label = QLabel("Iniciando sincronización...")
        self.data_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.data_status_label.setStyleSheet("font-size: 11px; color: #4A524E;")
        data_pull_layout.addWidget(self.data_status_label)

        self.stacked_widget.addWidget(self.data_pull_screen)
        
        # ─────────────────────────────────────────────────────────────
        # CONTROL DE TEMPORIZADOR DEL SPLASH INICIAL (~5.8s)
        # ─────────────────────────────────────────────────────────────
        self.min_splash_ms = 5800
        self.splash_elapsed_ms = 0
        self.splash_finished = False
        self.session_valid = None  # None = comprobando, True = válida, False = inválida
        
        self.splash_timer = QTimer(self)
        self.splash_timer.setInterval(50)  # 20 FPS para animación fluida de la barra
        self.splash_timer.timeout.connect(self._on_splash_tick)
        self.splash_timer.start()
        
        self.init_screens()

        # Iniciar verificación de sesión guardada en segundo plano
        if supabase:
            self.session_check_worker = SessionCheckWorker(supabase)
            self.session_check_worker.valid.connect(self._on_session_check_valid)
            self.session_check_worker.invalid.connect(self._on_session_check_invalid)
            self.session_check_worker.start()
        else:
            self.session_valid = False

    def _on_session_check_valid(self):
        self.session_valid = True
        if self.splash_finished:
            self.start_initial_pull()

    def _on_session_check_invalid(self):
        self.session_valid = False
        if self.splash_finished:
            self.stacked_widget.setCurrentWidget(self.login_screen)

    def _on_splash_tick(self):
        self.splash_elapsed_ms += 50
        pct = min(100, int((self.splash_elapsed_ms / self.min_splash_ms) * 100))
        self.splash_progress_bar.setValue(pct)
        
        if self.splash_elapsed_ms >= self.min_splash_ms:
            self.splash_timer.stop()
            self.splash_finished = True
            if self.movie:
                self.movie.stop()
            
            if self.session_valid is True:
                self.start_initial_pull()
            elif self.session_valid is False:
                self.stacked_widget.setCurrentWidget(self.login_screen)
            # Si self.session_valid is None, _on_session_check_valid o invalid se encargará al terminar

    def init_screens(self):
        self.login_screen = LoginScreen(supabase)
        self.login_screen.login_successful.connect(self.start_initial_pull)
        
        self.main_view = MainView(supabase)
        self.main_view.logout_requested.connect(self.handle_logout)
        
        self.stacked_widget.addWidget(self.login_screen)
        self.stacked_widget.addWidget(self.main_view)
        
        # Iniciar en el splash screen con video
        self.stacked_widget.setCurrentWidget(self.splash_screen)

    def start_initial_pull(self):
        """Inicia el Pull Inicial con logo estático y barra de progreso tras el login."""
        self.stacked_widget.setCurrentWidget(self.data_pull_screen)
        self.data_progress_bar.setValue(0)
        self.data_status_label.setText("Cargando catálogo y obras...")

        if not supabase:
            self.go_to_main_app()
            return

        self.initial_pull_worker = FetchInitialBatchWorker(supabase, force_refresh=True)
        self.initial_pull_worker.progress.connect(self.update_pull_progress)
        self.initial_pull_worker.success.connect(self.finish_initial_pull)
        self.initial_pull_worker.error.connect(self.on_initial_pull_error)
        self.initial_pull_worker.start()

    def update_pull_progress(self, pct: int, msg: str):
        self.data_progress_bar.setValue(pct)
        self.data_status_label.setText(msg)

    def finish_initial_pull(self, data=None):
        self.go_to_main_app()

    def on_initial_pull_error(self, err_msg: str):
        print(f"Advertencia en pull inicial: {err_msg}")
        self.go_to_main_app()

    def go_to_main_app(self):
        self.stacked_widget.setCurrentWidget(self.main_view)
        # Refrescar vista actual utilizando los datos del caché inicial
        self.main_view.switch_view(self.main_view.content_stack.currentIndex())
        # Comprobar actualizaciones silenciosamente en segundo plano
        QTimer.singleShot(2500, self.check_updates_background)

    def check_updates_background(self):
        self.bg_update_checker = CheckUpdateWorker(parent=self)
        self.bg_update_checker.update_available.connect(self._on_background_update_available)
        self.bg_update_checker.start()

    def _on_background_update_available(self, data: dict):
        # Solo desplegar si el usuario se encuentra actualmente en la vista principal
        if self.stacked_widget.currentWidget() == self.main_view:
            dlg = UpdateDialog(data, parent=self)
            dlg.exec()

    def handle_logout(self):
        self.stacked_widget.setCurrentWidget(self.data_pull_screen)
        self.data_status_label.setText("Cerrando sesión...")
        self.data_progress_bar.setValue(100)
        self.logout_worker = LogoutWorker(supabase)
        self.logout_worker.finished.connect(self.go_to_login)
        self.logout_worker.start()

    def go_to_login(self):
        self.stacked_widget.setCurrentWidget(self.login_screen)

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide icon
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_candidates = [
        os.path.join(base_dir, "assets", "app_icon.ico"),
        os.path.join(base_dir, "assets", "logo_gryphus_solo_sf.png"),
        os.path.join(base_dir, "assets", "logo_gryphus_solo_sf.png"),
        os.path.join(base_dir, "assets", "logo_gryphus_circular_sf.png"),
        os.path.join(base_dir, "assets", "LOGO.png"),
        os.path.join(os.path.dirname(base_dir), "INFO PROYECTO", "LOGOS", "LOGO.png")
    ]
    icon_path = next((p for p in icon_candidates if os.path.exists(p)), None)
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    
    # Load QSS
    try:
        qss_path = os.path.join(os.path.dirname(__file__), "src", "ui", "style.qss")
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            print("Stylesheet style.qss loaded and applied successfully!")
    except Exception as e:
        print(f"Failed to load stylesheet: {e}")
        
    window = MainAppWindow()
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
