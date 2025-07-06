# -*- coding:UTF-8 -*-
import RPi.GPIO as GPIO
import time
from aip import AipFace
import threading
import smtplib  # 导入smtp模块-
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
import requests
import base64
import cv2
import json

import speech_recognition as sr
import re
from gtts import gTTS
import os
import logging

import openai
import base64
import os
import cv2
import time
import httpx
from flask import Flask, Response, render_template_string
import threading

# --- 配置 ---
# API 密钥将从环境变量 "OPENAI_API_KEY" 中读取，以提高安全性。
# 在运行脚本前，请先设置该环境变量。
API_KEY = os.environ.get("OPENAI_API_KEY") 
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
EMAIL_AUTH_CODE = os.getenv('EMAIL_AUTH_CODE')
# 您想要使用的模型
MODEL = "google/gemini-2.5-flash"
# API 地址, 如果您使用代理或第三方服务，请在此修改
BASE_URL = "https://openrouter.ai/api/v1"
WEATHER_API = "https://restapi.amap.com/v3/weather/weatherInfo?"
RECEIVER_EMAIL = "sqzrmhj@gmail.com"
# 如果您需要通过HTTPS代理访问，请在此处设置代理地址，例如 "http://127.0.0.1:7890"
# 如果不需要代理，请将其留空 ""
HTTPS_PROXY = os.environ.get("https_proxy", "")
# 图片保存的文件夹
IMGS_DIR = "imgs"

# API_KEY = "hux9tzno5WcO00k0cMWu7k69"
SECRET_KEY = "DI1QwKbl1NX4UZWojVGMYYSq4HWwyomm"

POSTCAL_CODE = 330106 # 杭州市西湖区

speed_of_sound = 0 # 声速
temperature = 0 # 温度
weather_info = None # 天气信息

