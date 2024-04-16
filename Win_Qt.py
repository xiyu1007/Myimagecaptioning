import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox
from config import save_flag

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Caption")
        self.setGeometry(100, 100, 300, 200)
        
        self.button = QPushButton('保存模型', self)
        self.button.setGeometry(50, 50, 200, 50)
       

        self.input_path = QLineEdit(self)
        self.input_path.setGeometry(50, 50, 300, 30)
        self.predict_button = QPushButton('生成文本', self)
        self.predict_button.setGeometry(50, 100, 100, 30)
    
        self.result_label = QLabel(self)
        self.result_label.setGeometry(50, 150, 300, 300)
        self.result_label.setScaledContents(True)  # 让图片适应label的大小
self.predict_button.clicked.connect(self.predict_image)
         self.button.clicked.connect(self.toggle_save_flag)
    def predict_image(self):
        image_path = self.input_path.text()
        processed_image = pre(image_path)
        pixmap = QPixmap(processed_image)
        self.result_label.setPixmap(pixmap)
    def toggle_save_flag(self):
        global save_flag
        save_flag = not save_flag
        QMessageBox.information(self, '提示', '模型已保存！', QMessageBox.Ok)
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())