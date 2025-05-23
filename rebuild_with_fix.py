import os
os.environ['FUNASR_CACHE'] = os.path.join(os.getcwd(), 'models')

# rebuild_with_fix.py - 完整的修复和重新打包脚本
import os
import sys
import subprocess
import shutil
import importlib.util


def create_funasr_fix():
    """创建FunASR修复模块"""
    print("创建FunASR修复模块...")

    funasr_fix_content = '''# funasr_fix.py - FunASR模型加载修复模块
import os
import sys
import shutil
import urllib.request
import zipfile
import json
from pathlib import Path

def get_model_cache_dir():
    """获取模型缓存目录"""
    # 尝试多个可能的缓存位置
    possible_dirs = [
        os.path.expanduser("~/.cache/funasr"),
        os.path.join(os.getcwd(), "models"),
        os.path.join(os.path.dirname(sys.executable), "models") if getattr(sys, 'frozen', False) else None,
        os.path.join(os.environ.get('TEMP', '/tmp'), "funasr_models")
    ]

    for dir_path in possible_dirs:
        if dir_path:
            try:
                os.makedirs(dir_path, exist_ok=True)
                # 测试写入权限
                test_file = os.path.join(dir_path, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return dir_path
            except Exception as e:
                print(f"无法使用目录 {dir_path}: {e}")
                continue

    raise Exception("无法找到可写的模型缓存目录")

def check_model_availability():
    """检查模型可用性"""
    try:
        cache_dir = get_model_cache_dir()
        print(f"模型缓存目录: {cache_dir}")

        # 检查必要的模型目录
        required_models = [
            "paraformer-zh-streaming",
            "fsmn-vad", 
            "ct-punc"
        ]

        available_models = []
        for model in required_models:
            model_dir = os.path.join(cache_dir, model)
            if os.path.exists(model_dir) and os.listdir(model_dir):
                available_models.append(model)
                print(f"✓ 模型 {model} 已存在")
            else:
                print(f"✗ 模型 {model} 不存在")

        return len(available_models) == len(required_models)

    except Exception as e:
        print(f"检查模型时出错: {e}")
        return False

def fix_funasr_environment():
    """修复FunASR运行环境"""
    print("修复FunASR运行环境...")

    # 1. 设置环境变量
    os.environ["FUNASR_DISABLE_UPDATE"] = "True"
    os.environ["MODELSCOPE_CACHE"] = get_model_cache_dir()

    # 2. 设置模型缓存目录
    cache_dir = get_model_cache_dir()
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)

    print(f"FunASR缓存目录设置为: {cache_dir}")

    # 3. 检查网络连接
    test_network_connection()

def test_network_connection():
    """测试网络连接"""
    test_urls = [
        "https://www.modelscope.cn",
        "https://huggingface.co", 
        "https://www.baidu.com"
    ]

    print("测试网络连接...")
    for url in test_urls:
        try:
            response = urllib.request.urlopen(url, timeout=5)
            print(f"✓ 连接成功: {url}")
            return True
        except Exception as e:
            print(f"✗ 连接失败: {url} - {e}")

    print("⚠ 网络连接可能有问题，这会影响模型下载")
    return False

def create_offline_models_info():
    """创建离线模型信息"""
    info_text = """
# FunASR模型下载说明

如果遇到模型加载失败，可以尝试以下解决方案：

## 方案1：联网环境下首次运行
1. 确保计算机有稳定的网络连接
2. 关闭防火墙和杀毒软件（临时）
3. 以管理员身份运行应用
4. 等待模型自动下载完成

## 方案2：手动下载模型
1. 访问 https://www.modelscope.cn/models/damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx
2. 下载模型文件
3. 解压到用户目录下的 .cache/funasr/ 文件夹

## 方案3：使用备用下载源
如果ModelScope访问困难，可以尝试：
- 使用VPN或代理
- 切换网络环境
- 联系技术支持获取离线模型包

模型文件较大（约300MB），首次下载需要耐心等待。
"""

    try:
        with open("模型下载说明.txt", "w", encoding="utf-8") as f:
            f.write(info_text)
        print("已创建模型下载说明文件")
    except Exception as e:
        print(f"创建说明文件失败: {e}")

if __name__ == "__main__":
    fix_funasr_environment()
    check_model_availability()
    create_offline_models_info()
'''

    with open("funasr_fix.py", "w", encoding="utf-8") as f:
        f.write(funasr_fix_content)

    print("✓ funasr_fix.py 创建成功")


