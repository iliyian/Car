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

try:
    init()
    print("硬件初始化完成")
    print("开始双线S型过弯循迹测试...")
    print("-" * 50)
    
    while True:
        #检测到黑线时循迹模块相应的指示灯亮，端口电平为LOW
        #未检测到黑线时循迹模块相应的指示灯灭，端口电平为HIGH
        TrackSensorLeftValue1  = GPIO.input(TrackSensorLeftPin1)
        TrackSensorLeftValue2  = GPIO.input(TrackSensorLeftPin2)
        TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
        TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)
        
        # 显示传感器状态
        sensor_status = "传感器状态: L1:{} L2:{} R1:{} R2:{}".format(
            TrackSensorLeftValue1, TrackSensorLeftValue2, 
            TrackSensorRightValue1, TrackSensorRightValue2)
        print(sensor_status, end=" | ")
        
        # 双线S型过弯的核心逻辑
        if TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False and TrackSensorRightValue2 == False:
            print("左锐角/直角转弯")
            spin_left(30, 35)
            time.sleep(0.1)

        #四路循迹引脚电平状态
        # 0 0 X 0
        # 1 0 X 0
        # 0 1 X 0
        #以上6种电平状态时小车原地右转
        #处理右锐角和右直角的转动
        elif (TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == True) and (TrackSensorRightValue2 == False or TrackSensorRightValue1 == False):
           print("最右边触线，左转")
           left(0,35)
           time.sleep(0.1)
 
        #四路循迹引脚电平状态
        # 0 X 0 0       
        # 0 X 0 1 
        # 0 X 1 0       
        #处理左锐角和左直角的转动
        elif (TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False) and (TrackSensorRightValue2 == True or TrackSensorRightValue1 == True):
           print("最左边触线，右转")
           right(35, 0)
           time.sleep(0.1)
  
        # 0 X X X
        #最左边检测到
        # elif TrackSensorLeftValue1 == False:
        #     print("最左边检测到，左转")
        #     spin_left(30, 30)
     
        # # X X X 0
        # #最右边检测到
        # elif TrackSensorRightValue2 == False:
        #     print("最右边检测到，右转")
        #     spin_right(30, 30)
   
        #四路循迹引脚电平状态
        # X 0 1 X
        #处理左小弯
        # elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
        #     print("左小弯")
        #     left(0,35)
   
        # #四路循迹引脚电平状态
        # # X 1 0 X  
        # #处理右小弯
        # elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
        #     print("右小弯")
        #     right(35, 0)
   
        #四路循迹引脚电平状态
        # X 0 0 X
        #处理直线
        elif TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == True and TrackSensorRightValue1 == True and TrackSensorRightValue2 == True:
            print("直线行驶")
            run(20, 20)
   
        #当为1 1 1 1时小车保持上一个小车运行状态
        else:
            print("保持当前状态")
except KeyboardInterrupt:
    print("\n" + "=" * 50)
    print("程序被用户中断")
    print("停止所有电机")
    brake()
    print("停止PWM输出")
    pwm_ENA.stop()
    pwm_ENB.stop()
    print("清理GPIO")
    GPIO.cleanup()
    print("程序结束，GPIO已清理")
    print("=" * 50)