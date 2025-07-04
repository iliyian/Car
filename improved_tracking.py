# -*- coding: UTF-8 -*-
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
from enum import Enum
import math

class TrackingState(Enum):
    """循迹状态枚举"""
    FORWARD = "forward"
    LEFT_TURN = "left_turn"
    RIGHT_TURN = "right_turn"
    SHARP_LEFT = "sharp_left"
    SHARP_RIGHT = "sharp_right"
    SPIN_LEFT = "spin_left"
    SPIN_RIGHT = "spin_right"
    STOPPED = "stopped"
    LOST = "lost"
    RECOVERING = "recovering"

class ImprovedCarController:
    """改进的小车控制器类"""
    
    def __init__(self):
        """
        初始化小车控制器
        """
        # 配置参数
        self.config = {
            "motor_pins": {
                "IN1": 20, "IN2": 21, "IN3": 19, "IN4": 26,
                "ENA": 16, "ENB": 13
            },
            "control_pins": {
                "key": 8
            },
            "sensor_pins": {
                "left1": 3, "left2": 5, "right1": 4, "right2": 18
            },
            "speeds": {
                "base": 30, "turn": 25, "sharp_turn": 20, "spin": 25,
                "recovery": 15, "slow": 10
            },
            "control_params": {
                "turn_delay": 0.08,
                "sensor_read_interval": 0.02,
                "lost_timeout": 3.0,
                "recovery_timeout": 5.0,
                "history_size": 3,
                "confidence_threshold": 0.7,
                "max_recovery_attempts": 5
            },
            "debug": {
                "enabled": True,
                "log_file": "improved_tracking_debug.log"
            }
        }
        
        # 电机引脚定义
        self.IN1 = self.config["motor_pins"]["IN1"]
        self.IN2 = self.config["motor_pins"]["IN2"]
        self.IN3 = self.config["motor_pins"]["IN3"]
        self.IN4 = self.config["motor_pins"]["IN4"]
        self.ENA = self.config["motor_pins"]["ENA"]
        self.ENB = self.config["motor_pins"]["ENB"]
        
        # 按键定义
        self.key = self.config["control_pins"]["key"]
        
        # 循迹传感器引脚定义
        sensor_pins = self.config["sensor_pins"]
        self.TrackSensorLeftPin1 = sensor_pins["left1"]
        self.TrackSensorLeftPin2 = sensor_pins["left2"]
        self.TrackSensorRightPin1 = sensor_pins["right1"]
        self.TrackSensorRightPin2 = sensor_pins["right2"]
        
        # 速度配置
        speeds = self.config["speeds"]
        self.base_speed = speeds["base"]
        self.turn_speed = speeds["turn"]
        self.sharp_turn_speed = speeds["sharp_turn"]
        self.spin_speed = speeds["spin"]
        self.recovery_speed = speeds["recovery"]
        self.slow_speed = speeds["slow"]
        
        # 控制参数
        control_params = self.config["control_params"]
        self.turn_delay = control_params["turn_delay"]
        self.sensor_read_interval = control_params["sensor_read_interval"]
        self.lost_timeout = control_params["lost_timeout"]
        self.recovery_timeout = control_params["recovery_timeout"]
        self.history_size = control_params["history_size"]
        self.confidence_threshold = control_params["confidence_threshold"]
        self.max_recovery_attempts = control_params["max_recovery_attempts"]
        
        # 状态变量
        self.current_state = TrackingState.STOPPED
        self.last_valid_state = TrackingState.FORWARD
        self.lost_start_time = None
        self.recovery_start_time = None
        self.running = False
        self.debug_mode = self.config["debug"]["enabled"]
        
        # 统计信息
        self.stats = {
            "start_time": None,
            "total_distance": 0,
            "state_changes": 0,
            "sensor_readings": 0,
            "lost_count": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0
        }
        
        # 传感器历史记录
        self.sensor_history = []
        
        # 路径记忆
        self.path_memory = {
            "last_positions": [],  # 最近的位置记录
            "turn_history": [],    # 转弯历史
            "lost_positions": []   # 丢失位置记录
        }
        
        # 恢复策略
        self.recovery_strategy = {
            "current_attempt": 0,
            "search_pattern": "spiral",  # spiral, back_and_forth, circle
            "search_direction": 1,  # 1: 顺时针, -1: 逆时针
            "search_radius": 0.1
        }
        
        # 初始化GPIO
        self.init_gpio()
        
        print("改进版小车控制器初始化完成")
        self.print_config()
    
    def print_config(self):
        """打印当前配置"""
        print("=" * 60)
        print("         改进版循迹系统配置")
        print("=" * 60)
        print(f"基础速度: {self.base_speed}")
        print(f"转弯速度: {self.turn_speed}")
        print(f"急转速度: {self.sharp_turn_speed}")
        print(f"原地转速度: {self.spin_speed}")
        print(f"恢复速度: {self.recovery_speed}")
        print(f"慢速: {self.slow_speed}")
        print(f"转弯延时: {self.turn_delay}s")
        print(f"传感器读取间隔: {self.sensor_read_interval}s")
        print(f"丢失超时: {self.lost_timeout}s")
        print(f"恢复超时: {self.recovery_timeout}s")
        print(f"历史记录大小: {self.history_size}")
        print(f"置信度阈值: {self.confidence_threshold}")
        print(f"最大恢复尝试次数: {self.max_recovery_attempts}")
        print(f"调试模式: {'开启' if self.debug_mode else '关闭'}")
        print("=" * 60)
    
    def init_gpio(self):
        """初始化GPIO"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 电机引脚初始化
        GPIO.setup(self.ENA, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.IN1, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.IN2, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ENB, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.IN3, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.IN4, GPIO.OUT, initial=GPIO.LOW)
        
        # 按键和传感器引脚初始化
        GPIO.setup(self.key, GPIO.IN)
        GPIO.setup(self.TrackSensorLeftPin1, GPIO.IN)
        GPIO.setup(self.TrackSensorLeftPin2, GPIO.IN)
        GPIO.setup(self.TrackSensorRightPin1, GPIO.IN)
        GPIO.setup(self.TrackSensorRightPin2, GPIO.IN)
        
        # 设置PWM
        self.pwm_ENA = GPIO.PWM(self.ENA, 2000)
        self.pwm_ENB = GPIO.PWM(self.ENB, 2000)
        self.pwm_ENA.start(0)
        self.pwm_ENB.start(0)
        
        print("GPIO初始化完成")
    
    def read_sensors(self):
        """读取传感器数据（改进版）"""
        # 多次读取取平均值，提高稳定性
        readings = []
        for _ in range(3):
            reading = {
                'left1': GPIO.input(self.TrackSensorLeftPin1) == 0,  # 检测到黑线为True
                'left2': GPIO.input(self.TrackSensorLeftPin2) == 0,
                'right1': GPIO.input(self.TrackSensorRightPin1) == 0,
                'right2': GPIO.input(self.TrackSensorRightPin2) == 0
            }
            readings.append(reading)
            time.sleep(0.001)  # 短暂延时
        
        # 计算平均值
        sensor_data = {}
        for sensor in ['left1', 'left2', 'right1', 'right2']:
            true_count = sum(1 for reading in readings if reading[sensor])
            sensor_data[sensor] = true_count >= 2  # 至少2次检测到才认为有效
        
        # 添加到历史记录
        self.sensor_history.append(sensor_data)
        if len(self.sensor_history) > self.history_size:
            self.sensor_history.pop(0)
        
        self.stats["sensor_readings"] += 1
        
        if self.debug_mode:
            self.debug_log(f"传感器读取: {sensor_data}")
        
        return sensor_data
    
    def get_sensor_confidence(self, sensors):
        """计算传感器读数的置信度"""
        # 基于历史数据计算置信度
        if not self.sensor_history:
            return 1.0
        
        # 计算当前读数与历史的一致性
        consistency = 0
        for hist_sensors in self.sensor_history:
            if hist_sensors == sensors:
                consistency += 1
        
        return consistency / len(self.sensor_history)
    
    def analyze_track_state(self, sensors):
        """分析循迹状态（改进版）"""
        l1, l2, r1, r2 = sensors['left1'], sensors['left2'], sensors['right1'], sensors['right2']
        
        # 计算置信度
        confidence = self.get_sensor_confidence(sensors)
        
        # 如果置信度太低，可能需要重新校准
        if confidence < self.confidence_threshold and len(self.sensor_history) > 1:
            if self.debug_mode:
                self.debug_log(f"置信度低: {confidence:.2f}")
        
        # 改进的状态判断逻辑
        # 1. 全白 - 可能丢失，但先尝试保持当前状态
        if not any([l1, l2, r1, r2]):
            # 检查是否真的丢失
            if self.current_state != TrackingState.LOST:
                # 记录丢失位置
                self.record_lost_position()
                return TrackingState.LOST
            else:
                return TrackingState.LOST
        
        # 2. 全黑 - 特殊标记点
        if all([l1, l2, r1, r2]):
            if self.debug_mode:
                self.debug_log("检测到特殊标记点")
            return TrackingState.STOPPED
        
        # 3. 急转弯检测（改进）
        if (l1 and l2) and (r1 or r2):
            return TrackingState.SPIN_RIGHT
        elif (r1 and r2) and (l1 or l2):
            return TrackingState.SPIN_LEFT
        
        # 4. 边缘检测
        if l1 and not any([l2, r1, r2]):
            return TrackingState.SHARP_LEFT
        elif r2 and not any([l1, l2, r1]):
            return TrackingState.SHARP_RIGHT
        
        # 5. 转弯检测
        if l2 and not r1:
            return TrackingState.LEFT_TURN
        elif r1 and not l2:
            return TrackingState.RIGHT_TURN
        
        # 6. 直线检测
        if l2 and r1:
            return TrackingState.FORWARD
        
        # 7. 部分检测到的情况
        if l1 or l2:
            return TrackingState.LEFT_TURN
        elif r1 or r2:
            return TrackingState.RIGHT_TURN
        
        # 默认保持上一状态
        return self.current_state
    
    def record_lost_position(self):
        """记录丢失位置"""
        if len(self.path_memory["lost_positions"]) >= 10:
            self.path_memory["lost_positions"].pop(0)
        
        lost_info = {
            "time": time.time(),
            "last_state": self.current_state,
            "sensor_history": self.sensor_history.copy(),
            "recovery_attempts": self.recovery_strategy["current_attempt"]
        }
        self.path_memory["lost_positions"].append(lost_info)
    
    def handle_lost_state(self):
        """处理丢失状态（改进版）"""
        if self.lost_start_time is None:
            self.lost_start_time = time.time()
            self.stats["lost_count"] += 1
            self.recovery_strategy["current_attempt"] = 0
            if self.debug_mode:
                self.debug_log("进入丢失状态")
        
        elapsed = time.time() - self.lost_start_time
        
        if elapsed < self.lost_timeout:
            # 智能恢复策略
            self.smart_recovery()
        else:
            # 超时，尝试更激进的恢复
            if self.recovery_strategy["current_attempt"] < self.max_recovery_attempts:
                self.aggressive_recovery()
            else:
                # 最终停止
                self.brake()
                if self.debug_mode:
                    self.debug_log("恢复失败，停止运动")
    
    def smart_recovery(self):
        """智能恢复策略"""
        self.recovery_strategy["current_attempt"] += 1
        
        # 基于历史数据选择恢复方向
        if self.path_memory["lost_positions"]:
            # 分析最近的丢失模式
            recent_lost = self.path_memory["lost_positions"][-1]
            if recent_lost["last_state"] in [TrackingState.LEFT_TURN, TrackingState.SHARP_LEFT]:
                self.spin_left(self.recovery_speed, self.recovery_speed)
                time.sleep(0.1)
            elif recent_lost["last_state"] in [TrackingState.RIGHT_TURN, TrackingState.SHARP_RIGHT]:
                self.spin_right(self.recovery_speed, self.recovery_speed)
                time.sleep(0.1)
            else:
                # 默认向前慢速搜索
                self.run(self.slow_speed, self.slow_speed)
        else:
            # 没有历史数据，使用默认策略
            if self.last_valid_state in [TrackingState.LEFT_TURN, TrackingState.SHARP_LEFT]:
                self.spin_left(self.recovery_speed, self.recovery_speed)
                time.sleep(0.1)
            elif self.last_valid_state in [TrackingState.RIGHT_TURN, TrackingState.SHARP_RIGHT]:
                self.spin_right(self.recovery_speed, self.recovery_speed)
                time.sleep(0.1)
            else:
                self.run(self.slow_speed, self.slow_speed)
    
    def aggressive_recovery(self):
        """激进恢复策略"""
        if self.debug_mode:
            self.debug_log(f"尝试激进恢复 #{self.recovery_strategy['current_attempt']}")
        
        # 螺旋搜索
        search_time = 0.2 * self.recovery_strategy["current_attempt"]
        
        if self.recovery_strategy["search_direction"] == 1:
            self.spin_right(self.recovery_speed, self.recovery_speed)
        else:
            self.spin_left(self.recovery_speed, self.recovery_speed)
        
        time.sleep(search_time)
        self.recovery_strategy["search_direction"] *= -1  # 改变搜索方向
    
    def execute_movement(self, state):
        """执行运动控制（改进版）"""
        if state == TrackingState.FORWARD:
            self.run(self.base_speed, self.base_speed)
        elif state == TrackingState.LEFT_TURN:
            self.left(0, self.turn_speed)
        elif state == TrackingState.RIGHT_TURN:
            self.right(self.turn_speed, 0)
        elif state == TrackingState.SHARP_LEFT:
            self.spin_left(self.sharp_turn_speed, self.sharp_turn_speed)
            time.sleep(self.turn_delay)
        elif state == TrackingState.SHARP_RIGHT:
            self.spin_right(self.sharp_turn_speed, self.sharp_turn_speed)
            time.sleep(self.turn_delay)
        elif state == TrackingState.SPIN_LEFT:
            self.spin_left(self.spin_speed, self.spin_speed)
        elif state == TrackingState.SPIN_RIGHT:
            self.spin_right(self.spin_speed, self.spin_speed)
        elif state == TrackingState.STOPPED:
            self.brake()
        elif state == TrackingState.LOST:
            self.handle_lost_state()
        elif state == TrackingState.RECOVERING:
            self.smart_recovery()
    
    # 基础运动控制函数
    def run(self, left_speed, right_speed):
        """前进"""
        GPIO.output(self.IN1, GPIO.HIGH)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.HIGH)
        GPIO.output(self.IN4, GPIO.LOW)
        self.pwm_ENA.ChangeDutyCycle(left_speed)
        self.pwm_ENB.ChangeDutyCycle(right_speed)
    
    def left(self, left_speed, right_speed):
        """左转"""
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.HIGH)
        GPIO.output(self.IN4, GPIO.LOW)
        self.pwm_ENA.ChangeDutyCycle(left_speed)
        self.pwm_ENB.ChangeDutyCycle(right_speed)
    
    def right(self, left_speed, right_speed):
        """右转"""
        GPIO.output(self.IN1, GPIO.HIGH)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.LOW)
        self.pwm_ENA.ChangeDutyCycle(left_speed)
        self.pwm_ENB.ChangeDutyCycle(right_speed)
    
    def spin_left(self, left_speed, right_speed):
        """原地左转"""
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.HIGH)
        GPIO.output(self.IN3, GPIO.HIGH)
        GPIO.output(self.IN4, GPIO.LOW)
        self.pwm_ENA.ChangeDutyCycle(left_speed)
        self.pwm_ENB.ChangeDutyCycle(right_speed)
    
    def spin_right(self, left_speed, right_speed):
        """原地右转"""
        GPIO.output(self.IN1, GPIO.HIGH)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.HIGH)
        self.pwm_ENA.ChangeDutyCycle(left_speed)
        self.pwm_ENB.ChangeDutyCycle(right_speed)
    
    def brake(self):
        """停止"""
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.LOW)
    
    def key_scan(self):
        """按键检测"""
        print("等待按键启动...")
        while GPIO.input(self.key):
            time.sleep(0.01)
        
        # 消抖处理
        time.sleep(0.05)
        if not GPIO.input(self.key):
            while not GPIO.input(self.key):
                time.sleep(0.01)
            print("按键检测到，开始循迹...")
            return True
        return False
    
    def debug_log(self, message):
        """调试日志"""
        if self.debug_mode:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_message = f"[{timestamp}] {message}"
            print(log_message)
            
            # 写入日志文件
            log_file = self.config["debug"]["log_file"]
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(log_message + "\n")
            except:
                pass
    
    def print_status(self):
        """打印状态信息"""
        sensors = self.read_sensors()
        sensor_str = f"L1:{int(sensors['left1'])} L2:{int(sensors['left2'])} R1:{int(sensors['right1'])} R2:{int(sensors['right2'])}"
        
        elapsed = time.time() - self.stats["start_time"] if self.stats["start_time"] else 0
        
        print(f"\r状态: {self.current_state.value:12} | 传感器: {sensor_str} | "
              f"运行时间: {elapsed:.1f}s | 状态变化: {self.stats['state_changes']:4} | "
              f"丢失次数: {self.stats['lost_count']:2} | 恢复尝试: {self.recovery_strategy['current_attempt']:2}", end="")
    
    def start_tracking(self):
        """开始循迹"""
        print("=" * 60)
        print("         改进版循迹系统启动")
        print("=" * 60)
        
        try:
            # 等待按键启动
            if not self.key_scan():
                return
            
            # 初始化统计
            self.stats["start_time"] = time.time()
            self.running = True
            
            # 启动状态监控线程
            if self.debug_mode:
                status_thread = threading.Thread(target=self.status_monitor)
                status_thread.daemon = True
                status_thread.start()
            
            print("\n开始循迹模式...")
            print("按 Ctrl+C 停止")
            
            # 主循迹循环
            while self.running:
                # 读取传感器
                sensors = self.read_sensors()
                
                # 分析状态
                new_state = self.analyze_track_state(sensors)
                
                # 状态变化处理
                if new_state != self.current_state:
                    if new_state != TrackingState.LOST:
                        self.last_valid_state = new_state
                        self.lost_start_time = None
                        self.recovery_strategy["current_attempt"] = 0
                    
                    self.current_state = new_state
                    self.stats["state_changes"] += 1
                    
                    if self.debug_mode:
                        self.debug_log(f"状态变化: {new_state.value}")
                
                # 执行运动
                self.execute_movement(self.current_state)
                
                # 状态显示
                if not self.debug_mode:
                    self.print_status()
                
                # 延时
                time.sleep(self.sensor_read_interval)
        
        except KeyboardInterrupt:
            print("\n\n用户中断，停止循迹...")
        except Exception as e:
            print(f"\n\n程序异常: {e}")
        finally:
            self.stop_tracking()
    
    def status_monitor(self):
        """状态监控线程"""
        while self.running:
            self.print_status()
            time.sleep(0.5)
    
    def stop_tracking(self):
        """停止循迹"""
        self.running = False
        self.brake()
        
        # 打印统计信息
        if self.stats["start_time"]:
            elapsed = time.time() - self.stats["start_time"]
            print(f"\n\n循迹统计:")
            print(f"总运行时间: {elapsed:.2f}秒")
            print(f"传感器读取次数: {self.stats['sensor_readings']}")
            print(f"状态变化次数: {self.stats['state_changes']}")
            print(f"丢失次数: {self.stats['lost_count']}")
            print(f"恢复尝试次数: {self.recovery_strategy['current_attempt']}")
            print(f"平均传感器读取频率: {self.stats['sensor_readings']/elapsed:.1f} Hz")
    
    def calibrate_sensors(self):
        """传感器校准模式"""
        print("=" * 50)
        print("         传感器校准模式")
        print("=" * 50)
        print("将小车放在不同位置，观察传感器读数")
        print("按 Ctrl+C 退出校准模式")
        
        try:
            while True:
                sensors = self.read_sensors()
                raw_sensors = {
                    'left1': GPIO.input(self.TrackSensorLeftPin1),
                    'left2': GPIO.input(self.TrackSensorLeftPin2),
                    'right1': GPIO.input(self.TrackSensorRightPin1),
                    'right2': GPIO.input(self.TrackSensorRightPin2)
                }
                
                print(f"\r原始读数: L1:{raw_sensors['left1']} L2:{raw_sensors['left2']} "
                      f"R1:{raw_sensors['right1']} R2:{raw_sensors['right2']} | "
                      f"处理后: L1:{int(sensors['left1'])} L2:{int(sensors['left2'])} "
                      f"R1:{int(sensors['right1'])} R2:{int(sensors['right2'])}", end="")
                
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n校准模式退出")
    
    def cleanup(self):
        """清理资源"""
        self.running = False
        self.brake()
        self.pwm_ENA.stop()
        self.pwm_ENB.stop()
        GPIO.cleanup()
        print("资源清理完成")

def main():
    """主函数"""
    car = ImprovedCarController()
    
    try:
        while True:
            print("\n请选择模式:")
            print("1. 开始循迹")
            print("2. 传感器校准")
            print("3. 显示配置")
            print("4. 退出")
            
            choice = input("请输入选项 (1-4): ").strip()
            
            if choice == '1':
                car.start_tracking()
            elif choice == '2':
                car.calibrate_sensors()
            elif choice == '3':
                car.print_config()
            elif choice == '4':
                break
            else:
                print("无效选项，请重新输入")
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序发生错误: {e}")
    finally:
        car.cleanup()

if __name__ == "__main__":
    main() 