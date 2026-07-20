import cv2
import time
import pyautogui
from gesture_detector import GestureDetector
from controller import MouseController

def main():
    wCam, hCam = 640, 480
    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    detector = GestureDetector(max_num_hands=1)
    
    # 獲取螢幕解析度
    screen_w, screen_h = pyautogui.size()
    # 分開設定 X 與 Y 軸操作框大小以調整靈敏度：
    # 穩定性：history_size 設為 4，代表取過去 4 個位置的平均值 (平衡反應速度與穩定度)
    controller = MouseController(screen_w, screen_h, frame_x=150, frame_y=175, history_size=4)

    pTime = 0
    last_action_time = 0
    scroll_start_y = None
    
    print("程式已啟動！請將手移入鏡頭內。")
    print("操作說明：")
    print("- 移動滑鼠：只有大拇指與食指伸出 (指槍手勢 🔫)")
    print("- 點擊/拖曳：大拇指與食指【捏合】")
    print("- 頁面滾動：食指與中指朝上 (比 YA ✌️) 並上下移動")
    # print("- 空白鍵：食指與小拇指朝上 (搖滾 🤘)") # 暫時移除
    print("- 右 Alt 鍵：只有小拇指朝上 (打勾勾)")
    print("按 ESC 鍵可退出程式。")

    while True:
        success, img = cap.read()
        if not success:
            print("無法讀取鏡頭畫面。")
            break
            
        img = cv2.flip(img, 1) # 水平翻轉，變成鏡像
        img = detector.find_hands(img)
        lm_list = detector.find_position(img)

        if len(lm_list) != 0:
            # 改為取得食指指根座標 (ID 5) 作為滑鼠追蹤點，非常穩定
            x1, y1 = lm_list[5][1], lm_list[5][2]
            
            # 判斷哪些手指伸出
            fingers = detector.fingers_up(lm_list)
            # fingers = [Thumb, Index, Middle, Ring, Pinky]
            
            # 畫出操控範圍框架
            cv2.rectangle(img, (controller.frame_x, controller.frame_y),
                          (wCam - controller.frame_x, hCam - controller.frame_y),
                          (255, 0, 255), 2)

            length, _, _ = detector.find_distance(4, 8, lm_list)
            
            # 判斷是否為滾動模式 (食指與中指伸出)
            is_scroll_mode = (fingers == [0, 1, 1, 0, 0] or fingers == [1, 1, 1, 0, 0])
            
            # 1. 移動滑鼠：只有大拇指與食指伸出 [1, 1, 0, 0, 0] 或 準備捏合時(length < 90)，且非滾動模式
            # 加入 length < 90 可以完美解決大拇指與食指靠近時游標卡死的問題
            if (fingers == [1, 1, 0, 0, 0] or length < 90) and not is_scroll_mode:
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                controller.move_mouse(x1, y1, wCam, hCam)

            # 2. 點擊與拖曳：判斷食指與大拇指距離
            is_pinching = controller.check_pinch(length, threshold=15)
            if is_pinching:
                cv2.circle(img, (x1, y1), 15, (0, 255, 0), cv2.FILLED)
                cv2.putText(img, "Pinch/Drag!", (50, 150), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)

            current_time = time.time()
            
            # 3. 滾動頁面 (Scroll)：食指與中指伸出 (Peace sign)
            if is_scroll_mode:
                cv2.circle(img, (x1, y1), 15, (255, 255, 0), cv2.FILLED)
                cv2.putText(img, "Scroll Mode", (50, 200), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 3)
                if scroll_start_y is None:
                    scroll_start_y = y1
                else:
                    dy = y1 - scroll_start_y
                    if dy > 15: # 手往下移動，頁面向下捲動
                        pyautogui.scroll(-200)
                        scroll_start_y = y1
                    elif dy < -15: # 手往上移動，頁面向上捲動
                        pyautogui.scroll(200)
                        scroll_start_y = y1
            else:
                scroll_start_y = None
                
            # 4. 空白鍵 (Space)：暫時移除
            # if fingers == [0, 1, 0, 0, 1] or fingers == [1, 1, 0, 0, 1]:
            #     if current_time - last_action_time > 1.0:
            #         controller.press_space()
            #         last_action_time = current_time
            #         cv2.putText(img, "Space!", (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)

            # 5. 右 Alt 鍵：只有小拇指伸出
            if fingers == [0, 0, 0, 0, 1]:
                if current_time - last_action_time > 1.0:
                    controller.press_right_alt()
                    last_action_time = current_time
                    cv2.putText(img, "Right Alt!", (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)

        # 計算並顯示 FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime) if (cTime - pTime) > 0 else 0
        pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)

        cv2.imshow("Gesture Control AI", img)
        if cv2.waitKey(1) & 0xFF == 27: # 按 ESC 退出
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()