def create_fixed_launcher():
    """创建修复后的启动器"""
    print("创建修复后的启动器...")

    launcher_content = '''# app_launcher.py - 同声传译应用启动器（修复版）
import os
import sys
import tkinter as tk
from tkinter import ttk
import threading
import time
import traceback
import asyncio

# 设置环境变量
os.environ["FUNASR_DISABLE_UPDATE"] = "True"

# 设置工作目录
if getattr(sys, "frozen", False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_dir)

class ModelInitializer:
    """模型初始化管理器"""
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("同声传译应用 - 初始化")
        self.parent.geometry("700x600")
        self.parent.resizable(False, False)

        # 窗口居中
        self.parent.eval("tk::PlaceWindow . center")

        self.create_ui()
        self.init_complete = False
        self.init_success = False

        # 启动初始化
        self.start_initialization()

    def create_ui(self):
        """创建UI界面"""
        # 标题
        title_frame = ttk.Frame(self.parent)
        title_frame.pack(pady=20)

        ttk.Label(title_frame, text="同声传译应用", 
                 font=("Arial", 18, "bold")).pack()
        ttk.Label(title_frame, text="Real-time Voice Translation", 
                 font=("Arial", 10, "italic")).pack()

        # 状态信息
        status_frame = ttk.Frame(self.parent)
        status_frame.pack(pady=10)

        self.status_var = tk.StringVar(value="正在初始化应用组件...")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     font=("Arial", 11))
        self.status_label.pack()

        # 进度条
        self.progress = ttk.Progressbar(self.parent, length=500, mode="indeterminate")
        self.progress.pack(pady=15)

        # 日志区域
        log_frame = ttk.LabelFrame(self.parent, text="初始化日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 创建文本框和滚动条
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(text_frame, height=20, wrap=tk.WORD, 
                               font=("Consolas", 9))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", 
                                 command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 启动按钮（初始隐藏）
        self.button_frame = ttk.Frame(self.parent)
        self.button_frame.pack(pady=10)

        self.launch_btn = ttk.Button(self.button_frame, text="启动应用", 
                                    command=self.launch_main_app, state="disabled")
        self.launch_btn.pack(side=tk.LEFT, padx=5)

        self.retry_btn = ttk.Button(self.button_frame, text="重试初始化", 
                                   command=self.retry_initialization, state="disabled")
        self.retry_btn.pack(side=tk.LEFT, padx=5)

    def add_log(self, message):
        """添加日志信息"""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"

        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, full_message + "\\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

        print(full_message)

    def start_initialization(self):
        """开始初始化过程"""
        self.progress.start()
        self.init_thread = threading.Thread(target=self.initialize_components)
        self.init_thread.daemon = True
        self.init_thread.start()

        # 监控初始化状态
        self.monitor_initialization()

    def initialize_components(self):
        """初始化所有组件"""
        try:
            self.add_log("开始初始化同声传译应用...")

            # 1. 检查基础环境
            self.status_var.set("检查Python环境...")
            self.add_log(f"Python版本: {sys.version}")
            self.add_log(f"工作目录: {os.getcwd()}")

            # 2. 应用FunASR修复
            self.status_var.set("修复FunASR环境...")
            self.add_log("应用FunASR环境修复...")

            try:
                import funasr_fix
                funasr_fix.fix_funasr_environment()

                # 检查模型可用性
                if not funasr_fix.check_model_availability():
                    self.add_log("⚠ 检测到模型文件缺失")
                    self.add_log("尝试在联网环境中运行以自动下载模型")

                    # 创建说明文件
                    funasr_fix.create_offline_models_info()

            except Exception as e:
                self.add_log(f"FunASR环境修复失败: {e}")

            # 3. 导入和初始化FunASR（增强错误处理）
            self.status_var.set("初始化语音识别模块...")
            self.add_log("正在导入FunASR模块...")

            try:
                from FunASR import FastLoadASR
                self.add_log("FunASR模块导入成功")

                # 创建ASR实例以触发模型下载
                self.add_log("创建语音识别实例（将自动下载模型）...")
                self.add_log("注意：首次运行可能需要几分钟下载模型，请耐心等待...")

                # 使用更详细的错误捕获
                try:
                    asr_instance = FastLoadASR(use_vad=True, use_punc=True)
                    self.add_log("ASR实例创建成功")
                except Exception as e:
                    self.add_log(f"ASR实例创建失败: {e}")
                    self.add_log("可能的原因：")
                    self.add_log("1. 网络连接问题，无法下载模型")
                    self.add_log("2. 模型文件损坏")
                    self.add_log("3. 磁盘空间不足")
                    self.add_log("4. 权限不足")
                    raise Exception(f"ASR实例创建失败: {e}")

                # 确保模型加载完成（增加超时处理）
                self.add_log("等待ASR主模型加载完成...")

                import threading
                import time

                # 创建一个加载状态检查
                load_success = [False]
                load_error = [None]

                def load_with_timeout():
                    try:
                        if asr_instance.ensure_asr_model_loaded():
                            load_success[0] = True
                        else:
                            load_error[0] = "模型加载返回False"
                    except Exception as e:
                        load_error[0] = str(e)

                load_thread = threading.Thread(target=load_with_timeout)
                load_thread.daemon = True
                load_thread.start()

                # 等待加载完成或超时
                timeout = 120  # 120秒超时
                start_time = time.time()

                while load_thread.is_alive() and time.time() - start_time < timeout:
                    time.sleep(2)
                    elapsed = int(time.time() - start_time)
                    self.add_log(f"模型加载中... ({elapsed}/{timeout}秒)")

                if load_thread.is_alive():
                    self.add_log("⚠ 模型加载超时，可能网络较慢或模型文件较大")
                    self.add_log("建议：")
                    self.add_log("1. 检查网络连接")
                    self.add_log("2. 尝试在网络良好的环境中重新运行")
                    self.add_log("3. 查看'模型下载说明.txt'文件")
                    raise Exception("模型加载超时")

                if load_error[0]:
                    self.add_log(f"模型加载错误: {load_error[0]}")
                    raise Exception(f"模型加载失败: {load_error[0]}")

                if not load_success[0]:
                    raise Exception("模型加载状态未知")

                self.add_log("✓ ASR主模型加载成功")

                # 加载其他模型（VAD和标点）
                if asr_instance.use_vad:
                    self.add_log("加载语音端点检测模型...")
                    try:
                        if asr_instance.load_vad_model_if_needed():
                            self.add_log("✓ VAD模型加载成功")
                        else:
                            self.add_log("⚠ VAD模型加载失败，将禁用VAD功能")
                            asr_instance.use_vad = False
                    except Exception as e:
                        self.add_log(f"⚠ VAD模型加载异常: {e}")
                        asr_instance.use_vad = False

                if asr_instance.use_punc:
                    self.add_log("加载标点恢复模型...")
                    try:
                        if asr_instance.load_punc_model_if_needed():
                            self.add_log("✓ 标点模型加载成功")
                        else:
                            self.add_log("⚠ 标点模型加载失败，将禁用标点功能")
                            asr_instance.use_punc = False
                    except Exception as e:
                        self.add_log(f"⚠ 标点模型加载异常: {e}")
                        asr_instance.use_punc = False

            except Exception as e:
                self.add_log(f"✗ FunASR初始化失败: {e}")
                self.add_log("")
                self.add_log("=== 故障排除建议 ===")
                self.add_log("1. 确保网络连接正常")
                self.add_log("2. 尝试以管理员身份运行")
                self.add_log("3. 关闭防火墙和杀毒软件后重试")
                self.add_log("4. 检查磁盘空间（需要至少1GB可用空间）")
                self.add_log("5. 查看生成的'模型下载说明.txt'文件")
                self.add_log("==================")
                raise

            # 4. 检查翻译模块
            self.status_var.set("检查翻译模块...")
            self.add_log("检查翻译模块...")

            try:
                from translation_module import TranslationModule
                # 测试翻译模块实例化
                translation = TranslationModule("test", "test", "test")
                self.add_log("✓ 翻译模块导入成功")
            except Exception as e:
                self.add_log(f"⚠ 翻译模块导入失败: {e}")

            # 5. 检查Edge TTS
            self.status_var.set("检查语音合成模块...")
            self.add_log("检查Edge TTS模块...")

            try:
                import edge_TTS
                self.add_log("✓ Edge TTS模块导入成功")

                # 测试异步功能
                async def test_edge_tts():
                    try:
                        voices = await edge_TTS.get_available_languages()
                        return len(voices) > 0
                    except Exception as e:
                        self.add_log(f"Edge TTS测试失败: {e}")
                        return False

                # 运行异步测试
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tts_ok = loop.run_until_complete(test_edge_tts())
                loop.close()

                if tts_ok:
                    self.add_log("✓ Edge TTS功能测试通过")
                else:
                    self.add_log("⚠ Edge TTS功能测试失败")

            except Exception as e:
                self.add_log(f"✗ Edge TTS检查失败: {e}")
                self.add_log("⚠ 语音合成功能可能不可用")

            # 6. 检查音频设备
            self.status_var.set("检查音频设备...")
            self.add_log("检查音频设备...")

            try:
                import sounddevice as sd
                import pygame.mixer

                # 检查输入设备
                devices = sd.query_devices()
                input_devices = [d for d in devices if d['max_input_channels'] > 0]
                output_devices = [d for d in devices if d['max_output_channels'] > 0]

                self.add_log(f"✓ 找到 {len(input_devices)} 个输入设备")
                self.add_log(f"✓ 找到 {len(output_devices)} 个输出设备")

                # 初始化pygame mixer
                pygame.mixer.init()
                self.add_log("✓ 音频播放组件初始化成功")

            except Exception as e:
                self.add_log(f"⚠ 音频设备检查失败: {e}")

            # 初始化完成
            self.add_log("所有组件初始化完成！")
            self.init_success = True

        except Exception as e:
            self.add_log(f"✗ 初始化失败: {str(e)}")
            self.add_log("详细错误信息:")
            self.add_log(traceback.format_exc())
            self.init_success = False

        finally:
            self.init_complete = True

    def monitor_initialization(self):
        """监控初始化状态"""
        if self.init_complete:
            self.progress.stop()

            if self.init_success:
                self.status_var.set("初始化完成，准备启动应用")
                self.add_log("✓ 应用初始化成功！")
                self.launch_btn.config(state="normal")
            else:
                self.status_var.set("初始化失败")
                self.add_log("✗ 应用初始化失败！")
                self.retry_btn.config(state="normal")
        else:
            # 继续监控
            self.parent.after(500, self.monitor_initialization)

    def retry_initialization(self):
        """重试初始化"""
        self.init_complete = False
        self.init_success = False
        self.launch_btn.config(state="disabled")
        self.retry_btn.config(state="disabled")

        # 清空日志
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state="disabled")

        self.start_initialization()

    def launch_main_app(self):
        """启动主应用"""
        self.add_log("正在启动主应用...")
        self.parent.destroy()

        try:
            from simultaneous_translator_app import SimultaneousTranslatorApp

            root = tk.Tk()
            app = SimultaneousTranslatorApp(root)
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            root.mainloop()

        except Exception as e:
            print(f"启动主应用失败: {e}")
            traceback.print_exc()

def main():
    """主函数"""
    # 检查是否需要初始化
    model_cache_dir = os.path.expanduser("~/.cache/funasr")

    if os.path.exists(model_cache_dir) and len(os.listdir(model_cache_dir)) > 0:
        # 模型已下载，直接启动
        try:
            from simultaneous_translator_app import SimultaneousTranslatorApp

            root = tk.Tk()
            app = SimultaneousTranslatorApp(root)
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            root.mainloop()

        except Exception as e:
            print(f"直接启动失败，进入初始化模式: {e}")
            # 启动初始化窗口
            root = tk.Tk()
            initializer = ModelInitializer(root)
            root.mainloop()
    else:
        # 需要初始化
        root = tk.Tk()
        initializer = ModelInitializer(root)
        root.mainloop()

if __name__ == "__main__":
    main()
'''

    with open("app_launcher.py", "w", encoding="utf-8") as f:
        f.write(launcher_content)

    print("✓ app_launcher.py 创建成功")


