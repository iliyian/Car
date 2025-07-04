# -*- coding:UTF-8 -*-
import cv2
import RPi.GPIO as GPIO
import time
import os
import datetime
import threading
import numpy as np

# 舵机引脚定义 (根据pre目录中TCP_Control.py的定义)
ServoUpDownPin = 9       # 摄像头上下舵机
ServoLeftRightPin = 11   # 摄像头左右舵机

# 舵机状态常量定义 (根据pre目录中的定义)
enSERVOUP = 3
enSERVODOWN = 4
enSERVOUPDOWNINIT = 5
enSERVOLEFT = 6
enSERVORIGHT = 7
enSERVOSTOP = 8

# 设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

# 忽略警告信息
GPIO.setwarnings(False)

class CameraController:
    def __init__(self, camera_id=1, save_path='/home/pi/Desktop/'):
        """
        初始化摄像头控制器
        :param camera_id: 摄像头设备ID (默认1)
        :param save_path: 图片和视频保存路径
        """
        self.camera_id = camera_id
        self.save_path = save_path
        self.cap = None
        self.recording = False
        self.out = None
        
        # 舵机角度偏移量（用于校正）
        self.updown_offset = -15  # 上下舵机偏移量，硬编码为-15度
        
        # 舵机状态和位置变量
        self.g_ServoState = 0                # 舵机状态
        self.ServoUpDownPos = 90             # 当前上下舵机角度（显示角度）
        self.ServoLeftRightPos = 90          # 当前左右舵机角度（显示角度）
        
        # 初始化舵机
        self.init_servo()
        
        # 创建保存目录
        os.makedirs(save_path, exist_ok=True)
        
        print("摄像头控制器初始化完成")
        print(f"保存路径: {save_path}")
        print(f"摄像头设备ID: {camera_id}")
        print(f"上下舵机偏移量: {self.updown_offset}°")
    
    def init_servo(self):
        """初始化舵机"""
        GPIO.setup(ServoUpDownPin, GPIO.OUT)
        GPIO.setup(ServoLeftRightPin, GPIO.OUT)
        
        # 设置舵机的频率为50Hz
        self.pwm_UpDownServo = GPIO.PWM(ServoUpDownPin, 50)
        self.pwm_LeftRightServo = GPIO.PWM(ServoLeftRightPin, 50)
        
        self.pwm_UpDownServo.start(0)
        self.pwm_LeftRightServo.start(0)
        
        # 设置初始位置为中心
        self.servo_init()
        
        print("舵机初始化完成，摄像头位置已居中")
    
    def updownservo_appointed_detection(self, pos):
        """
        摄像头舵机上下旋转到指定角度
        :param pos: 角度 (0-180)
        """
        # 应用偏移量校正
        actual_pos = pos + self.updown_offset
        
        # 限制实际角度范围
        actual_pos = max(0, min(180, actual_pos))
        
        for i in range(1):
            self.pwm_UpDownServo.ChangeDutyCycle(0 + 10 * actual_pos/180)
            time.sleep(0.02)  # 等待20ms周期结束
        
        self.ServoUpDownPos = pos  # 保存显示角度
        print(f"摄像头上下角度已设置: {pos}° (实际: {actual_pos}°)")
    
    def leftrightservo_appointed_detection(self, pos):
        """
        摄像头舵机左右旋转到指定角度
        :param pos: 角度 (0-180)
        """
        # 限制角度范围
        pos = max(0, min(180, pos))
        
        for i in range(1):
            self.pwm_LeftRightServo.ChangeDutyCycle(2.5 + 10 * pos/180)
            time.sleep(0.02)  # 等待20ms周期结束
        
        self.ServoLeftRightPos = pos
        print(f"摄像头左右角度已设置: {pos}°")
    
    def servo_up(self):
        """摄像头舵机向上运动"""
        pos = self.ServoUpDownPos
        self.updownservo_appointed_detection(pos)
        pos += 10  # 每次增加10度
        self.ServoUpDownPos = pos
        if self.ServoUpDownPos >= 180:
            self.ServoUpDownPos = 180
    
    def servo_down(self):
        """摄像头舵机向下运动"""
        pos = self.ServoUpDownPos
        self.updownservo_appointed_detection(pos)
        pos -= 10  # 每次减少10度
        self.ServoUpDownPos = pos
        if self.ServoUpDownPos <= 45:
            self.ServoUpDownPos = 45
    
    def servo_left(self):
        """摄像头舵机向左运动"""
        pos = self.ServoLeftRightPos
        self.leftrightservo_appointed_detection(pos)
        pos += 10  # 每次增加10度
        self.ServoLeftRightPos = pos
        if self.ServoLeftRightPos >= 180:
            self.ServoLeftRightPos = 180
    
    def servo_right(self):
        """摄像头舵机向右运动"""
        pos = self.ServoLeftRightPos
        self.leftrightservo_appointed_detection(pos)
        pos -= 10  # 每次减少10度
        self.ServoLeftRightPos = pos
        if self.ServoLeftRightPos <= 0:
            self.ServoLeftRightPos = 0
    
    def servo_updown_init(self):
        """摄像头舵机上下归位"""
        self.updownservo_appointed_detection(90)
        self.ServoUpDownPos = 90
    
    def servo_init(self):
        """所有舵机归位"""
        servo_init_pos = 90
        self.updownservo_appointed_detection(servo_init_pos)
        self.leftrightservo_appointed_detection(servo_init_pos)
        self.ServoUpDownPos = servo_init_pos
        self.ServoLeftRightPos = servo_init_pos
        time.sleep(0.5)
        # 归零信号
        self.pwm_UpDownServo.ChangeDutyCycle(0)
        self.pwm_LeftRightServo.ChangeDutyCycle(0)
        print("摄像头舵机已归位到中心位置")
    
    def servo_stop(self):
        """舵机停止"""
        self.pwm_UpDownServo.ChangeDutyCycle(0)     # 归零信号
        self.pwm_LeftRightServo.ChangeDutyCycle(0)  # 归零信号
    
    def ServorThread(self):
        """
        舵机控制线程 (根据pre目录中TCP_Control.py的设计)
        """
        # 舵机状态判断并执行相应的函数
        if self.g_ServoState == enSERVOUP:
            self.servo_up()
        elif self.g_ServoState == enSERVODOWN:
            self.servo_down()
        elif self.g_ServoState == enSERVOLEFT:
            self.servo_left()
        elif self.g_ServoState == enSERVORIGHT:
            self.servo_right()
        elif self.g_ServoState == enSERVOUPDOWNINIT:
            self.servo_updown_init()
        elif self.g_ServoState == enSERVOSTOP:
            self.servo_stop()
        
        # 重置状态
        self.g_ServoState = 0
    
    def set_servo_state(self, state):
        """设置舵机状态"""
        self.g_ServoState = state
        self.ServorThread()
    
    def init_camera(self):
        """初始化摄像头"""
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            print(f"无法打开摄像头设备 {self.camera_id}")
            return False
        
        # 设置摄像头分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("摄像头初始化成功")
        return True
    
    def take_photo(self, filename=None):
        """
        拍照并保存
        :param filename: 文件名(可选)
        :return: 是否成功
        """
        if self.cap is None or not self.cap.isOpened():
            print("摄像头未初始化")
            return False
        
        ret, frame = self.cap.read()
        if not ret:
            print("无法获取摄像头画面")
            return False
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
        
        # 保存图片
        filepath = os.path.join(self.save_path, filename)
        cv2.imwrite(filepath, frame)
        
        print(f"照片已保存: {filepath}")
        return True
    
    def start_recording(self, filename=None):
        """
        开始录像
        :param filename: 文件名(可选)
        :return: 是否成功
        """
        if self.cap is None or not self.cap.isOpened():
            print("摄像头未初始化")
            return False
        
        if self.recording:
            print("已在录像中")
            return False
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.avi"
        
        filepath = os.path.join(self.save_path, filename)
        
        # 设置视频编码器
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(filepath, fourcc, 20.0, (640, 480))
        
        self.recording = True
        print(f"开始录像: {filepath}")
        return True
    
    def stop_recording(self):
        """停止录像"""
        if not self.recording:
            print("当前未在录像")
            return False
        
        self.recording = False
        if self.out:
            self.out.release()
            self.out = None
        
        print("录像已停止")
        return True
    
    def live_preview(self, headless=False):
        """
        实时预览
        :param headless: 是否为无头模式（无图形界面）
        """
        if not self.init_camera():
            return
        
        if headless:
            print("开始无头模式预览...")
            print("按键说明:")
            print("  Enter: 拍照")
            print("  'r': 开始/停止录像")
            print("  'w': 摄像头向上")
            print("  's': 摄像头向下")
            print("  'a': 摄像头向左")
            print("  'd': 摄像头向右")
            print("  'c': 摄像头居中")
            print("  'q': 退出")
            
            self._headless_preview()
        else:
            print("开始实时预览...")
            print("按键说明:")
            print("  空格键: 拍照")
            print("  'r': 开始/停止录像")
            print("  'w': 摄像头向上")
            print("  's': 摄像头向下")
            print("  'a': 摄像头向左")
            print("  'd': 摄像头向右")
            print("  'c': 摄像头居中")
            print("  'q': 退出")
            
            self._gui_preview()
    
    def _headless_preview(self):
        """无头模式预览"""
        import threading
        import sys
        import select
        
        self.preview_running = True
        frame_count = 0
        
        def input_thread():
            while self.preview_running:
                try:
                    if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.readline().strip().lower()
                        self._process_command(key)
                except:
                    pass
        
        # 启动输入线程
        input_handler = threading.Thread(target=input_thread)
        input_handler.daemon = True
        input_handler.start()
        
        print("摄像头预览已启动（无图形界面模式）")
        print("输入命令后按Enter执行...")
        
        try:
            while self.preview_running:
                ret, frame = self.cap.read()
                if not ret:
                    print("无法获取摄像头画面")
                    break
                
                # 录像处理
                if self.recording and self.out:
                    self.out.write(frame)
                
                # 每100帧显示一次状态
                frame_count += 1
                if frame_count % 100 == 0:
                    status = "录像中" if self.recording else "预览中"
                    print(f"状态: {status} | 角度: 上下={self.ServoUpDownPos}° 左右={self.ServoLeftRightPos}° | 帧数: {frame_count}")
                
                time.sleep(0.03)  # 约30fps
                
        except KeyboardInterrupt:
            print("\n预览被中断")
        
        self.preview_running = False
        
        # 清理资源
        if self.recording:
            self.stop_recording()
        
        self.cap.release()
        print("无头模式预览已退出")
    
    def _gui_preview(self):
        """图形界面预览"""
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("无法获取摄像头画面")
                    break
                
                # 在画面上显示信息
                info_text = f"角度: 上下={self.ServoUpDownPos}° 左右={self.ServoLeftRightPos}°"
                cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if self.recording:
                    cv2.putText(frame, "录像中...", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    if self.out:
                        self.out.write(frame)
                
                # 显示画面
                cv2.imshow('摄像头预览', frame)
                
                # 处理按键
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord(' '):  # 空格键拍照
                    self.take_photo()
                elif key == ord('r'):  # 录像开关
                    if self.recording:
                        self.stop_recording()
                    else:
                        self.start_recording()
                elif key == ord('w'):  # 向上
                    self.set_servo_state(enSERVOUP)
                elif key == ord('s'):  # 向下
                    self.set_servo_state(enSERVODOWN)
                elif key == ord('a'):  # 向左
                    self.set_servo_state(enSERVOLEFT)
                elif key == ord('d'):  # 向右
                    self.set_servo_state(enSERVORIGHT)
                elif key == ord('c'):  # 居中
                    self.set_servo_state(enSERVOUPDOWNINIT)
            
            # 清理资源
            if self.recording:
                self.stop_recording()
            
            self.cap.release()
            cv2.destroyAllWindows()
            print("实时预览已退出")
            
        except Exception as e:
            print(f"图形界面预览出错: {e}")
            print("尝试使用无头模式...")
            self._headless_preview()
    
    def _process_command(self, cmd):
        """处理命令"""
        if cmd == 'q':
            self.preview_running = False
            print("退出预览...")
        elif cmd == '' or cmd == 'enter':  # Enter键拍照
            self.take_photo()
        elif cmd == 'r':  # 录像开关
            if self.recording:
                self.stop_recording()
            else:
                self.start_recording()
        elif cmd == 'w':  # 向上
            self.set_servo_state(enSERVOUP)
        elif cmd == 's':  # 向下
            self.set_servo_state(enSERVODOWN)
        elif cmd == 'a':  # 向左
            self.set_servo_state(enSERVOLEFT)
        elif cmd == 'd':  # 向右
            self.set_servo_state(enSERVORIGHT)
        elif cmd == 'c':  # 居中
            self.set_servo_state(enSERVOUPDOWNINIT)
        else:
            print(f"未知命令: {cmd}")
    
    def scan_mode(self):
        """扫描模式 - 摄像头自动旋转扫描"""
        print("启动扫描模式...")
        
        # 扫描路径
        scan_positions = [
            (90, 45),   # 中央偏左
            (90, 90),   # 中央
            (90, 135),  # 中央偏右
            (135, 90),  # 向下
            (60, 90),   # 向上
        ]
        
        for i, (updown, leftright) in enumerate(scan_positions):
            print(f"扫描位置 {i+1}: 上下={updown}°, 左右={leftright}°")
            self.updownservo_appointed_detection(updown)
            self.leftrightservo_appointed_detection(leftright)
            time.sleep(2)  # 在每个位置停留2秒
        
        # 回到中心位置
        self.set_servo_state(enSERVOUPDOWNINIT)
        print("扫描模式完成")
    
    def panorama_mode(self):
        """全景模式 - 连续拍摄多张照片"""
        print("启动全景模式...")
        
        if not self.init_camera():
            return
        
        # 全景拍摄位置
        panorama_positions = [
            (90, 30),   # 左侧
            (90, 60),   # 中左
            (90, 90),   # 中央
            (90, 120),  # 中右
            (90, 150),  # 右侧
        ]
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, (updown, leftright) in enumerate(panorama_positions):
            print(f"拍摄全景照片 {i+1}/5...")
            self.updownservo_appointed_detection(updown)
            self.leftrightservo_appointed_detection(leftright)
            time.sleep(1)  # 等待稳定
            
            filename = f"panorama_{timestamp}_{i+1}.jpg"
            self.take_photo(filename)
        
        # 回到中心位置
        self.set_servo_state(enSERVOUPDOWNINIT)
        self.cap.release()
        print("全景模式完成")
    
    def cleanup(self):
        """清理资源"""
        if self.recording:
            self.stop_recording()
        
        if self.cap:
            self.cap.release()
        
        # 清理舵机
        self.servo_stop()
        self.pwm_UpDownServo.stop()
        self.pwm_LeftRightServo.stop()
        
        cv2.destroyAllWindows()
        GPIO.cleanup()
        print("资源清理完成")

def main():
    """主函数"""
    print("=" * 50)
    print("         摄像头控制程序")
    print("=" * 50)
    
    # 创建摄像头控制器
    camera = CameraController()
    
    try:
        while True:
            print("\n请选择功能:")
            print("1. 实时预览（图形界面）")
            print("2. 实时预览（无头模式）")
            print("3. 拍照")
            print("4. 扫描模式")
            print("5. 全景模式")
            print("6. 设置摄像头角度")
            print("7. 舵机归位")
            print("8. 测试舵机控制")
            print("9. 退出")
            
            choice = input("请输入选项 (1-9): ").strip()
            
            if choice == '1':
                camera.live_preview(headless=False)
            elif choice == '2':
                camera.live_preview(headless=True)
            elif choice == '3':
                if camera.init_camera():
                    camera.take_photo()
                    camera.cap.release()
            elif choice == '4':
                camera.scan_mode()
            elif choice == '5':
                camera.panorama_mode()
            elif choice == '6':
                try:
                    updown = int(input("请输入上下角度 (45-180): "))
                    leftright = int(input("请输入左右角度 (0-180): "))
                    camera.updownservo_appointed_detection(updown)
                    camera.leftrightservo_appointed_detection(leftright)
                except ValueError:
                    print("请输入有效的数字")
            elif choice == '7':
                camera.set_servo_state(enSERVOUPDOWNINIT)
            elif choice == '8':
                # 测试舵机控制状态机
                print("测试舵机控制...")
                print("1-上, 2-下, 3-左, 4-右, 5-归位, 6-停止")
                test_choice = input("请输入测试选项: ").strip()
                if test_choice == '1':
                    camera.set_servo_state(enSERVOUP)
                elif test_choice == '2':
                    camera.set_servo_state(enSERVODOWN)
                elif test_choice == '3':
                    camera.set_servo_state(enSERVOLEFT)
                elif test_choice == '4':
                    camera.set_servo_state(enSERVORIGHT)
                elif test_choice == '5':
                    camera.set_servo_state(enSERVOUPDOWNINIT)
                elif test_choice == '6':
                    camera.set_servo_state(enSERVOSTOP)
            elif choice == '9':
                break
            else:
                print("无效选项，请重新输入")
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序发生错误: {e}")
    finally:
        camera.cleanup()

if __name__ == "__main__":
    main() 