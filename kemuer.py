
# -*- coding:UTF-8 -*-
import RPi.GPIO as GPIO
import time
from aip import AipFace
import threading
import smtplib  # 导入smtp模块-
from email.mime.text import MIMEText
from email.header import Header
import requests
import base64
import cv2
import json
API_KEY = "hux9tzno5WcO00k0cMWu7k69"
SECRET_KEY = "DI1QwKbl1NX4UZWojVGMYYSq4HWwyomm"
# 设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

# 忽略警告信息
GPIO.setwarnings(False)

# 管脚参数
# 小车按键定义
key = 8
# 小车电机引脚定义
IN1 = 20
IN2 = 21
IN3 = 19
IN4 = 26
ENA = 16
ENB = 13
# 超声波引脚定义
EchoPin = 0
TrigPin = 1
# RGB三色灯引脚定义
LED_R = 22
LED_G = 27
LED_B = 24
# 舵机引脚定义
FrontServoPin = 23
ServoUpDownPin = 9
ServoLeftRightPin = 11
# 红外避障引脚定义
AvoidSensorLeft = 12
AvoidSensorRight = 17
# 蜂鸣器引脚定义
buzzer = 8
# 灭火电机引脚设置
OutfirePin = 2  # 灭火电机
# 循迹红外引脚定义
TrackSensorLeftPin1 = 3  # 定义左边第一个循迹红外传感器引脚为3
TrackSensorLeftPin2 = 5  # 定义左边第二个循迹红外传感器引脚为5
TrackSensorRightPin1 = 4  # 定义右边第一个循迹红外传感器引脚为4
TrackSensorRightPin2 = 18  # 定义右边第二个循迹红外传感器引脚为18
# 光敏电阻引脚定义
LdrSensorLeft = 7
LdrSensorRight = 6



def key_scan():
    while GPIO.input(key):
        pass
    while not GPIO.input(key):
        time.sleep(0.01)
        if not GPIO.input(key):
            time.sleep(0.01)
        while not GPIO.input(key):
            pass


# 超声波测距，如果为1000则未检测到
# 由于实践中存在测距异常的情况（没有障碍，但是会偶然测到障碍），实现中每次测距会测3次，取平均值，其中只要有1次为1000就表示没检测到
def Distance():
    GPIO.output(TrigPin, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TrigPin, GPIO.HIGH)
    time.sleep(0.000012)
    GPIO.output(TrigPin, GPIO.LOW)
    t3 = time.time()
    while not GPIO.input(EchoPin):  # 等回音超过3ms，视为无关障碍
        t4 = time.time()
        if (t4 - t3) > 0.003:
            return 1000
    t1 = time.time()
    while GPIO.input(EchoPin):  # 看回音持续了多久，超过3ms视为噪音
        t5 = time.time()
        if (t5 - t1) > 0.003:
            return 1000

    t2 = time.time()
    k1 = ((t2 - t1) * 340 / 2) * 100
    GPIO.output(TrigPin, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TrigPin, GPIO.HIGH)
    time.sleep(0.000012)
    GPIO.output(TrigPin, GPIO.LOW)
    t3 = time.time()
    while not GPIO.input(EchoPin):  # 等回音超过3ms，视为无关障碍
        t4 = time.time()
        if (t4 - t3) > 0.003:
            return 1000
    t1 = time.time()
    while GPIO.input(EchoPin):  # 看回音持续了多久，超过3ms视为噪音
        t5 = time.time()
        if (t5 - t1) > 0.003:
            return 1000

    t2 = time.time()
    k2 = ((t2 - t1) * 340 / 2) * 100

    GPIO.output(TrigPin, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TrigPin, GPIO.HIGH)
    time.sleep(0.000012)
    GPIO.output(TrigPin, GPIO.LOW)
    t3 = time.time()
    while not GPIO.input(EchoPin):  # 等回音超过3ms，视为无关障碍
        t4 = time.time()
        if (t4 - t3) > 0.003:
            return 1000
    t1 = time.time()
    while GPIO.input(EchoPin):  # 看回音持续了多久，超过3ms视为噪音
        t5 = time.time()
        if (t5 - t1) > 0.003:
            return 1000

    t2 = time.time()
    k3 = ((t2 - t1) * 340 / 2) * 100
    return (k1 + k2 + k3) / 3.0