def create_enhanced_spec_file():
    """创建增强的spec文件"""
    print("创建增强的spec文件...")

    # 获取关键包的路径
    torch_path = None
    funasr_path = None

    try:
        import torch
        torch_path = os.path.dirname(torch.__file__)
        print(f"找到torch路径: {torch_path}")
    except ImportError:
        print("警告: 未找到torch")

    try:
        import funasr
        funasr_path = os.path.dirname(funasr.__file__)
        print(f"找到funasr路径: {funasr_path}")
    except ImportError:
        print("警告: 未找到funasr")

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# 收集所有必要的数据文件和二进制文件
datas = []
binaries = []
hiddenimports = []

# 1. 收集项目文件
project_files = [
    'FunASR.py',
    'edge_TTS.py', 
    'simultaneous_translator_app.py',
    'translation_module.py',
    'funasr_fix.py'
]

for file in project_files:
    if os.path.exists(file):
        datas.append((file, '.'))

# 2. 收集FunASR相关文件
funasr_path = {repr(funasr_path)}
if funasr_path and os.path.exists(funasr_path):
    # 收集FunASR的所有数据文件
    for root, dirs, files in os.walk(funasr_path):
        for file in files:
            if file.endswith(('.yaml', '.txt', '.json', '.model', '.py')):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(os.path.dirname(file_path), os.path.dirname(funasr_path))
                datas.append((file_path, rel_path))

