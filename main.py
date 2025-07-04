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

#超声波测距函数
def Distance():
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
    return ((t2 - t1)* 340 / 2) * 100

#超声波测距测试函数
def Distance_test():
    num = 0
    ultrasonic = []
    while num < 5:
        distance = Distance()
        while int(distance) == -1 :
            distance = Distance()
        while (int(distance) >= MAX_DISTANCE or int(distance) == 0) :
            distance = Distance()
        ultrasonic.append(distance)
        num = num + 1
        time.sleep(0.01)
    distance = (ultrasonic[1] + ultrasonic[2] + ultrasonic[3])/3
    return distance

#检测特殊标识（全部为黑线）
def detect_special_mark():
    TrackSensorLeftValue1  = GPIO.input(TrackSensorLeftPin1)
    TrackSensorLeftValue2  = GPIO.input(TrackSensorLeftPin2)
    TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
    TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)
    
    # 全部为黑线时返回True
    return (TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and 
            TrackSensorRightValue1 == False and TrackSensorRightValue2 == False)

#检测双线（识别不到线）
def detect_double_line():
    TrackSensorLeftValue1  = GPIO.input(TrackSensorLeftPin1)
    TrackSensorLeftValue2  = GPIO.input(TrackSensorLeftPin2)
    TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
    TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)
    
    # 全部为白线时返回True
    return (TrackSensorLeftValue1 == True and TrackSensorLeftValue2 == True and 
            TrackSensorRightValue1 == True and TrackSensorRightValue2 == True)

#稳定的传感器读取函数（多次读取取平均值）
def read_sensors_stable():
    readings = []
    for i in range(3):  # 读取3次
        TrackSensorLeftValue1  = GPIO.input(TrackSensorLeftPin1)
        TrackSensorLeftValue2  = GPIO.input(TrackSensorLeftPin2)
        TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
        TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)
        readings.append([TrackSensorLeftValue1, TrackSensorLeftValue2, TrackSensorRightValue1, TrackSensorRightValue2])
        time.sleep(SENSOR_DEBOUNCE_TIME)
    
    # 取多数值作为最终结果
    final_values = []
    for i in range(4):
        values = [reading[i] for reading in readings]
        # 如果False的数量大于True的数量，则认为是False（检测到黑线）
        final_values.append(values.count(False) > values.count(True))
    
    return final_values[0], final_values[1], final_values[2], final_values[3]

#改进的转弯检测函数
def detect_turn_type():
    # 使用稳定的传感器读取
    L1, L2, R1, R2 = read_sensors_stable()
    
    left_black = [L1, L2].count(False)
    right_black = [R1, R2].count(False)
    
    if ENABLE_SENSOR_PRINT:
        print("稳定传感器状态: L1:{} L2:{} R1:{} R2:{}".format(L1, L2, R1, R2))
        print("左侧黑线数: {}, 右侧黑线数: {}".format(left_black, right_black))
    
    # 判断转弯类型
    if left_black >= 2 and right_black >= 1:
        return "left_sharp"  # 左锐角
    elif right_black >= 2 and left_black >= 1:
        return "right_sharp"  # 右锐角
    elif left_black >= 1 and right_black >= 1:
        if left_black > right_black:
            return "left_90"  # 左直角
        else:
            return "right_90"  # 右直角
    elif left_black >= 1:
        return "left_slight"  # 左轻微
    elif right_black >= 1:
        return "right_slight"  # 右轻微
    else:
        return "straight"  # 直线

#转弯补偿函数
def turn_compensation(turn_type):
    if not TURN_COMPENSATION:
        return
    
    print("执行转弯补偿...")
    
    # 根据转弯类型进行补偿
    if turn_type in ["left_sharp", "left_90"]:
        # 左转补偿：继续左转一小段时间
        spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
        time.sleep(COMPENSATION_DELAY)
        brake()
        time.sleep(SENSOR_DEBOUNCE_TIME)
        
        # 检查是否回到线上
        L1, L2, R1, R2 = read_sensors_stable()
        if L1 and L2 and R1 and R2:  # 如果还是全部白线
            print("补偿后仍未检测到线，继续左转")
            spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
            time.sleep(COMPENSATION_DELAY)
            brake()
    
    elif turn_type in ["right_sharp", "right_90"]:
        # 右转补偿：继续右转一小段时间
        spin_right(SPIN_RIGHT_SPEED, SPIN_RIGHT_SPEED)
        time.sleep(COMPENSATION_DELAY)
        brake()
        time.sleep(SENSOR_DEBOUNCE_TIME)
        
        # 检查是否回到线上
        L1, L2, R1, R2 = read_sensors_stable()
        if L1 and L2 and R1 and R2:  # 如果还是全部白线
            print("补偿后仍未检测到线，继续右转")
            spin_right(SPIN_RIGHT_SPEED, SPIN_RIGHT_SPEED)
            time.sleep(COMPENSATION_DELAY)
            brake()
    
    print("转弯补偿完成")