# 舵机旋转到指定角度,占空比为2.5-12.5为0~180度
def set_servo_angle(k):
    pwm_FrontServo.ChangeDutyCycle(2.5 + 10 * k / 180)


def set_camera_updown(k):
    for i in range(18):
        pwm_UpDownServo.ChangeDutyCycle(2.5 + 10 * k / 180)


def set_camera_leftright(k):
    pwm_LeftRightServo.ChangeDutyCycle(2.5 + 10 * k / 180)


# 舵机电压清零，持续保持在某个电平会使得电机持续运转，所以在设置后需要再清零，此时电机不会重置位置而是直接停机，
def stop_servo_angle():
    pwm_FrontServo.ChangeDutyCycle(0)


def stop_camera_updown():
    pwm_UpDownServo.ChangeDutyCycle(0)


def stop_camera_leftright():
    pwm_LeftRightServo.ChangeDutyCycle(0)


# 设置七彩灯颜色
def set_color(R, G, B):
    if R == 1:
        GPIO.output(LED_R, GPIO.HIGH)
    else:
        GPIO.output(LED_R, GPIO.LOW)
    if G == 1:
        GPIO.output(LED_G, GPIO.HIGH)
    else:
        GPIO.output(LED_G, GPIO.LOW)
    if B == 1:
        GPIO.output(LED_B, GPIO.HIGH)
    else:
        GPIO.output(LED_B, GPIO.LOW)


# 小车鸣笛
def whistle():
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(1.5)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.001)


# 小车前进，两驱动轮前进
def run(leftSpeed, rightSpeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftSpeed)
    pwm_ENB.ChangeDutyCycle(rightSpeed)


# 小车左转，右驱动轮前进
def left(leftSpeed, rightSpeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftSpeed)
    pwm_ENB.ChangeDutyCycle(rightSpeed)


# 小车右转，左驱动轮前进
def right(leftSpeed, rightSpeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftSpeed)
    pwm_ENB.ChangeDutyCycle(rightSpeed)


# 小车原地左转，左驱动轮后退，右驱动轮前进
def spin_left(leftSpeed, rightSpeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftSpeed)
    pwm_ENB.ChangeDutyCycle(rightSpeed)


# 小车原地右转，左驱动轮前进，右驱动轮后退
def spin_right(leftSpeed, rightSpeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(leftSpeed)
    pwm_ENB.ChangeDutyCycle(rightSpeed)


# 小车停止
def brake():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)


