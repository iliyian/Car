#-*- coding:UTF-8 -*-
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

#优化的循迹逻辑判断函数
def get_tracking_action(L1, L2, R1, R2):
    """
    根据四个传感器的状态返回相应的循迹动作
    参数: L1, L2, R1, R2 - 四个传感器的状态 (False=黑线, True=白线)
    返回: (动作名称, 左轮速度, 右轮速度, 是否需要延时)
    """
    
    # 计算黑线数量
    left_black = [L1, L2].count(False)
    right_black = [R1, R2].count(False)
    total_black = left_black + right_black
    
    # 特殊标识检测（全部黑线）
    if total_black == 4:
        return ("特殊标识", 20, 20, True)
    
    # 直角转弯检测
    if left_black >= 1 and right_black >= 1:
        if left_black > right_black:
            return ("左直角转弯", 80, 85, True)
        else:
            return ("右直角转弯", 85, 80, True)
    
    # 锐角转弯检测
    if left_black >= 2:
        return ("左锐角转弯", 80, 85, True)
    if right_black >= 2:
        return ("右锐角转弯", 85, 80, True)
    
    # 单侧检测
    if L1 == False:  # 最左边
        return ("最左边检测", 80, 80, False)
    if L2 == False:  # 左中
        return ("左小弯", 0, 85, False)
    if R1 == False:  # 右中
        return ("右小弯", 85, 0, False)
    if R2 == False:  # 最右边
        return ("最右边检测", 80, 80, False)
    
    # 直线行驶
    if L2 == False and R1 == False:
        return ("直线行驶", 20, 20, False)
    
    # 默认状态
    return ("保持当前状态", 0, 0, False)

#延时2s	
time.sleep(2)

print("=" * 50)
print("循迹测试程序启动")
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
print("=" * 50)

#try/except语句用来检测try语句块中的错误，
#从而让except语句捕获异常信息并处理。

cnt = 0

try:
    init()
    print("硬件初始化完成")
    print("开始循迹测试...")
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
        
        # 特殊标识处理
        if TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False and TrackSensorRightValue2 == False:
            if cnt == 0:
                run(20, 20)
            else:
                brake()
            time.sleep(0.1)
            cnt += 1
            continue
        
        # 使用优化的循迹逻辑
        action_name, left_speed, right_speed, need_delay = get_tracking_action(
            TrackSensorLeftValue1, TrackSensorLeftValue2, 
            TrackSensorRightValue1, TrackSensorRightValue2)
        
        print(action_name)
        
        # 执行相应的动作
        if action_name == "特殊标识":
            run(left_speed, right_speed)
        elif action_name in ["左直角转弯", "左锐角转弯", "最左边检测"]:
            spin_left(left_speed, right_speed)
        elif action_name in ["右直角转弯", "右锐角转弯", "最右边检测"]:
            spin_right(left_speed, right_speed)
        elif action_name == "左小弯":
            left(left_speed, right_speed)
        elif action_name == "右小弯":
            right(left_speed, right_speed)
        elif action_name == "直线行驶":
            run(left_speed, right_speed)
        else:  # 保持当前状态
            brake()
        
        # 根据动作类型决定是否需要延时
        if need_delay:
            time.sleep(0.1)
       
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

