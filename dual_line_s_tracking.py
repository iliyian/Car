#-*- coding:UTF-8 -*-
from turtle import Turtle
import RPi.GPIO as GPIO
import time

#小车电机引脚定义
IN1 = 20
IN2 = 21
IN3 = 19
IN4 = 26
ENA = 16
ENB = 13

#小车按键定义
key = 8

#循迹红外引脚定义
#TrackSensorLeftPin1 TrackSensorLeftPin2 TrackSensorRightPin1 TrackSensorRightPin2
#      3                 5                  4                   18
TrackSensorLeftPin1  =  3   #定义左边第一个循迹红外传感器引脚为3口
TrackSensorLeftPin2  =  5   #定义左边第二个循迹红外传感器引脚为5口
TrackSensorRightPin1 =  4   #定义右边第一个循迹红外传感器引脚为4口
TrackSensorRightPin2 =  18  #定义右边第二个循迹红外传感器引脚为18口

#设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

#忽略警告信息
GPIO.setwarnings(False)

#电机引脚初始化为输出模式
#按键引脚初始化为输入模式
#寻迹引脚初始化为输入模式
def init():
    global pwm_ENA
    global pwm_ENB
    GPIO.setup(ENA,GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(IN1,GPIO.OUT,initial=GPIO.LOW)
    GPIO.setup(IN2,GPIO.OUT,initial=GPIO.LOW)
    GPIO.setup(ENB,GPIO.OUT,initial=GPIO.HIGH)
    GPIO.setup(IN3,GPIO.OUT,initial=GPIO.LOW)
    GPIO.setup(IN4,GPIO.OUT,initial=GPIO.LOW)
    GPIO.setup(key,GPIO.IN)
    GPIO.setup(TrackSensorLeftPin1,GPIO.IN)
    GPIO.setup(TrackSensorLeftPin2,GPIO.IN)
    GPIO.setup(TrackSensorRightPin1,GPIO.IN)
    GPIO.setup(TrackSensorRightPin2,GPIO.IN)
    #设置pwm引脚和频率为2000hz
    pwm_ENA = GPIO.PWM(ENA, 2000)
    pwm_ENB = GPIO.PWM(ENB, 2000)
    pwm_ENA.start(0)
    pwm_ENB.start(0)

#小车前进
def run(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

#小车后退
def back(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

#小车左转
def left(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

#小车右转
def right(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

#小车原地左转
def spin_left(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

#小车原地右转
def spin_right(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

#小车停止
def brake():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)

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
        code = code + '1'
    else:
        code = code + '0'
    if TrackSensorLeftValue2:
        code = code + '1'
    else:
        code = code + '0'
    if TrackSensorRightValue1:
        code = code + '1'
    else:
        code = code + '0'
    if TrackSensorRightValue2:
        code = code + '1'
    else:
        code = code + '0'
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
            if code == '1110':  # 右侧出现黑线
                self.status = 1
            if code == '0111':  # 左侧出现黑线
                self.status = 6
        elif self.status == 1:
            if code == '1111':  # 右侧黑线消失
                self.count = 0
                self.status = 0
            if code == '1100' or code == '1101':  # 黑线的范围变大
                self.count = 0
                self.status = 3
            if code == '1000' or code == '1001' or code == '1011':  # 黑线的范围变大
                self.count = 0
                self.status = 4
            if code == '1110':  # 黑线保持，计数器累加
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
            if code == '1111':  # 黑线消失
                self.status = 0
            if code == '1000' or code == '1001' or code == '1011':  # 黑线左移
                self.status = 4
        elif self.status == 4:
            if code == '1111':  # 黑线消失
                self.status = 0
            if code == '0000' or code == '0001' or code == '0011' or code == '0111':  # 黑线完全左移，说明该左转了
                self.status = 5
        elif self.status == 5:  # 左转
            spin_left(15, 15)
            time.sleep(spin_time_long)  # 旋转比较长的时间，旋转90°
            run(15, 15)
            self.status = 0
        elif self.status == 6:
            if code == '1111':
                self.count = 0
                self.status = 0
            if code == '0011' or code == '1011':
                self.count = 0
                self.status = 8
            if code == '0001' or code == '1001' or code == '1101':
                self.count = 0
                self.status = 9
            if code == '0111':
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
            if code == '1111':
                self.status = 0
            if code == '0001' or code == '1001' or code == '1101':
                self.status = 9
        elif self.status == 9:
            if code == '1111':
                self.status = 0
            if code == '0000' or code == '1000' or code == '1100' or code == '1110':
                self.status = 10
        elif self.status == 10:
            spin_right(15, 15)
            time.sleep(spin_time_long)
            run(15, 15)
            self.status = 0
        if code == '0000' and self.flag == 0:  # 遇到黑线，计数器加一，等待下一条
            self.flag = 1
            self.black_line = self.black_line + 1
            brake()
            time.sleep(0.1)
            return 1
        if code == '1111' and self.flag == 1:  # 只有遇到纯白，才会寻找下一条黑线
            run(15, 15)
            self.flag = 0
        return 0

#延时2s
time.sleep(2)

print("=" * 50)
print("双线S型过弯循迹程序启动")
print("=" * 50)
print("硬件配置:")
print("   • 电机引脚: IN1={}, IN2={}, IN3={}, IN4={}".format(IN1, IN2, IN3, IN4))
print("   • PWM引脚: ENA={}, ENB={}".format(ENA, ENB))
print("   • 循迹传感器: L1={}, L2={}, R1={}, R2={}".format(
    TrackSensorLeftPin1, TrackSensorLeftPin2, TrackSensorRightPin1, TrackSensorRightPin2))
print("   • 按键引脚: {}".format(key))
print("=" * 50)
print("传感器状态说明:")
print("   • 0 = 检测到黑线")
print("   • 1 = 检测到白线")
print("   • 格式: L1 L2 R1 R2")
print("   • 双线S型过弯: 0111=右小弯, 1110=左小弯")
print("=" * 50)


init()
print("硬件初始化完成")

# 创建状态机实例
status = Status()

print("开始双线S型过弯循迹测试...")
print("-" * 50)
    
print("进入双线模式")
while True:
    TrackSensorLeftValue1  = GPIO.input(TrackSensorLeftPin1)
    TrackSensorLeftValue2  = GPIO.input(TrackSensorLeftPin2)
    TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
    TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)
        
        # 显示传感器状态1
    sensor_status = "传感器状态: L1:{} L2:{} R1:{} R2:{}".format(
        TrackSensorLeftValue1, TrackSensorLeftValue2, 
        TrackSensorRightValue1, TrackSensorRightValue2)
    print(sensor_status, end=" | ")
        # 根据四路循迹切换状态机的状态
    if status.change_status(get_code()):
        print("退出双线模式")
        break