# 小车后退，两驱动轮前进
def back(leftSpeed, rightSpeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(leftSpeed)
    pwm_ENB.ChangeDutyCycle(rightSpeed)


# 小车反方向左转，右驱动轮后退
def back_left(Speed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(Speed)
    pwm_ENB.ChangeDutyCycle(Speed)


# 小车反方向右转，左驱动轮后退
def back_right(Speed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(Speed)
    pwm_ENB.ChangeDutyCycle(Speed)


# 电机引脚初始化为输出模式
# 按键引脚初始化为输入模式
# 寻迹引脚初始化为输入模式
def init():
    global pwm_ENA
    global pwm_ENB
    global pwm_FrontServo
    global pwm_UpDownServo
    global pwm_LeftRightServo
    global pwm_Rled
    global pwm_Gled
    global pwm_Bled
    GPIO.setup(ENA, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN1, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN2, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ENB, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN3, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN4, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(buzzer, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(OutfirePin, GPIO.OUT)
    GPIO.setup(EchoPin, GPIO.IN)
    GPIO.setup(TrigPin, GPIO.OUT)
    GPIO.setup(LED_R, GPIO.OUT)
    GPIO.setup(LED_G, GPIO.OUT)
    GPIO.setup(LED_B, GPIO.OUT)
    GPIO.setup(FrontServoPin, GPIO.OUT)
    GPIO.setup(ServoUpDownPin, GPIO.OUT)
    GPIO.setup(ServoLeftRightPin, GPIO.OUT)
    GPIO.setup(AvoidSensorLeft, GPIO.IN)
    GPIO.setup(AvoidSensorRight, GPIO.IN)
    GPIO.setup(LdrSensorLeft, GPIO.IN)
    GPIO.setup(LdrSensorRight, GPIO.IN)
    GPIO.setup(TrackSensorLeftPin1, GPIO.IN)
    GPIO.setup(TrackSensorLeftPin2, GPIO.IN)
    GPIO.setup(TrackSensorRightPin1, GPIO.IN)
    GPIO.setup(TrackSensorRightPin2, GPIO.IN)
    # 设置pwm引脚和频率为2000hz
    pwm_ENA = GPIO.PWM(ENA, 2000)
    pwm_ENB = GPIO.PWM(ENB, 2000)
    pwm_ENA.start(0)
    pwm_ENB.start(0)
    # 设置舵机的频率和起始占空比
    pwm_FrontServo = GPIO.PWM(FrontServoPin, 50)
    pwm_UpDownServo = GPIO.PWM(ServoUpDownPin, 50)
    pwm_LeftRightServo = GPIO.PWM(ServoLeftRightPin, 50)
    pwm_FrontServo.start(0)
    pwm_UpDownServo.start(0)
    pwm_LeftRightServo.start(0)
    pwm_Rled = GPIO.PWM(LED_R, 1000)
    pwm_Gled = GPIO.PWM(LED_G, 1000)
    pwm_Bled = GPIO.PWM(LED_B, 1000)
    pwm_Rled.start(0)
    pwm_Gled.start(0)
    pwm_Bled.start(0)


# 巡线模式，在遇到全黑或者距离障碍物小于40cm的时候退出程序
def search_line(i):
    while True:
        print("search_line: ", i, end=" | ")
        # 前方发现障碍，执行避障程序
        a = Distance()
        print("距离: {:.2f} cm".format(a), end=" | ")
        if a <= 20:
            print("发现障碍物，退出巡线模式！")
            return 1

        # 检测到黑线时循迹模块相应的指示灯亮，端口电平为LOW
        # 未检测到黑线时循迹模块相应的指示灯灭，端口电平为HIGH
        TrackSensorLeftValue1 = GPIO.input(TrackSensorLeftPin1)
        TrackSensorLeftValue2 = GPIO.input(TrackSensorLeftPin2)
        TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
        TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)

        # 显示传感器状态
        sensor_status = "传感器状态: {} {} {} {}".format(
            int(TrackSensorLeftValue1), int(TrackSensorLeftValue2),
            int(TrackSensorRightValue1), int(TrackSensorRightValue2))
        print(sensor_status, end=" | ")

        # 全黑，表示抵达特殊任务点，返回2
        if TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False and TrackSensorRightValue2 == False:
            print("searc_line: 发现特殊任务点，退出巡线模式！")
            brake()
            return 2

        # 0 0 1 0
        # 1 0 X 0
        # 0 1 X 0
        # 处理右锐角和右直角的转动
        if (TrackSensorLeftValue1 == False or TrackSensorLeftValue2 == False) and TrackSensorRightValue2 == False:
            print("右锐角/右直角转动 - 原地右转(15,15)")
            spin_right(15, 15)
            set_color(1, 0, 0)
            time.sleep(0.08)

        # 0 1 0 0
        # 0 X 0 1
        # 0 X 1 0
        # 处理左锐角和左直角的转动
        elif TrackSensorLeftValue1 == False and (TrackSensorRightValue1 == False or TrackSensorRightValue2 == False):
            print("左锐角/左直角转动 - 原地左转(15,15)")
            spin_left(15, 15)
            set_color(1, 0, 0)
            time.sleep(0.08)

        # 0 X X X
        # 最左边检测到
        elif TrackSensorLeftValue1 == False:
            print("最左边检测到 - 原地左转(15,15)")
            spin_left(15, 15)
            set_color(0, 0, 0)
            # time.sleep(0.02)

        # X X X 0
        # 最右边检测到
        elif TrackSensorRightValue2 == False:
            print("最右边检测到 - 原地右转(15,15)")
            spin_right(15, 15)
            set_color(0, 0, 0)
            # time.sleep(0.02)

        # X 0 1 X
        # 处理左小弯
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
            print("左小弯 - 左转(0,15)")
            left(0, 15)
            set_color(0, 0, 0)

        # X 1 0 X
        # 处理右小弯
        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
            print("右小弯 - 右转(15,0)")
            right(15, 0)
            set_color(0, 0, 0)

        # X 0 0 X
        # 处理直线
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
            print("直线行驶 - 前进(15,15)")
            run(15, 15)
            set_color(0, 0, 0)
        
        else:
            print("保持上一状态 - 传感器状态: {} {} {} {}".format(
                int(TrackSensorLeftValue1), int(TrackSensorLeftValue2),
                int(TrackSensorRightValue1), int(TrackSensorRightValue2)))
        
        # 当为1 1 1 1时小车保持上一个小车运行状态


# 无障碍检测下的巡线模式，只有在全黑的时候会退出程序，这个函数更快，更灵敏
def search_line_only(i):
    while True:
        print("search_line_only: ", i, end=" | ")
        # 检测到黑线时循迹模块相应的指示灯亮，端口电平为LOW
        # 未检测到黑线时循迹模块相应的指示灯灭，端口电平为HIGH
        TrackSensorLeftValue1 = GPIO.input(TrackSensorLeftPin1)
        TrackSensorLeftValue2 = GPIO.input(TrackSensorLeftPin2)
        TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
        TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)

        # 显示传感器状态
        sensor_status = "传感器状态: {} {} {} {}".format(
            int(TrackSensorLeftValue1), int(TrackSensorLeftValue2),
            int(TrackSensorRightValue1), int(TrackSensorRightValue2))
        print(sensor_status, end=" | ")

        # 全黑，表示抵达特殊任务点，返回2
        if TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False and TrackSensorRightValue2 == False:
            print("发现特殊任务点，退出巡线模式！")
            brake()
            return 2

        # 0 0 1 0
        # 1 0 X 0
        # 0 1 X 0
        # 处理右锐角和右直角的转动
        if (TrackSensorLeftValue1 == False or TrackSensorLeftValue2 == False) and TrackSensorRightValue2 == False:
            print("右锐角/右直角转动 - 原地右转(15,15)")
            spin_right(15, 15)
            set_color(1, 0, 0)
            time.sleep(0.08)

        # 0 1 0 0
        # 0 X 0 1
        # 0 X 1 0
        # 处理左锐角和左直角的转动
        elif TrackSensorLeftValue1 == False and (TrackSensorRightValue1 == False or TrackSensorRightValue2 == False):
            print("左锐角/左直角转动 - 原地左转(15,15)")
            spin_left(15, 15)
            set_color(1, 0, 0)
            time.sleep(0.08)

        # 0 X X X
        # 最左边检测到
        elif TrackSensorLeftValue1 == False:
            print("最左边检测到 - 原地左转(15,15)")
            spin_left(15, 15)
            set_color(0, 0, 0)
            # time.sleep(0.02)

        # X X X 0
        # 最右边检测到
        elif TrackSensorRightValue2 == False:
            print("最右边检测到 - 原地右转(15,15)")
            spin_right(15, 15)
            set_color(0, 0, 0)
            # time.sleep(0.02)

        # X 0 1 X
        # 处理左小弯
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
            print("左小弯 - 左转(0,15)")
            left(0, 15)
            set_color(0, 0, 0)

        # X 1 0 X
        # 处理右小弯
        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
            print("右小弯 - 右转(15,0)")
            right(15, 0)
            set_color(0, 0, 0)

        # X 0 0 X
        # 处理直线
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
            print("直线行驶 - 前进(15,15)")
            run(15, 15)
            set_color(0, 0, 0)
        
        else:
            print("保持上一状态 - 传感器状态: {} {} {} {}".format(
                int(TrackSensorLeftValue1), int(TrackSensorLeftValue2),
                int(TrackSensorRightValue1), int(TrackSensorRightValue2)))
        
        # 当为1 1 1 1时小车保持上一个小车运行状态


# 双线寻迹模式参数
check_time = 1  # 边界旋转重试次数
spin_time = 0.08  # 修正方向旋转的时间
spin_time_long = 0.45


# 双线寻迹模式下，获取四路循迹的状态码
def get_code():
    # False为检测到黑色,code为1
    # True为未检测到，code为0
    TrackSensorLeftValue1 = GPIO.input(TrackSensorLeftPin1)
    TrackSensorLeftValue2 = GPIO.input(TrackSensorLeftPin2)
    TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
    TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)
    code = ''
    if TrackSensorLeftValue1:
        code = code + '0'
    else:
        code = code + '1'
    if TrackSensorLeftValue2:
        code = code + '0'
    else:
        code = code + '1'
    if TrackSensorRightValue1:
        code = code + '0'
    else:
        code = code + '1'
    if TrackSensorRightValue2:
        code = code + '0'
    else:
        code = code + '1'
    return code


# 双线寻迹模式，用于维护寻迹模式的状态
class Status:
    def __init__(self):
        pass

    status = 0  # 状态机当前状态
    count = 0  # 边缘重试计数器
    flag = 0  # 黑线标志位
    black_line = 0  # 黑线数量

    # status列表
    # 0：正常前进
    # 1：右1有障碍，应该继续前进
    # 2：右1一直有障碍，应该略微左转
    # 3：右2有障碍
    # 4：右3有障碍
    # 5：右4有障碍，应该左转90°
    # 6：左1有障碍，应该继续前进
    # 7：左1一直有障碍，应该略微右转
    # 8：左2有障碍
    # 9：左3有障碍
    # 10：左4有障碍，应该左转90°

    def change_status(self, code):
        # print(self.status, ' ', code)
        if self.status == 0:
            if code == '0001':  # 右侧出现黑线
                self.status = 1
            if code == '1000':  # 左侧出现黑线
                self.status = 6
        elif self.status == 1:
            if code == '0000':  # 右侧黑线消失
                self.count = 0
                self.status = 0
            if code == '0011' or code == '0010':  # 黑线的范围变大
                self.count = 0
                self.status = 3
            if code == '0111' or code == '0110' or code == '0100':  # 黑线的范围变大
                self.count = 0
                self.status = 4
            if code == '0001':  # 黑线保持，计数器累加
                self.count = self.count + 1
                if self.count == check_time:
                    self.status = 2
        elif self.status == 2:  # 适当旋转，离开黑线
            spin_left(15, 15)
            time.sleep(spin_time)
            run(15, 15)
            self.count = 0
            self.status = 0
        elif self.status == 3:
            if code == '0000':  # 黑线消失
                self.status = 0
            if code == '0111' or code == '0110' or code == '0100':  # 黑线左移
                self.status = 4
        elif self.status == 4:
            if code == '0000':  # 黑线消失
                self.status = 0
            if code == '1111' or code == '1110' or code == '1100' or code == '1000':  # 黑线完全左移，说明该左转了
                self.status = 5
        elif self.status == 5:  # 左转
            spin_left(15, 15)
            time.sleep(spin_time_long)  # 旋转比较长的时间，旋转90°
            run(15, 15)
            self.status = 0
        elif self.status == 6:
            if code == '0000':
                self.count = 0
                self.status = 0
            if code == '1100' or code == '0100':
                self.count = 0
                self.status = 8
            if code == '1110' or code == '0110' or code == '0010':
                self.count = 0
                self.status = 9
            if code == '1000':
                self.count = self.count + 1
                if self.count == check_time:
                    self.status = 7
        elif self.status == 7:
            spin_right(15, 15)
            time.sleep(spin_time)
            run(15, 15)
            self.count = 0
            self.status = 0
        elif self.status == 8:
            if code == '0000':
                self.status = 0
            if code == '1110' or code == '0110' or code == '0010':
                self.status = 9
        elif self.status == 9:
            if code == '0000':
                self.status = 0
            if code == '1111' or code == '0111' or code == '0011' or code == '0001':
                self.status = 10
        elif self.status == 10:
            spin_right(15, 15)
            time.sleep(spin_time_long)
            run(15, 15)
            self.status = 0
        if code == '1111' and self.flag == 0:  # 遇到黑线，计数器加一，等待下一条
            self.flag = 1
            self.black_line = self.black_line + 1
            brake()
            time.sleep(0.1)
            return 1
        elif self.flag == 1:
            return 1
        if code == '0000' and self.flag == 1:  # 只有遇到纯白，才会寻找下一条黑线
            run(15, 15)
            self.flag = 0
        return 0


# 避障，当距离障碍物30cm的时候从右侧绕过去，为了体现运行的速度，没有进行左右位置障碍物的判断
def avoid():
    while True:
        a = Distance()
        if a >= 20:
            run(15, 15)  # 当快靠近障碍物时慢速前进
            time.sleep(0.01)
        elif a < 20:
            spin_right(21, 21)
            time.sleep(0.4)  # 当靠近障碍物时原地右转大约90度
            run(15, 15)  # 转弯后当前方距离大于25cm时前进
            time.sleep(0.65)
            spin_left(15,15)
            time.sleep(0.4)  # 转弯后前方距离小于25cm时向左原地转弯180度
            run(15, 15)  # 转弯后当前方距离大于25cm时前进
            time.sleep(0.75)
            spin_left(15, 15)
            time.sleep(0.8)  # 转弯后前方距离小于25cm时向左原地转弯180度
            run(15, 15)  # 转弯后当前方距离大于25cm时前进
            time.sleep(0.3)
            # right(20, 20)
            # time.sleep(0.3)
            # run(20, 20)
            return


# 侧方停车任务


def parallel_parking():
    left(15, 15)
    time.sleep(0.75)
    run(15, 15)
    time.sleep(0.6)
    back(15, 15)
    time.sleep(1.65)
    back_left(15)
    time.sleep(1.2)
    back(15, 15)
    time.sleep(0.1)
    
    brake()
    time.sleep(2)
    print("侧方停车完成")
    
    spin_right(10,10)
    time.sleep(0.1)
    brake()
    time.sleep(1)
    run(15, 15)
    time.sleep(1)
    spin_left(15, 15)
    time.sleep(0.35)  # 转弯后前方距离小于25cm时向左原地转弯180度
    run(12, 12)  # 转弯后当前方距离大于25cm时前进
    time.sleep(0.4)

# 倒车入库
def park():
    run(15, 15)
    time.sleep(0.7)
    right(20, 20)
    time.sleep(1.4)
    back(15, 15)
    time.sleep(1.1)
    brake()
    time.sleep(2) # 等待2秒


# 邮件发送函数，参数recipient是接受者，subject是邮件主题，text是邮件内容
# 注意，发送方的邮箱需要先开通SMTP的权限，允许第三方调用接口登录发送邮件

# 上传考核成绩，并设置邮件发送的内容
def upload():
    email_host = 'smtp.qq.com'
    email_port = 25
    email_passwd = 'hghswlojovfofdee'  # 这个是发送QQ账号的授权码，而不是QQ账号的密码，否则发送会失败
    sender = '1773819794@qq.com'  # 发送账号
    receivers = '2809867235@qq.com'  # receivers接收账号
    msg = MIMEMultipart()
    msg['Subject'] = "科目二考核结果通知"
    msg['From'] = sender
    msg['To'] = ';'.join(receivers)
    msg_text = MIMEText(_text='尊敬的陆先生：'+"\n"+"恭喜您在结束的科目二考试已完成成绩核查，考试得分：100分。"+"\n"+"您已成功通过科目二考试。\r\n30天后您可以选择申请科目三考试，祝您早日取得驾照。\n                                                                                                      "+time.strftime("%Y-%m-%d %H:%M:%S"),
                        _subtype='plain', _charset='utf-8')
    msg.attach(msg_text)
    try:
        smtpObj = smtplib.SMTP(email_host, email_port)
        smtpObj.login(sender, email_passwd)
        smtpObj.sendmail(sender, receivers, msg.as_string())
        print("邮件发送成功！")
        smtpObj.close()
    except smtplib.SMTPException as e:
        print("错误：邮件发送失败！")
        print(e)


# 调用百度API接口，进行人脸比对
def picture_shoot(image_name='img.jpg', image_path='/home/pi/Desktop/'):
    '''
    调用摄像头拍照并保存图片到本地
    :param image_name: 图片名字
    :param image_path: 图片保存路径
    :return: None
    '''
    cap = cv2.VideoCapture(1)
    while (cap.isOpened()):
        ret, frame = cap.read()
        # cv2.imshow("Capture_Paizhao", frame) # 显示窗口
        cv2.imwrite(image_path  +""+ image_name, frame)
        print("保存" + image_name + "成功!")
        break
    cap.release()
    cv2.destroyAllWindows()

def id_check():
    picture_shoot()
    url = "https://aip.baidubce.com/rest/2.0/face/v3/match?access_token=" + get_access_token()

    image_path1 = "/home/pi/Desktop/cmp.jpg"
    image_path2 = "/home/pi/Desktop/img.jpg"

    image_data1 = get_file_content(image_path1)
    image_data2 = get_file_content(image_path2)

    payload = json.dumps([
        {
            "image_type": "BASE64",
            "image": image_data1
        },
        {
            "image_type": "BASE64",
            "image": image_data2
        }
    ])
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    result=response.json()
    #print(result)
    if "result" in result:
        if(result["result"] is None):
            print('error')
            return 0
        score = result["result"]["score"]
        print(score)
        if(score>80):
            print("识别成功")
            return 1
        else:print("识别失败")
    else:
        print("没有匹配结果")

    return 0


def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))


