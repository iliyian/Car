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

#超声波引脚定义
EchoPin = 0
TrigPin = 1

#避障距离阈值设置
OBSTACLE_DISTANCE = 30  # 障碍物距离阈值（厘米）
SAFE_DISTANCE = 50      # 安全距离阈值（厘米）

#环境温度设置（用于声速计算）
ENVIRONMENT_TEMPERATURE = 25  # 环境温度（摄氏度）

#传感器读取模式配置
SENSOR_READING_MODE = "multiple_samples"  # 可选: "single", "multiple_samples", "timing_compensation"
# single: 单次读取（原始方法）
# multiple_samples: 多次采样多数表决
# timing_compensation: 时序补偿（推荐，专门解决R2偏后问题）

#设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

#忽略警告信息
GPIO.setwarnings(False)

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
    #设置pwm引脚和频率为2000hz
    pwm_ENA = GPIO.PWM(ENA, 2000)
    pwm_ENB = GPIO.PWM(ENB, 2000)
    pwm_ENA.start(0)
    pwm_ENB.start(0)

#声速计算函数（根据温度）
def calculate_sound_speed(temperature):
    """
    根据温度计算声速
    声速 = 331.4 + 0.6 × 温度(℃)
    参数: temperature - 温度（摄氏度）
    返回: 声速（米/秒）
    """
    return 331.4 + 0.6 * temperature