#超声波避障函数
def avoid_obstacle():
    global current_state
    print("检测到障碍物，开始避障...")
    print("当前距离: {:.1f}cm".format(Distance_test()))
    
    # 停止前进
    print("停止前进")
    brake()
    time.sleep(BRAKE_TIME)
    
    # 右转90度
    print("右转90度避障")
    spin_right(SPIN_RIGHT_SPEED, SPIN_RIGHT_SPEED)
    time.sleep(TURN_90_DEGREE)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 检测前方距离
    distance = Distance_test()
    print("避障后距离: {:.1f}cm".format(distance))
    if distance < SAFE_DISTANCE:
        # 如果前方仍有障碍物，左转180度
        print("前方仍有障碍物，左转180度")
        spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
        time.sleep(TURN_180_DEGREE)
        brake()
        time.sleep(BRAKE_TIME)
        distance = Distance_test()
        print("180度转后距离: {:.1f}cm".format(distance))
        if distance < SAFE_DISTANCE:
            # 如果还是不行，再左转90度
            print("仍有障碍物，再左转90度")
            spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
            time.sleep(TURN_90_DEGREE)
            brake()
            time.sleep(BRAKE_TIME)
    
    # 前进一段距离
    print("前进绕过障碍物")
    run(NORMAL_SPEED, NORMAL_SPEED)
    time.sleep(FORWARD_TIME)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 左转90度回到线上
    print("左转90度回到路线")
    spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
    time.sleep(TURN_90_DEGREE)
    brake()
    time.sleep(BRAKE_TIME)
    
    current_state = STATE_TRACKING
    print("避障完成，继续循迹...")
    print("已避障次数: {}".format(obstacle_count))

#侧方停车函数
def parallel_parking():
    global current_state
    print("开始侧方停车...")
    print("当前特殊标识计数: {}".format(special_mark_count))
    
    # 停止前进
    print("停止前进")
    brake()
    time.sleep(BRAKE_TIME)
    
    # 后退
    print("后退准备停车")
    back(PARKING_SPEED, PARKING_SPEED)
    time.sleep(BACKWARD_TIME_1)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 右转90度
    print("右转90度")
    spin_right(SPIN_RIGHT_SPEED, SPIN_RIGHT_SPEED)
    time.sleep(TURN_90_DEGREE)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 继续后退
    print("继续后退")
    back(PARKING_SPEED, PARKING_SPEED)
    time.sleep(BACKWARD_TIME_2)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 左转90度
    print("左转90度调整")
    spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
    time.sleep(TURN_90_DEGREE)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 前进调整位置
    print("前进调整位置")
    run(PARKING_SPEED, PARKING_SPEED)
    time.sleep(FORWARD_ADJUST_TIME)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 后退到停车位
    print("后退到停车位")
    back(PARKING_SPEED, PARKING_SPEED)
    time.sleep(BACKWARD_PARK_TIME)
    brake()
    time.sleep(1.0)
    print("停车完成，等待1秒")
    
    # 前进离开停车位
    print("前进离开停车位")
    run(PARKING_SPEED, PARKING_SPEED)
    time.sleep(FORWARD_EXIT_TIME)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 左转90度
    print("左转90度")
    spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
    time.sleep(TURN_90_DEGREE)
    brake()
    time.sleep(BRAKE_TIME)
    
    # 前进越过特殊标识
    print("前进越过特殊标识")
    run(NORMAL_SPEED, NORMAL_SPEED)
    time.sleep(FORWARD_CROSS_TIME)
    brake()
    time.sleep(BRAKE_TIME)
    
    current_state = STATE_TRACKING
    print("侧方停车完成，继续循迹...")
    print("已完成侧方停车次数: {}".format(special_mark_count - 1))

#双线处理函数
def handle_double_line():
    global current_state, double_line_count
    print("检测到双线，开始处理...")
    print("当前双线计数: {}".format(double_line_count))
    
    # 直走直到识别到线
    print("直行寻找路线")
    run(NORMAL_SPEED, NORMAL_SPEED)
    time.sleep(DOUBLE_LINE_FORWARD_TIME)
    
    # 检测是否识别到线
    TrackSensorLeftValue1  = GPIO.input(TrackSensorLeftPin1)
    TrackSensorLeftValue2  = GPIO.input(TrackSensorLeftPin2)
    TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
    TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)
    
    if (TrackSensorLeftValue1 == False or TrackSensorLeftValue2 == False or 
        TrackSensorRightValue1 == False or TrackSensorRightValue2 == False):
        # 识别到线，左转
        print("识别到线，准备左转")
        brake()
        time.sleep(BRAKE_TIME)
        spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
        time.sleep(TURN_90_DEGREE)
        brake()
        time.sleep(BRAKE_TIME)
        print("左转完成，回到正确路线")
    else:
        print("未识别到线，继续直行")
    
    current_state = STATE_TRACKING

