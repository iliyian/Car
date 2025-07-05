#-*- coding:UTF-8 -*-
import RPi.GPIO as GPIO
import time
import sys
import select
import tty
import termios

#小车电机引脚定义
IN1 = 20
IN2 = 21
IN3 = 19
IN4 = 26
ENA = 16
ENB = 13

#小车按键定义
key = 8

#设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

#忽略警告信息
GPIO.setwarnings(False)

#电机引脚初始化为输出模式
#按键引脚初始化为输入模式
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

#获取键盘输入（非阻塞）
def get_key():
    """获取键盘输入，非阻塞模式"""
    if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
        return sys.stdin.read(1)
    return None

#显示控制说明
def show_instructions():
    print("=" * 60)
    print("              WASD 键盘控制小车程序")
    print("=" * 60)
    print("控制说明:")
    print("   W - 前进")
    print("   S - 后退")
    print("   A - 左转")
    print("   D - 右转")
    print("   Q - 原地左转")
    print("   E - 原地右转")
    print("   空格 - 停止")
    print("   1-9 - 调整速度 (1=最慢, 9=最快)")
    print("   ESC/Ctrl+C - 退出程序")
    print("=" * 60)
    print("当前速度: 50%")
    print("请按键控制小车...")
    print("=" * 60)

#主程序
def main():
    # 保存原始终端设置
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # 设置终端为非缓冲模式
        tty.setraw(sys.stdin.fileno())
        
        init()
        print("硬件初始化完成")
        
        show_instructions()
        
        # 默认速度
        current_speed = 50
        
        while True:
            # 获取键盘输入
            key_input = get_key()
            
            if key_input:
                key_input = key_input.lower()
                
                if key_input == 'w':
                    print(f"前进 - 速度: {current_speed}%")
                    run(current_speed, current_speed)
                    
                elif key_input == 's':
                    print(f"后退 - 速度: {current_speed}%")
                    back(current_speed, current_speed)
                    
                elif key_input == 'a':
                    print(f"左转 - 速度: {current_speed}%")
                    left(0, current_speed)
                    
                elif key_input == 'd':
                    print(f"右转 - 速度: {current_speed}%")
                    right(current_speed, 0)
                    
                elif key_input == 'q':
                    print(f"原地左转 - 速度: {current_speed}%")
                    spin_left(current_speed, current_speed)
                    
                elif key_input == 'e':
                    print(f"原地右转 - 速度: {current_speed}%")
                    spin_right(current_speed, current_speed)
                    
                elif key_input == ' ':
                    print("停止")
                    brake()
                    
                elif key_input in '123456789':
                    # 调整速度 (1-9 对应 10%-90%)
                    speed_level = int(key_input)
                    current_speed = speed_level * 10
                    print(f"速度调整为: {current_speed}%")
                    
                elif key_input == '\x1b':  # ESC键
                    print("退出程序")
                    break
                    
                elif key_input == '\x03':  # Ctrl+C
                    print("程序被中断")
                    break
                    
                else:
                    print(f"未知按键: {repr(key_input)}")
            
            # 短暂延时，避免CPU占用过高
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        
    finally:
        # 恢复终端设置
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        # 清理GPIO
        print("停止所有电机")
        brake()
        print("停止PWM输出")
        pwm_ENA.stop()
        pwm_ENB.stop()
        print("清理GPIO")
        GPIO.cleanup()
        print("程序结束")

if __name__ == "__main__":
    main() 