# 3. 收集torch相关文件
torch_path = {repr(torch_path)}
if torch_path and os.path.exists(torch_path):
    # 收集torch的库文件
    torch_lib_path = os.path.join(torch_path, 'lib')
    if os.path.exists(torch_lib_path):
        for file in os.listdir(torch_lib_path):
            if file.endswith('.dll') or file.endswith('.so'):
                src = os.path.join(torch_lib_path, file)
                binaries.append((src, '.'))

# 4. 收集证书文件
try:
    import certifi
    cert_file = certifi.where()
    if os.path.exists(cert_file):
        datas.append((cert_file, '.'))
        print(f"添加证书文件: {{cert_file}}")
except ImportError:
    print("certifi未安装，跳过证书文件")

# 5. 隐藏导入
hiddenimports.extend([
    # 基础模块
    'tkinter',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    'queue',
    'threading',
    'asyncio',
    'concurrent.futures',

    # 音频相关
    'sounddevice',
    'pygame',
    'pygame.mixer',
    'numpy',

    # FunASR相关
    'funasr',
    'torch',
    'torch.nn',
    'torch._C',
    'torchaudio',
    'torchaudio._torchaudio',

    # 网络相关
    'edge_tts',
    'httpx',
    'requests',
    'websocket',
    'ssl',
    'certifi',
    'ujson',

    # 修复模块
    'funasr_fix',

    # 其他
    'base64',
    'hashlib',
    'hmac',
    'urllib.parse',
    'datetime',
    'time',
    'json',
    'io',
    'platform',
    'traceback',
    'pathlib'
])

