import sys
import os
import signal
import multiprocessing
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from loguru import logger
import atexit

from .ui.main_window import MainWindow
from .core.config import ConfigManager

def run_app():
    app = None
    window = None
    
    try:
        # Check for existing instance
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            
        app.setApplicationName("VipeDown")
        app.setApplicationVersion("0.1.0")

        config = ConfigManager()
        log_file = config.get_log_path() / "vipedown.log"

        logger.remove()
        logger.add(
            log_file,
            rotation="10 MB",
            retention="1 month",
            compression="gz",
            level="INFO"
        )
        logger.add(sys.stderr, level="ERROR")

        # Check for existing windows
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, MainWindow):
                widget.show()
                widget.raise_()
                widget.activateWindow()
                return app.exec()

        window = MainWindow()
        window.show()

        return app.exec()
    except Exception as e:
        logger.exception("Application error")
        return 1
    finally:
        try:
            if window:
                window.safe_quit()
            if app:
                app.quit()
        except:
            pass

def main():
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    
    app_process = multiprocessing.Process(target=run_app)
    app_process.daemon = True
    app_process.start()
    
    def cleanup_process():
        if app_process.is_alive():
            app_process.terminate()
            app_process.join(timeout=3)
            if app_process.is_alive():
                os.kill(app_process.pid, signal.SIGKILL)
    
    atexit.register(cleanup_process)
    
    try:
        app_process.join()
        return app_process.exitcode or 0
    except KeyboardInterrupt:
        cleanup_process()
        return 0
    except Exception as e:
        logger.exception("Process error")
        cleanup_process()
        return 1

if __name__ == '__main__':
    sys.exit(main())