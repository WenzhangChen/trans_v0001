import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, ttk
import threading
import json
import os
from openai import OpenAI

# 配置文件路径
CONFIG_FILE = "config.json"

# 现代主题配色方案 (白色明亮模式)
class Theme:
    # 主色调
    BG_PRIMARY = "#f5f5f7"      # 主背景色（浅灰白）
    BG_SECONDARY = "#ffffff"    # 次要背景色（纯白）
    BG_CARD = "#ffffff"         # 卡片背景色（纯白）
    BG_INPUT = "#fafafa"        # 输入框背景色（极浅灰）
    
    # 文字颜色
    TEXT_PRIMARY = "#1d1d1f"    # 主要文字（深黑）
    TEXT_SECONDARY = "#6e6e73"  # 次要文字（中灰）
    TEXT_HINT = "#a1a1a6"       # 提示文字（浅灰）
    
    # 强调色
    ACCENT_PRIMARY = "#e0e0e0"  # 主要强调色（浅灰）
    ACCENT_SECONDARY = "#d0d0d0" # 次要强调色（深一点的灰）
    ACCENT_SUCCESS = "#34c759"  # 成功色（绿色）
    
    # 边框和分隔
    BORDER_COLOR = "#e5e5e7"    # 边框颜色
    SEPARATOR_COLOR = "#d2d2d7" # 分隔线颜色
    
    # 按钮
    BUTTON_BG = "#0071e3"       # 按钮背景色
    BUTTON_HOVER = "#0051a8"    # 按钮悬停色
    
    # 阴影
    SHADOW_COLOR = "#000000"    # 阴影颜色
    
    # 字体（使用 ClearType 优化的字体）
    FONT_TITLE = ("Microsoft YaHei UI", 15, "bold")
    FONT_LABEL = ("Microsoft YaHei UI", 11)
    FONT_CONTENT = ("Microsoft YaHei UI", 12)
    FONT_BUTTON = ("Microsoft YaHei UI", 12, "bold")
    FONT_MONO = ("Consolas", 11)

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "domains": "This translation is for an economics paper that is to be submitted to a journal. Please pay attention to the writing norms and professional economic expressions when translating."
}

# 加载配置
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 合并缺失的默认值
                for k, v in DEFAULT_CONFIG.items():
                    if k not in config:
                        config[k] = v
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

# 保存配置
def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding=" utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save config: {e}")

