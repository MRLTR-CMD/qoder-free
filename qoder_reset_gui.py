#!/usr/bin/env python3
"""
Qoder Reset Tool - 现代化GUI版本
使用PyQt5实现，完全按照用户原型图设计
"""

import os
import sys
import json
import uuid
import shutil
import hashlib
import subprocess
import webbrowser
import platform
from pathlib import Path
from datetime import datetime

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    print("错误: 未安装PyQt5")
    print("请运行: pip install PyQt5")
    sys.exit(1)

def get_qoder_data_dir():
    """获取Qoder数据目录的跨平台路径"""
    system = platform.system()
    home_dir = Path.home()
    
    if system == "Darwin":  # macOS
        return home_dir / "Library/Application Support/Qoder"
    elif system == "Windows":
        # Windows 上 Qoder 数据存储在 AppData\Roaming\Qoder
        appdata = os.getenv('APPDATA')
        if appdata:
            return Path(appdata) / "Qoder"
        else:
            return home_dir / "AppData/Roaming/Qoder"
    elif system == "Linux":
        # Linux 支持（如果需要的话）
        return home_dir / ".config/Qoder"
    else:
        # 默认路径
        return home_dir / "Qoder"

def check_process_running(process_name):
    """跨平台检查进程是否运行"""
    system = platform.system()
    
    try:
        if system == "Darwin" or system == "Linux":  # macOS/Linux
            result = subprocess.run(['pgrep', '-f', process_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                return True, pids
        
        elif system == "Windows":
            # 使用 tasklist 命令
            result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}*'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0 and process_name.lower() in result.stdout.lower():
                # 解析输出获取PID
                lines = result.stdout.strip().split('\n')
                pids = []
                for line in lines:
                    if process_name.lower() in line.lower():
                        parts = line.split()
                        if len(parts) >= 2:
                            pids.append(parts[1])  # PID 在第二列
                return True, pids
        
    except Exception as e:
        # 备用方案：使用 psutil（如果安装了）
        try:
            import psutil
            pids = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        pids.append(str(proc.info['pid']))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if pids:
                return True, pids
        except ImportError:
            pass
    
    return False, []

class QoderResetGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.system = platform.system()
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Qoder-Free")
        self.setFixedSize(800, 1000)
        self.setStyleSheet("background-color: white;")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)
        
        # 1. 标题
        title_label = QLabel("Qoder-Free")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: black;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 2. 说明文字
        intro_label = QLabel("Qoder-Free主要用于重置Qoder应用程序的用户身份信息")
        intro_label.setAlignment(Qt.AlignCenter)
        intro_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666666;
                margin-bottom: 20px;
            }
        """)
        main_layout.addWidget(intro_label)
        
        # 3. 操作区域标题
        operation_title = QLabel("操作区域:")
        operation_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: black;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(operation_title)
        
        # 4. 蓝色横幅按钮
        self.one_click_btn = QPushButton("一键修改配置")
        self.one_click_btn.setFixedSize(300, 40)  # 设置固定宽度300px，高度40px
        self.one_click_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
            QPushButton:pressed {
                background-color: #2851a3;
            }
        """)
        self.one_click_btn.clicked.connect(self.one_click_reset)
        
        # 将按钮居中显示
        button_center_layout = QHBoxLayout()
        button_center_layout.addStretch()
        button_center_layout.addWidget(self.one_click_btn)
        button_center_layout.addStretch()
        main_layout.addLayout(button_center_layout)
        
        # 5. 四个操作按钮（扩展为2x2布局）
        button_layout = QVBoxLayout()
        
        # 第一行按钮
        button_row1 = QHBoxLayout()
        button_row1.setSpacing(15)
        
        # 关闭Qoder按钮 (红色)
        self.close_qoder_btn = QPushButton("关闭Qoder")
        self.close_qoder_btn.setFixedSize(150, 40)
        self.close_qoder_btn.setStyleSheet("""
            QPushButton {
                background-color: #ea4335;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d33b2c;
            }
            QPushButton:pressed {
                background-color: #b52d20;
            }
        """)
        self.close_qoder_btn.clicked.connect(self.close_qoder)
        button_row1.addWidget(self.close_qoder_btn)
        
        # 重置机器ID按钮 (蓝色)
        self.reset_machine_id_btn = QPushButton("重置机器ID")
        self.reset_machine_id_btn.setFixedSize(150, 40)
        self.reset_machine_id_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
            QPushButton:pressed {
                background-color: #2851a3;
            }
        """)
        self.reset_machine_id_btn.clicked.connect(self.reset_machine_id)
        button_row1.addWidget(self.reset_machine_id_btn)
        
        button_layout.addLayout(button_row1)
        
        # 第二行按钮
        button_row2 = QHBoxLayout()
        button_row2.setSpacing(15)
        
        # 重置遥测数据按钮 (蓝色)
        self.reset_telemetry_btn = QPushButton("重置遥测数据")
        self.reset_telemetry_btn.setFixedSize(150, 40)
        self.reset_telemetry_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
            QPushButton:pressed {
                background-color: #2851a3;
            }
        """)
        self.reset_telemetry_btn.clicked.connect(self.reset_telemetry)
        button_row2.addWidget(self.reset_telemetry_btn)
        
        # 深度身份清理按钮 (橙色，新增)
        self.deep_clean_btn = QPushButton("深度身份清理")
        self.deep_clean_btn.setFixedSize(150, 40)
        self.deep_clean_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
            QPushButton:pressed {
                background-color: #e65100;
            }
        """)
        self.deep_clean_btn.clicked.connect(self.deep_identity_cleanup)
        button_row2.addWidget(self.deep_clean_btn)
        
        button_layout.addLayout(button_row2)
        main_layout.addLayout(button_layout)

        # 5.5. 保留对话记录勾选框
        self.preserve_chat_checkbox = QCheckBox("保留对话记录")
        self.preserve_chat_checkbox.setChecked(True)  # 默认勾选
        self.preserve_chat_checkbox.setStyleSheet("""
            QCheckBox {
                color: black;
                font-size: 12px;
                font-weight: bold;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #4285f4;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4285f4;
                border: 2px solid #4285f4;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #3367d6;
                border: 2px solid #3367d6;
            }
        """)

        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.preserve_chat_checkbox)
        checkbox_layout.addStretch()
        main_layout.addLayout(checkbox_layout)

        # 6. 操作日志区域
        log_title = QLabel("操作日志:")
        log_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: black;
                margin-top: 10px;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(log_title)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setFixedHeight(380)  # 设置固定高度以显示更多日志行
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #333333;
                border: 1px solid #dadce0;
                border-radius: 5px;
                font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)
        
        # 清空日志按钮 (右下角)
        clear_layout = QHBoxLayout()
        clear_layout.addStretch()
        
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.setFixedSize(100, 30)
        self.clear_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #9aa0a6;
                color: white;
                font-size: 11px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #80868b;
            }
            QPushButton:pressed {
                background-color: #5f6368;
            }
        """)
        self.clear_log_btn.clicked.connect(self.clear_log)
        clear_layout.addWidget(self.clear_log_btn)
        
        main_layout.addLayout(clear_layout)
        
        # 7. 底部GitHub链接
        github_btn = QPushButton("Github")
        github_btn.setFixedSize(120, 40)
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                font-size: 11px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
        """)
        github_btn.clicked.connect(self.open_github)
        
        github_layout = QHBoxLayout()
        github_layout.addStretch()
        github_layout.addWidget(github_btn)
        github_layout.addStretch()
        main_layout.addLayout(github_layout)
        
        # 添加初始日志
        self.log("Qoder-Free 重置工具已启动")
        self.log("=" * 50)
        self.initialize_status_check()
    
    def log(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_text.append(log_message)

        # 自动滚动到最新日志
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log("日志已清空")

    def initialize_status_check(self):
        """初始化时检查各项状态"""
        try:
            # 1. 检查Qoder进程状态
            self.log("1. 检查Qoder进程状态...")
            is_running, pids = self.check_qoder_running()
            if is_running:
                self.log(f"   ✅ Qoder正在运行 (PID: {', '.join(pids)})")
            else:
                self.log("   ✅ Qoder未运行")

            # 2. 检查Qoder目录
            self.log("2. 检查Qoder目录...")
            qoder_support_dir = get_qoder_data_dir()

            if qoder_support_dir.exists():
                self.log(f"   ✅ Qoder目录存在")

                # 3. 检查机器ID文件
                self.log("3. 检查机器ID文件...")
                machine_id_file = qoder_support_dir / "machineid"
                if machine_id_file.exists():
                    try:
                        with open(machine_id_file, 'r') as f:
                            current_id = f.read().strip()
                        self.log(f"   ✅ 机器ID: {current_id}")
                    except Exception as e:
                        self.log(f"   ❌ 读取机器ID失败: {e}")
                else:
                    self.log("   ❌ 机器ID文件不存在")

                # 4. 检查遥测数据文件
                self.log("4. 检查遥测数据文件...")
                storage_json_file = qoder_support_dir / "User/globalStorage/storage.json"
                if storage_json_file.exists():
                    try:
                        with open(storage_json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if 'telemetry.machineId' in data:
                            machine_id = data['telemetry.machineId']
                            self.log(f"   ✅ 遥测机器ID: {machine_id[:16]}...")
                        else:
                            self.log("   ⚠️  未找到遥测机器ID")

                        if 'telemetry.devDeviceId' in data:
                            device_id = data['telemetry.devDeviceId']
                            self.log(f"   ✅ 设备ID: {device_id}")
                        else:
                            self.log("   ⚠️  未找到设备ID")

                    except Exception as e:
                        self.log(f"   ❌ 读取遥测数据失败: {e}")
                else:
                    self.log("   ❌ 遥测数据文件不存在")

                # 5. 检查缓存目录
                self.log("5. 检查缓存目录...")
                cache_dirs = [
                    "Cache", "blob_storage", "Code Cache", "SharedClientCache",
                    "GPUCache", "DawnGraphiteCache", "DawnWebGPUCache"
                ]

                cache_count = 0
                for cache_dir in cache_dirs:
                    cache_path = qoder_support_dir / cache_dir
                    if cache_path.exists():
                        cache_count += 1

                self.log(f"   ✅ 发现 {cache_count}/{len(cache_dirs)} 个缓存目录")

                # 6. 检查对话记录相关目录
                self.log("6. 检查对话记录...")
                chat_dirs = [
                    "User/workspaceStorage", "User/History", "logs", "CachedData"
                ]

                chat_count = 0
                for chat_dir in chat_dirs:
                    chat_path = qoder_support_dir / chat_dir
                    if chat_path.exists():
                        chat_count += 1

                self.log(f"   ✅ 发现 {chat_count}/{len(chat_dirs)} 个对话相关目录")
                
                # 7. 检查身份识别文件（更新）
                self.log("7. 检查身份识别文件...")
                identity_files = [
                    "Local State",  # 包含加密密钥 - 新增
                    "Preferences",
                    "SharedStorage", 
                    "SharedStorage-wal"
                ]
                
                identity_count = 0
                for identity_file in identity_files:
                    file_path = qoder_support_dir / identity_file
                    if file_path.exists():
                        identity_count += 1
                
                # 检查 Network 目录中的身份文件
                network_dir = qoder_support_dir / "Network"
                network_identity_files = [
                    "Cookies", "Network Persistent State", "Trust Tokens", 
                    "TransportSecurity", "NetworkDataMigrated"
                ]
                network_count = 0
                if network_dir.exists():
                    for network_file in network_identity_files:
                        file_path = network_dir / network_file
                        if file_path.exists():
                            network_count += 1
                
                self.log(f"   ✅ 发现 {identity_count}/{len(identity_files)} 个根目录身份文件")
                self.log(f"   ✅ 发现 {network_count}/{len(network_identity_files)} 个网络身份文件")
                
                # 8. 检查 SharedClientCache 内部文件
                self.log("8. 检查 SharedClientCache 内部文件...")
                shared_cache = qoder_support_dir / "SharedClientCache"
                if shared_cache.exists():
                    critical_files = [".info", ".lock", "mcp.json"]
                    shared_count = 0
                    for file_name in critical_files:
                        if (shared_cache / file_name).exists():
                            shared_count += 1
                    
                    # 检查 index 目录
                    if (shared_cache / "index").exists():
                        shared_count += 1
                    
                    self.log(f"   ✅ SharedClientCache 内部文件: {shared_count}/4 个")
                else:
                    self.log("   ⚠️  SharedClientCache 目录不存在")

            else:
                self.log("   ❌ Qoder目录不存在")
                self.log("   请确保已安装Qoder应用程序")

            self.log("=" * 50)
            self.log("状态检查完成，可以开始操作")

        except Exception as e:
            self.log(f"❌ 状态检查失败: {e}")
            self.log("=" * 50)
    
    def check_qoder_running(self):
        """检查Qoder是否正在运行"""
        return check_process_running('Qoder')

    def close_qoder(self):
        """关闭Qoder"""
        self.log("正在检查 Qoder 运行状态...")

        is_running, pids = self.check_qoder_running()

        if is_running:
            self.log(f"检测到 Qoder 正在运行 (PID: {', '.join(pids)})")
            self.log("请手动关闭 Qoder 应用程序")
            QMessageBox.information(self, "检测到 Qoder 正在运行",
                                  f"检测到 Qoder 正在运行 (PID: {', '.join(pids)})\n\n"
                                  "请手动关闭 Qoder 应用程序：\n"
                                  "1. 使用 Cmd+Q 快捷键\n"
                                  "2. 或从菜单选择 Qoder → 退出 Qoder")
        else:
            self.log("Qoder 未运行")
            QMessageBox.information(self, "状态检查", "Qoder 当前未运行")

    def deep_identity_cleanup(self):
        """深度身份清理功能"""
        self.log("开始深度身份清理...")

        # 检查Qoder是否在运行
        is_running, pids = self.check_qoder_running()
        if is_running:
            reply = QMessageBox.question(self, "检测到 Qoder 正在运行",
                                       f"检测到 Qoder 正在运行 (PID: {', '.join(pids)})\n\n"
                                       "深度清理需要先关闭 Qoder。\n"
                                       "请手动关闭后点击'Yes'继续。",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.log("用户取消操作")
                return

            # 再次检查
            is_running, _ = self.check_qoder_running()
            if is_running:
                self.log("Qoder 仍在运行，操作取消")
                QMessageBox.critical(self, "错误", "请先完全关闭 Qoder 应用程序")
                return

        # 确认操作
        reply = QMessageBox.question(self, "确认深度清理",
                                   f"深度身份清理将：\n\n"
                                   f"• 清除所有网络状态和 Cookie\n"
                                   f"• 清除所有本地存储数据\n"
                                   f"• 清除 SharedClientCache 内部文件\n"
                                   f"• 清除系统级别身份文件\n"
                                   f"• 清除崩溃报告和缓存数据\n\n"
                                   f"这是最强力的身份重置，确定继续吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            self.log("用户取消深度清理")
            return

        try:
            qoder_support_dir = get_qoder_data_dir()
            
            if not qoder_support_dir.exists():
                raise Exception("未找到 Qoder 应用数据目录")
            
            self.log("=" * 40)
            self.log("开始深度身份清理")
            self.log("=" * 40)
            
            # 执行高级身份清理
            self.perform_advanced_identity_cleanup(qoder_support_dir)
            
            self.log("=" * 40)
            self.log("深度身份清理完成！")
            self.log("=" * 40)
            
            QMessageBox.information(self, "完成", "深度身份清理完成！\n现在可以重新启动 Qoder。")
            
        except Exception as e:
            self.log(f"深度清理失败: {e}")
            QMessageBox.critical(self, "错误", f"深度清理失败: {e}")

    def reset_machine_id(self):
        """重置机器ID"""
        self.log("开始重置机器ID...")

        # 检查Qoder是否在运行
        is_running, _ = self.check_qoder_running()
        if is_running:
            self.log("错误: Qoder 正在运行，请先关闭")
            QMessageBox.critical(self, "错误", "请先关闭 Qoder 应用程序")
            return

        try:
            qoder_support_dir = get_qoder_data_dir()
            machine_id_file = qoder_support_dir / "machineid"

            if not qoder_support_dir.exists():
                raise Exception("未找到 Qoder 应用数据目录")

            if machine_id_file.exists():
                new_machine_id = str(uuid.uuid4())
                with open(machine_id_file, 'w') as f:
                    f.write(new_machine_id)
                self.log(f"机器ID已重置为: {new_machine_id}")
                QMessageBox.information(self, "成功", "机器ID重置完成")
            else:
                self.log("未找到机器ID文件")
                QMessageBox.warning(self, "警告", "未找到机器ID文件")

        except Exception as e:
            self.log(f"重置机器ID失败: {e}")
            QMessageBox.critical(self, "错误", f"重置机器ID失败: {e}")

    def reset_telemetry(self):
        """重置遥测数据"""
        self.log("开始重置遥测数据...")

        # 检查Qoder是否在运行
        is_running, _ = self.check_qoder_running()
        if is_running:
            self.log("错误: Qoder 正在运行，请先关闭")
            QMessageBox.critical(self, "错误", "请先关闭 Qoder 应用程序")
            return

        try:
            qoder_support_dir = get_qoder_data_dir()
            storage_json_file = qoder_support_dir / "User/globalStorage/storage.json"

            if not storage_json_file.exists():
                raise Exception("未找到遥测数据文件")

            with open(storage_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 生成新的遥测ID
            new_uuid = str(uuid.uuid4())
            machine_id_hash = hashlib.sha256(new_uuid.encode()).hexdigest()
            device_id = str(uuid.uuid4())

            data['telemetry.machineId'] = machine_id_hash
            data['telemetry.devDeviceId'] = device_id

            with open(storage_json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self.log("遥测数据已重置")
            self.log(f"新遥测机器ID: {machine_id_hash[:16]}...")
            self.log(f"新设备ID: {device_id}")
            QMessageBox.information(self, "成功", "遥测数据重置完成")

        except Exception as e:
            self.log(f"重置遥测数据失败: {e}")
            QMessageBox.critical(self, "错误", f"重置遥测数据失败: {e}")

    def one_click_reset(self):
        """一键修改所有配置"""
        self.log("开始一键修改所有配置...")

        # 检查Qoder是否在运行
        is_running, pids = self.check_qoder_running()
        if is_running:
            reply = QMessageBox.question(self, "检测到 Qoder 正在运行",
                                       f"检测到 Qoder 正在运行 (PID: {', '.join(pids)})\n\n"
                                       "一键修改需要先关闭 Qoder。\n"
                                       "请手动关闭后点击'Yes'继续。",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.log("用户取消操作")
                return

            # 再次检查
            is_running, _ = self.check_qoder_running()
            if is_running:
                self.log("Qoder 仍在运行，操作取消")
                QMessageBox.critical(self, "错误", "请先完全关闭 Qoder 应用程序")
                return

        # 确认操作
        preserve_chat = self.preserve_chat_checkbox.isChecked()
        chat_action = "保留对话记录" if preserve_chat else "清除对话记录"

        reply = QMessageBox.question(self, "确认一键修改",
                                   f"一键修改所有配置将：\n\n"
                                   f"• 重置机器ID\n"
                                   f"• 重置遥测数据\n"
                                   f"• 清理缓存数据\n"
                                   f"• 清理身份识别文件 (Cookies, 网络状态等)\n"
                                   f"• 执行高级身份清理 (SharedClientCache 等)\n"
                                   f"• {chat_action}\n\n"
                                   f"这是最全面的重置方案，确定继续吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            self.log("用户取消一键修改")
            return

        try:
            self.log("=" * 40)
            self.log("开始一键修改所有配置")
            self.log("=" * 40)

            # 执行重置操作
            preserve_chat = self.preserve_chat_checkbox.isChecked()
            self.perform_full_reset(preserve_chat)

            self.log("=" * 40)
            self.log("一键修改完成！")
            self.log("=" * 40)

            QMessageBox.information(self, "完成", "一键修改所有配置完成！\n现在可以重新启动 Qoder。")

        except Exception as e:
            self.log(f"一键修改失败: {e}")
            QMessageBox.critical(self, "错误", f"一键修改失败: {e}")

    def perform_full_reset(self, preserve_chat=True):
        """执行完整重置"""
        qoder_support_dir = get_qoder_data_dir()

        if not qoder_support_dir.exists():
            raise Exception("未找到 Qoder 应用数据目录")

        # 1. 重置机器ID
        self.log("1. 重置机器ID...")
        machine_id_file = qoder_support_dir / "machineid"
        if machine_id_file.exists():
            new_machine_id = str(uuid.uuid4())
            with open(machine_id_file, 'w') as f:
                f.write(new_machine_id)
            self.log("   机器ID已重置")

        # 2. 重置遥测数据
        self.log("2. 重置遥测数据...")
        storage_json_file = qoder_support_dir / "User/globalStorage/storage.json"
        if storage_json_file.exists():
            with open(storage_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            new_uuid = str(uuid.uuid4())
            machine_id_hash = hashlib.sha256(new_uuid.encode()).hexdigest()
            device_id = str(uuid.uuid4())

            data['telemetry.machineId'] = machine_id_hash
            data['telemetry.devDeviceId'] = device_id

            with open(storage_json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self.log("   遥测数据已重置")

        # 3. 清理缓存
        self.log("3. 清理缓存数据...")
        cache_dirs = [
            "Cache", "blob_storage", "Code Cache", "SharedClientCache",
            "GPUCache", "DawnGraphiteCache", "DawnWebGPUCache"
        ]

        cleaned = 0
        for cache_dir in cache_dirs:
            cache_path = qoder_support_dir / cache_dir
            if cache_path.exists():
                try:
                    shutil.rmtree(cache_path)
                    cleaned += 1
                except:
                    pass

        self.log(f"   已清理 {cleaned} 个缓存目录")
        
        # 4. 清理身份识别文件（新增）
        self.log("4. 清理身份识别文件...")
        identity_files = [
            "Network Persistent State",
            "Cookies", "Cookies-journal",
            "SharedStorage", "SharedStorage-wal",
            "Trust Tokens", "Trust Tokens-journal",
            "TransportSecurity",
            "Preferences",
            "Local State",  # 包含加密密钥，极其重要！
            "NetworkDataMigrated"  # 网络数据迁移标记
        ]
        
        identity_cleaned = 0
        for identity_file in identity_files:
            file_path = qoder_support_dir / identity_file
            if file_path.exists():
                try:
                    file_path.unlink()
                    self.log(f"   已清除: {identity_file}")
                    identity_cleaned += 1
                except Exception as e:
                    self.log(f"   清除失败 {identity_file}: {e}")
        
        # 专门处理 Network 目录中的文件
        network_dir = qoder_support_dir / "Network"
        if network_dir.exists():
            network_files = [
                "Cookies", "Cookies-journal", 
                "Network Persistent State",
                "NetworkDataMigrated",
                "TransportSecurity",
                "Trust Tokens", "Trust Tokens-journal"
            ]
            for network_file in network_files:
                file_path = network_dir / network_file
                if file_path.exists():
                    try:
                        file_path.unlink()
                        self.log(f"   已清除: Network/{network_file}")
                        identity_cleaned += 1
                    except Exception as e:
                        self.log(f"   清除失败 Network/{network_file}: {e}")
        
        # 5. 清理存储目录
        storage_dirs = [
            "Local Storage",
            "Session Storage", 
            "WebStorage",
            "Shared Dictionary",
            "Service Worker",
            "clp",  # 剪贴板数据，可能包含敏感信息
            "logs",  # 日志文件，可能记录用户活动
            "Backups",  # 备份文件，可能包含历史身份信息
            "CachedExtensionVSIXs"  # 扩展缓存，显示用户安装的扩展
        ]
        
        for storage_dir in storage_dirs:
            storage_path = qoder_support_dir / storage_dir
            if storage_path.exists():
                try:
                    shutil.rmtree(storage_path)
                    self.log(f"   已清除: {storage_dir}")
                    identity_cleaned += 1
                except Exception as e:
                    self.log(f"   清除失败 {storage_dir}: {e}")
        
        self.log(f"   已清理 {identity_cleaned} 个身份识别文件/目录")
        
        # 5. 执行高级身份清理（新增）
        self.log("5. 执行高级身份清理...")
        self.perform_advanced_identity_cleanup(qoder_support_dir)

        # 6. 处理对话记录
        if preserve_chat:
            self.log("6. 保留对话记录...")
            self.log("   对话记录已保留")
        else:
            self.log("6. 清除对话记录...")
            self.clear_chat_history(qoder_support_dir)

    def perform_advanced_identity_cleanup(self, qoder_support_dir):
        """执行高级身份清理，清除所有可能的身份识别信息"""
        try:
            self.log("开始高级身份清理...")
            cleaned_count = 0
            
            # 1. 清理 SharedClientCache 内部文件
            shared_cache = qoder_support_dir / "SharedClientCache"
            if shared_cache.exists():
                # 保留目录结构，但清除关键文件
                critical_files = [".info", ".lock", "mcp.json"]
                for file_name in critical_files:
                    file_path = shared_cache / file_name
                    if file_path.exists():
                        try:
                            file_path.unlink()
                            self.log(f"   已清除: SharedClientCache/{file_name}")
                            cleaned_count += 1
                        except Exception as e:
                            self.log(f"   清除失败 {file_name}: {e}")
                
                # 清理 index 目录（包含索引数据）
                index_dir = shared_cache / "index"
                if index_dir.exists():
                    try:
                        shutil.rmtree(index_dir)
                        self.log("   已清除: SharedClientCache/index")
                        cleaned_count += 1
                    except Exception as e:
                        self.log(f"   清除失败 index: {e}")
                
                # 清理 cache 目录
                cache_dir = shared_cache / "cache"
                if cache_dir.exists():
                    try:
                        shutil.rmtree(cache_dir)
                        self.log("   已清除: SharedClientCache/cache")
                        cleaned_count += 1
                    except Exception as e:
                        self.log(f"   清除失败 cache: {e}")
            
            # 2. 清理系统级别的身份文件
            system_files = [
                "code.lock",
                "languagepacks.json"
            ]
            
            for sys_file in system_files:
                file_path = qoder_support_dir / sys_file
                if file_path.exists():
                    try:
                        file_path.unlink()
                        self.log(f"   已清除: {sys_file}")
                        cleaned_count += 1
                    except Exception as e:
                        self.log(f"   清除失败 {sys_file}: {e}")
            
            # 3. 清理崩溃报告目录（可能包含设备信息）
            crashpad_dir = qoder_support_dir / "Crashpad"
            if crashpad_dir.exists():
                try:
                    shutil.rmtree(crashpad_dir)
                    self.log("   已清除: Crashpad")
                    cleaned_count += 1
                except Exception as e:
                    self.log(f"   清除失败 Crashpad: {e}")
            
            # 4. 清理缓存目录（CachedData和 CachedProfilesData）
            cached_dirs = ["CachedData", "CachedProfilesData"]
            for cached_dir in cached_dirs:
                dir_path = qoder_support_dir / cached_dir
                if dir_path.exists():
                    try:
                        shutil.rmtree(dir_path)
                        self.log(f"   已清除: {cached_dir}")
                        cleaned_count += 1
                    except Exception as e:
                        self.log(f"   清除失败 {cached_dir}: {e}")
            
            # 5. 清理 socket 文件
            import glob
            socket_pattern = str(qoder_support_dir / "*.sock")
            socket_files = glob.glob(socket_pattern)
            for socket_file in socket_files:
                try:
                    Path(socket_file).unlink()
                    self.log(f"   已清除: {Path(socket_file).name}")
                    cleaned_count += 1
                except Exception as e:
                    self.log(f"   清除失败 {Path(socket_file).name}: {e}")
            
            self.log(f"   高级身份清理完成，处理了 {cleaned_count} 个项目")
            
        except Exception as e:
            self.log(f"   高级身份清理失败: {e}")

    def clear_chat_history(self, qoder_support_dir):
        """清除对话记录"""
        try:
            cleared = 0

            # 1. 清除工作区中的对话会话
            workspace_storage = qoder_support_dir / "User/workspaceStorage"
            if workspace_storage.exists():
                for workspace_dir in workspace_storage.iterdir():
                    if workspace_dir.is_dir():
                        # 清除chatSessions目录
                        chat_sessions = workspace_dir / "chatSessions"
                        if chat_sessions.exists():
                            try:
                                shutil.rmtree(chat_sessions)
                                self.log(f"   已清除: {chat_sessions.relative_to(qoder_support_dir)}")
                                cleared += 1
                            except Exception as e:
                                self.log(f"   清除失败 {chat_sessions.relative_to(qoder_support_dir)}: {e}")

                        # 清除chatEditingSessions目录
                        chat_editing = workspace_dir / "chatEditingSessions"
                        if chat_editing.exists():
                            try:
                                shutil.rmtree(chat_editing)
                                self.log(f"   已清除: {chat_editing.relative_to(qoder_support_dir)}")
                                cleared += 1
                            except Exception as e:
                                self.log(f"   清除失败 {chat_editing.relative_to(qoder_support_dir)}: {e}")

            # 2. 清除历史记录
            history_dir = qoder_support_dir / "User/History"
            if history_dir.exists():
                try:
                    shutil.rmtree(history_dir)
                    self.log(f"   已清除: User/History")
                    cleared += 1
                except Exception as e:
                    self.log(f"   清除失败 User/History: {e}")

            # 3. 清除会话存储中的对话相关数据
            session_storage = qoder_support_dir / "Session Storage"
            if session_storage.exists():
                try:
                    shutil.rmtree(session_storage)
                    self.log(f"   已清除: Session Storage")
                    cleared += 1
                except Exception as e:
                    self.log(f"   清除失败 Session Storage: {e}")

            # 4. 清除用户数据中的对话相关配置
            user_data_file = qoder_support_dir / "User/globalStorage/storage.json"
            if user_data_file.exists():
                try:
                    with open(user_data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 清除对话相关的键
                    chat_keys = [key for key in data.keys() if
                               'chat' in key.lower() or
                               'conversation' in key.lower() or
                               'history' in key.lower() or
                               'session' in key.lower()]

                    if chat_keys:
                        for key in chat_keys:
                            del data[key]
                            self.log(f"   已清除配置: {key}")

                        with open(user_data_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)

                        cleared += 1

                except Exception as e:
                    self.log(f"   清除用户配置失败: {e}")

            self.log(f"   对话记录清除完成 (处理了 {cleared} 个项目)")

        except Exception as e:
            self.log(f"   清除对话记录失败: {e}")

    def open_github(self):
        """打开GitHub链接"""
        self.log("打开GitHub链接...")
        webbrowser.open("https://github.com/itandelin/qoder-free")

def main():
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle('Fusion')

    # 设置全局样式表，确保对话框文字和按钮可见
    app.setStyleSheet("""
        QMessageBox {
            background-color: white;
            color: black;
        }
        QMessageBox QLabel {
            color: black;
        }
        QMessageBox QPushButton {
            background-color: white;
            color: black;
            border: 1px solid #ccc;
            padding: 5px 15px;
        }
    """)

    window = QoderResetGUI()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
