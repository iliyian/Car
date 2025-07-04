# -*- coding:UTF-8 -*-
import cv2
import RPi.GPIO as GPIO
import time
import os
import datetime
import threading
import numpy as np

# 舵机引脚定义 (根据kemuer.py中的定义)
ServoUpDownPin = 9       # 摄像头上下舵机
ServoLeftRightPin = 11   # 摄像头左右舵机

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
        self.current_updown = 90    # 当前上下舵机角度
        self.current_leftright = 90  # 当前左右舵机角度
        
        # 初始化舵机
        self.init_servo()
        
        # 创建保存目录
        os.makedirs(save_path, exist_ok=True)
        
        print("摄像头控制器初始化完成")
        print(f"保存路径: {save_path}")
        print(f"摄像头设备ID: {camera_id}")
    
    def init_servo(self):
        """初始化舵机"""
        GPIO.setup(ServoUpDownPin, GPIO.OUT)
        GPIO.setup(ServoLeftRightPin, GPIO.OUT)
        
        # 设置舵机的频率为50Hz
        self.pwm_updown = GPIO.PWM(ServoUpDownPin, 50)
        self.pwm_leftright = GPIO.PWM(ServoLeftRightPin, 50)
        
        self.pwm_updown.start(0)
        self.pwm_leftright.start(0)
        
        # 设置初始位置为中心
        self.set_camera_angle(90, 90)
        time.sleep(1)
        
        print("舵机初始化完成，摄像头位置已居中")
    
    def set_camera_angle(self, updown_angle, leftright_angle):
        """
        设置摄像头角度
        :param updown_angle: 上下角度 (0-180)
        :param leftright_angle: 左右角度 (0-180)
        """
        # 限制角度范围
        updown_angle = max(0, min(180, updown_angle))
        leftright_angle = max(0, min(180, leftright_angle))
        
        # 计算占空比 (2.5-12.5 对应 0-180度)
        updown_duty = 2.5 + 10 * updown_angle / 180
        leftright_duty = 2.5 + 10 * leftright_angle / 180
        
        # 设置舵机角度
        self.pwm_updown.ChangeDutyCycle(updown_duty)
        self.pwm_leftright.ChangeDutyCycle(leftright_duty)
        
        # 更新当前角度
        self.current_updown = updown_angle
        self.current_leftright = leftright_angle
        
        # 等待舵机转到位置
        time.sleep(0.5)
        
        # 停止PWM信号防止舵机抖动
        self.pwm_updown.ChangeDutyCycle(0)
        self.pwm_leftright.ChangeDutyCycle(0)
        
        print(f"摄像头角度已设置: 上下={updown_angle}°, 左右={leftright_angle}°")
    
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
    
    def live_preview(self):
        """实时预览"""
        if not self.init_camera():
            return
        
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
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("无法获取摄像头画面")
                break
            
            # 在画面上显示信息
            info_text = f"角度: 上下={self.current_updown}° 左右={self.current_leftright}°"
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
                new_angle = min(180, self.current_updown + 10)
                self.set_camera_angle(new_angle, self.current_leftright)
            elif key == ord('s'):  # 向下
                new_angle = max(0, self.current_updown - 10)
                self.set_camera_angle(new_angle, self.current_leftright)
            elif key == ord('a'):  # 向左
                new_angle = max(0, self.current_leftright - 10)
                self.set_camera_angle(self.current_updown, new_angle)
            elif key == ord('d'):  # 向右
                new_angle = min(180, self.current_leftright + 10)
                self.set_camera_angle(self.current_updown, new_angle)
            elif key == ord('c'):  # 居中
                self.set_camera_angle(90, 90)
        
        # 清理资源
        if self.recording:
            self.stop_recording()
        
        self.cap.release()
        cv2.destroyAllWindows()
        print("实时预览已退出")
    
    def scan_mode(self):
        """扫描模式 - 摄像头自动旋转扫描"""
        print("启动扫描模式...")
        
        # 扫描路径
        scan_positions = [
            (90, 45),   # 中央偏左
            (90, 90),   # 中央
            (90, 135),  # 中央偏右
            (135, 90),  # 向下
            (45, 90),   # 向上
        ]
        
        for i, (updown, leftright) in enumerate(scan_positions):
            print(f"扫描位置 {i+1}: 上下={updown}°, 左右={leftright}°")
            self.set_camera_angle(updown, leftright)
            time.sleep(2)  # 在每个位置停留2秒
        
        # 回到中心位置
        self.set_camera_angle(90, 90)
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
            self.set_camera_angle(updown, leftright)
            time.sleep(1)  # 等待稳定
            
            filename = f"panorama_{timestamp}_{i+1}.jpg"
            self.take_photo(filename)
        
        # 回到中心位置
        self.set_camera_angle(90, 90)
        self.cap.release()
        print("全景模式完成")
    
    def cleanup(self):
        """清理资源"""
        if self.recording:
            self.stop_recording()
        
        if self.cap:
            self.cap.release()
        
        # 清理舵机
        self.pwm_updown.stop()
        self.pwm_leftright.stop()
        
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
            print("1. 实时预览")
            print("2. 拍照")
            print("3. 扫描模式")
            print("4. 全景模式")
            print("5. 设置摄像头角度")
            print("6. 退出")
            
            choice = input("请输入选项 (1-6): ").strip()
            
            if choice == '1':
                camera.live_preview()
            elif choice == '2':
                if camera.init_camera():
                    camera.take_photo()
                    camera.cap.release()
            elif choice == '3':
                camera.scan_mode()
            elif choice == '4':
                camera.panorama_mode()
            elif choice == '5':
                try:
                    updown = int(input("请输入上下角度 (0-180): "))
                    leftright = int(input("请输入左右角度 (0-180): "))
                    camera.set_camera_angle(updown, leftright)
                except ValueError:
                    print("请输入有效的数字")
            elif choice == '6':
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