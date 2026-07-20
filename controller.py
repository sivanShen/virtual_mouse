import pyautogui
import numpy as np
from collections import deque

class MouseController:
    def __init__(self, screen_w, screen_h, frame_x=150, frame_y=175, history_size=12):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.frame_x = frame_x  # 左右螢幕內縮邊界
        self.frame_y = frame_y  # 上下螢幕內縮邊界
        
        # 歷史軌跡佇列，用來做移動平均 (Moving Average)
        self.history_size = history_size
        self.history_x = deque(maxlen=self.history_size)
        self.history_y = deque(maxlen=self.history_size)
        
        self.cloc_x, self.cloc_y = 0, 0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_moving_while_dragging = False
        pyautogui.FAILSAFE = False

    def move_mouse(self, x, y, cam_w, cam_h):
        # 映射座標：將攝影機畫面座標對應到螢幕座標
        x3 = np.interp(x, (self.frame_x, cam_w - self.frame_x), (0, self.screen_w))
        y3 = np.interp(y, (self.frame_y, cam_h - self.frame_y), (0, self.screen_h))
        
        # 將最新的座標加入歷史佇列
        self.history_x.append(x3)
        self.history_y.append(y3)
        
        # 計算過去 N 個位置的移動平均 (Moving Average)
        target_x = sum(self.history_x) / len(self.history_x)
        target_y = sum(self.history_y) / len(self.history_y)
        
        # 增加「拖曳容錯區間 (Drag Tolerance)」
        if self.dragging and not self.is_moving_while_dragging:
            # 如果捏合後，移動距離小於 20 像素，我們鎖定滑鼠位置，確保這是一次乾淨的「點擊」而不是「拖曳」
            if abs(target_x - self.drag_start_x) > 20 or abs(target_y - self.drag_start_y) > 20:
                self.is_moving_while_dragging = True
            else:
                target_x = self.drag_start_x
                target_y = self.drag_start_y
                
        self.cloc_x = target_x
        self.cloc_y = target_y
        
        # 移動滑鼠
        try:
            pyautogui.moveTo(self.cloc_x, self.cloc_y)
        except pyautogui.FailSafeException:
            pass # 避免滑鼠移到死角導致程式崩潰

    def check_pinch(self, distance, threshold=40):
        if distance < threshold:
            if not self.dragging:
                pyautogui.mouseDown()
                self.dragging = True
                self.drag_start_x = self.cloc_x
                self.drag_start_y = self.cloc_y
                self.is_moving_while_dragging = False
            return True
        else:
            if self.dragging:
                pyautogui.mouseUp()
                self.dragging = False
            return False

    def press_space(self):
        pyautogui.press('space')
        
    def press_right_alt(self):
        pyautogui.press('altright')
        
    def press_win_tab(self):
        pyautogui.hotkey('win', 'tab')