# 收集子模块
try:
    hiddenimports.extend(collect_submodules('funasr'))
    hiddenimports.extend(collect_submodules('torch'))
    hiddenimports.extend(collect_submodules('edge_tts'))
except Exception as e:
    print(f"收集子模块时出错: {{e}}")

# PyInstaller配置
a = Analysis(
    ['app_launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas', 
        'scipy',
        'cv2',
        'PIL',
        'tensorflow'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='同声传译应用',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None  # 可以添加图标文件
)
'''

    with open("translator_enhanced.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)

    print("✓ translator_enhanced.spec 创建成功")


def create_fixed_files():
    """创建所有修复文件"""
    print("创建修复文件...")

    create_funasr_fix()
    create_fixed_launcher()
    create_enhanced_spec_file()

    print("✓ 所有修复文件创建完成")


def rebuild_application():
    """重新构建应用"""
    print("重新构建应用...")

    # 清理旧的构建文件
    if os.path.exists("dist"):
        shutil.rmtree("dist")
        print("✓ 清理旧的dist目录")

    if os.path.exists("build"):
        shutil.rmtree("build")
        print("✓ 清理旧的build目录")

    # 检查spec文件是否存在
    if not os.path.exists("translator_enhanced.spec"):
        print("✗ spec文件不存在，请先运行create_fixed_files()")
        return False

    # 重新构建
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "translator_enhanced.spec"]

    try:
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ PyInstaller执行成功")

        # 检查输出文件
        exe_path = os.path.join("dist", "同声传译应用.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"✓ 可执行文件生成成功: {exe_path}")
            print(f"✓ 文件大小: {size_mb:.1f} MB")
            return True
        else:
            print("✗ 可执行文件未生成")
            return False

    except subprocess.CalledProcessError as e:
        print(f"✗ PyInstaller执行失败: {e}")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("同声传译应用修复和重新打包工具")
    print("=" * 60)

    # 检查必要文件
    required_files = [
        "FunASR.py",
        "edge_TTS.py",
        "simultaneous_translator_app.py",
        "translation_module.py"
    ]

    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"✗ 缺少必要文件: {', '.join(missing_files)}")
        return

    print("✓ 所有必要文件都存在")

    # 创建修复文件
    create_fixed_files()

    # 重新构建应用
    if rebuild_application():
        print("\n" + "=" * 60)
        print("✅ 修复和重新打包完成！")
        print("=" * 60)
        print("可执行文件位置: dist/同声传译应用.exe")
        print("请在有网络连接的环境中测试应用")
    else:
        print("\n" + "=" * 60)
        print("❌ 重新打包失败")
        print("=" * 60)


if __name__ == "__main__":
    main()