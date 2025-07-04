#-*- coding:UTF-8 -*-
import RPi.GPIO as GPIO
import time

#小车电机引脚定义
IN1 = 10
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
    #设置pwm引脚和频率为1000hz
    pwm_ENA = GPIO.PWM(ENA, 1000)
    pwm_ENB = GPIO.PWM(ENB, 1000)
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

#按键检测
def key_scan():
    while GPIO.input(key):
        pass
    while not GPIO.input(key):
        time.sleep(0.01)
        if not GPIO.input(key):
            time.sleep(0.01)
        while not GPIO.input(key):
            pass

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
        
        if TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == True and TrackSensorRightValue1 == True and TrackSensorRightValue2 == True:
            run(40, 40)
            time.sleep(0.1)
        
        # 双线S型过弯的核心逻辑
        # 0111 - 向右小弯 (左边第一个传感器检测到黑线，其他都是白线)
        elif (TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == True and 
            TrackSensorRightValue1 == True and TrackSensorRightValue2 == True):
            print("双线S型右小弯 (0111)")
            right(85, 85)  # 右转，左轮快右轮慢
            time.sleep(0.1)
            
        # 1110 - 向左小弯 (右边第一个传感器检测到黑线，其他都是白线)
        elif (TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == True and 
              TrackSensorRightValue1 == True and TrackSensorRightValue2 == False):
            print("双线S型左小弯 (1110)")
            left(85, 85)  # 左转，右轮快左轮慢
            time.sleep(0.1)
            
        # 0011 - 右弯 (左边两个传感器检测到黑线)
        elif (TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and 
              TrackSensorRightValue1 == True and TrackSensorRightValue2 == True):
            print("右弯 (0011)")
            right(85, 85)  # 右转，左轮快右轮慢
            time.sleep(0.1)
            
        # 1100 - 左弯 (右边两个传感器检测到黑线)
        elif (TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == True and 
              TrackSensorRightValue1 == False and TrackSensorRightValue2 == False):
            print("左弯 (1100)")
            left(85, 85)  # 左转，右轮快左轮慢
            time.sleep(0.1)
            
        # 0011 - 双线直行 (两个中间传感器检测到黑线)
        # elif (TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and 
        #       TrackSensorRightValue1 == True and TrackSensorRightValue2 == True):
        #     # print("双线直行 (0011)")
        #     # run(10, 40)
        #     right(85, 85)
        #     time.sleep(0.1)
        #     
        # # 1100 - 双线直行 (两个中间传感器检测到黑线)
        # elif (TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == True and 
        #       TrackSensorRightValue1 == False and TrackSensorRightValue2 == False):
        #     # print("双线直行 (1100)")
        #     # run(10, 40)
        #     left(85, 85)
        #     time.sleep(0.1)
            
        # 0110 - 双线直行 (两个中间传感器检测到黑线)
        elif (TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == True and 
              TrackSensorRightValue1 == True and TrackSensorRightValue2 == False):
            print("双线直行 (0110)")
            run(40, 40)
            time.sleep(0.1)
            
        # 1001 - 双线直行 (两个外侧传感器检测到黑线)
        elif (TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == False and 
              TrackSensorRightValue1 == False and TrackSensorRightValue2 == True):
            print("双线直行 (1001)")
            run(40, 40)
            time.sleep(0.1)
            
        # # 0001 - 右侧偏移修正
        # elif (TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and 
        #       TrackSensorRightValue1 == False and TrackSensorRightValue2 == True):
        #     print("右侧偏移修正 (0001)")
        #     left(38, 85)
        #     time.sleep(0.1)
        #     
        # # 1000 - 左侧偏移修正
        # elif (TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == False and 
        #       TrackSensorRightValue1 == False and TrackSensorRightValue2 == False):
        #     print("左侧偏移修正 (1000)")
        #     right(85, 38)
        #     time.sleep(0.1)
            
        # 0000 - 全部检测到黑线，可能是交叉路口或起始点
        elif (TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and 
              TrackSensorRightValue1 == False and TrackSensorRightValue2 == False):
            print("全线检测 (0000) - 交叉路口或起始点")
            # run(10, 10)  # 继续前进
            brake()
            time.sleep(0.1)
            
        # 1111 - 全部检测到白线，脱离轨道
        elif (TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == True and 
              TrackSensorRightValue1 == True and TrackSensorRightValue2 == True):
            print("脱离轨道 (1111) - 寻找线路")
            # 可以添加寻线逻辑，这里暂时停止
            brake()
            time.sleep(0.1)
            
        # 其他情况的处理
        else:
            print("其他状态 - 保持当前运动")
            time.sleep(0.1)
            # 可以根据需要添加更多的状态处理
            
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