#循迹函数
def tracking():
    global current_state, obstacle_count, special_mark_count, double_line_count
    
    # 检测障碍物
    distance = Distance_test()
    if ENABLE_DISTANCE_PRINT:
        print("距离: {:.1f}cm".format(distance))
    
    if distance < OBSTACLE_DISTANCE:  # 距离小于30cm时避障
        obstacle_count += 1
        print("检测到障碍物! 距离: {:.1f}cm".format(distance))
        current_state = STATE_AVOIDING
        return
    
    # 检测特殊标识
    if detect_special_mark():
        special_mark_count += 1
        print("检测到特殊标识 #{}".format(special_mark_count))
        if special_mark_count >= PARKING_START_COUNT:  # 第二个特殊标识开始侧方停车
            print("准备执行侧方停车")
            current_state = STATE_PARKING
            return
        else:
            print("第一个特殊标识，继续循迹")
    
    # 检测双线
    if detect_double_line():
        double_line_count += 1
        print("检测到双线 #{}".format(double_line_count))
        current_state = STATE_DOUBLE_LINE
        return
    
    # 使用改进的转弯检测
    turn_type = detect_turn_type()
    
    # 根据转弯类型执行相应的动作
    if turn_type == "left_sharp":
        if ENABLE_PRINT:
            print("左锐角转弯")
        spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
        time.sleep(TURN_DELAY * 2)  # 锐角转弯需要更长时间
        brake()
        turn_compensation("left_sharp")
    
    elif turn_type == "right_sharp":
        if ENABLE_PRINT:
            print("右锐角转弯")
        spin_right(SPIN_RIGHT_SPEED, SPIN_RIGHT_SPEED)
        time.sleep(TURN_DELAY * 2)  # 锐角转弯需要更长时间
        brake()
        turn_compensation("right_sharp")
    
    elif turn_type == "left_90":
        if ENABLE_PRINT:
            print("左直角转弯")
        spin_left(SPIN_LEFT_SPEED, SPIN_LEFT_SPEED)
        time.sleep(TURN_DELAY)
        brake()
        turn_compensation("left_90")
    
    elif turn_type == "right_90":
        if ENABLE_PRINT:
            print("右直角转弯")
        spin_right(SPIN_RIGHT_SPEED, SPIN_RIGHT_SPEED)
        time.sleep(TURN_DELAY)
        brake()
        turn_compensation("right_90")
    
    elif turn_type == "left_slight":
        if ENABLE_PRINT:
            print("左轻微转弯")
        left(LEFT_SPEED, RIGHT_SPEED)
        time.sleep(TURN_DELAY)
    
    elif turn_type == "right_slight":
        if ENABLE_PRINT:
            print("右轻微转弯")
        right(RIGHT_SPEED, LEFT_SPEED)
        time.sleep(TURN_DELAY)
    
    elif turn_type == "straight":
        if ENABLE_PRINT:
            print("直线行驶")
        run(NORMAL_SPEED, NORMAL_SPEED)
    
    else:
        if ENABLE_PRINT:
            print("未知状态，停止等待")
        brake()
        time.sleep(SENSOR_DEBOUNCE_TIME)

#主程序
def main():
    global current_state
    
    print("=" * 50)
    print("树莓派小车科目二项目实践")
    print("=" * 50)
    print("功能说明:")
    print("   • 循迹行驶")
    print("   • 障碍物避让")
    print("   • 侧方停车")
    print("   • 双线处理")
    print("=" * 50)
    print("硬件配置:")
    print("   • 电机引脚: IN1={}, IN2={}, IN3={}, IN4={}".format(IN1, IN2, IN3, IN4))
    print("   • PWM引脚: ENA={}, ENB={}".format(ENA, ENB))
    print("   • 循迹传感器: L1={}, L2={}, R1={}, R2={}".format(
        TrackSensorLeftPin1, TrackSensorLeftPin2, TrackSensorRightPin1, TrackSensorRightPin2))
    print("   • 超声波模块: Echo={}, Trig={}".format(EchoPin, TrigPin))
    print("   • 按键引脚: {}".format(key))
    print("=" * 50)
    print("参数配置:")
    print("   • 正常速度: {}".format(NORMAL_SPEED))
    print("   • 避障距离: {}cm".format(OBSTACLE_DISTANCE))
    print("   • 安全距离: {}cm".format(SAFE_DISTANCE))
    print("=" * 50)
    print("按按键开始运行...")
    
    init()
    print("硬件初始化完成")
    #key_scan()
    print("开始运行!")
    print("-" * 50)
    
    try:
        while True:
            if current_state == STATE_TRACKING:
                tracking()
            elif current_state == STATE_AVOIDING:
                avoid_obstacle()
            elif current_state == STATE_PARKING:
                parallel_parking()
            elif current_state == STATE_DOUBLE_LINE:
                handle_double_line()
            
            time.sleep(DETECT_DELAY)  # 短暂延时
            
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("程序被用户中断")
        print("运行统计:")
        print("   • 避障次数: {}".format(obstacle_count))
        print("   • 特殊标识: {}".format(special_mark_count))
        print("   • 双线处理: {}".format(double_line_count))
        print("=" * 50)
    finally:
        print("停止所有电机")
        brake()
        print("停止PWM输出")
        pwm_ENA.stop()
        pwm_ENB.stop()
        print("清理GPIO")
        GPIO.cleanup()
        print("程序结束，GPIO已清理")
        print("再见!")

if __name__ == "__main__":
    main()
