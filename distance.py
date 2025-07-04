#-*- coding:UTF-8 -*-
import RPi.GPIO as GPIO
import time

#超声波引脚定义 (根据pre目录下的引脚定义)
ECHOPIN = 0
TRIGPIN = 1

#温度和声速设置
TEMPERATURE = 30
SPEED_OF_SOUND = 331 + 0.6 * TEMPERATURE

#设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

#忽略警告信息
GPIO.setwarnings(False)

def init():
    """初始化超声波引脚"""
    GPIO.setup(TRIGPIN, GPIO.OUT)
    GPIO.setup(ECHOPIN, GPIO.IN)

def distance():
    """单次超声波测距，带超时检测"""
    GPIO.output(TRIGPIN, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TRIGPIN, GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(TRIGPIN, GPIO.LOW)

    t3 = time.time()

    # 等待回声引脚变高，带超时检测
    while not GPIO.input(ECHOPIN):
        t4 = time.time()
        if (t4 - t3) > 0.03:  # 超时30ms
            return -1

    t1 = time.time()
    
    # 等待回声引脚变低，带超时检测
    while GPIO.input(ECHOPIN):
        t5 = time.time()
        if (t5 - t1) > 0.03:  # 超时30ms
            return -1

    t2 = time.time()
    time.sleep(0.01)
    
    # 计算距离 (cm)
    distance_cm = ((t2 - t1) * 340 / 2) * 100
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

def cleanup():
    """清理GPIO资源"""
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        print("超声波测距程序启动")
        print("引脚配置: TrigPin=%d, EchoPin=%d" % (TRIGPIN, ECHOPIN))
        
        # 初始化引脚
        init()
        
        # 延时2秒
        time.sleep(2)
        
        # 连续测距
        while True:
            dist = distance_test()
            print("当前距离: %.2f cm" % dist)
            print("-" * 30)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print("程序发生错误:", str(e))
    finally:
        cleanup()
        print("程序结束，GPIO资源已清理")
  