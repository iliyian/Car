#-*- coding:UTF-8 -*-
import RPi.GPIO as GPIO
import time
import random

# 小车电机引脚定义
IN1 = 20
IN2 = 21
IN3 = 19
IN4 = 26
ENA = 16
ENB = 13

# 小车按键定义
key = 8

# 超声波引脚定义
EchoPin = 0
TrigPin = 1

# 循迹红外引脚定义
TrackSensorLeftPin1 = 3
TrackSensorLeftPin2 = 5
TrackSensorRightPin1 = 4
TrackSensorRightPin2 = 18

# RGB三色灯引脚定义
LED_R = 22
LED_G = 27
LED_B = 24

# 舵机引脚定义
ServoPin = 23

# 蜂鸣器引脚定义
buzzer = 8

# 设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# 全局变量
car_speed = 35
exam_score = 100
current_project = 0
project_names = ["倒车入库", "侧方停车", "直角转弯", "曲线行驶", "坡道定点停车"]

def init():
    """初始化所有引脚"""
    global pwm_ENA, pwm_ENB, pwm_servo

    # 电机引脚初始化
    GPIO.setup(ENA, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN1, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN2, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ENB, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN3, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN4, GPIO.OUT, initial=GPIO.LOW)

    # 其他引脚初始化
    GPIO.setup(key, GPIO.IN)
    GPIO.setup(EchoPin, GPIO.IN)
    GPIO.setup(TrigPin, GPIO.OUT)
    GPIO.setup(LED_R, GPIO.OUT)
    GPIO.setup(LED_G, GPIO.OUT)
    GPIO.setup(LED_B, GPIO.OUT)
    GPIO.setup(ServoPin, GPIO.OUT)
    GPIO.setup(buzzer, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(TrackSensorLeftPin1, GPIO.IN)
    GPIO.setup(TrackSensorLeftPin2, GPIO.IN)
    GPIO.setup(TrackSensorRightPin1, GPIO.IN)
    GPIO.setup(TrackSensorRightPin2, GPIO.IN)

    # PWM初始化
    pwm_ENA = GPIO.PWM(ENA, 2000)
    pwm_ENB = GPIO.PWM(ENB, 2000)
    pwm_servo = GPIO.PWM(ServoPin, 50)
    pwm_ENA.start(0)
    pwm_ENB.start(0)
    pwm_servo.start(0)

def run(leftspeed, rightspeed):
    """小车前进"""
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

def back(leftspeed, rightspeed):
    """小车后退"""
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

def left(leftspeed, rightspeed):
    """小车左转"""
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

def right(leftspeed, rightspeed):
    """小车右转"""
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

def spin_left(leftspeed, rightspeed):
    """小车原地左转"""
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

def spin_right(leftspeed, rightspeed):
    """小车原地右转"""
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)

def brake():
    """小车停止"""
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)

