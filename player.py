import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QListWidget, QListWidgetItem, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QUrl, QFile, QPropertyAnimation, QEasingCurve
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QColor, QPalette, QLinearGradient, QGradient

MUSIC_DIR = Path(__file__).parent / "music"

class AudioPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_player()
        self.setup_animations()
        self.load_music_folder(MUSIC_DIR)
        
    def setup_ui(self):
        loader = QUiLoader()
        file = QFile("player.ui")
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file, self)
        file.close()
        
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
       
        self.apply_shadow(self.ui.btnPlayPause, 20)
        self.apply_shadow(self.ui.btnNext, 10)
        self.apply_shadow(self.ui.btnPrev, 10)
        self.apply_shadow(self.ui.listWidget, 15)
        self.apply_shadow(self.ui.labelTrackName, 10)
        
       
        self.ui.centralwidget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a2e, stop:1 #16213e);
            border-radius: 15px;
        """)
        
        
        self.ui.btnPlayPause.clicked.connect(self.play_pause)
        self.ui.btnNext.clicked.connect(self.next_track)
        self.ui.btnPrev.clicked.connect(self.prev_track)
        self.ui.sliderPosition.sliderMoved.connect(self.seek)
        self.ui.sliderVolume.valueChanged.connect(self.change_volume)
        self.ui.listWidget.itemClicked.connect(self.on_playlist_item_clicked)
        self.ui.btnClose.clicked.connect(self.close)
        self.ui.btnMinimize.clicked.connect(self.showMinimized)
        
        self.ui.show()
        
    def apply_shadow(self, widget, blur_radius):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(100, 0, 150, 150))
        shadow.setOffset(0, 0)
        widget.setGraphicsEffect(shadow)
        
    def setup_player(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        
        self.ui.sliderVolume.setRange(0, 100)
        self.ui.sliderVolume.setValue(30)
        self.audio_output.setVolume(0.3)
        self.ui.sliderPosition.setRange(0, 0)
        
        self.update_labels(0, 0)
        
    def setup_animations(self):
        
        self.setup_button_animation(self.ui.btnPlayPause)
        self.setup_button_animation(self.ui.btnNext)
        self.setup_button_animation(self.ui.btnPrev)
        
      
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in.start()
        
    def setup_button_animation(self, button):
        effect = QGraphicsDropShadowEffect(button)
        effect.setColor(QColor(150, 50, 200))
        effect.setBlurRadius(0)
        effect.setOffset(0, 0)
        button.setGraphicsEffect(effect)
        
        self.anim = QPropertyAnimation(effect, b"blurRadius")
        self.anim.setDuration(200)
        button.enterEvent = lambda e: self.anim.start()
        button.leaveEvent = lambda e: self.anim.reverse()
        
    def load_music_folder(self, folder_path):
        if not folder_path.exists() or not folder_path.is_dir():
            print(f"Music folder not found: {folder_path}")
            return

        files = sorted([f for f in folder_path.iterdir() if f.suffix.lower() in [".mp3", ".wav", ".m4a"]])
        self.playlist = files
        self.current_index = 0 if files else -1
        self.update_playlist()

        if self.current_index >= 0:
            self.load_track(self.current_index, auto_play=False)

    def update_playlist(self):
        self.ui.listWidget.clear()
        for path in self.playlist:
            item = QListWidgetItem(path.stem)
            item.setToolTip(str(path))
            self.ui.listWidget.addItem(item)
            
    def on_playlist_item_clicked(self, item):
        index = self.ui.listWidget.row(item)
        self.load_track(index)

    def load_track(self, index, auto_play=True):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            path = self.playlist[index]
            url = QUrl.fromLocalFile(str(path))
            
            
            anim = QPropertyAnimation(self.ui.labelTrackName, b"geometry")
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.setStartValue(self.ui.labelTrackName.geometry())
            anim.setEndValue(self.ui.labelTrackName.geometry().adjusted(0, -10, 0, -10))
            anim.start()
            
            self.player.stop()
            self.player.setSource(QUrl())  
            self.player.setSource(url)
            self.ui.labelTrackName.setText(path.stem)
            self.ui.sliderPosition.setValue(0)
            self.update_labels(0, 0)
        
            for i in range(self.ui.listWidget.count()):
                item = self.ui.listWidget.item(i)
                item.setSelected(i == index)
                if i == index:
                    self.ui.listWidget.scrollToItem(item)
        
            if auto_play:
                self.play()
            else:
                self.pause()

    def play(self):
        self.player.play()
        self.is_playing = True
        
        self.ui.btnPlayPause.setText("PAUSE")  
        self.ui.btnPlayPause.setStyleSheet("""
        QPushButton {
            font-size: 28pt;
            padding: 7px;
            border: 3px solid #9c27b0;
            border-radius: 35px;
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #6a11cb, stop:1 #2575fc);
            color: white;
            font-weight: 650;
            font-family: "Montserrat", sans-serif;
        }
    """)
        
       

    def pause(self):
        self.player.pause()
        self.is_playing = False
        
        self.ui.btnPlayPause.setText("PLAY")  
        self.ui.btnPlayPause.setStyleSheet("""
        QPushButton {
            font-size: 28pt;
            padding: 7px;
            border: 3px solid #9c27b0;
            border-radius: 35px;
            background-color: #2d2d4d;
            color: #9c27b0;
            font-weight: 650;
            font-family: "Montserrat", sans-serif;
        }
        """)

    def play_pause(self):
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def next_track(self):
        if self.playlist:
            next_index = (self.current_index + 1) % len(self.playlist)
            self.load_track(next_index)
            
            

    def prev_track(self):
        if self.playlist:
            prev_index = (self.current_index - 1) % len(self.playlist)
            self.load_track(prev_index)
            
            anim = QPropertyAnimation(self.ui.labelTrackName, b"pos")
            anim.setDuration(300)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            
            anim.setEndValue(self.ui.labelTrackName.pos())
            anim.start()

    def seek(self, position):
        self.player.setPosition(position)

    def change_volume(self, value):
        volume = value / 100
        self.audio_output.setVolume(volume)
        
        
        self.ui.sliderVolume.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: #535353;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: #ffffff;
                border: none;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6a11cb, stop:1 #2575fc);
            }}
        """)

    def update_position(self, position):
        self.ui.sliderPosition.setValue(position)
        self.update_labels(position, self.player.duration())

    def update_duration(self, duration):
        self.ui.sliderPosition.setRange(0, duration)
        self.update_labels(self.player.position(), duration)

    def update_labels(self, position, duration):
        self.ui.labelTotalTime.setText(f"{self.ms_to_time(position)} / {self.ms_to_time(duration)}")

    def ms_to_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def media_status_changed(self, status):
        from PySide6.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_track()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        
    def closeEvent(self, event):
        self.player.stop()
        self.player.setSource(QUrl())
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
   
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(26, 26, 46))  
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(45, 45, 77))    
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 89))
    palette.setColor(QPalette.ToolTipBase, QColor(156, 39, 176))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(45, 45, 77))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 127))
    palette.setColor(QPalette.Highlight, QColor(106, 17, 203))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    player = AudioPlayer()
    sys.exit(app.exec())