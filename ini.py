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
    GPIO.setup(EchoPin,GPIO.IN)
    GPIO.setup(TrigPin,GPIO.OUT)
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
    
#超声波引脚定义
EchoPin = 0
TrigPin = 1

TEMPERATURE = 30
SPEED_OF_SOUND = 331 + 0.6 * TEMPERATURE
    
def distance():
    """单次超声波测距，带超时检测"""
    GPIO.output(TrigPin, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TrigPin, GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(TrigPin, GPIO.LOW)

    t3 = time.time()

    # 等待回声引脚变高，带超时检测
    while not GPIO.input(EchoPin):
        t4 = time.time()
        if (t4 - t3) > 0.03:  # 超时30ms
            return -1

    t1 = time.time()
    
    # 等待回声引脚变低，带超时检测
    while GPIO.input(EchoPin):
        t5 = time.time()
        if (t5 - t1) > 0.03:  # 超时30ms
            return -1

    t2 = time.time()
    time.sleep(0.01)
    
    # 计算距离 (cm)
    distance_cm = ((t2 - t1) * SPEED_OF_SOUND / 2) * 100
    return distance_cm

def distance_test():
    """多次测量取平均值，提高测量准确性"""
    num = 0
    ultrasonic = []
    
    while num < 5:
        dist = distance()
        
        # 重新测量直到获得有效数据
        while int(dist) == -1:
            dist = distance()
            print("测量超时，重新测量...")
        
        # 过滤异常数据
        while (int(dist) >= 500 or int(dist) == 0):
            dist = distance()
            print("测量数据异常: %f cm，重新测量..." % dist)
        
        ultrasonic.append(dist)
        num = num + 1
        time.sleep(0.01)
    
    print("五次测量结果:", ultrasonic)
    
    # 取中间三次测量的平均值，去除极值
    distance_avg = (ultrasonic[1] + ultrasonic[2] + ultrasonic[3]) / 3
    print("平均距离: %.2f cm" % distance_avg)
    return distance_avg
  
#绕行函数
def avoid_obstacle():
    print("检测到障碍物，开始硬编码绕行...")
    
    # 停止前进
    brake()
    time.sleep(0.1)
    
    # 硬编码绕行动作序列
    # 1. 原地右转90度
    print("步骤1: 原地右转90度")
    spin_right(40, 40)
    time.sleep(0.355)  # 调整时间以达到90度
    brake()
    time.sleep(0.1)
    
    # 2. 前进一段距离绕过障碍物
    print("步骤2: 前进绕过障碍物")
    run(35, 35)
    time.sleep(0.5)  # 前进1秒
    brake()
    time.sleep(0.1)
    
    # 3. 原地左转90度
    print("步骤3: 原地左转90度")
    spin_left(40, 40)
    time.sleep(0.355)  # 调整时间以达到90度
    brake()
    time.sleep(0.1)
    
    # 4. 前进回到原路径
    print("步骤4: 前进回到原路径")
    run(35, 35)
    time.sleep(1.2)  # 前进0.8秒
    brake()
    time.sleep(0.1)
    
    # 5. 原地左转90度
    print("步骤5: 原地左转90度")
    spin_left(40, 40)
    time.sleep(0.405)  # 调整时间以达到90度
    brake()
    time.sleep(0.1)
    
    # 6. 前进回到循迹线
    print("步骤6: 前进回到循迹线")
    run(35, 35)
    time.sleep(0.5)  # 前进0.5秒
    brake()
    
    print("转弯")
    spin_right(40, 40)
    time.sleep(0.5)
    brake()
    time.sleep(0.1)
    
    print("硬编码绕行完成，继续循迹")
    return True

def search_line():
    while True:
        distance = distance_test()
        print("距离: ", distance, end=' | ')
        if distance < 10:
            return

        #检测到黑线时循迹模块相应的指示灯亮，端口电平为LOW
        #未检测到黑线时循迹模块相应的指示灯灭，端口电平为HIGH
        TrackSensorLeftValue1  = GPIO.input(TrackSensorLeftPin1)
        TrackSensorLeftValue2  = GPIO.input(TrackSensorLeftPin2)
        TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
        TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)

        # 显示传感器状态
        sensor_status = "传感器状态: {} {} {} {}".format(
            int(TrackSensorLeftValue1), int(TrackSensorLeftValue2),
            int(TrackSensorRightValue1), int(TrackSensorRightValue2))
        print(sensor_status, end=" | ")
        
        if TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False and TrackSensorRightValue2 == False:
          brake()
          time.sleep(0.1)
          break

        #四路循迹引脚电平状态
        # 0 0 X 0
        # 1 0 X 0
        # 0 1 X 0
        #以上6种电平状态时小车原地右转
        #处理右锐角和右直角的转动
        if (TrackSensorLeftValue1 == False or TrackSensorLeftValue2 == False) and  TrackSensorRightValue2 == False:
           print("右锐角/右直角转动 - 原地右转(35,30)")
           spin_right(35, 30)
           time.sleep(0.1)

        #四路循迹引脚电平状态
        # 0 X 0 0
        # 0 X 0 1
        # 0 X 1 0
        #处理左锐角和左直角的转动
        elif TrackSensorLeftValue1 == False and (TrackSensorRightValue1 == False or  TrackSensorRightValue2 == False):
           print("左锐角/左直角转动 - 原地左转(30,35)")
           spin_left(30,35 )
           time.sleep(0.1)

        # 0 X X X
        #最左边检测到
        elif TrackSensorLeftValue1 == False:
           print("最左边检测到 - 原地左转(30,30)")
           spin_left(30, 30)

        # X X X 0
        #最右边检测到
        elif TrackSensorRightValue2 == False:
           print("最右边检测到 - 原地右转(30,30)")
           spin_right(30, 30)

        #四路循迹引脚电平状态
        # X 0 1 X
        #处理左小弯
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
           print("左小弯 - 左转(0,35)")
           left(0,35)

        #四路循迹引脚电平状态
        # X 1 0 X
        #处理右小弯
        elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
           print("右小弯 - 右转(35,0)")
           right(35, 0)

        #四路循迹引脚电平状态
        # X 0 0 X
        #处理直线
        elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
           print("直线行驶 - 前进(35,35)")
           run(35, 35)
        
        else:
           print("保持上一状态 - 传感器状态: {} {} {} {}".format(
               int(TrackSensorLeftValue1), int(TrackSensorLeftValue2),
               int(TrackSensorRightValue1), int(TrackSensorRightValue2)))

        #当为1 1 1 1时小车保持上一个小车运行状态
        
        # 添加短暂延时，避免输出过快
        # time.sleep(0.1)

#try/except语句用来检测try语句块中的错误，
#从而让except语句捕获异常信息并处理。
try:
    init()
    print("硬件初始化完成")
    print("=" * 50)
    print("循迹程序启动")
    print("=" * 50)
    print("传感器状态说明:")
    print("   • False/0 = 检测到黑线")
    print("   • True/1 = 检测到白线")
    print("   • 格式: L1 L2 R1 R2")
    print("=" * 50)
    
    search_line()
    avoid_obstacle()
    search_line()
    


except KeyboardInterrupt:
    print("\n" + "=" * 50)
    print("程序被用户中断")
    print("停止所有电机")
    print("停止PWM输出")
    print("清理GPIO")
    print("=" * 50)
    pass
pwm_ENA.stop()
pwm_ENB.stop()
GPIO.cleanup()