def get_file_content(file_path):
    with open(file_path, 'rb') as file:
        image_data = file.read()
    return base64.b64encode(image_data).decode('utf-8')


# 一种七彩灯点亮的策略，根据转动的角度来点亮相应的颜色
def color_light(pos):
    if pos > 100:
        if pos > 150:
            GPIO.output(LED_R, GPIO.HIGH)
            GPIO.output(LED_G, GPIO.LOW)
            GPIO.output(LED_B, GPIO.LOW)
        elif pos > 125:
            GPIO.output(LED_R, GPIO.LOW)
            GPIO.output(LED_G, GPIO.HIGH)
            GPIO.output(LED_B, GPIO.LOW)
        else:
            GPIO.output(LED_R, GPIO.LOW)
            GPIO.output(LED_G, GPIO.LOW)
            GPIO.output(LED_B, GPIO.HIGH)
    else:
        if pos > 75:
            GPIO.output(LED_R, GPIO.HIGH)
            GPIO.output(LED_G, GPIO.HIGH)
            GPIO.output(LED_B, GPIO.LOW)
        elif pos > 50:
            GPIO.output(LED_R, GPIO.LOW)
            GPIO.output(LED_G, GPIO.HIGH)
            GPIO.output(LED_B, GPIO.HIGH)
        elif pos > 25:
            GPIO.output(LED_R, GPIO.HIGH)
            GPIO.output(LED_G, GPIO.LOW)
            GPIO.output(LED_B, GPIO.HIGH)
        else:
            GPIO.output(LED_R, GPIO.HIGH)
            GPIO.output(LED_G, GPIO.HIGH)
            GPIO.output(LED_B, GPIO.HIGH)