#超声波测距函数（支持温度补偿）
def Distance(temperature=25):
    """
    超声波测距函数
    参数: temperature - 环境温度（摄氏度），默认25度
    返回: 距离（厘米）
    """
    # 根据温度计算声速
    sound_speed = calculate_sound_speed(temperature)
    
    GPIO.output(TrigPin,GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TrigPin,GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(TrigPin,GPIO.LOW)

    t3 = time.time()

    while not GPIO.input(EchoPin):
        t4 = time.time()
        if (t4 - t3) > 0.03 :
            return -1

    t1 = time.time()
    while GPIO.input(EchoPin):
        t5 = time.time()
        if(t5 - t1) > 0.03 :
            return -1

    t2 = time.time()
    time.sleep(0.01)
    
    # 使用动态计算的声速
    distance = ((t2 - t1) * sound_speed / 2) * 100
    return distance

#超声波测距测试函数（多次测量取平均值，支持温度补偿）
def Distance_test(temperature=25):
    """
    超声波测距测试函数
    参数: temperature - 环境温度（摄氏度），默认25度
    返回: 平均距离（厘米）
    """
    num = 0
    ultrasonic = []
    while num < 3:  # 减少测量次数以提高响应速度
        distance = Distance(temperature)
        while int(distance) == -1 :
            distance = Distance(temperature)
        while (int(distance) >= 500 or int(distance) == 0) :
            distance = Distance(temperature)
        ultrasonic.append(distance)
        num = num + 1
        time.sleep(0.01)
    distance = sum(ultrasonic) / len(ultrasonic)
    return distance

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
        elif left_black < right_black:
            return ("右直角转弯", 85, 80, True)
        else:
            return ("直线行驶", 20, 20, False)
    
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
    
    if total_black == 0:
        return ("直线", 20, 20, True)
    
    # 默认状态
    return ("保持当前状态", 0, 0, False)

#多次采样传感器读取函数（解决R2传感器偏后的时序问题）
def read_sensors_multiple_samples(sample_count=5, sample_interval=0.001):
    """
    多次采样读取传感器状态，采用多数表决法
    参数: 
        sample_count - 采样次数，默认5次
        sample_interval - 采样间隔时间（秒），默认0.01秒
    返回: (L1, L2, R1, R2) - 四个传感器的最终状态
    """
    # 存储每次采样的结果
    samples = {
        'L1': [],
        'L2': [], 
        'R1': [],
        'R2': []
    }
    
    # 进行多次采样
    for i in range(sample_count):
        # 读取传感器状态
        L1 = GPIO.input(TrackSensorLeftPin1)
        L2 = GPIO.input(TrackSensorLeftPin2)
        R1 = GPIO.input(TrackSensorRightPin1)
        R2 = GPIO.input(TrackSensorRightPin2)
        
        # 存储采样结果
        samples['L1'].append(L1)
        samples['L2'].append(L2)
        samples['R1'].append(R1)
        samples['R2'].append(R2)
        
        # 采样间隔
        if i < sample_count - 1:  # 最后一次采样后不需要延时
            time.sleep(sample_interval)
    
    # 多数表决法确定最终状态
    # 如果False（黑线）的数量 >= True（白线）的数量，则判定为False
    final_L1 = samples['L1'].count(False) >= samples['L1'].count(True)
    final_L2 = samples['L2'].count(False) >= samples['L2'].count(True)
    final_R1 = samples['R1'].count(False) >= samples['R1'].count(True)
    final_R2 = samples['R2'].count(False) >= samples['R2'].count(True)
    
    # 调试信息：显示采样统计
    debug_info = "采样统计 - L1:{}/{} L2:{}/{} R1:{}/{} R2:{}/{}".format(
        samples['L1'].count(False), samples['L1'].count(True),
        samples['L2'].count(False), samples['L2'].count(True),
        samples['R1'].count(False), samples['R1'].count(True),
        samples['R2'].count(False), samples['R2'].count(True)
    )
    
    return (final_L1, final_L2, final_R1, final_R2), debug_info

#时序补偿传感器读取函数（专门处理R2传感器偏后问题）
def read_sensors_with_timing_compensation():
    """
    时序补偿传感器读取，专门处理R2传感器偏后的问题
    返回: (L1, L2, R1, R2) - 四个传感器的最终状态
    """
    # 第一轮采样：读取所有传感器
    L1_1 = GPIO.input(TrackSensorLeftPin1)
    L2_1 = GPIO.input(TrackSensorLeftPin2)
    R1_1 = GPIO.input(TrackSensorRightPin1)
    R2_1 = GPIO.input(TrackSensorRightPin2)
    
    # 短暂延时，等待R2传感器稳定
    time.sleep(0.02)  # 20ms延时，给R2传感器更多时间
    
    # 第二轮采样：重点检查R2传感器
    L1_2 = GPIO.input(TrackSensorLeftPin1)
    L2_2 = GPIO.input(TrackSensorLeftPin2)
    R1_2 = GPIO.input(TrackSensorRightPin1)
    R2_2 = GPIO.input(TrackSensorRightPin2)
    
    # 第三轮采样：再次确认R2状态
    time.sleep(0.01)  # 10ms延时
    L1_3 = GPIO.input(TrackSensorLeftPin1)
    L2_3 = GPIO.input(TrackSensorLeftPin2)
    R1_3 = GPIO.input(TrackSensorRightPin1)
    R2_3 = GPIO.input(TrackSensorRightPin2)
    
    # 确定最终状态
    # 对于L1, L2, R1：使用前两轮采样的多数表决
    final_L1 = (L1_1 + L1_2) >= 1  # 如果两轮中有1轮或以上为True，则判定为True
    final_L2 = (L2_1 + L2_2) >= 1
    final_R1 = (R1_1 + R1_2) >= 1
    
    # 对于R2：使用三轮采样的多数表决，并考虑时序补偿
    R2_votes = [R2_1, R2_2, R2_3]
    final_R2 = R2_votes.count(False) >= R2_votes.count(True)
    
    # 时序补偿逻辑：如果L1检测到黑线但R2没有，可能是R2还没检测到
    if not final_L1 and final_R2:  # L1=黑线，R2=白线
        # 检查R2是否在后续采样中变为黑线
        if R2_2 == False or R2_3 == False:
            final_R2 = False  # 补偿R2为黑线
    
    # 调试信息
    debug_info = "时序补偿 - R2采样:{}->{}->{} 最终:{}".format(
        R2_1, R2_2, R2_3, final_R2)
    
    return (final_L1, final_L2, final_R1, final_R2), debug_info

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
    time.sleep(0.405)  # 调整时间以达到90度
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
    time.sleep(0.405)  # 调整时间以达到90度
    brake()
    time.sleep(0.1)
    
    # 4. 前进回到原路径
    print("步骤4: 前进回到原路径")
    run(35, 35)
    time.sleep(1.0)  # 前进0.8秒
    brake()
    time.sleep(0.1)
    
    # 5. 原地左转90度
    print("步骤5: 原地左转90度")
    spin_left(40, 40)
    time.sleep(0.5)  # 调整时间以达到90度
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


init()
print("硬件初始化完成")

#延时2s	
# time.sleep(2)
# avoid_obstacle()
# raise Exception("测试")

print("=" * 50)
print("循迹避障测试程序启动")
print("=" * 50)
print("硬件配置:")
print("   • 电机引脚: IN1={}, IN2={}, IN3={}, IN4={}".format(IN1, IN2, IN3, IN4))
print("   • PWM引脚: ENA={}, ENB={}".format(ENA, ENB))
print("   • 循迹传感器: L1={}, L2={}, R1={}, R2={}".format(
    TrackSensorLeftPin1, TrackSensorLeftPin2, TrackSensorRightPin1, TrackSensorRightPin2))
print("   • 超声波传感器: Echo={}, Trig={}".format(EchoPin, TrigPin))
print("   • 按键引脚: {}".format(key))
print("=" * 50)
print("避障设置:")
print("   • 障碍物距离阈值: {} cm".format(OBSTACLE_DISTANCE))
print("   • 安全距离阈值: {} cm".format(SAFE_DISTANCE))
print("   • 环境温度: {}°C".format(ENVIRONMENT_TEMPERATURE))
print("   • 计算声速: {:.1f} m/s".format(calculate_sound_speed(ENVIRONMENT_TEMPERATURE)))
print("=" * 50)
print("传感器读取模式: {}".format(SENSOR_READING_MODE))
if SENSOR_READING_MODE == "timing_compensation":
    print("   • 时序补偿模式：专门解决R2传感器偏后问题")
elif SENSOR_READING_MODE == "multiple_samples":
    print("   • 多次采样模式：使用多数表决法提高准确性")
else:
    print("   • 单次读取模式：原始方法，可能存在时序问题")
print("=" * 50)
print("传感器状态说明:")
print("   • 0 = 检测到黑线")
print("   • 1 = 检测到白线")
print("   • 格式: L1 L2 R1 R2")
print("=" * 50)

#try/except语句用来检测try语句块中的错误，
#从而让except语句捕获异常信息并处理。

cnt = 0
distance = Distance_test(ENVIRONMENT_TEMPERATURE)
sound_speed = calculate_sound_speed(ENVIRONMENT_TEMPERATURE)

try:
    print("开始循迹避障测试...")
    print("-" * 50)
    
    
    while True:
        # 超声波测距检测（使用温度补偿）
        print("前方距离: {:.1f} cm".format(distance), end=" | ")
        
        # 如果检测到障碍物，执行绕行
        if distance < OBSTACLE_DISTANCE and cnt > 0:
            print("检测到障碍物！")
            if avoid_obstacle():
                continue  # 绕行成功，继续循迹
            else:
                # 绕行失败，等待障碍物移除
                while Distance_test(ENVIRONMENT_TEMPERATURE) < OBSTACLE_DISTANCE:
                    time.sleep(0.5)
                print("障碍物已移除，继续循迹")
                continue
        
        # 根据配置选择传感器读取方法
        if SENSOR_READING_MODE == "single":
            # 单次读取（原始方法）
            TrackSensorLeftValue1  = GPIO.input(TrackSensorLeftPin1)
            TrackSensorLeftValue2  = GPIO.input(TrackSensorLeftPin2)
            TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
            TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)
            debug_info = "单次读取模式"
        elif SENSOR_READING_MODE == "multiple_samples":
            # 多次采样多数表决
            (TrackSensorLeftValue1, TrackSensorLeftValue2, TrackSensorRightValue1, TrackSensorRightValue2), debug_info = read_sensors_multiple_samples()
        else:
            # 时序补偿（默认推荐方法）
            (TrackSensorLeftValue1, TrackSensorLeftValue2, TrackSensorRightValue1, TrackSensorRightValue2), debug_info = read_sensors_with_timing_compensation()
        
        # 显示传感器状态、采样统计和测距结果
        sensor_status = "传感器状态: {} {} {} {} | 测距: {:.1f}cm".format(
            int(TrackSensorLeftValue1), int(TrackSensorLeftValue2), 
            int(TrackSensorRightValue1), int(TrackSensorRightValue2), distance)
        print(sensor_status, end=" | ")
        # print(debug_info, end=" | ")
        
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
            pass
            # brake()
        
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