# 设置日志系统
def setup_logging():
    global current_log_file
    # 创建logs目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 生成日志文件名（包含时间戳）
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    current_log_file = f"logs/car_exam_{timestamp}.log"
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(current_log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    return logging.getLogger(__name__)

# 获取当前日志文件路径的全局变量
current_log_file = None

# 初始化日志系统
logger = setup_logging()

def send_system_log(exam_status="系统运行完成"):
    """发送系统日志邮件"""
    try:
        log_file = current_log_file
        if not os.path.exists(log_file):
            print(f"警告：日志文件不存在 - {log_file}")
            return False
        
        # 获取日志文件信息
        file_size = os.path.getsize(log_file)
        file_size_mb = file_size / (1024 * 1024)
        
        # 构造邮件内容
        end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        subject = f"科目二考试系统运行日志 - {end_time}"
        
        email_content = f"""
科目二考试系统运行报告

系统状态：{exam_status}

系统信息：
- 结束时间：{end_time}
- 日志文件：{os.path.basename(log_file)}
- 文件大小：{file_size_mb:.2f} MB
- 环境温度：{temperature}℃
- 计算声速：{speed_of_sound:.2f} m/s

附件包含完整的系统运行日志，包括：
- 系统初始化记录
- 身份验证过程
- 考试项目执行详情
- 传感器数据记录
- 错误和异常信息

此邮件由科目二考试系统自动发送。
        """
        
        success = send_mail(RECEIVER_EMAIL, subject, email_content.strip(), log_file)
        
        if success:
            print("系统日志邮件发送成功")
        else:
            print("系统日志邮件发送失败")
            
        return success
        
    except Exception as e:
        print(f"发送系统日志时发生错误：{str(e)}")
        return False

# 重写print函数，使其既输出到控制台又保存到日志
def print(*args, **kwargs):
    # 将所有参数转换为字符串并连接
    message = ' '.join(str(arg) for arg in args)
    
    # 处理end参数
    end = kwargs.get('end', '\n')
    if end != '\n':
        message += end
    
    # 使用logger输出（会同时输出到控制台和文件）
    logger.info(message)

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
    k1 = ((t2 - t1) * speed_of_sound / 2) * 100
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
    k2 = ((t2 - t1) * speed_of_sound / 2) * 100

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
    k3 = ((t2 - t1) * speed_of_sound / 2) * 100
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
    
    global speed_of_sound
    global temperature
    global weather_info
    
    try:
        if WEATHER_API_KEY:
            response = requests.get(WEATHER_API, params={"city": POSTCAL_CODE, "key": WEATHER_API_KEY})
            weather_info = response.json()
            
            if 'lives' in weather_info and len(weather_info['lives']) > 0:
                temperature = int(weather_info["lives"][0]["temperature"])
                speed_of_sound = 331.4 + 0.6 * temperature
                print(f"天气信息获取成功，温度：{temperature}℃，声速：{speed_of_sound}m/s")
            else:
                print("天气API返回数据格式错误")
                temperature = 20  # 默认温度
                speed_of_sound = 331.4 + 0.6 * temperature
        else:
            print("未设置天气API密钥，使用默认温度20℃")
            temperature = 20  # 默认温度
            speed_of_sound = 331.4 + 0.6 * temperature
    except Exception as e:
        print(f"获取天气信息失败：{e}")
        temperature = 20  # 默认温度
        speed_of_sound = 331.4 + 0.6 * temperature


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
    print("侧方停车完成")
    time.sleep(2)
    
    spin_right(10,10)
    time.sleep(0.1)
    brake()
    time.sleep(1)
    run(15, 15)
    time.sleep(1)
    spin_left(15, 15)
    time.sleep(0.35)  # 转弯后前方距离小于25cm时向左原地转弯180度
    run(12, 12)  # 转弯后当前方距离大于25cm时前进
    time.sleep(0.7)

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

def play_voice_prompt():
    prompt_text = "请报出场次科目二考试考生的编号"
    tts = gTTS(prompt_text, lang='zh')  # 使用中文语音
    tts.save("prompt.mp3")
    os.system("mpg321 prompt.mp3")  # 播放语音提示


def voice_welcome():
# 初始化语音识别器
    recognizer = sr.Recognizer()

    play_voice_prompt()

    # 使用麦克风作为输入源
    with sr.Microphone() as source:
        print("Please say your exam number...")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        audio = recognizer.listen(source)

    # 将音频转换为文本
    print("Recognizing...")

    try:
        # 使用 Google 语音识别 API 将语音转换为中文文本
        result = recognizer.recognize_google(audio, language="zh-CN", show_all=True)
        print("Recognized speech content:", result)
        
        # 选择最佳候选结果（有可能是数字）
        best_transcript = None
        for alternative in result['alternative']:
            if '1234567' in alternative['transcript']:  # 如果识别到数字，选这个结果
                best_transcript = alternative['transcript']
                break
            elif re.search(r'\d+', alternative['transcript']):  # 如果识别到数字，选这个结果
                best_transcript = alternative['transcript']
                break

        if best_transcript:
            print("Best transcript:", best_transcript)
            
            # 使用正则表达式提取文本中的所有数字
            numbers = re.findall(r'\d+', best_transcript)  # 提取文本中的所有数字（连续的数字）
            
            # 如果识别到的数字中有空格，拼接成一个完整的数字
            if numbers:
                exam_number = ''.join(numbers)  # 合并识别到的所有数字

                # 构造文本
                speech_text = f"欢迎{exam_number}号考生参加科目二考试"
                
                # 使用 gTTS 将文本转换为语音
                tts = gTTS(speech_text, lang='zh')  # 使用中文语音

                # 保存为 MP3 文件
                output_filename = "exam_welcome.mp3"
                tts.save(output_filename)

                # 播放生成的音频
                os.system(f"mpg321 {output_filename}")  # 或者使用 aplay

            else:
                print("No valid number recognized in the speech.")

        else:
            print("No valid transcript found.")

    except sr.UnknownValueError:
        print("Sorry, I couldn't understand the speech")
    except sr.RequestError:
        print("Unable to connect to the speech recognition service")
        
def voice_play(id):
    os.system("mpg321 ./music/" + str(id) + ".mp3")

def voice(prompt_text):
    print(f"语音播报：{prompt_text}")
    try:
        tts = gTTS(prompt_text, lang='zh')  # 使用中文语音
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"voice_{timestamp}.mp3"
        
        print(f"正在生成语音文件：{filename}")
        tts.save(filename)
        
        print("正在播放语音...")
        os.system(f"mpg321 {filename}")
        print("语音播放完成")
    except Exception as e:
        print(f"语音播报失败：{str(e)}")

def send_mail(recipient, subject, text, attachment_path=None):
    sender = '1715428260@qq.com'
    
    print(f"准备发送邮件 - 收件人：{recipient}, 主题：{subject}")
    
    # 检查是否获取到授权码
    if not EMAIL_AUTH_CODE:
        print("错误：未找到邮箱授权码，请设置环境变量 EMAIL_AUTH_CODE")
        return False
    
    try:
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 添加邮件正文
        msg.attach(MIMEText(text, 'plain', 'utf-8'))
        
        # 如果有附件，添加附件
        if attachment_path and os.path.exists(attachment_path):
            print(f"正在添加附件：{attachment_path}")
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            # 对附件进行编码
            encoders.encode_base64(part)
            
            # 添加附件头信息
            filename = os.path.basename(attachment_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}',
            )
            
            msg.attach(part)
            print(f"附件添加成功：{filename}")
        
        print("正在连接邮箱服务器...")
        # 连接到QQ邮箱SMTP服务器
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(sender, EMAIL_AUTH_CODE)
        
        print("正在发送邮件...")
        # 发送邮件
        server.sendmail(sender, [recipient], msg.as_string())
        server.quit()
        
        print(f"邮件发送成功！收件人：{recipient}, 主题：{subject}")
        return True
        
    except Exception as e:
        print(f"邮件发送失败：{str(e)}")
        return False
    