# try/except语句用来检测try语句块中的错误，
# 从而让except语句捕获异常信息并处理。
try:
    init()

    # 任务1：考生人脸识别
    
#     set_camera_updown(180)
#     # pwm_UpDownServo.ChangeDutyCycle(180)
#     pwm_
#     raise KeyError
#
#     while True:
#         for i in range(10):
#             set_camera_updown(180)
#             set_camera_leftright(90)
#             set_servo_angle(90)
#         time.sleep(0.5)
#         stop_camera_updown()
#         stop_camera_leftright()
#         stop_servo_angle()
#         key_scan()
#         if id_check():
#             whistle()
#             set_camera_updown(90)
#             stop_camera_updown()
#             break
#
#     # 任务2：S弯
#     # 实现方式：巡线模式


    # 任务3：直角转弯
    # 实现方式：巡线模式
    search_line_only(1)

    # 任务4：避障
    # 实现方式：先避障，再回到巡线模式
    run(15,15)
    time.sleep(0.5)
    search_line(2)
    avoid()
    search_line_only(3)

    # 任务5：倒车入库
    park()

    # 任务6：双线行驶，但在进入双线寻路循环前先行驶一段，驶离黑线
    run(20, 20)
    time.sleep(0.6)
    spin_left(15,15)
    time.sleep(0.1)
    search_line_only(4)
    run(10,10)
    time.sleep(0.2)
    status = Status()
    print("进入双线模式")
    while True:
        # 根据四路循迹切换状态机的状态
        if status.change_status(get_code()):
            print("退出双线模式")
            run(15,15)
            time.sleep(1)
            break

    # 任务7：侧方停车
    # 实现方式：巡线时遇到黑色横线，表示特殊任务触发
    search_line_only(5)
    parallel_parking()
    search_line_only(6)


    # 任务8：再次人脸识别并提交考核成绩（发送邮件给考生）
