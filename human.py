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
TrackSensorLeftPin1  =  3   #定义左边第一个循迹红外传感器引脚为3口
TrackSensorLeftPin2  =  5   #定义左边第二个循迹红外传感器引脚为5口
TrackSensorRightPin1 =  4   #定义右边第一个循迹红外传感器引脚为4口
TrackSensorRightPin2 =  18  #定义右边第二个循迹红外传感器引脚为18口

#超声波引脚定义
EchoPin = 0
TrigPin = 1

#设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

#忽略警告信息
GPIO.setwarnings(False)

#速度参数
NORMAL_SPEED = 35      # 正常行驶速度
SLOW_SPEED = 25        # 慢速行驶
TURN_SPEED = 30        # 转弯速度
PARKING_SPEED = 30     # 停车速度
LEFT_SPEED = 0         # 左转时左轮速度
RIGHT_SPEED = 35       # 左转时右轮速度
SPIN_LEFT_SPEED = 30   # 原地左转速度
SPIN_RIGHT_SPEED = 30  # 原地右转速度

#时间参数
TURN_90_DEGREE = 0.35  # 90度转弯时间
TURN_180_DEGREE = 0.7  # 180度转弯时间
FORWARD_TIME = 1.0     # 前进时间
BACKWARD_TIME = 1.0    # 后退时间
BRAKE_TIME = 0.5       # 刹车时间
DETECT_DELAY = 0.01    # 检测延时

#距离参数
OBSTACLE_DISTANCE = 30  # 障碍物检测距离(cm)
SAFE_DISTANCE = 50      # 安全距离(cm)
MAX_DISTANCE = 500      # 最大检测距离(cm)

#循迹参数
LINE_DETECT_DELAY = 0.1  # 循迹检测延时
DOUBLE_LINE_FORWARD_TIME = 0.5  # 双线直行时间
TURN_DELAY = 0.05  # 转弯检测延时
SENSOR_DEBOUNCE_TIME = 0.02  # 传感器防抖时间

#停车参数
BACKWARD_TIME_1 = 1.0    # 第一次后退时间
BACKWARD_TIME_2 = 1.5    # 第二次后退时间
FORWARD_ADJUST_TIME = 0.5 # 前进调整时间
BACKWARD_PARK_TIME = 0.8  # 后退停车时间
FORWARD_EXIT_TIME = 1.0   # 前进离开时间
FORWARD_CROSS_TIME = 1.5  # 前进越过标识时间

#状态定义
STATE_TRACKING = "tracking"      # 循迹状态
STATE_AVOIDING = "avoiding"      # 避障状态
STATE_PARKING = "parking"        # 停车状态
STATE_DOUBLE_LINE = "double_line" # 双线处理状态

#特殊标识配置
PARKING_START_COUNT = 2    # 开始侧方停车的特殊标识计数
MIN_BLACK_COUNT = 4        # 检测特殊标识所需的最少黑线数量

#调试配置
ENABLE_PRINT = True        # 启用打印输出
ENABLE_DISTANCE_PRINT = False  # 启用距离打印
ENABLE_SENSOR_PRINT = False     # 启用传感器状态打印

#转弯补偿配置
TURN_COMPENSATION = True   # 启用转弯补偿
COMPENSATION_DELAY = 0.1   # 补偿延时

#PWM配置
PWM_FREQUENCY = 2000       # PWM频率

#全局变量
pwm_ENA = None
pwm_ENB = None
current_state = STATE_TRACKING  # 当前状态
obstacle_count = 0  # 障碍物计数
special_mark_count = 0  # 特殊标识计数
double_line_count = 0  # 双线计数

#电机引脚初始化为输出模式
#按键引脚初始化为输入模式
#寻迹引脚初始化为输入模式
#超声波引脚初始化
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
    GPIO.setup(EchoPin,GPIO.IN)
    GPIO.setup(TrigPin,GPIO.OUT)
    #设置pwm引脚和频率
    pwm_ENA = GPIO.PWM(ENA, PWM_FREQUENCY)
    pwm_ENB = GPIO.PWM(ENB, PWM_FREQUENCY)
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
    
if __name__ == "__main__":
  try:
    init()
    run(NORMAL_SPEED, NORMAL_SPEED)
  except KeyboardInterrupt:
    print("程序被用户中断")
  finally:
    print("停止所有电机")
    brake()
    print("停止PWM输出")
    pwm_ENA.stop()
    pwm_ENB.stop()
    print("清理GPIO")
    GPIO.cleanup()