# send_mail(RECEIVER_EMAIL, "测试邮件", "这是一封测试邮件")
# raise Exception("测试")

# 初始化 OpenAI 客户端
http_client = None
if HTTPS_PROXY:
    print(f"正在使用代理: {HTTPS_PROXY}")
    proxies = {
        "http://": HTTPS_PROXY,
        "https://": HTTPS_PROXY,
    }
    # 使用代理创建 httpx 客户端
    http_client = httpx.Client(proxies=proxies)

# 如果您已经设置了 OPENAI_API_KEY 环境变量，则无需传递 api_key 参数
client = openai.OpenAI(
    base_url=BASE_URL,
    http_client=http_client # 将配置好的客户端传递给 OpenAI
)

def capture_image_from_camera(save_dir):
    """
    调用摄像头拍照并保存图片。
    
    :param save_dir: 图片保存的目录。
    :return: 保存的图片路径，如果失败则返回 None。
    """
    print(f"开始拍照流程 - 保存目录：{save_dir}")
    
    # 确保保存目录存在
    if not os.path.exists(save_dir):
        print(f"创建目录: {save_dir}")
        os.makedirs(save_dir)
        
    # 0 代表系统默认的摄像头
    print("正在初始化摄像头...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("错误：无法打开摄像头。请检查摄像头是否连接并可用。")
        return None
        
    print("摄像头已启动，3秒后拍照...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("拍照！")

    # 读取一帧
    ret, frame = cap.read()
    
    if not ret:
        print("错误：无法从摄像头捕获图像。")
        cap.release()
        return None
        
    # 生成文件名
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    image_name = f"capture_{timestamp}.jpg"
    image_path = os.path.join(save_dir, image_name)
    
    # 保存图片
    cv2.imwrite(image_path, frame)
    print(f"图片已保存到: {image_path}")
    
    # 释放摄像头资源
    cap.release()
    cv2.destroyAllWindows()
    print("摄像头资源已释放")
    
    return image_path

def encode_image_to_base64(image_path):
    """将图片文件编码为 Base64 字符串"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"错误：找不到图片文件 {image_path}")
        return None
    except Exception as e:
        print(f"读取或编码图片时发生错误: {e}")
        return None

def recognize_image_content(image_path, prompt="接下来请仅识别和输出图片中的文字，不要输出任何其他信息，谢谢！"):
    """
    :param image_path: 本地图片文件的路径。
    :param prompt: 您想对图片提出的问题。
    :return: 模型的回答，如果出错则返回 None。
    """
    print(f"正在识别图片: {image_path}")
    
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return None

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300, # 您可以根据需要调整返回内容的最大长度
        )
        
        # 提取并返回模型的回答
        return response.choices[0].message.content
        
    except openai.APIConnectionError as e:
        print(f"无法连接到 OpenAI API: {e.__cause__}")
    except openai.RateLimitError as e:
        print(f"达到 OpenAI API 的速率限制: {e.response.text}")
    except openai.APIStatusError as e:
        print(f"OpenAI API 返回错误状态: status={e.status_code}, response={e.response}")
    except Exception as e:
        print(f"调用 API 时发生未知错误: {e}")
        
    return None

def camera_scan():
    if not API_KEY:
        print("错误：未设置 OPENAI_API_KEY 环境变量。")
        print("请在运行脚本前设置该变量，例如：")
        print("export OPENAI_API_KEY='你的API密钥'")
    else:
        # 1. 拍照
        image_to_recognize = capture_image_from_camera(IMGS_DIR)
        
        # 2. 如果拍照成功，则进行识别
        if image_to_recognize:
            description = recognize_image_content(image_to_recognize)
            if description:
                print("\n--- 识别结果 ---")
                print(description) 
                return description
    return None

def id_check():
    print("开始身份验证")
    voice("请出示身份证")
    print("正在调用摄像头扫描身份证...")
    desp = camera_scan()
    if desp:
        print(f"身份证识别结果：{desp}")
        if "黄" in desp or "雨" in desp or "风" in desp or "阳" in desp:
            print("身份证验证通过")
            return True
        else:
            print("身份证验证失败：未找到关键字")
    else:
        print("身份证识别失败：无法获取识别结果")
    return False

def play_weather():
    if weather_info and 'lives' in weather_info and len(weather_info['lives']) > 0:
        text = "时间：" + time.strftime("%Y-%m-%d %H:%M", time.localtime())
        text += f"，天气：{weather_info['lives'][0]['weather']}，气温：{weather_info['lives'][0]['temperature']}℃"
        text += f"，计算声速：{int(speed_of_sound)}米每秒"
        voice(text)
        if temperature > 30:
            voice("天气炎热，请考生做好防暑措施。")
        elif temperature < 10:
            voice("天气寒冷，请注意保暖。")
    else:
        print("天气信息获取失败，无法播报天气")
        voice("天气信息获取失败")

# 全局变量用于摄像头流
camera = None
streaming_active = False

# Flask应用
app = Flask(__name__)

def generate_frames():
    """生成摄像头帧用于流媒体"""
    global camera, streaming_active
    
    while streaming_active:
        if camera is None:
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                print("无法打开摄像头")
                break
        
        success, frame = camera.read()
        if not success:
            print("无法读取摄像头帧")
            break
        else:
            # 编码帧为JPEG格式
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                print("帧编码失败")
                break
    
    # 清理摄像头资源
    if camera is not None:
        camera.release()
        camera = None

@app.route('/')
def index():
    """主页面"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>科目二考试实时监控</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f0f0f0;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .video-container {
                text-align: center;
                margin-bottom: 20px;
            }
            img {
                max-width: 100%;
                height: auto;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
            .info {
                background-color: #e8f4f8;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
            }
            .status {
                color: #28a745;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 科目二考试实时监控系统</h1>
            <div class="video-container">
                <img src="{{ url_for('video_feed') }}" alt="实时视频流">
            </div>
            <div class="info">
                <h3>系统信息</h3>
                <p><span class="status">● 在线</span> 摄像头实时监控</p>
                <p>📍 端口：7070</p>
                <p>🔄 自动刷新视频流</p>
                <p>⏰ 当前时间：<span id="current-time"></span></p>
            </div>
        </div>
        
        <script>
            // 更新当前时间
            function updateTime() {
                const now = new Date();
                document.getElementById('current-time').textContent = now.toLocaleString('zh-CN');
            }
            
            // 每秒更新时间
            setInterval(updateTime, 1000);
            updateTime();
        </script>
    </body>
    </html>
    ''')

@app.route('/video_feed')
def video_feed():
    """视频流路由"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def start_web_server():
    """启动Web服务器"""
    global streaming_active
    streaming_active = True
    print("正在启动Web服务器...")
    print("摄像头实时监控地址：http://localhost:7070")
    print("请在浏览器中访问上述地址查看实时视频")
    app.run(host='0.0.0.0', port=7070, debug=False, use_reloader=False)

def stop_web_server():
    """停止Web服务器"""
    global streaming_active, camera
    streaming_active = False
    if camera is not None:
        camera.release()
        camera = None
    print("Web服务器已停止")

# try/except语句用来检测try语句块中的错误，
# 从而让except语句捕获异常信息并处理。
try:
    print("=== 科目二考试系统启动 ===")
    print("正在初始化系统...")
    
    # 记录开始时间
    start_time = time.time()
    
    init()
    print("系统初始化完成")
    
    # 默认状态为正常完成
    exam_status = "考试正常完成"
    
    print("=== 开始身份验证流程 ===")
    while True:
        if id_check():
            print("身份验证成功")
            voice("身份认证成功，请开始考试。")
            break
        else:
            print("身份验证失败，请重新尝试")
            voice("身份认证失败，请重新认证。")
            
    print("=== 启动实时监控系统 ===")
    # 在后台线程中启动Web服务器
    web_server_thread = threading.Thread(target=start_web_server, daemon=True)
    web_server_thread.start()
    
    # 等待服务器启动
    voice("实时监控系统已启动")

    print("=== 开始语音欢迎流程 ===")
    voice_welcome()
    
    
    print("=== 播报天气信息 ===")
    # 播报天气信息
    play_weather()

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


    print("=== 开始科目二考试项目 ===")
    
    # 任务1：直角转弯
    print("--- 任务1：直角转弯 ---")
    voice_play(1)
    search_line_only(1)
    print("直角转弯任务完成")

    # 任务_plus：避障
    print("--- 任务加分项：障碍绕行 ---")
    voice("下一项目：障碍绕行。请准备。")
    
    run(15,15)
    time.sleep(0.5)
    search_line(2)
    avoid()
    search_line_only(3)
    print("障碍绕行任务完成")

    # 任务2：倒车入库
    print("--- 任务2：倒车入库 ---")
    voice_play(2)
    park()
    print("倒车入库任务完成")

    # 任务3：曲线
    print("--- 任务3：曲线行驶 ---")
    
    run(20, 20)
    time.sleep(0.6)
    spin_left(15,15)
    time.sleep(0.1)
    search_line_only(4)
    
    voice_play(3)
    
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
    print("曲线行驶任务完成")

    # 任务4：侧方停车
    print("--- 任务4：侧方停车 ---")
    
    search_line_only(5)
    voice_play(4)
    
    parallel_parking()
    search_line_only(6)
    print("侧方停车任务完成")


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

    # 任务5：庆祝通过
    print("=== 所有任务完成，考试通过！ ===")
    
    # 发送考试通过通知邮件（简单通知，不带附件）
    send_mail(RECEIVER_EMAIL, "科目二考试通过！", "恭喜您科目二考试通过！祝您早日取得驾照！")
    voice_play(5)
    # 计算耗时并格式化
    total_seconds = int(time.time() - start_time)
    if total_seconds >= 60:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_str = f"耗时：{minutes}分{seconds}秒"
    else:
        time_str = f"耗时：{total_seconds}秒"
    voice(time_str)
    print(time_str)
    print("庆祝流程完成")
    
    # for pos in range(181):
    #     set_servo_angle(pos)
    #     color_light(pos)
    #     set_camera_updown(pos)
    #     set_camera_leftright(pos)
    #     time.sleep(0.01)
    # for pos in reversed(range(181)):
    #     set_servo_angle(pos)
    #     color_light(pos)
    #     set_camera_updown(pos)
    #     set_camera_leftright(pos)
    #     time.sleep(0.01)
    # for pos in range(181):
    #     set_servo_angle(pos)
    #     color_light(pos)
    #     set_camera_updown(pos)
    #     set_camera_leftright(181 - pos)
    #     time.sleep(0.01)
    # for pos in reversed(range(181)):
    #     set_servo_angle(pos)
    #     color_light(pos)
    #     set_camera_updown(pos)
    #     set_camera_leftright(181 - pos)
    #     time.sleep(0.01)
    # stop_camera_leftright()
    # stop_camera_updown()
    # stop_servo_angle()
    # time.sleep(0.1)
    # spin_left(35, 35)
    # time.sleep(1.4)
    # spin_right(35, 35)
    # time.sleep(1.4)
except KeyboardInterrupt:
    print("=== 程序被用户中断 ===")
    print("正在清理资源...")
    exam_status = "程序被用户中断"
except Exception as e:
    print(f"=== 程序发生异常：{str(e)} ===")
    print("正在清理资源...")
    exam_status = f"程序异常退出：{str(e)}"
finally:
    print("正在停止Web服务器...")
    try:
        stop_web_server()
        print("Web服务器已停止")
    except:
        print("Web服务器停止时发生错误")
    
    print("正在停止PWM...")
    try:
        pwm_ENA.stop()
        pwm_ENB.stop()
        print("PWM已停止")
    except:
        print("PWM停止时发生错误")
    
    print("正在清理GPIO...")
    try:
        GPIO.cleanup()
        print("GPIO清理完成")
    except:
        print("GPIO清理时发生错误")
    
    print("=== 发送系统日志 ===")
    try:
        send_system_log(exam_status)
    except:
        print("发送系统日志时发生错误")
    
    print("=== 程序结束 ===")