def distance_test():
    """超声波测距"""
    GPIO.output(TrigPin, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TrigPin, GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(TrigPin, GPIO.LOW)

    t3 = time.time()
    while not GPIO.input(EchoPin):
        t4 = time.time()
        if (t4 - t3) > 0.03:
            return -1

    t1 = time.time()
    while GPIO.input(EchoPin):
        t5 = time.time()
        if (t5 - t1) > 0.03:
            return -1

    t2 = time.time()
    return ((t2 - t1) * 340 / 2) * 100

def buzzer_beep(times):
    """蜂鸣器提示"""
    for i in range(times):
        GPIO.output(buzzer, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(buzzer, GPIO.HIGH)
        time.sleep(0.1)

def set_led_color(r, g, b):
    """设置LED颜色"""
    GPIO.output(LED_R, r)
    GPIO.output(LED_G, g)
    GPIO.output(LED_B, b)

def key_scan():
    """按键检测"""
    while GPIO.input(key):
        pass
    while not GPIO.input(key):
        time.sleep(0.01)
        if not GPIO.input(key):
            time.sleep(0.01)
            while not GPIO.input(key):
                pass

def deduct_score(points, reason):
    """扣分函数"""
    global exam_score
    exam_score -= points
    # print(f"扣分: {points}分 - {reason}")
    # print(f"当前分数: {exam_score}分")
    buzzer_beep(2)  # 扣分提示音
    set_led_color(1, 0, 0)  # 红灯警告
    time.sleep(1)
    set_led_color(0, 0, 0)

def project_1_reverse_parking():
    """项目1: 倒车入库"""
    print("开始倒车入库项目...")
    set_led_color(0, 1, 0)  # 绿灯表示开始

    # 模拟倒车入库过程
    print("前进到起始位置")
    run(car_speed, car_speed)
    time.sleep(2)

    print("开始倒车")
    back(car_speed, car_speed)
    time.sleep(1)

    print("向右打方向盘倒车")
    # 模拟右转倒车
    for i in range(10):
        back(car_speed - 10, car_speed)
        time.sleep(0.2)
        distance = distance_test()
        if distance != -1 and distance < 20:
            deduct_score(10, "车身距离边线过近")
            break

    print("回正方向盘")
    back(car_speed, car_speed)
    time.sleep(1)

    print("停车")
    brake()
    time.sleep(1)

    # 检查停车位置
    if random.choice([True, False]):  # 模拟随机成功/失败
        print("倒车入库成功!")
        set_led_color(0, 1, 0)
    else:
        deduct_score(10, "车身未完全入库")

    time.sleep(2)
    set_led_color(0, 0, 0)

def project_2_side_parking():
    """项目2: 侧方停车"""
    print("开始侧方停车项目...")
    set_led_color(0, 1, 0)

    print("前进到停车位前方")
    run(car_speed, car_speed)
    time.sleep(2)

    print("开始倒车侧方停车")
    back(car_speed, car_speed)
    time.sleep(0.5)

    print("向右打方向盘")
    for i in range(8):
        back(car_speed - 10, car_speed)
        time.sleep(0.2)

    print("向左打方向盘")
    for i in range(8):
        back(car_speed, car_speed - 10)
        time.sleep(0.2)

    print("停车")
    brake()

    # 检查停车效果
    if random.choice([True, True, False]):  # 80%成功率
        print("侧方停车成功!")
        set_led_color(0, 1, 0)
    else:
        deduct_score(10, "车身压线")

    time.sleep(2)
    set_led_color(0, 0, 0)

def project_3_right_angle_turn():
    """项目3: 直角转弯"""
    print("开始直角转弯项目...")
    set_led_color(0, 1, 0)

    print("直行进入弯道")
    run(car_speed, car_speed)
    time.sleep(2)

    print("开始右转")
    # 模拟直角右转
    spin_right(car_speed, car_speed)
    time.sleep(1.5)  # 转90度

    print("继续直行")
    run(car_speed, car_speed)
    time.sleep(2)

    brake()

    # 检查转弯效果
    if random.choice([True, True, True, False]):  # 75%成功率
        print("直角转弯成功!")
        set_led_color(0, 1, 0)
    else:
        deduct_score(10, "转弯时车轮压线")

    time.sleep(2)
    set_led_color(0, 0, 0)

def project_4_curve_driving():
    """项目4: 曲线行驶"""
    print("开始曲线行驶项目...")
    set_led_color(0, 1, 0)

    print("进入S弯道")

    # 模拟S弯行驶
    print("左弯")
    for i in range(15):
        left(car_speed - 5, car_speed)
        time.sleep(0.1)
        # 检查循迹传感器
        if not GPIO.input(TrackSensorLeftPin1):
            deduct_score(10, "车轮压线")
            break

    print("右弯")
    for i in range(15):
        right(car_speed, car_speed - 5)
        time.sleep(0.1)
        if not GPIO.input(TrackSensorRightPin1):
            deduct_score(10, "车轮压线")
            break

    print("驶出弯道")
    run(car_speed, car_speed)
    time.sleep(1)
    brake()

    print("曲线行驶完成!")
    set_led_color(0, 1, 0)
    time.sleep(2)
    set_led_color(0, 0, 0)

def project_5_hill_parking():
    """项目5: 坡道定点停车"""
    print("开始坡道定点停车项目...")
    set_led_color(0, 1, 0)

    print("上坡")
    # 模拟上坡，需要更大动力
    run(car_speed + 15, car_speed + 15)
    time.sleep(3)

    print("到达定点停车位置")
    brake()
    time.sleep(2)

    print("坡道起步")
    # 模拟坡道起步
    run(car_speed + 20, car_speed + 20)
    time.sleep(1)

    # 检查定点停车精度
    distance = distance_test()
    if distance != -1:
        if distance > 50:
            deduct_score(10, "定点停车距离过远")
        elif distance < 10:
            deduct_score(10, "定点停车距离过近")
        else:
            print("定点停车成功!")
            set_led_color(0, 1, 0)

    time.sleep(2)
    set_led_color(0, 0, 0)

def display_exam_result():
    """显示考试结果"""
    print("\n" + "="*50)
    print("科目二考试结束!")
    # print(f"最终得分: {exam_score}分")

    if exam_score >= 80:
        print("考试合格! 恭喜通过科目二考试!")
        set_led_color(0, 1, 0)  # 绿灯
        buzzer_beep(3)  # 成功提示音
    else:
        print("考试不合格，需要重新考试。")
        set_led_color(1, 0, 0)  # 红灯
        buzzer_beep(5)  # 失败提示音

    print("="*50)
    time.sleep(3)
    set_led_color(0, 0, 0)

def main_exam():
    """主考试流程"""
    global current_project

    print("欢迎参加科目二模拟考试!")
    print("考试项目包括: 倒车入库、侧方停车、直角转弯、曲线行驶、坡道定点停车")
    print("满分100分，80分及格")
    print("按下按键开始考试...")

    key_scan()  # 等待按键开始

    buzzer_beep(1)  # 开始提示音

    # 执行各个考试项目
    projects = [
        project_1_reverse_parking,
        project_2_side_parking,
        project_3_right_angle_turn,
        project_4_curve_driving,
        project_5_hill_parking
    ]

    for i, project in enumerate(projects):
        current_project = i
        # print(f"\n开始第{i+1}项: {project_names[i]}")
        time.sleep(1)

        try:
            project()
        except Exception as e:
            print(f"项目执行出错: {e}")
            deduct_score(20, "操作失误")

        if exam_score <= 0:
            print("分数已扣完，考试结束!")
            break

        # print(f"第{i+1}项完成，当前分数: {exam_score}分")
        time.sleep(2)

    display_exam_result()

# 主程序
if __name__ == "__main__":
    try:
        init()
        print("系统初始化完成")
        time.sleep(2)

        while True:
            main_exam()

            print("\n是否重新考试? 按键继续，Ctrl+C退出")
            try:
                key_scan()
                # 重置分数
                exam_score = 100
                current_project = 0
            except KeyboardInterrupt:
                break

    except KeyboardInterrupt:
        print("\n考试系统退出")
    finally:
        pwm_ENA.stop()
        pwm_ENB.stop()
        pwm_servo.stop()
        GPIO.cleanup()
        print("系统清理完成")

