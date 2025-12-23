#!/usr/bin/env python3
"""
高级温度监控系统 - 完全符合用户要求
基于network_test.sh的11个网络设备 + nav PC
基于can_temperature_reader.py的CAN温度读取
实时硬件资源监控 + 压力测试 + 温度可视化
"""

import argparse
import datetime
import json
import logging
import math
import os
import psutil
import random
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path
import can

class TemperatureMonitor:
    """高级温度监控系统主类"""
    
    def __init__(self, duration=300, interval=2, stress_level='medium', output_file=None, log_dir=None):
        self.duration = duration
        self.interval = interval
        self.stress_level = stress_level
        self.output_file = output_file or f"temperature_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.stop_flag = False
        self.start_time = None
        
        # 温度数据
        self.cpu_temp = 0.0
        self.vulcan_temp_s1 = -999.0  # 用-999表示读取失败
        self.vulcan_temp_s2 = -999.0
        
        # CAN相关
        self.can_bus = None
        self.can_temp_enabled = False
        
        # 网络设备列表（基于network_test.sh的11个设备）
        self.network_devices = {
            # 相机设备（5个）
            'hazard_cam': '192.168.11.9',
            'dock_cam': '192.168.11.10', 
            'ptz_cam': '192.168.11.68',
            'ptz_ir_cam': '192.168.11.69',
            'bosch_cam': '192.168.11.65',
            
            # 雷达设备（4个）
            'airy_front': '10.7.5.152',
            'airy_rear': '10.7.5.153',
            'e1r_left': '10.7.5.103',
            'e1r_right': '10.7.5.104',
            
            # VA PC和nav PC（2个）
            'va_pc': '192.168.140.75',
            'nav_pc': '192.168.11.88'  # 额外添加的nav PC
        }
        
        # 设置日志系统
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志系统"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建logger
        self.logger = logging.getLogger('TemperatureMonitor')
        self.logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"temperature_monitor_{timestamp}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器（仅显示关键信息）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # 只显示警告及以上级别
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器到logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"日志系统初始化完成，日志文件: {log_file}")
    
    def get_system_stats(self):
        """获取系统硬件资源使用情况"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except Exception as e:
            self.logger.debug(f"系统状态读取失败: {e}")
            return {'cpu_percent': 0.0, 'memory_percent': 0.0, 'disk_percent': 0.0}
    
    def check_network_connectivity(self):
        """检查11个网络设备的连通性"""
        network_status = {}
        
        try:
            for device_name, ip_addr in self.network_devices.items():
                try:
                    # 使用ping测试连通性，超时3秒
                    result = subprocess.run(
                        ['ping', '-c', '1', '-W', '3', ip_addr],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        # 提取ping时间
                        ping_time = "N/A"
                        for line in result.stdout.split('\n'):
                            if 'time=' in line:
                                import re
                                time_match = re.search(r'time=([0-9.]+)', line)
                                if time_match:
                                    ping_time = f"{time_match.group(1)}ms"
                                break
                        
                        network_status[device_name] = {
                            'ip': ip_addr,
                            'status': 'UP',
                            'ping_time': ping_time,
                            'last_check': datetime.datetime.now().strftime('%H:%M:%S')
                        }
                    else:
                        network_status[device_name] = {
                            'ip': ip_addr,
                            'status': 'DOWN',
                            'ping_time': 'N/A',
                            'last_check': datetime.datetime.now().strftime('%H:%M:%S')
                        }
                        
                except subprocess.TimeoutExpired:
                    network_status[device_name] = {
                        'ip': ip_addr,
                        'status': 'TIMEOUT',
                        'ping_time': 'N/A',
                        'last_check': datetime.datetime.now().strftime('%H:%M:%S')
                    }
                except Exception as e:
                    network_status[device_name] = {
                        'ip': ip_addr,
                        'status': 'ERROR',
                        'ping_time': str(e),
                        'last_check': datetime.datetime.now().strftime('%H:%M:%S')
                    }
                    
        except Exception as e:
            self.logger.debug(f"网络连通性检查失败: {e}")
            network_status['system_error'] = {'status': 'CHECK_FAILED', 'error': str(e)}
        
        return network_status
    
    def init_can_bus(self):
        """初始化CAN总线连接，基于can_temperature_reader.py"""
        self.logger.info("开始初始化CAN总线连接...")
        
        try:
            # 检查CAN接口是否存在
            result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
            can_interfaces = []
            for line in result.stdout.split('\n'):
                if 'can' in line.lower() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        interface_name = parts[1].strip()
                        if interface_name.startswith('can'):
                            can_interfaces.append(interface_name)
            
            if can_interfaces:
                self.logger.info(f"发现CAN接口: {can_interfaces}")
            else:
                self.logger.warning("未检测到CAN接口")
                
        except Exception as e:
            self.logger.debug(f"CAN接口检测失败: {e}")
        
        # 尝试连接CAN0（主要接口）
        try:
            # 基于can_temperature_reader.py的配置
            filters = [{"can_id": 0x510, "can_mask": 0x7FF, "extended": False}]
            self.can_bus = can.interface.Bus(interface='socketcan', channel='can0', can_filters=filters)
            self.logger.info("✅ CAN总线连接成功: socketcan on can0")
            self.can_temp_enabled = True
            return True
        except Exception as e:
            self.logger.warning(f"⚠️  CAN连接失败: {e}")
            self.can_temp_enabled = False
            return False
    
    def read_can_temperature(self):
        """读取Vulcan CAN温度，基于can_temperature_reader.py"""
        if not self.can_bus or not self.can_temp_enabled:
            return False
        
        try:
            # 非阻塞读取，超时0.1秒
            msg = self.can_bus.recv(timeout=0.1)
            
            if msg is not None and msg.arbitration_id == 0x510 and len(msg.data) >= 4:
                try:
                    # 基于can_temperature_reader.py的解析方法
                    temp1_raw = struct.unpack('<h', msg.data[0:2])[0]  # 小端序int16
                    temp1_celsius = temp1_raw / 10.0
                    
                    temp2_raw = struct.unpack('<h', msg.data[2:4])[0]  # 小端序int16
                    temp2_celsius = temp2_raw / 10.0
                    
                    self.vulcan_temp_s1 = temp1_celsius
                    self.vulcan_temp_s2 = temp2_celsius
                    
                    self.logger.debug(f"🌡️ Vulcan温度: S1={temp1_celsius:.1f}°C, S2={temp2_celsius:.1f}°C")
                    return True
                    
                except struct.error as e:
                    self.logger.debug(f"CAN数据解析错误: {e}")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.debug(f"CAN温度读取失败: {e}")
            return False
    
    def read_cpu_temperature(self):
        """读取CPU温度"""
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return temps['coretemp'][0].current
            elif 'cpu_thermal' in temps:
                return temps['cpu_thermal'][0].current
            else:
                # 尝试获取第一个可用的CPU温度
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
        except Exception as e:
            self.logger.debug(f"CPU温度读取失败: {e}")
        return 0.0
    
    def create_temperature_bar(self, temp, min_temp=0, max_temp=100, width=15):
        """创建温度可视化进度条"""
        if temp < -900:  # 异常值
            return "[------]"
        
        # 计算进度条填充长度
        fill_length = int((temp - min_temp) / (max_temp - min_temp) * width)
        fill_length = max(0, min(width, fill_length))
        
        # 根据温度设置颜色指示
        if temp >= 80:
            bar_char = "🔴"  # 高温 - 红色
        elif temp >= 60:
            bar_char = "🟡"  # 中高温 - 黄色
        elif temp >= 40:
            bar_char = "🟢"  # 中温 - 绿色
        else:
            bar_char = "🔵"  # 低温 - 蓝色
        
        empty_char = "▫"
        bar = bar_char * fill_length + empty_char * (width - fill_length)
        return f"[{bar}]"
    
    def print_progress_bar(self, percentage, width=20):
        """打印进度条"""
        filled = int(percentage / 100 * width)
        empty = width - filled
        
        if percentage >= 80:
            color = "🔴"  # 高负载 - 红色
        elif percentage >= 60:
            color = "🟡"  # 中高负载 - 黄色
        else:
            color = "🟢"  # 正常负载 - 绿色
            
        bar = color * filled + "▫" * empty
        print(f"[{bar}] {percentage:5.1f}%")
    
    def record_temperature_data(self, cpu_temp, vulcan_s1, vulcan_s2):
        """记录温度数据到CSV文件"""
        current_time = time.time()
        current_datetime = datetime.datetime.now()
        
        # 创建CSV记录
        csv_line = f"{current_time},{current_datetime.strftime('%Y-%m-%d %H:%M:%S')},{cpu_temp:.1f},{vulcan_s1:.1f},{vulcan_s2:.1f}\n"
        
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write(csv_line)
        except Exception as e:
            self.logger.error(f"温度数据写入失败: {e}")
    
    def setup_temperature_monitor(self):
        """设置温度监控文件"""
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入CSV标题行
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("timestamp,datetime,cpu_temp,vulcan_s1_temp,vulcan_s2_temp\n")
        
        self.logger.info(f"温度数据文件已创建: {self.output_file}")
    
    def run_monitoring_loop(self):
        """运行主监控循环"""
        self.logger.info("=== 开始温度监控系统 ===")
        self.logger.info(f"运行时长: {self.duration}秒")
        self.logger.info(f"刷新间隔: {self.interval}秒")
        self.logger.info(f"压力测试: {self.stress_level}")
        
        # 初始化
        self.setup_temperature_monitor()
        self.init_can_bus()
        
        # 启动后台线程
        threads = []
        self.start_time = datetime.datetime.now()
        last_display_time = 0
        last_can_read_time = 0
        
        try:
            # 启动网络监控线程
            network_thread = threading.Thread(target=self._network_monitor_thread, daemon=True)
            network_thread.start()
            threads.append(network_thread)
            
            # 启动压力测试线程
            self.start_stress_tests(threads)
            
            # 主监控循环
            iteration = 0
            while not self.stop_flag:
                current_time = time.time()
                current_datetime = datetime.datetime.now()
                elapsed = current_time - self.start_time.timestamp()
                
                # 检查运行时长
                if elapsed >= self.duration:
                    print(f"\n\n⏰ 达到运行时间 {self.duration} 秒，停止监控")
                    break
                
                # 读取温度数据
                self.cpu_temp = self.read_cpu_temperature()
                
                # 按设定间隔读取CAN温度
                if current_time - last_can_read_time >= self.interval:
                    self.read_can_temperature()
                    last_can_read_time = current_time
                
                # 记录温度数据
                self.record_temperature_data(self.cpu_temp, self.vulcan_temp_s1, self.vulcan_temp_s2)
                
                # 按设定间隔更新显示
                if current_time - last_display_time >= self.interval:
                    self.display_dashboard(current_datetime)
                    last_display_time = current_time
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print(f"\n\n⏹️  用户中断，停止监控")
            self.logger.info("用户中断，停止监控")
        except Exception as e:
            print(f"\n\n❌ 监控过程出错: {e}")
            import traceback
            self.logger.error(f"监控过程出错: {e}")
            traceback.print_exc()
        finally:
            # 设置停止标志
            self.stop_flag = True
            
            # 等待所有后台线程完成
            self.logger.info("等待所有监控线程完成...")
            for thread in threads:
                thread.join(timeout=5)
            
            self.logger.info("所有监控线程已完成")
            
            # 保存结果
            self.save_results()
            
            # 清理资源
            if self.can_bus:
                self.can_bus.shutdown()
                self.logger.info("CAN总线已关闭")
    
    def display_dashboard(self, current_datetime):
        """显示实时监控仪表板"""
        # 获取系统状态
        system_stats = self.get_system_stats()
        network_status = self.check_network_connectivity()
        
        # 清屏并显示完整仪表板
        print("\033[2J\033[H", end='')  # 清屏
        print("=" * 80)
        print(f"🏠 高级温度监控系统 - {current_datetime.strftime('%Y-%m-%d %H:%M:%S')} - 间隔: {self.interval}s")
        print("=" * 80)
        
        # 温度区域
        print("🌡️  温度监控:")
        cpu_bar = self.create_temperature_bar(self.cpu_temp, 0, 100, 15)
        s1_bar = self.create_temperature_bar(self.vulcan_temp_s1, 0, 100, 15)
        s2_bar = self.create_temperature_bar(self.vulcan_temp_s2, 0, 100, 15)
        
        print(f"  CPU: {self.cpu_temp:5.1f}°C {cpu_bar}")
        print(f"  Vulcan S1: {self.vulcan_temp_s1:5.1f}°C {s1_bar}")
        print(f"  Vulcan S2: {self.vulcan_temp_s2:5.1f}°C {s2_bar}")
        print()
        
        # 硬件资源区域
        print("💻 硬件资源:")
        print(f"  CPU使用率: {system_stats['cpu_percent']:5.1f}% ", end='')
        self.print_progress_bar(system_stats['cpu_percent'], 50)
        print(f"  内存使用率: {system_stats['memory_percent']:5.1f}% ", end='')
        self.print_progress_bar(system_stats['memory_percent'], 50)
        print(f"  磁盘使用率: {system_stats['disk_percent']:5.1f}% ", end='')
        self.print_progress_bar(system_stats['disk_percent'], 50)
        print()
        
        # 网络状态区域 - 显示11个设备的连通性
        print("🌐 网络设备连通性 (11个设备):")
        if network_status and 'system_error' not in network_status:
            up_count = 0
            for device_name, info in network_status.items():
                if info['status'] == 'UP':
                    status_icon = "🟢"
                    up_count += 1
                elif info['status'] == 'DOWN':
                    status_icon = "🔴"
                else:
                    status_icon = "🟡"  # TIMEOUT或其他状态
                
                # 格式化显示设备信息
                device_type = "📹" if "cam" in device_name else "📡" if "airy" in device_name or "e1r" in device_name else "💻"
                ping_info = f"({info['ping_time']})" if info['ping_time'] != 'N/A' else ""
                print(f"  {status_icon} {device_type} {device_name}: {info['status']} | {info['ip']} {ping_info}")
            
            # 显示连通性统计
            total_devices = len(network_status)
            down_count = total_devices - up_count
            print(f"\n  📊 统计: {up_count}/{total_devices} 设备在线, {down_count} 设备离线")
        else:
            print("  ⚠️  网络连通性检查失败")
        print()
        
        # CAN状态
        can_icon = "🟢" if (self.can_temp_enabled and self.vulcan_temp_s1 > -900) else "🔴"
        print(f"{can_icon} Vulcan CAN状态: {'正常' if self.can_temp_enabled else '禁用'}")
        print("=" * 80)
        
        # 强制刷新输出缓冲区
        sys.stdout.flush()
    
    def start_stress_tests(self, threads):
        """启动压力测试，根据硬件资源自动调整强度"""
        try:
            # 获取CPU核心数作为基础
            cpu_cores = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            # 根据硬件资源自动选择压力级别
            if self.stress_level == 'auto':
                if cpu_cores >= 8 and memory_gb >= 16:
                    self.stress_level = 'extreme'
                elif cpu_cores >= 4 and memory_gb >= 8:
                    self.stress_level = 'high'
                elif cpu_cores >= 2 and memory_gb >= 4:
                    self.stress_level = 'medium'
                else:
                    self.stress_level = 'low'
            
            self.logger.info(f"启动{self.stress_level}强度压力测试")
            
            if self.stress_level == 'low':
                self.start_low_stress(threads)
            elif self.stress_level == 'medium':
                self.start_medium_stress(threads)
            elif self.stress_level == 'high':
                self.start_high_stress(threads)
            elif self.stress_level == 'extreme':
                self.start_extreme_stress(threads)
                
        except Exception as e:
            self.logger.error(f"压力测试启动失败: {e}")
    
    def start_low_stress(self, threads):
        """低强度压力测试"""
        # 单线程轻负载
        stress_thread = threading.Thread(target=self._low_stress_thread, daemon=True, name="Low-Stress")
        stress_thread.start()
        threads.append(stress_thread)
    
    def start_medium_stress(self, threads):
        """中等强度压力测试"""
        # 多线程中等负载
        for i in range(4):
            cpu_thread = threading.Thread(target=self._medium_cpu_stress_thread, args=(i,), daemon=True, name=f"CPU-Medium-{i}")
            cpu_thread.start()
            threads.append(cpu_thread)
        
        memory_thread = threading.Thread(target=self._medium_memory_stress_thread, daemon=True, name="Memory-Medium")
        memory_thread.start()
        threads.append(memory_thread)
        
        disk_thread = threading.Thread(target=self._medium_disk_stress_thread, daemon=True, name="Disk-Medium")
        disk_thread.start()
        threads.append(disk_thread)
    
    def start_high_stress(self, threads):
        """高强度压力测试"""
        # 多线程高负载
        for i in range(8):
            cpu_thread = threading.Thread(target=self._high_cpu_stress_thread, args=(i,), daemon=True, name=f"CPU-High-{i}")
            cpu_thread.start()
            threads.append(cpu_thread)
        
        for i in range(2):
            memory_thread = threading.Thread(target=self._high_memory_stress_thread, args=(i,), daemon=True, name=f"Memory-High-{i}")
            memory_thread.start()
            threads.append(memory_thread)
        
        for i in range(2):
            disk_thread = threading.Thread(target=self._high_disk_stress_thread, args=(i,), daemon=True, name=f"Disk-High-{i}")
            disk_thread.start()
            threads.append(disk_thread)
    
    def start_extreme_stress(self, threads):
        """极限强度压力测试"""
        # 最大线程极限负载
        for i in range(16):
            cpu_thread = threading.Thread(target=self._extreme_cpu_stress_thread, args=(i,), daemon=True, name=f"CPU-Extreme-{i}")
            cpu_thread.start()
            threads.append(cpu_thread)
        
        for i in range(4):
            memory_thread = threading.Thread(target=self._extreme_memory_stress_thread, args=(i,), daemon=True, name=f"Memory-Extreme-{i}")
            memory_thread.start()
            threads.append(memory_thread)
        
        for i in range(4):
            disk_thread = threading.Thread(target=self._extreme_disk_stress_thread, args=(i,), daemon=True, name=f"Disk-Extreme-{i}")
            disk_thread.start()
            threads.append(disk_thread)
    
    def _low_stress_thread(self):
        """低强度CPU压力测试线程"""
        try:
            while not self.stop_flag:
                # 轻量级CPU计算
                for _ in range(50000):
                    math.sqrt(random.random() * 10)
                    math.sin(random.random() * 180)
                
                # 轻量级内存操作
                small_data = [random.random() for _ in range(10000)]
                for i in range(500):
                    idx = random.randint(0, len(small_data) - 1)
                    small_data[idx] = math.sqrt(small_data[idx])
                
                # 轻量级磁盘操作
                try:
                    with open(f"/tmp/low_stress_{random.randint(1000, 9999)}.tmp", 'w') as f:
                        f.write("test" * 1000)
                    os.remove(f"/tmp/low_stress_{random.randint(1000, 9999)}.tmp")
                except:
                    pass
                
                time.sleep(0.05)  # 较长休眠，降低负载
                
        except Exception as e:
            self.logger.error(f"低强度压力测试错误: {e}")
    
    def _medium_cpu_stress_thread(self, thread_id):
        """中等强度CPU压力测试线程"""
        try:
            while not self.stop_flag:
                # 中等强度浮点运算
                for _ in range(200000):
                    math.sqrt(random.random() * 100)
                    math.sin(random.random() * 360)
                    math.cos(random.random() * 360)
                    math.pow(random.random(), 2)
                time.sleep(0.001)
        except Exception as e:
            self.logger.error(f"中等强度CPU压力测试错误: {e}")
    
    def _medium_memory_stress_thread(self):
        """中等强度内存压力测试线程"""
        try:
            # 分配中等大小内存
            data = [random.random() for _ in range(500000)]  # 约4MB
            while not self.stop_flag:
                # 频繁内存访问
                for _ in range(2000):
                    idx = random.randint(0, len(data) - 1)
                    data[idx] = math.sqrt(data[idx] * random.random())
                time.sleep(0.001)
        except Exception as e:
            self.logger.error(f"中等强度内存压力测试错误: {e}")
    
    def _medium_disk_stress_thread(self):
        """中等强度磁盘压力测试线程"""
        try:
            while not self.stop_flag:
                # 中等强度磁盘IO
                test_file = Path(f"/tmp/medium_stress_{random.randint(1000, 9999)}.tmp")
                test_data = b"MediumStressData" * 10000  # 约160KB
                
                # 写入操作
                with open(test_file, 'wb') as f:
                    f.write(test_data)
                    f.flush()
                
                # 读取操作
                with open(test_file, 'rb') as f:
                    read_data = f.read()
                
                # 验证数据
                if read_data != test_data:
                    self.logger.warning("磁盘数据验证失败")
                
                # 清理
                if test_file.exists():
                    test_file.unlink()
                
                time.sleep(0.005)
        except Exception as e:
            self.logger.error(f"中等强度磁盘压力测试错误: {e}")
    
    def _high_cpu_stress_thread(self, thread_id):
        """高强度CPU压力测试线程"""
        try:
            while not self.stop_flag:
                # 高强度浮点运算
                result = 0
                for i in range(500000):
                    result += math.sqrt(random.random() * 1000)
                    result += math.sin(i * 0.001) * math.cos(i * 0.001)
                    result += math.pow(random.random(), random.random() * 5)
                    result += math.log10(abs(random.random() * 100) + 1)
                
                # 矩阵运算模拟
                matrix_size = 50
                matrix = [[random.random() for _ in range(matrix_size)] for _ in range(matrix_size)]
                for i in range(matrix_size):
                    for j in range(matrix_size):
                        for k in range(matrix_size):
                            matrix[i][j] += matrix[i][k] * matrix[k][j]
                
                # 最小化休眠
                time.sleep(0.0001)
                
        except Exception as e:
            self.logger.error(f"高强度CPU压力测试错误: {e}")
    
    def _high_memory_stress_thread(self, thread_id):
        """高强度内存压力测试线程"""
        try:
            # 分配大内存块
            large_data = []
            for _ in range(10):
                large_data.append([random.random() for _ in range(1000000)])  # 约80MB每块
            
            while not self.stop_flag:
                # 高强度内存访问和复制
                for data_block in large_data:
                    # 随机访问和修改
                    for _ in range(5000):
                        idx = random.randint(0, len(data_block) - 1)
                        data_block[idx] = math.sqrt(data_block[idx] * random.random())
                    
                    # 内存复制操作
                    temp_copy = data_block[::2].copy()
                    data_block[::2] = temp_copy
                    
                    # 内存排序（高消耗操作）
                    if random.random() < 0.01:
                        data_block.sort()
                
                # 分配临时内存并立即释放
                temp_large = [random.random() for _ in range(100000)]
                temp_large.reverse()
                del temp_large
                
                time.sleep(0.0001)
                
        except Exception as e:
            self.logger.error(f"高强度内存压力测试错误: {e}")
    
    def _high_disk_stress_thread(self, thread_id):
        """高强度磁盘压力测试线程"""
        try:
            while not self.stop_flag:
                # 高强度磁盘IO
                test_file = Path(f"/tmp/high_stress_{thread_id}_{random.randint(1000, 9999)}.tmp")
                large_data = b"HighStressData" * 50000  # 约780KB
                
                # 多次写入和读取
                for _ in range(5):
                    # 写入大文件
                    with open(test_file, 'wb') as f:
                        for _ in range(10):
                            f.write(large_data)
                            f.flush()
                    
                    # 随机位置读取
                    with open(test_file, 'rb') as f:
                        f.seek(random.randint(0, len(large_data) * 5))
                        read_data = f.read(random.randint(1000, 10000))
                    
                    # 文件复制
                    copy_file = test_file.with_name(f"copy_{thread_id}_{random.randint(1000, 9999)}.tmp")
                    import shutil
                    shutil.copy(test_file, copy_file)
                    
                    # 验证复制文件
                    with open(copy_file, 'rb') as f:
                        copy_data = f.read()
                    
                    if len(copy_data) != test_file.stat().st_size:
                        self.logger.warning(f"磁盘复制大小不匹配: {thread_id}")
                    
                    # 清理
                    copy_file.unlink()
                
                # 随机重命名和删除
                if test_file.exists():
                    final_name = test_file.with_name(f"final_{thread_id}_{random.randint(1000, 9999)}.tmp")
                    test_file.rename(final_name)
                    final_name.unlink()
                
                time.sleep(0.0005)
                
        except Exception as e:
            self.logger.error(f"高强度磁盘压力测试错误: {e}")
    
    def _extreme_cpu_stress_thread(self, thread_id):
        """极限强度CPU压力测试线程"""
        try:
            # 预计算一些常量避免重复计算
            constants = [math.sqrt(i) for i in range(1, 1000)]
            
            while not self.stop_flag:
                # 极限浮点运算
                result = 0
                for i in range(1000000):  # 百万次循环
                    # 多种复杂数学运算
                    result += math.sqrt(abs(math.sin(i * 0.001) * math.cos(i * 0.002)) * 1000)
                    result += math.pow(math.log10(abs(i) + 1), random.random() * 3)
                    result += math.atan2(random.random() * 100, random.random() * 100)
                    result += math.gamma(abs(random.random()) * 10 + 1)
                    
                    # 模运算和位运算
                    if i % 1000 == 0:
                        result ^= i
                        result = (result << 1) | (result >> 31)
                
                # 大矩阵运算
                matrix_size = 100
                matrix_a = [[random.random() for _ in range(matrix_size)] for _ in range(matrix_size)]
                matrix_b = [[random.random() for _ in range(matrix_size)] for _ in range(matrix_size)]
                
                # 矩阵乘法
                result_matrix = [[0 for _ in range(matrix_size)] for _ in range(matrix_size)]
                for i in range(matrix_size):
                    for j in range(matrix_size):
                        for k in range(matrix_size):
                            result_matrix[i][j] += matrix_a[i][k] * matrix_b[k][j]
                
                # 特征值计算（简化版）
                for i in range(matrix_size):
                    row_sum = sum(result_matrix[i])
                    if row_sum != 0:
                        for j in range(matrix_size):
                            result_matrix[i][j] /= row_sum
                
                # 复杂的三角函数组合
                angle = 0
                for i in range(10000):
                    angle += i * 0.01
                    result += math.sin(angle) * math.cos(angle * 1.1) * math.tan(angle * 0.9)
                
                # 最小化休眠 - 极限模式
                if thread_id % 4 == 0:  # 每4个线程中有一个短暂休眠
                    time.sleep(0.00001)  # 10微秒
                
        except Exception as e:
            self.logger.error(f"极限强度CPU压力测试错误: {e}")
    
    def _extreme_memory_stress_thread(self, thread_id):
        """极限强度内存压力测试线程"""
        try:
            # 分配极大内存块 - 每块约200MB，共10块 = 2GB
            huge_data_blocks = []
            for block_id in range(10):
                huge_data_blocks.append([random.random() for _ in range(25000000)])  # 约200MB
            
            while not self.stop_flag:
                # 极限内存访问
                for block_id, data_block in enumerate(huge_data_blocks):
                    # 全块扫描和修改
                    for i in range(len(data_block)):
                        # 复杂数学运算
                        data_block[i] = math.sqrt(abs(data_block[i]) * random.random() * 1000)
                        data_block[i] += math.sin(i * 0.0001) * math.cos(i * 0.0001)
                        
                        # 每1000个元素进行复杂操作
                        if i % 1000 == 0 and i + 1000 < len(data_block):
                            # 子数组排序
                            sub_array = data_block[i:i+1000]
                            sub_array.sort()
                            data_block[i:i+1000] = sub_array
                            
                            # 子数组统计计算
                            mean_val = sum(sub_array) / len(sub_array)
                            variance = sum((x - mean_val) ** 2 for x in sub_array) / len(sub_array)
                            std_dev = math.sqrt(variance)
                            
                            # 标准化处理
                            if std_dev > 0:
                                for j in range(1000):
                                    data_block[i+j] = (data_block[i+j] - mean_val) / std_dev
                        
                        # 内存复制和交换操作
                        if random.random() < 0.1:  # 10%概率
                            other_block_id = random.randint(0, len(huge_data_blocks) - 1)
                            if other_block_id != block_id:
                                # 块间数据交换
                                swap_size = min(100000, len(data_block))
                                start_idx = random.randint(0, len(data_block) - swap_size)
                                other_start_idx = random.randint(0, len(huge_data_blocks[other_block_id]) - swap_size)
                                
                                temp_data = data_block[start_idx:start_idx + swap_size].copy()
                                data_block[start_idx:start_idx + swap_size] = huge_data_blocks[other_block_id][other_start_idx:other_start_idx + swap_size]
                                huge_data_blocks[other_block_id][other_start_idx:other_start_idx + swap_size] = temp_data
                        
                        # 内存分配和释放（造成碎片化）
                        if random.random() < 0.05:  # 5%概率
                            temp_allocation = [random.random() for _ in range(100000)]  # 临时分配
                            temp_allocation.sort()  # 操作后删除
                            del temp_allocation
                    
                    # 极短暂休眠
                    time.sleep(0.00001)
                    
        except Exception as e:
            self.logger.error(f"极限强度内存压力测试错误: {e}")
    
    def _extreme_disk_stress_thread(self, thread_id):
        """极限强度磁盘压力测试线程"""
        try:
            # 多个测试文件并行操作
            test_files = []
            for i in range(5):
                test_files.append(Path(f"/tmp/extreme_stress_{thread_id}_{i}_{random.randint(1000, 9999)}.tmp"))
            
            while not self.stop_flag:
                # 极限磁盘IO - 每个文件约5MB，总共25MB
                for test_file in test_files:
                    # 生成大数据块
                    large_data = b"ExtremeStressData" * 300000  # 约5MB
                    
                    # 多次写入操作
                    for write_round in range(10):
                        with open(test_file, 'wb') as f:
                            for _ in range(10):
                                f.write(large_data)
                                f.flush()
                                os.fsync(f.fileno())  # 强制同步到磁盘
                    
                    # 随机位置多次读取
                    file_size = test_file.stat().st_size
                    for read_round in range(20):
                        with open(test_file, 'rb') as f:
                            # 随机位置读取
                            start_pos = random.randint(0, max(0, file_size - 1000000))
                            f.seek(start_pos)
                            read_data = f.read(random.randint(10000, 500000))
                            
                            # 数据验证
                            if len(read_data) > 0:
                                expected_byte = b"ExtremeStressData"[read_round % len(b"ExtremeStressData")]
                                if read_data[0] != expected_byte:
                                    self.logger.warning(f"磁盘数据验证失败: {thread_id}")
                    
                    # 文件追加操作
                    with open(test_file, 'ab') as f:
                        for _ in range(5):
                            f.write(large_data[:100000])  # 追加100KB
                            f.flush()
                    
                    # 随机修改文件内容
                    with open(test_file, 'r+b') as f:
                        for modify_round in range(5):
                            modify_pos = random.randint(0, max(0, test_file.stat().st_size - 1000))
                            f.seek(modify_pos)
                            f.write(b"MODIFIED" * 125)  # 写入1KB修改数据
                            f.flush()
                    
                    # 文件间复制和移动（造成磁盘碎片化）
                    for i, source_file in enumerate(test_files):
                        if random.random() < 0.3:  # 30%概率
                            target_file = test_files[(i + 1) % len(test_files)]
                            
                            # 复制文件
                            import shutil
                            shutil.copy(source_file, target_file)
                            
                            # 验证复制
                            if source_file.stat().st_size != target_file.stat().st_size:
                                self.logger.warning(f"磁盘复制大小不匹配: {thread_id}")
                    
                    # 随机删除和重建文件（造成磁盘碎片化）
                    for test_file in test_files:
                        if random.random() < 0.2:  # 20%概率删除重建
                            if test_file.exists():
                                test_file.unlink()
                                # 立即重建
                                with open(test_file, 'wb') as f:
                                    f.write(b"RecreatedData" * 10000)
                    
                    # 极短休眠 - 极限模式
                    time.sleep(0.00005)  # 50微秒
                    
        except Exception as e:
            self.logger.error(f"极限强度磁盘压力测试错误: {e}")
    
    def _network_monitor_thread(self):
        """网络设备监控线程"""
        try:
            while not self.stop_flag:
                # 网络监控运行中...
                time.sleep(30)  # 每30秒检查一次
        except Exception as e:
            self.logger.error(f"网络监控错误: {e}")
    
    def save_results(self):
        """保存所有监控结果"""
        try:
            # 创建结果目录
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = Path(f"monitor_results_{timestamp}")
            results_dir.mkdir(exist_ok=True)
            
            # 保存温度数据
            temp_summary = {
                "total_readings": 0,
                "cpu_avg": 0,
                "vulcan_s1_avg": 0,
                "vulcan_s2_avg": 0
            }
            
            # 复制温度数据文件
            import shutil
            shutil.copy(self.output_file, results_dir / "temperature_data.csv")
            
            # 创建总结报告
            summary_report = {
                "system_info": {
                    "start_time": self.start_time.isoformat(),
                    "duration": self.duration,
                    "interval": self.interval,
                    "stress_level": self.stress_level,
                    "log_file": str(self.log_dir / f"temperature_monitor_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log")
                },
                "temperature_summary": temp_summary,
                "network_performance": {
                    "total_tests": 0,
                    "successful_tests": 0
                },
                "stress_test_summary": {
                    "cpu_threads": 0,
                    "memory_allocation_mb": 0,
                    "disk_io_operations": 0,
                    "disk_io_mb": 0
                }
            }
            
            with open(results_dir / "summary_report.json", "w", encoding="utf-8") as f:
                json.dump(summary_report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ 所有结果已保存到: {results_dir}")
            
        except Exception as e:
            self.logger.error(f"保存结果错误: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='高级温度监控系统 - 基于network_test.sh和can_temperature_reader.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python3 temperature_monitor.py --duration 3600 --interval 2 --stress-level medium
  python3 temperature_monitor.py --duration 14400 --interval 2 --stress-level high
  python3 temperature_monitor.py --duration 7200 --interval 5 --stress-level extreme
        """
    )
    
    parser.add_argument('--duration', '-d', type=int, default=300, 
                       help='运行时长（秒，默认: 300）')
    parser.add_argument('--interval', '-i', type=int, choices=[1, 2, 5, 10, 30], default=2,
                       help='刷新间隔（秒: 1/2/5/10/30，默认: 2）')
    parser.add_argument('--stress-level', '-s', choices=['low', 'medium', 'high', 'extreme', 'auto'], default='medium',
                       help='压力测试强度（低/中/高/极限/自动，默认: medium）')
    parser.add_argument('--output', '-o', help='温度数据输出文件名（默认: temperature_log_YYYYMMDD_HHMMSS.csv）')
    parser.add_argument('--log-dir', help='日志文件目录（默认: logs）')
    parser.add_argument('--no-stress', action='store_true', help='禁用后台压力测试')
    parser.add_argument('--no-network', action='store_true', help='禁用后台网络测试')
    
    args = parser.parse_args()
    
    # 创建监控器
    monitor = TemperatureMonitor(
        duration=args.duration,
        interval=args.interval,
        stress_level='low' if args.no_stress else args.stress_level,
        output_file=args.output,
        log_dir=args.log_dir
    )
    
    try:
        monitor.run_monitoring_loop()
    except KeyboardInterrupt:
        print("\n\n用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()