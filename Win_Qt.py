import json
import os.path
import sys
import threading

import torch
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, \
    QLabel, QLineEdit, QMessageBox, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QPlainTextEdit
from PyQt5.QtGui import QPixmap
from colorama import Fore

from caption import qt_show
from utils import path_checker


class MainWindow(QMainWindow):
    def __init__(self, model_path, temp_path, word_map_path):
        global pre_image
        super().__init__()
        self.setWindowTitle("Image Caption")
        self.setMinimumSize(650, 500)  # 设置窗口的最小大小为 700x700
        self.pixmap = None
        self.model_path = model_path
        log_path = os.path.join(temp_path, "save_log.json")
        self.log_path = log_path

        self.word_map_path = word_map_path
        central_widget = QWidget()

        self.setCentralWidget(central_widget)

        # 创建布局管理器
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 输入框与生成文本按钮水平布局
        input_layout = QHBoxLayout()
        main_layout.addLayout(input_layout)
        train_layout = QHBoxLayout()
        main_layout.addLayout(train_layout)
        model_layout = QHBoxLayout()
        main_layout.addLayout(model_layout)

        self.input_path = QLineEdit()
        self.input_path.setText(pre_image)
        input_layout.addWidget(self.input_path)

        self.model_path_text = QLineEdit()
        self.model_path_text.setPlaceholderText("Enter model path...")
        model_layout.addWidget(self.model_path_text)

        self.predict_button = QPushButton('预测')
        input_layout.addWidget(self.predict_button)

        # 创建只读文本框
        self.running_train_time = QLineEdit()
        self.running_train_time.setReadOnly(True)  # 设置为只读
        self.running_train_time.setText("模型训练时间：00:00:00")
        # self.running_train_time.setFixedWidth(400)  # 设置固定宽度为200像素
        train_layout.addWidget(self.running_train_time)

        # 创建只读文本框
        self.model_train_time = QLineEdit()
        self.model_train_time.setReadOnly(True)  # 设置为只读
        self.model_train_time.setAlignment(Qt.AlignCenter)  # 设置文本居中显示
        self.model_train_time.setText("时间-批次：00:00:00—0")
        self.model_train_time.setFixedWidth(250)  # 设置固定宽度为200像素
        model_layout.addWidget(self.model_train_time)

        # 保存模型按钮
        self.button = QPushButton('保存模型')
        self.button.setFixedWidth(150)  # 设置固定宽度为200像素
        train_layout.addWidget(self.button)

        self.predict_button.clicked.connect(self.predict_image)
        self.button.clicked.connect(self.toggle_save_flag)
        self.model_path_text.textChanged.connect(self.text_changed_slot)

        # 结果标签
        self.result_label = QLabel()
        self.result_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.result_label)
        QTimer.singleShot(15000, self.set_train_time)

    def predict_image(self):
        image_path = self.input_path.text()

        if os.path.exists(image_path):
            self.predict_button.setEnabled(False)
            self.predict_button.setText("预测中...")
            model_path_text = self.model_path_text.text()

            def show_thread(model_path):
                qimage = qt_show(model_path, image_path, self.word_map_path)
                # 创建 QPixmap 并将 QImage 转换为 QPixmap
                self.pixmap = QPixmap.fromImage(qimage)
                self.result_label.setPixmap(self.pixmap)
                self.result_label.setScaledContents(True)  # 将图片缩放以填充 QLabel
                self.predict_button.setEnabled(True)
                self.predict_button.setText("预测")

            if model_path_text == "":
                show_t = threading.Thread(target=show_thread, args=(self.model_path,))
                show_t.start()
            elif not os.path.exists(model_path_text):
                self.predict_button.setEnabled(True)
                self.predict_button.setText("预测")
                QMessageBox.information(self, '提示', '模型不存在！', QMessageBox.Ok)
            else:
                show_t = threading.Thread(target=show_thread, args=(model_path_text,))
                show_t.start()

        else:
            QMessageBox.information(self, '提示', '图片不存在！', QMessageBox.Ok)

    def toggle_save_flag(self):
        # 将更新后的数据写入 log.json 文件
        log_data = {"save_flag": True,
                    "train_time": "00:00:00"}
        with open(self.log_path, "w") as file:
            json.dump(log_data, file)
        self.button.setEnabled(False)  # 设置按钮为不可点击状态
        self.predict_button.setEnabled(False)  # 设置按钮为不可点击状态
        # 创建定时器，在5秒后调用 update_message 方法
        msg_box_saving = QMessageBox()
        msg_box_saving.setText('模型保存中...')
        QTimer.singleShot(10000, lambda: self.save_recall(msg_box_saving))
        QTimer.singleShot(15000, self.button_reset)
        # 显示模型保存中提示
        msg_box_saving.exec_()

    def save_recall(self, msg_box_saving):
        save_flag = True
        try:
            with open(self.log_path, "r") as file:
                log_data = json.load(file)
                save_flag = log_data.get("save_flag", True)
                train_time = log_data.get("train_time", "00:00:00")
                self.running_train_time.setText("模型训练时间：" + train_time)
        except FileNotFoundError:
            pass
        # 根据保存结果显示不同的消息
        if not save_flag:
            msg_box_saving.setText('模型已保存！')
        else:
            msg_box_saving.setText('模型保存失败！')
        msg_box_saving.exec_()

        self.predict_button.setText("文件刷新中...")  # 设置按钮为不可点击状态

    def button_reset(self):
        self.button.setEnabled(True)
        self.predict_button.setText("预测")  # 设置按钮为不可点击状态
        self.predict_button.setEnabled(True)  # 设置按钮为不可点击状态

    def text_changed_slot(self, checkpoint):
        def text_thread(checkpoint):
            try:
                checkpoint = torch.load(checkpoint)
                train_time = checkpoint['train_time']
                number = checkpoint['number']
                self.model_train_time.setText(f"时间-批次：{train_time}—{number}")
            except Exception as e:
                print(Fore.YELLOW + "\nError loading model:", e)
            self.model_path_text.textChanged.connect(self.text_changed_slot)

        if os.path.exists(checkpoint):
            self.model_path_text.textChanged.disconnect(self.text_changed_slot)
            set_text = threading.Thread(target=text_thread, args=(checkpoint,))
            set_text.start()

    def set_train_time(self):
        try:
            with open(self.log_path, "r") as file:
                log_data = json.load(file)
                train_time = log_data.get("train_time", "00:00:00")
                self.running_train_time.setText("模型训练时间：" + train_time)
        except FileNotFoundError:
            pass


pre_image = 'datasets/img/img.png'

if __name__ == '__main__':
    datasets_name = 'coco'

    data_folder = f'out_data/{datasets_name}/out_hdf5/per_5_freq_5_maxlen_20'  # folder with data files saved by create_input_files.py
    data_name = f'{datasets_name}_5_cap_per_img_5_min_word_freq'  # base name shared by data files
    temp_path = f'out_data/{datasets_name}/save_model'

    log_path = os.path.join(temp_path, "save_log.json")
    checkpoint = r"out_data/coco/save_model/temp_checkpoint_coco_5_cap_per_img_5_min_word_freq_3318.pth"
    checkpoint, _, _ = path_checker(checkpoint, True, False)

    word_map_file = os.path.join(data_folder, 'WORDMAP_' + data_name + '.json')
    word_map_file = os.path.normpath(word_map_file)

    app = QApplication(sys.argv)
    filename = 'checkpoint_' + data_name + '_epoch_2' + '.pth'
    model_path = os.path.join(temp_path, filename)
    model_path, _, _ = path_checker(model_path, True, False)
    window = MainWindow(model_path, temp_path, word_map_file)
    window.show()

    sys.exit(app.exec_())
