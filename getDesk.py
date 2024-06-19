import tkinter as tk
import tkinter.filedialog as filedialog
import time
import pyautogui
from datetime import datetime
import os
import json

CONFIG_FILE = "config.json"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("滑鼠座標偵測")

        # 拉寬視窗
        self.geometry("600x170")
        self.resizable(False, False)  # 禁止調整視窗大小

        # 讀取配置文件
        self.config = self.load_config()

        # 主要框架
        main_frame = tk.Frame(self)
        main_frame.pack(padx=10, pady=2)

        # 按鈕框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(side=tk.TOP, pady=2)

        # 建立按鈕
        self.button = tk.Button(button_frame, text="擷取螢幕", command=self.start_detection)
        self.button.pack(side=tk.LEFT, padx=10, pady=1)

        # 建立延遲時間輸入框和自動開啟資料夾的 checkbox
        self.delay_label = tk.Label(button_frame, text="延遲擷取 0 ~ 10 (秒):")
        self.delay_label.pack(side=tk.RIGHT, padx=10, pady=2)

        self.delay_entry = tk.Entry(button_frame, width=5)
        self.delay_entry.pack(side=tk.RIGHT, padx=5, pady=2)
        self.delay_entry.insert(tk.END, "0")  # 預設為 0

        self.open_folder_var = tk.BooleanVar()
        self.open_folder_checkbox = tk.Checkbutton(button_frame, text="自動開啟資料夾", variable=self.open_folder_var)
        self.open_folder_checkbox.pack(side=tk.RIGHT, padx=10, pady=2)

        # 建立文字視窗
        self.text = tk.Text(main_frame, height=7, width=80, wrap=tk.WORD)
        self.text.pack(pady=2)

        # 建立描述框架
        description_frame = tk.Frame(main_frame)  # 把 description_frame 移動到 main_frame 下方
        description_frame.pack(pady=2)

        self.path_label = tk.Label(description_frame, text=f"存放路徑：{self.config.get('save_path', '未設定')}", anchor='w', width=65)
        self.path_label.pack(side=tk.LEFT, padx=10, pady=2)

        change_button = tk.Button(description_frame, text="改變位置", command=self.change_save_path, width=12, height=2)  # 設置寬度和高度
        change_button.pack(side=tk.LEFT, padx=10, pady=2)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            return {}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def change_save_path(self):
        new_path = filedialog.askdirectory()
        if new_path:
            self.config['save_path'] = new_path
            self.path_label.config(text=f"存放路徑：{new_path}")
            self.save_config()

    def start_detection(self):
        save_path = self.config.get('save_path')
        if not save_path or not os.path.isdir(save_path):
            self.text.insert(tk.END, "請先設定有效的存放路徑\n")
            self.text.update()
            return

        # 清空文字區塊
        self.text.delete('1.0', tk.END)

        self.text.insert(tk.END, "請點擊並拖曳，拖曳過程可按ESC取消...\n")
        self.text.update()  # 強制更新文字視窗

        # 創建一個全螢幕遮罩視窗
        self.mask = tk.Toplevel(self)
        self.mask.attributes('-fullscreen', True)
        self.mask.attributes('-alpha', 0.3)
        self.mask.config(bg='black')
        
        # 綁定 ESC 鍵以取消選取
        self.mask.bind("<Escape>", self.on_escape)
        self.mask.bind("<ButtonPress-1>", self.on_mouse_press)
        self.mask.bind("<B1-Motion>", self.on_mouse_drag)
        self.mask.bind("<ButtonRelease-1>", self.on_mouse_release)

        self.selection_box = None

    def on_mouse_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        if self.selection_box:
            self.selection_box.destroy()
        self.selection_box = tk.Label(self.mask, bg='blue', bd=1, relief='solid')
        self.selection_box.place(x=self.start_x, y=self.start_y, width=1, height=1)
        # self.text.insert(tk.END, f"按下座標: ({self.start_x}, {self.start_y})\n")
        # self.text.update()  # 強制更新文字視窗

    def on_mouse_drag(self, event):
        if not self.selection_box:
            return
        cur_x, cur_y = event.x, event.y
        width = cur_x - self.start_x
        height = cur_y - self.start_y
        self.selection_box.place(x=self.start_x, y=self.start_y, width=width, height=height)

    def on_mouse_release(self, event):
        self.end_x, self.end_y = event.x, event.y
        # self.text.insert(tk.END, f"放開座標: ({self.end_x}, {self.end_y})\n")
        # self.text.insert(tk.END, f"從 ({self.start_x}, {self.start_y}) 到 ({self.end_x}, {self.end_y})\n")
        # self.text.update()  # 強制更新文字視窗

        # 隱藏遮罩視窗
        self.mask.withdraw()

        if self.start_x != self.end_x and self.start_y != self.end_y:
            x = min(self.start_x, self.end_x)
            y = min(self.start_y, self.end_y)
            width = abs(self.end_x - self.start_x)
            height = abs(self.end_y - self.start_y)
            
            # 檢查是否有延遲時間
            delay_seconds = float(self.delay_entry.get())
            if delay_seconds > 10:
                delay_seconds = min(delay_seconds, 10)
                self.delay_entry.delete(0, tk.END)  # 刪除原來的值
                self.delay_entry.insert(0, str(delay_seconds))
            if delay_seconds > 0:
                self.text.insert(tk.END, f"等待 {delay_seconds} 秒後擷取螢幕...\n")
                self.text.update()
                time.sleep(delay_seconds)

            # 擷取區域畫面並儲存
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            folder = self.config['save_path']
            sub_folder = datetime.now().strftime("%Y")
            full_path = os.path.join(folder, sub_folder)
            os.makedirs(full_path, exist_ok=True)
            file_name = self.getFileName()
            screenshot.save(os.path.join(full_path, file_name))
            self.text.insert(tk.END, f"成功儲存擷取區域畫面: {os.path.join(full_path, file_name)}\n")

            # 將路徑設為可點擊的超連結
            self.text.tag_config("hyperlink", foreground="blue", underline=True)
            self.text.insert(tk.END, "點擊這裡開啟資料夾\n", "hyperlink")
            parent_folder = os.path.dirname(os.path.join(full_path, file_name))
            self.text.tag_bind("hyperlink", "<Button-1>", lambda event, path=parent_folder: os.startfile(path))
            self.text.update()  # 強制更新文字視窗

            # 若勾選預設開啟資料夾，則開啟檔案上層目錄資料夾
            if self.open_folder_var.get():
                os.startfile(parent_folder)

    def on_escape(self, event):
        if self.mask:
            self.mask.destroy()

        self.text.insert(tk.END, "選取已取消\n")
        self.text.update()  # 強制更新文字視窗

    def getFileName(self):
        now = datetime.now()
        formatted_time = now.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{formatted_time}.png"
        return filename

if __name__ == "__main__":
    app = App()
    app.mainloop()