#     while True:
#         for i in range(10):
#             set_camera_updown(180)
#             set_camera_leftright(90)
#             set_servo_angle(90)
#         time.sleep(0.5)
#         stop_camera_updown()
#         stop_camera_leftright()
#         stop_servo_angle()
#         key_scan()
#         if id_check():
#             whistle()
#             set_camera_updown(90)
#             stop_camera_updown()
#             upload()
#             break

    # 任务9：庆祝通过
    for pos in range(181):
        set_servo_angle(pos)
        color_light(pos)
        set_camera_updown(pos)
        set_camera_leftright(pos)
        time.sleep(0.01)
    for pos in reversed(range(181)):
        set_servo_angle(pos)
        color_light(pos)
        set_camera_updown(pos)
        set_camera_leftright(pos)
        time.sleep(0.01)
    for pos in range(181):
        set_servo_angle(pos)
        color_light(pos)
        set_camera_updown(pos)
        set_camera_leftright(181 - pos)
        time.sleep(0.01)
    for pos in reversed(range(181)):
        set_servo_angle(pos)
        color_light(pos)
        set_camera_updown(pos)
        set_camera_leftright(181 - pos)
        time.sleep(0.01)
    stop_camera_leftright()
    stop_camera_updown()
    stop_servo_angle()
    time.sleep(0.1)
    spin_left(35, 35)
    time.sleep(1.4)
    spin_right(35, 35)
    time.sleep(1.4)
except KeyboardInterrupt:
    pass
pwm_ENA.stop()
pwm_ENB.stop()
GPIO.cleanup()
