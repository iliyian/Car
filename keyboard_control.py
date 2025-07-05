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

#清屏函数
def clear_screen():
    """清屏"""
    print("\033[2J\033[H", end="")

#显示状态信息
def show_status(action, speed):
    """显示当前状态信息"""
    print(f"\r[状态] {action} | 速度: {speed}% | 按ESC退出", end="", flush=True)

#显示控制说明
def show_instructions():
    clear_screen()
    print("=" * 60)
    print("              WASD 键盘控制小车程序")
    print("=" * 60)
    print("控制说明:")
    print("   W - 前进          S - 后退")
    print("   A - 左转          D - 右转")
    print("   Q - 原地左转      E - 原地右转")
    print("   空格 - 停止       1-9 - 调整速度")
    print("   ESC/Ctrl+C - 退出程序")
    print("=" * 60)
    print("状态显示: [状态] 动作 | 速度: XX% | 按ESC退出")
    print("=" * 60)
    print()

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
        
        # 显示初始状态
        show_status("待命", current_speed)
        
        while True:
            # 获取键盘输入
            key_input = get_key()
            
            if key_input:
                key_input = key_input.lower()
                
                if key_input == 'w':
                    show_status("前进", current_speed)
                    run(current_speed, current_speed)
                    
                elif key_input == 's':
                    show_status("后退", current_speed)
                    back(current_speed, current_speed)
                    
                elif key_input == 'a':
                    show_status("左转", current_speed)
                    left(0, current_speed)
                    
                elif key_input == 'd':
                    show_status("右转", current_speed)
                    right(current_speed, 0)
                    
                elif key_input == 'q':
                    show_status("原地左转", current_speed)
                    spin_left(current_speed, current_speed)
                    
                elif key_input == 'e':
                    show_status("原地右转", current_speed)
                    spin_right(current_speed, current_speed)
                    
                elif key_input == ' ':
                    show_status("停止", current_speed)
                    brake()
                    
                elif key_input in '123456789':
                    # 调整速度 (1-9 对应 10%-90%)
                    speed_level = int(key_input)
                    current_speed = speed_level * 10
                    show_status("速度调整", current_speed)
                    
                elif key_input == '\x1b':  # ESC键
                    print("\n退出程序")
                    break
                    
                elif key_input == '\x03':  # Ctrl+C
                    print("\n程序被中断")
                    break
            
            # 短暂延时，避免CPU占用过高
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        
    finally:
        # 恢复终端设置
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        # 清理GPIO
        print("\n正在清理资源...")
        brake()
        pwm_ENA.stop()
        pwm_ENB.stop()
        GPIO.cleanup()
        print("程序已安全退出")

if __name__ == "__main__":
    main() 