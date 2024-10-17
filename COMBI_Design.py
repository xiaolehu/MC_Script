import sys
import cv2
import pyscreeze
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtCore import QTimer
from PySide6.QtGui import QClipboard
from COMBI import Ui_MainWindow
import pyautogui

# 创建主窗口类
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # 创建 UI 实例并将其设置为主窗口的界面
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 连接按钮信号到槽函数
        self.ui.clear.clicked.connect(self.clear_fields)
        self.ui.start.clicked.connect(self.start_detection)
        self.ui.stop.clicked.connect(self.stop_detection)
        self.ui.copy.clicked.connect(self.copy_to_clipboard)
        # 初始化定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_target)  # 每次超时后调用 check_target 方法

        self.image_path = None  # 存储上传的图片路径
        self.default_check_interval = 0  # 初始检查间隔时间，单位毫秒（默认1秒）
        self.current_check_interval = self.default_check_interval  # 当前检查间隔时间
        self.total_checks = 63  # 总共需要检测的次数
        self.current_check = 0  # 当前检测次数
        self.failed_checks = []  # 存储未检测到目标的检测次数
        self.first_success = False  # 是否成功完成第一次检测
        self.ui.stop.setEnabled(False)
        # 设置初始定时器间隔为默认值
        self.timer.setInterval(self.default_check_interval)

    def clear_fields(self):
        """清空所有文本框"""
        self.ui.Card38.clear()
        self.ui.Card44.clear()
        self.ui.Card46.clear()
        self.ui.Card48.clear()
        self.ui.Card49.clear()
        self.ui.Card50.clear()
        self.ui.Card51.clear()
        self.ui.Card53.clear()
        self.ui.Card54.clear()
        self.ui.Card56.clear()
        self.ui.Card57.clear()
        self.ui.Card59.clear()
        self.ui.Card61.clear()
        self.ui.Card65.clear()
        self.ui.Card68.clear()

    def start_detection(self):
        """开始检测的入口函数"""
        # 1. 检查 'Second' 的 LineEdit 是否有数字值，并且是正数
        second_text = self.ui.Second.text()
        try:
            interval_sec = float(second_text)
            if interval_sec <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for the waiting time (e.g., 2.6).")
            return

        # 2. 验证坐标输入
        coordinates_text = self.ui.coordinate.text()
        try:
            self.x, self.y = map(int, coordinates_text.split(","))
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid coordinates in the format 'x,y'.")
            return
        # 如果第一次没有上传图片或者用户强制选择新图片，则弹出文件选择框
        if not self.image_path:
            self.select_image_file()
        else:
            # 直接开始检测，不选择文件
            self.start_testing()
    def select_image_file(self):

        """选择目标图片并开始检测"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )

        if file_path:  # 如果选择了文件
            print(f"Selected file: {file_path}")
            self.image_path = file_path
            self.start_testing()  # 直接开始检测


    def start_testing(self):
        """开始检测流程"""
        self.current_check = 0  # 重置当前检测次数
        self.failed_checks.clear()  # 清空失败检查记录
        self.first_success = False  # 重置第一次成功标志
        self.ui.start.setEnabled(False)  # 禁用 start 按钮
        self.timer.setInterval(self.default_check_interval)  # 恢复默认的间隔时间
        self.timer.start(self.default_check_interval)  # 开始检测
        self.ui.stop.setEnabled(True)
    def check_target(self):
        """进行目标图片检测"""
        if not self.image_path:
            return

        target = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        if target is None:
            print(f"Error: Cannot open the image file at {self.image_path}.")
            return

        # 截图并处理
        pyscreeze.screenshot('my_screenshot.png')
        temp = cv2.imread('my_screenshot.png', cv2.IMREAD_GRAYSCALE)
        if temp is None:
            print("Error: Screenshot could not be captured.")
            return

        # 缩放屏幕截图
        screenScale = 1
        temp = cv2.resize(temp, (int(temp.shape[1] / screenScale), int(temp.shape[0] / screenScale)))

        # 匹配目标图片
        res = cv2.matchTemplate(temp, target, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        if max_val >= 0.9:
            # 第一次成功检测
            if not self.first_success:
                print(f"First success at check {self.current_check + 1}.")
                self.first_success = True

                # 从 `Second` 控件获取时间间隔，并转换为毫秒

                interval_sec = float(self.ui.Second.text())
                self.current_check_interval = int(interval_sec * 1000)  # 将秒数转换为毫秒
                self.timer.setInterval(self.current_check_interval)  # 设置新的检测间隔


            # 检测成功，继续后续检测
            print(f"Check {self.current_check + 1}: Success")
        else:
            if self.first_success:
                # 记录失败的检测
                self.failed_checks.append(self.current_check + 1)
                print(f"Check {self.current_check + 1}: Failed")

        # 无论成功或失败，执行两次点击操作

        if self.first_success:
            # 只有第一次成功后才增加检测次数
            pyautogui.doubleClick(self.x, self.y)
            self.current_check += 1

        # 检测是否已经完成了总检测次数
        if self.current_check >= self.total_checks:
            self.timer.stop()  # 停止定时器
            self.ui.start.setEnabled(True)  # 检测结束后重新启用 start 按钮
            # 获取 combobox 选项的值，移除空格并找到对应的 line edit
            selected_card = self.ui.comboBox.currentText().replace(" ", "")

            # 动态选择对应的 LineEdit 控件
            try:
                selected_line_edit = getattr(self.ui, selected_card)
            except AttributeError:
                QMessageBox.warning(self, "Error", f"Invalid target: {selected_card}")
                return

            # 检查是否有失败的检测点
            if self.failed_checks:
                # 将失败的检测次数填写到选中的 LineEdit 上
                formatted_failed_checks = [f'{check:02d}' for check in self.failed_checks]
                failed_times = ",".join(formatted_failed_checks)
                selected_line_edit.setText(failed_times)
            else:
                # 没有失败点，填写 '-'
                selected_line_edit.setText("-")

            QMessageBox.information(self, "Check Completed", "All test point checks have been completed.")
            self.ui.stop.setEnabled(False)


    def copy_to_clipboard(self):
        selected_card = self.ui.comboBox.currentText().replace(" ", "")

        try:
            selected_line_edit = getattr(self.ui, selected_card)
        except AttributeError:
            QMessageBox.warning(self,"Error", f'Invalid target:{selected_card}')

        text_to_copy = selected_line_edit.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(text_to_copy)


    def stop_detection(self):
        """停止检测"""
        self.timer.stop()
        self.ui.start.setEnabled(True)
        self.current_check = 0
        self.failed_checks.clear()
        self.first_success = False


if __name__ == "__main__":
    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()

    # 显示窗口
    window.show()

    # 运行应用程序
    sys.exit(app.exec())