# 启用 Windows 高 DPI 感知，防止高分屏下文字模糊
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
except Exception:
    pass

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.client = None
        self.update_client()

        root.title("✦ 智能翻译助手 - AI Powered ✦")
        root.geometry("1200x700")
        root.minsize(1000, 600)
        
        # 记录初始窗口尺寸，用于比例缩放
        self._initial_width = 1200
        self._initial_height = 700
        
        # 设置窗口图标和背景
        root.configure(bg=Theme.BG_PRIMARY)
        
        # 设置ttk样式
        self.setup_styles()
        
        # 构建界面
        self.build_ui()

    def setup_styles(self):
        """设置ttk样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置各种样式
        style.configure("Title.TLabel", 
                       background=Theme.BG_PRIMARY, 
                       foreground=Theme.TEXT_PRIMARY, 
                       font=Theme.FONT_TITLE)
        
        style.configure("Subtitle.TLabel", 
                       background=Theme.BG_PRIMARY, 
                       foreground=Theme.TEXT_SECONDARY, 
                       font=Theme.FONT_LABEL)
        
        style.configure("Card.TFrame", 
                       background=Theme.BG_CARD, 
                       relief=tk.FLAT)
        
        style.configure("Status.TLabel", 
                       background=Theme.BG_SECONDARY, 
                       foreground=Theme.TEXT_SECONDARY, 
                       font=("Microsoft YaHei UI", 9))

    def build_ui(self):
        """构建用户界面"""
        # 主容器（不扩展，让内部元素自然分配空间）
        main_container = tk.Frame(self.root, bg=Theme.BG_PRIMARY)
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # 配置main_container的行：内容区扩展，底部固定
        main_container.rowconfigure(0, weight=1)  # 顶部标题+内容
        main_container.rowconfigure(1, weight=0)  # 底部状态栏（固定高度）
        main_container.columnconfigure(0, weight=1)
        
        # 上方区域（标题+内容）
        top_frame = tk.Frame(main_container, bg=Theme.BG_PRIMARY)
        top_frame.grid(row=0, column=0, sticky="nsew")
        
        # === 顶部标题栏 ===
        self.build_header(top_frame)
        
        # === 主内容区域（使用grid实现等宽布局）===
        content_frame = tk.Frame(top_frame, bg=Theme.BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 5))
        
        # 配置三列：全部等宽（weight=1）
        content_frame.columnconfigure(0, weight=1)  # 左侧输入
        content_frame.columnconfigure(1, weight=1, minsize=80)  # 中间控制（等比例扩展，最小80px）
        content_frame.columnconfigure(2, weight=1)  # 右侧输出
        content_frame.rowconfigure(0, weight=1)
        
        # 左侧输入面板
        self.build_input_panel(content_frame, 0)
        
        # 中间控制面板
        self.build_control_panel(content_frame, 1)
        
        # 右侧输出面板
        self.build_output_panel(content_frame, 2)
        
        # === 底部状态栏（固定在底部）===
        self.build_status_bar(main_container, 1, 0)
        
        # 绑定窗口缩放事件，动态调整按钮字体
        self.root.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event):
        """窗口缩放时动态调整按钮字体和宽度"""
        if event.widget != self.root:
            return
        
        # 计算缩放比例（基于高度）
        scale = event.height / self._initial_height
        scale = max(0.7, min(1.5, scale))  # 限制在0.7x到1.5x之间
        
        # 更新控制面板宽度
        if hasattr(self, 'control_frame'):
            self._update_control_panel_width()
        
        # 更新按钮字体
        self._update_button_fonts(scale)

    def build_header(self, parent):
        """构建顶部标题栏"""
        header_frame = tk.Frame(parent, bg=Theme.BG_PRIMARY, height=60)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        header_frame.pack_propagate(False)
    
        # 标题
        title_label = tk.Label(header_frame, 
                              text="🌐 中英智能翻译", 
                              font=Theme.FONT_TITLE,
                              bg=Theme.BG_PRIMARY, 
                              fg=Theme.TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=10)
    
        # 副标题
        subtitle = tk.Label(header_frame, 
                          text="Powered by Qwen AI", 
                           font=("Microsoft YaHei UI", 9),
                           bg=Theme.BG_PRIMARY, 
                           fg=Theme.TEXT_HINT)
        subtitle.pack(side=tk.LEFT, padx=(10, 0))
    
        # API状态指示器 - 先创建 the canvas and label attributes
        self.api_status_canvas = tk.Canvas(header_frame, 
                                          width=12, 
                                         height=12, 
                                          bg=Theme.BG_PRIMARY, 
                                          highlightthickness=0)
        self.api_status_canvas.pack(side=tk.RIGHT, padx=(5, 5))
    
        self.api_status_label = tk.Label(header_frame, 
                                        text="API: 未配置", 
                                        font=("Microsoft YaHei UI", 9),
                                        bg=Theme.BG_PRIMARY, 
                                        fg=Theme.TEXT_HINT)
        self.api_status_label.pack(side=tk.RIGHT)
    
        # Now update the API status after attributes are created
        self.update_api_status()

        # 设置按钮
        settings_btn = tk.Button(header_frame,
                                text="⚙️ 设置",
                                command=self.open_settings,
                                bg=Theme.BG_CARD,
                                fg=Theme.TEXT_PRIMARY,
                                font=("Microsoft YaHei UI", 9),
                                relief=tk.FLAT,
                                padx=15,
                                pady=5,
                                cursor="hand2")
        settings_btn.pack(side=tk.RIGHT, padx=5)
        settings_btn.bind("<Enter>", lambda e: settings_btn.config(bg=Theme.BG_SECONDARY))
        settings_btn.bind("<Leave>", lambda e: settings_btn.config(bg=Theme.BG_CARD))

    def build_input_panel(self, parent, column):
        """构建输入面板"""
        input_frame = tk.Frame(parent, bg=Theme.BG_PRIMARY)
        input_frame.grid(row=0, column=column, sticky="nsew", padx=(0, 5))
        
        # 卡片容器（带边框）
        card = tk.Frame(input_frame, bg=Theme.BG_CARD, relief=tk.FLAT, 
                       highlightbackground=Theme.BORDER_COLOR, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏
        title_bar = tk.Frame(card, bg=Theme.BG_SECONDARY, height=45)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        
        # 分隔线
        separator = tk.Frame(card, bg=Theme.SEPARATOR_COLOR, height=1)
        separator.pack(fill=tk.X)
        
        tk.Label(title_bar, 
                text="📝 中文输入", 
                font=Theme.FONT_LABEL,
                bg=Theme.BG_SECONDARY, 
                fg=Theme.TEXT_PRIMARY).pack(side=tk.LEFT, padx=15, pady=10)
        
        # 字数统计
        self.input_count_label = tk.Label(title_bar, 
                                         text="0 字符", 
                                         font=("Microsoft YaHei UI", 9),
                                         bg=Theme.BG_SECONDARY, 
                                         fg=Theme.TEXT_HINT)
        self.input_count_label.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # 输入文本框
        self.input_box = scrolledtext.ScrolledText(card, 
                                                   wrap=tk.WORD, 
                                                   font=Theme.FONT_CONTENT,
                                                   bg=Theme.BG_INPUT, 
                                                   fg=Theme.TEXT_PRIMARY,
                                                   insertbackground=Theme.TEXT_PRIMARY,
                                                   selectbackground=Theme.ACCENT_PRIMARY,
                                                   relief=tk.FLAT,
                                                   padx=15, 
                                                   pady=15,
                                                   borderwidth=0)
        self.input_box.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # 绑定输入事件更新字数
        self.input_box.bind("<KeyRelease>", lambda e: self.update_char_count())

    def build_control_panel(self, parent, column):
        """构建中间控制面板"""
        # 计算初始比例：控制面板宽度 / 窗口宽度
        self._control_panel_ratio = 100 / self._initial_width
        
        self.control_frame = tk.Frame(parent, bg=Theme.BG_PRIMARY)
        self.control_frame.grid(row=0, column=column, sticky="ns", padx=5)
        
        # 设置初始宽度
        self._update_control_panel_width()
        
        # 翻译按钮
        self.translate_btn = tk.Button(self.control_frame,
                                       text="翻译",
                                       command=self.on_translate,
                                       bg=Theme.ACCENT_PRIMARY,
                                       fg=Theme.TEXT_PRIMARY,
                                       font=("Microsoft YaHei UI", 12, "bold"),
                                       relief=tk.FLAT,
                                       padx=20,
                                       pady=25,
                                       cursor="hand2",
                                       activebackground=Theme.ACCENT_SECONDARY,
                                       activeforeground=Theme.TEXT_PRIMARY)
        self.translate_btn.pack(side=tk.TOP, pady=(30, 8), fill=tk.X)
        self.translate_btn.bind("<Enter>", lambda e: self.translate_btn.config(bg=Theme.ACCENT_SECONDARY))
        self.translate_btn.bind("<Leave>", lambda e: self.translate_btn.config(bg=Theme.ACCENT_PRIMARY))
        
        # 清空按钮
        self.clear_btn = tk.Button(self.control_frame,
                             text="清空",
                             command=self.clear_all,
                             bg=Theme.BG_CARD,
                             fg=Theme.TEXT_SECONDARY,
                             font=("Microsoft YaHei UI", 11),
                             relief=tk.FLAT,
                             padx=15,
                             pady=10,
                             cursor="hand2")
        self.clear_btn.pack(side=tk.TOP, pady=5, fill=tk.X)
        self.clear_btn.bind("<Enter>", lambda e: self.clear_btn.config(fg=Theme.TEXT_PRIMARY, bg=Theme.BG_SECONDARY))
        self.clear_btn.bind("<Leave>", lambda e: self.clear_btn.config(fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD))
        
        # 复制按钮
        self.copy_btn = tk.Button(self.control_frame,
                            text="复制\n结果",
                            command=self.copy_result,
                            bg=Theme.BG_CARD,
                            fg=Theme.TEXT_SECONDARY,
                            font=("Microsoft YaHei UI", 11),
                            relief=tk.FLAT,
                            padx=15,
                            pady=10,
                            cursor="hand2")
        self.copy_btn.pack(side=tk.TOP, pady=(5, 10), fill=tk.X)
        self.copy_btn.bind("<Enter>", lambda e: self.copy_btn.config(fg=Theme.TEXT_PRIMARY, bg=Theme.BG_SECONDARY))
        self.copy_btn.bind("<Leave>", lambda e: self.copy_btn.config(fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD))
    
    def _update_control_panel_width(self):
        """根据窗口宽度更新控制面板宽度"""
        new_width = int(self.root.winfo_width() * self._control_panel_ratio)
        new_width = max(80, min(150, new_width))  # 限制在80-150之间
        self.control_frame.config(width=new_width)
        self.control_frame.pack_propagate(False)
    
    def _update_button_fonts(self, scale):
        """根据缩放比例更新按钮字体"""
        translate_font_size = max(10, int(12 * 0.8 * scale))
        small_font_size = max(9, int(11 * 0.8 * scale))
        
        if hasattr(self, 'translate_btn'):
            self.translate_btn.config(font=("Microsoft YaHei UI", translate_font_size, "bold"))
        if hasattr(self, 'clear_btn'):
            self.clear_btn.config(font=("Microsoft YaHei UI", small_font_size))
        if hasattr(self, 'copy_btn'):
            self.copy_btn.config(font=("Microsoft YaHei UI", small_font_size))

    def build_output_panel(self, parent, column):
        """构建输出面板"""
        output_frame = tk.Frame(parent, bg=Theme.BG_PRIMARY)
        output_frame.grid(row=0, column=column, sticky="nsew", padx=(5, 0))
        
        # 卡片容器（带边框）
        card = tk.Frame(output_frame, bg=Theme.BG_CARD, relief=tk.FLAT,
                       highlightbackground=Theme.BORDER_COLOR, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏
        title_bar = tk.Frame(card, bg=Theme.BG_SECONDARY, height=45)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        
        # 分隔线
        separator = tk.Frame(card, bg=Theme.SEPARATOR_COLOR, height=1)
        separator.pack(fill=tk.X)
        
        tk.Label(title_bar, 
                text="✨ 英文翻译", 
                font=Theme.FONT_LABEL,
                bg=Theme.BG_SECONDARY, 
                fg=Theme.TEXT_PRIMARY).pack(side=tk.LEFT, padx=15, pady=10)
        
        # 字数统计
        self.output_count_label = tk.Label(title_bar, 
                                          text="0 字符", 
                                          font=("Microsoft YaHei UI", 9),
                                          bg=Theme.BG_SECONDARY, 
                                          fg=Theme.TEXT_HINT)
        self.output_count_label.pack(side=tk.RIGHT, padx=15, pady=10)
        
        # 输出文本框
        self.output_box = scrolledtext.ScrolledText(card, 
                                                    wrap=tk.WORD, 
                                                    font=Theme.FONT_CONTENT,
                                                    bg=Theme.BG_INPUT, 
                                                    fg=Theme.TEXT_PRIMARY,
                                                    insertbackground=Theme.TEXT_PRIMARY,
                                                    selectbackground=Theme.ACCENT_PRIMARY,
                                                    relief=tk.FLAT,
                                                    padx=15, 
                                                    pady=15,
                                                    borderwidth=0)
        self.output_box.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

    def build_status_bar(self, parent, row, column):
        """构建底部状态栏"""
        status_frame = tk.Frame(parent, bg=Theme.BG_SECONDARY, height=30)
        status_frame.grid(row=row, column=column, sticky="ew", pady=(15, 0))
        status_frame.pack_propagate(False)
        
        # 快捷键提示
        shortcut_label = tk.Label(status_frame, 
                                 text="快捷键: Ctrl+Enter 翻译  |  Ctrl+C 复制结果  |  Ctrl+A 全选", 
                                 font=("Microsoft YaHei UI", 8),
                                 bg=Theme.BG_SECONDARY, 
                                 fg=Theme.TEXT_HINT)
        shortcut_label.pack(side=tk.LEFT, padx=15, pady=5)
        
        # 版权信息
        copyright_label = tk.Label(status_frame,
                                  text="Wenzhang © 2026",
                                  font=("Microsoft YaHei UI", 8, "bold"),
                                  bg=Theme.BG_SECONDARY,
                                  fg=Theme.TEXT_SECONDARY)
        copyright_label.pack(side=tk.RIGHT, padx=15, pady=5)
        
        # 绑定键盘快捷键（在所有组件创建完成后）
        self.input_box.bind("<Control-Return>", lambda e: self.on_translate())

    def update_api_status(self):
        """更新API状态指示器"""
        if self.client:
            color = "#34c759"  # 绿色
            status_text = "API: 已配置"
        else:
            color = "#a1a1a6"  # 灰色
            status_text = "API: 未配置"
        
        self.api_status_canvas.delete("all")
        self.api_status_canvas.create_oval(2, 2, 10, 10, fill=color, outline=color)
        self.api_status_label.config(text=status_text, fg=color)

    def update_char_count(self):
        """更新字符计数"""
        input_text = self.input_box.get("1.0", tk.END).strip()
        count = len(input_text)
        self.input_count_label.config(text=f"{count} 字符")
        
        # 同时更新输出字符计数
        output_text = self.output_box.get("1.0", tk.END).strip()
        out_count = len(output_text)
        self.output_count_label.config(text=f"{out_count} 字符")

    def clear_all(self):
        """清空所有内容"""
        self.input_box.delete("1.0", tk.END)
        self.output_box.delete("1.0", tk.END)
        self.update_char_count()

    def copy_result(self):
        """复制翻译结果到剪贴板"""
        result = self.output_box.get("1.0", tk.END).strip()
        if result:
            self.root.clipboard_clear()
            self.root.clipboard_append(result)
            self.root.update()
            # 显示复制成功提示
            original_text = self.output_count_label.cget("text")
            self.output_count_label.config(text="✓ 已复制", fg=Theme.ACCENT_SUCCESS)
            self.root.after(1500, lambda: self.output_count_label.config(text=original_text, fg=Theme.TEXT_HINT))

    def update_client(self):
        api_key = self.config.get("api_key", "").strip()
        base_url = self.config.get("base_url", "").strip()
        if not api_key or not base_url:
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            except Exception:
                self.client = None
        
        # 更新API状态显示
        if hasattr(self, 'api_status_canvas'):
            self.update_api_status()

    def translate_text(self, chinese_text):
        if not self.client:
            return "[Error] API key or base URL not configured properly."
        try:
            messages = [{"role": "user", "content": chinese_text}]
            translation_options = {
                "source_lang": "auto",
                "target_lang": "English",
                "domains": self.config.get("domains", "")
            }
            completion = self.client.chat.completions.create(
                model="qwen-mt-turbo",
                messages=messages,
                extra_body={"translation_options": translation_options}
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"[Error] {str(e)}"

    def on_translate(self):
        input_text = self.input_box.get("1.0", tk.END).strip()
        if not input_text:
            self.output_box.delete("1.0", tk.END)
            self.output_box.insert("1.0", "请输入需要翻译的文本...", "center")
            self.output_box.tag_configure("center", justify="center")
            self.update_char_count()
            return

        # 按钮动画效果
        self.translate_btn.config(state="disabled", text="翻译中...", bg=Theme.TEXT_HINT)
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert("1.0", "正在翻译，请稍候...", "center")
        self.output_box.tag_configure("center", justify="center")
        self.output_box.config(fg=Theme.TEXT_HINT)

        def run_translation():
            result = self.translate_text(input_text)
            self.root.after(0, lambda: self.update_output(result))

        threading.Thread(target=run_translation, daemon=True).start()

    def update_output(self, text):
        self.output_box.config(fg=Theme.TEXT_PRIMARY)
        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, text)
        self.translate_btn.config(state="normal", text="翻  译", bg=Theme.ACCENT_PRIMARY)
        self.update_char_count()
        
        # 翻译完成提示
        if not text.startswith("[Error]"):
            original_text = self.output_count_label.cget("text")
            self.output_count_label.config(text="✓ 翻译完成", fg=Theme.ACCENT_SUCCESS)
            self.root.after(2000, lambda: self.output_count_label.config(text=original_text, fg=Theme.TEXT_HINT))

    def open_settings(self):
        ModernSettingsWindow(self.root, self.config, self.on_config_saved)

    def on_config_saved(self, new_config):
        self.config = new_config
        save_config(self.config)
        self.update_client()
        messagebox.showinfo("Success", "Settings saved successfully!")

class ModernSettingsWindow:
    def __init__(self, parent, config, on_save_callback):
        self.parent = parent
        self.config = config.copy()
        self.on_save = on_save_callback
        self.has_changes = False  # 跟踪是否有未保存的更改

        # 创建顶层窗口
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ 翻译设置")
        self.window.geometry("750x1000")
        self.window.minsize(750, 1000)
        self.window.transient(parent)
        self.window.grab_set()
        self.window.configure(bg=Theme.BG_PRIMARY)
        
        # 居中显示
        self.center_window()
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 构建UI
        self.build_settings_ui()

    def center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (750 // 2)
        y = (self.window.winfo_screenheight() // 2) - (750 // 2)
        self.window.geometry(f"750x750+{x}+{y}")

    def build_settings_ui(self):
        """构建设置界面"""
        # 配置窗口grid布局
        self.window.rowconfigure(0, weight=1)  # 内容区域
        self.window.rowconfigure(1, weight=0)  # 底部按钮区域
        self.window.columnconfigure(0, weight=1)
        
        # === 内容滚动区域 ===
        content_container = tk.Frame(self.window, bg=Theme.BG_PRIMARY)
        content_container.grid(row=0, column=0, sticky="nsew", padx=25, pady=(25, 10))
        content_container.rowconfigure(0, weight=1)
        content_container.columnconfigure(0, weight=1)
        
        # === 标题 ===
        title_label = tk.Label(content_container,
                              text="⚙️ API & 翻译设置",
                              font=Theme.FONT_TITLE,
                              bg=Theme.BG_PRIMARY,
                              fg=Theme.TEXT_PRIMARY)
        title_label.pack(pady=(0, 5))
        
        subtitle_label = tk.Label(content_container,
                                 text="配置您的翻译服务参数",
                                 font=("Microsoft YaHei UI", 9),
                                 bg=Theme.BG_PRIMARY,
                                 fg=Theme.TEXT_HINT)
        subtitle_label.pack(pady=(0, 20))
        
        # === 说明卡片 ===
        info_card = tk.Frame(content_container, bg=Theme.BG_CARD, relief=tk.FLAT)
        info_card.pack(fill=tk.X, pady=(0, 20))
        
        instructions = (
            "📖 使用说明：\n\n"
            "• API Key 必须是阿里云 DashScope（通义千问）的有效密钥\n"
            "• Base URL 已固定,无需修改\n"
            "• Domains 字段必须使用英文描述翻译场景（如学术、技术等），不可包含中文"
        )
        tk.Label(info_card,
                text=instructions,
                justify=tk.LEFT,
                fg=Theme.TEXT_SECONDARY,
                bg=Theme.BG_CARD,
                wraplength=620,
                font=("Microsoft YaHei UI", 9),
                anchor="w").pack(padx=20, pady=15)
        
        # === 输入卡片 ===
        input_card = tk.Frame(content_container, bg=Theme.BG_CARD, relief=tk.FLAT)
        input_card.pack(fill=tk.BOTH, expand=True)
        
        # API Key
        tk.Label(input_card,
                text="🔑 API Key (DashScope):",
                font=Theme.FONT_LABEL,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.api_key_entry = tk.Entry(input_card,
                                     width=75,
                                     show="*",
                                     font=Theme.FONT_MONO,
                                     bg=Theme.BG_INPUT,
                                     fg=Theme.TEXT_PRIMARY,
                                     insertbackground=Theme.TEXT_PRIMARY,
                                     relief=tk.FLAT,
                                     bd=0)
        self.api_key_entry.pack(padx=20, pady=5, ipady=5)
        self.api_key_entry.insert(0, self.config.get("api_key", ""))
        # 绑定更改事件
        self.api_key_entry.bind("<KeyRelease>", lambda e: self.mark_changed())
        
        # Base URL (只读)
        tk.Label(input_card,
                text="🔗 Base URL (Fixed):",
                font=Theme.FONT_LABEL,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.base_url_entry = tk.Entry(input_card,
                                      width=75,
                                      state="readonly",
                                      font=Theme.FONT_MONO,
                                      bg=Theme.BG_INPUT,
                                      fg=Theme.TEXT_HINT,
                                      relief=tk.FLAT,
                                      bd=0)
        self.base_url_entry.pack(padx=20, pady=5, ipady=5)
        self.base_url_entry.config(state="normal")
        self.base_url_entry.insert(0, "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.base_url_entry.config(state="readonly")
        
        # Domains (Prompt)
        tk.Label(input_card,
                text="📝 Translation Domain Prompt (English only):",
                font=Theme.FONT_LABEL,
                bg=Theme.BG_CARD,
                fg=Theme.TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.domains_text = scrolledtext.ScrolledText(input_card,
                                                     width=70,
                                                     height=8,
                                                     font=Theme.FONT_MONO,
                                                     bg=Theme.BG_INPUT,
                                                     fg=Theme.TEXT_PRIMARY,
                                                     insertbackground=Theme.TEXT_PRIMARY,
                                                     selectbackground=Theme.ACCENT_PRIMARY,
                                                     relief=tk.FLAT,
                                                     bd=0)
        self.domains_text.pack(padx=20, pady=5)
        self.domains_text.insert(tk.END, self.config.get("domains", ""))
        # 绑定更改事件
        self.domains_text.bind("<KeyRelease>", lambda e: self.mark_changed())
        
        # === 底部按钮区域（固定） ===
        btn_frame = tk.Frame(self.window, bg=Theme.BG_PRIMARY, height=60)
        btn_frame.grid(row=1, column=0, sticky="ew")
        btn_frame.pack_propagate(False)
        
        # 保存按钮
        save_btn = tk.Button(btn_frame,
                            text="💾 保存",
                            command=self.save,
                            bg=Theme.ACCENT_PRIMARY,
                            fg=Theme.TEXT_PRIMARY,
                            font=("Microsoft YaHei UI", 10, "bold"),
                            relief=tk.FLAT,
                            padx=20,
                            pady=8,
                            cursor="hand2",
                            activebackground=Theme.ACCENT_SECONDARY,
                            activeforeground=Theme.TEXT_PRIMARY)
        save_btn.pack(side=tk.RIGHT, padx=(0, 15))
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg=Theme.ACCENT_SECONDARY))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg=Theme.ACCENT_PRIMARY))
        
        # 取消按钮
        cancel_btn = tk.Button(btn_frame,
                              text="❌ 取消",
                              command=self.on_close,
                              bg=Theme.BG_CARD,
                              fg=Theme.TEXT_SECONDARY,
                              font=("Microsoft YaHei UI", 10),
                              relief=tk.FLAT,
                              padx=20,
                              pady=8,
                              cursor="hand2",
                              activebackground=Theme.BG_SECONDARY,
                              activeforeground=Theme.TEXT_PRIMARY)
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(fg=Theme.TEXT_PRIMARY))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(fg=Theme.TEXT_SECONDARY))

    def contains_chinese(self, text):
        """简单判断是否包含中文字符"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def mark_changed(self):
        """标记内容有更改"""
        self.has_changes = True
    
    def on_close(self):
        """关闭窗口时的处理"""
        if self.has_changes:
            result = messagebox.askyesnocancel(
                "未保存的更改",
                "您有未保存的更改。\n\n是否保存后再关闭？"
            )
            if result is None:  # 点击取消
                return
            elif result:  # 点击是，先保存
                self.save()
            # result == False 时直接关闭，不保存
        self.window.destroy()

    def save(self):
        api_key = self.api_key_entry.get().strip()
        domains = self.domains_text.get("1.0", tk.END).strip()

        # 校验 API Key
        if not api_key:
            messagebox.showwarning("Input Error", "API Key cannot be empty.")
            return

        # 校验 Domains 是否包含中文
        if self.contains_chinese(domains):
            messagebox.showwarning(
                "Input Error",
                "Domains field must be in English only.\nPlease do not include any Chinese characters."
            )
            return

        if not domains:
            messagebox.showwarning("Input Warning", "Domains is empty. This may reduce translation quality.")
            # 可选择是否允许保存，这里允许但警告

        new_config = {
            "api_key": api_key,
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",  # 固定值
            "domains": domains
        }
        self.has_changes = False  # 重置更改标志
        self.on_save(new_config)
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()