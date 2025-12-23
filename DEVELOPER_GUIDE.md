# 🔧 开发者指南 - Matrix FAT 温度测试系统

## 📋 项目概述

Matrix FAT温度测试系统是专为Matrix FAT环境设计的高级温度监控解决方案，集成11个网络设备监控、Vulcan CAN温度读取、硬件资源监控和智能压力测试功能。

## 🏗️ 系统架构

### 核心组件

```
temperature_monitor.py (主程序)
├── TemperatureMonitor (温度监控核心类)
├── CANTemperatureReader (CAN温度读取类)
├── NetworkMonitor (网络设备监控类)
├── ResourceMonitor (硬件资源监控类)
├── StressTestManager (压力测试管理类)
└── DisplayManager (显示管理类)
```

## 🔍 详细架构分析

### 1. 温度监控核心 (TemperatureMonitor)

**职责**: 协调所有监控组件，管理主循环

```python
class TemperatureMonitor:
    def __init__(self, duration=300, interval=2, stress_level='medium'):
        """
        初始化温度监控系统
        
        Args:
            duration: 运行时长（秒）
            interval: 刷新间隔（秒）
            stress_level: 压力测试强度
        """
        self.duration = duration
        self.interval = interval
        self.stress_level = stress_level
        
        # 初始化各个子系统
        self.can_reader = CANTemperatureReader()
        self.network_monitor = NetworkMonitor()
        self.resource_monitor = ResourceMonitor()
        self.stress_manager = StressTestManager(stress_level)
        self.display_manager = DisplayManager()
        
        # 数据记录
        self.data_logger = DataLogger()
        
    def run_monitoring(self):
        """主监控循环"""
        start_time = time.time()
        
        while not self.stop_flag:
            # 收集数据
            temps = self.can_reader.read_temperatures()
            network_status = self.network_monitor.check_all_devices()
            resources = self.resource_monitor.get_resources()
            stress_tests = self.stress_manager.run_tests()
            
            # 显示更新
            self.display_manager.update_display(temps, network_status, resources, stress_tests)
            
            # 数据记录
            self.data_logger.log_data(temps, network_status, resources)
            
            # 等待下一个周期
            time.sleep(self.interval)
```

### 2. CAN温度读取器 (CANTemperatureReader)

**职责**: 从Vulcan设备读取CAN总线温度数据

```python
class CANTemperatureReader:
    def __init__(self, can_interface='can0', can_id=0x510):
        """
        初始化CAN温度读取器
        
        Args:
            can_interface: CAN接口名称
            can_id: CAN消息ID
        """
        self.can_interface = can_interface
        self.can_id = can_id
        self.bus = None
        
    def read_temperatures(self):
        """读取温度数据"""
        try:
            # 基于can_temperature_reader.py的实现
            # 使用硬件过滤，避免软件过滤开销
            temps = self._read_can_temperatures()
            return {
                'vulcan_s1': temps[0] / 10.0,  # 转换为摄氏度
                'vulcan_s2': temps[1] / 10.0,
                'status': '正常'
            }
        except Exception as e:
            return {
                'vulcan_s1': -999.0,
                'vulcan_s2': -999.0,
                'status': f'错误: {str(e)}'
            }
```

### 3. 网络设备监控器 (NetworkMonitor)

**职责**: 监控11个网络设备的连通性

```python
class NetworkMonitor:
    def __init__(self):
        """基于network_test.sh的设备列表"""
        self.devices = [
            # 相机设备（5个）
            {'name': 'hazard_cam', 'ip': '192.168.11.9', 'type': '📹'},
            {'name': 'dock_cam', 'ip': '192.168.11.10', 'type': '📹'},
            {'name': 'ptz_cam', 'ip': '192.168.11.68', 'type': '📹'},
            {'name': 'ptz_ir_cam', 'ip': '192.168.11.69', 'type': '📹'},
            {'name': 'bosch_cam', 'ip': '192.168.11.65', 'type': '📹'},
            
            # 雷达设备（4个）
            {'name': 'airy_front', 'ip': '10.7.5.152', 'type': '📡'},
            {'name': 'airy_rear', 'ip': '10.7.5.153', 'type': '📡'},
            {'name': 'e1r_left', 'ip': '10.7.5.103', 'type': '📡'},
            {'name': 'e1r_right', 'ip': '10.7.5.104', 'type': '📡'},
            
            # PC设备（2个）
            {'name': 'va_pc', 'ip': '192.168.140.75', 'type': '💻'},
            {'name': 'nav_pc', 'ip': '192.168.11.88', 'type': '💻'}
        ]
    
    def check_all_devices(self):
        """检查所有设备状态"""
        results = []
        for device in self.devices:
            status = self._check_device(device)
            results.append(status)
        return results
```

### 4. 硬件资源监控器 (ResourceMonitor)

**职责**: 监控系统硬件资源使用情况

```python
class ResourceMonitor:
    def __init__(self):
        """初始化硬件资源监控器"""
        pass
        
    def get_resources(self):
        """获取系统资源使用情况"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'cpu_temp': self._get_cpu_temperature()
        }
```

### 5. 压力测试管理器 (StressTestManager)

**职责**: 管理4级压力测试，根据硬件自动调节强度

```python
class StressTestManager:
    def __init__(self, stress_level='medium'):
        """
        初始化压力测试管理器
        
        Args:
            stress_level: 压力测试强度 (low/medium/high/extreme/auto)
        """
        self.stress_level = stress_level
        self.auto_detect_level()
        
    def auto_detect_level(self):
        """根据硬件自动检测压力测试强度"""
        if self.stress_level == 'auto':
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            if cpu_count >= 8 and memory_gb >= 16:
                self.stress_level = 'extreme'
            elif cpu_count >= 4 and memory_gb >= 8:
                self.stress_level = 'high'
            elif cpu_count >= 2 and memory_gb >= 4:
                self.stress_level = 'medium'
            else:
                self.stress_level = 'low'
```

### 6. 显示管理器 (DisplayManager)

**职责**: 管理实时仪表板显示

```python
class DisplayManager:
    def __init__(self):
        """初始化显示管理器"""
        self.terminal_width = 80
        
    def update_display(self, temps, network_status, resources, stress_tests):
        """更新显示内容"""
        self.clear_screen()
        
        # 标题栏
        self.print_header()
        
        # 温度显示
        self.print_temperatures(temps)
        
        # 硬件资源
        self.print_resources(resources)
        
        # 网络设备状态
        self.print_network_status(network_status)
        
        # 状态信息
        self.print_status(temps, network_status)
        
    def print_temperatures(self, temps):
        """打印温度信息，带彩色进度条"""
        # CPU温度
        cpu_temp = temps.get('cpu_temp', 0)
        cpu_bar = self.create_temp_bar(cpu_temp)
        
        # Vulcan温度
        vulcan_s1 = temps.get('vulcan_s1', 0)
        vulcan_s2 = temps.get('vulcan_s2', 0)
        s1_bar = self.create_temp_bar(vulcan_s1)
        s2_bar = self.create_temp_bar(vulcan_s2)
        
        print(f"🌡️  温度监控:")
        print(f"  CPU:  {cpu_temp:5.1f}°C [{cpu_bar}]")
        print(f"  Vulcan S1:  {vulcan_s1:5.1f}°C [{s1_bar}]")
        print(f"  Vulcan S2:  {vulcan_s2:5.1f}°C [{s2_bar}]")
        print()
```

## 🎨 显示系统详细设计

### 彩色进度条算法

```python
def create_temp_bar(self, temp, max_temp=100, bar_length=20):
    """
    创建温度彩色进度条
    
    Args:
        temp: 温度值
        max_temp: 最大温度
        bar_length: 进度条长度
        
    Returns:
        彩色进度条字符串
    """
    # 计算填充长度
    fill_length = int((temp / max_temp) * bar_length)
    
    # 根据温度选择颜色
    if temp < 40:
        color = '🟢'  # 绿色 - 低温
    elif temp < 70:
        color = '🟡'  # 黄色 - 中温
    elif temp < 85:
        color = '🟠'  # 橙色 - 高温
    else:
        color = '🔴'  # 红色 - 极高温
    
    # 创建进度条
    filled = color * fill_length
    empty = '▫' * (bar_length - fill_length)
    
    return filled + empty
```

### 网络设备状态显示

```python
def print_network_status(self, network_status):
    """打印网络设备状态"""
    print(f"🌐 网络设备连通性 ({len(network_status)}个设备):")
    
    online_count = 0
    for device in network_status:
        status = '🟢' if device['status'] == 'UP' else '🔴'
        type_icon = device['type']
        
        if device['status'] == 'UP':
            online_count += 1
            print(f"  {status} {type_icon} {device['name']}: UP | {device['ip']} ({device['response_time']:.3f}ms)")
        else:
            print(f"  {status} {type_icon} {device['name']}: DOWN | {device['ip']} ")
    
    print(f"  📊 统计: {online_count}/{len(network_status)} 设备在线, {len(network_status) - online_count} 设备离线")
    print()
```

## 📊 数据记录系统

### CSV格式设计

```python
class DataLogger:
    def __init__(self, filename=None):
        """初始化数据记录器"""
        if filename is None:
            filename = f"temperature_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.filename = filename
        self._create_csv_file()
    
    def _create_csv_file(self):
        """创建CSV文件并写入表头"""
        with open(self.filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'timestamp',      # Unix时间戳
                'datetime',       # 可读时间
                'cpu_temp',       # CPU温度
                'vulcan_s1_temp', # Vulcan S1温度
                'vulcan_s2_temp', # Vulcan S2温度
                'cpu_percent',    # CPU使用率
                'memory_percent', # 内存使用率
                'disk_percent',   # 磁盘使用率
                'online_devices', # 在线设备数
                'total_devices'   # 总设备数
            ])
    
    def log_data(self, temps, network_status, resources):
        """记录数据到CSV文件"""
        with open(self.filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                time.time(),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                temps.get('cpu_temp', 0),
                temps.get('vulcan_s1', 0),
                temps.get('vulcan_s2', 0),
                resources.get('cpu_percent', 0),
                resources.get('memory_percent', 0),
                resources.get('disk_percent', 0),
                sum(1 for d in network_status if d['status'] == 'UP'),
                len(network_status)
            ])
```

## 🔧 压力测试详细实现

### 基础压力测试类

```python
class BaseStressTest:
    """基础压力测试类"""
    
    def __init__(self, intensity=1):
        """
        初始化压力测试
        
        Args:
            intensity: 强度等级 (1-4)
        """
        self.intensity = intensity
        self.start_time = None
        self.results = {}
    
    def run(self):
        """运行压力测试"""
        self.start_time = time.time()
        try:
            self.execute_test()
            self.results['status'] = 'success'
        except Exception as e:
            self.results['status'] = 'failed'
            self.results['error'] = str(e)
        
        self.results['duration'] = time.time() - self.start_time
        return self.results
    
    def execute_test(self):
        """执行具体的压力测试，子类需要实现"""
        raise NotImplementedError
```

### CPU压力测试

```python
class CPUStressTest(BaseStressTest):
    """CPU压力测试"""
    
    def execute_test(self):
        """执行CPU压力测试"""
        # 根据强度确定线程数
        thread_count = self.intensity * 2
        
        def cpu_intensive_task():
            """CPU密集型任务"""
            # 斐波那契数列计算
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)
            
            # 矩阵运算
            def matrix_multiply():
                size = 50 * self.intensity
                a = np.random.rand(size, size)
                b = np.random.rand(size, size)
                return np.dot(a, b)
            
            # 执行计算
            fibonacci(25 + self.intensity * 5)
            matrix_multiply()
        
        # 多线程执行
        threads = []
        for _ in range(thread_count):
            thread = threading.Thread(target=cpu_intensive_task)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
```

### 内存压力测试

```python
class MemoryStressTest(BaseStressTest):
    """内存压力测试"""
    
    def execute_test(self):
        """执行内存压力测试"""
        # 根据强度确定内存使用量
        base_size = 1024 * 1024  # 1MB
        memory_size = base_size * (2 ** (self.intensity - 1))
        
        # 创建大数据结构
        data = []
        for _ in range(memory_size):
            data.append(random.randint(0, 1000))
        
        # 执行内存操作
        self._perform_memory_operations(data)
        
        # 清理内存
        del data
        gc.collect()
    
    def _perform_memory_operations(self, data):
        """执行内存操作"""
        # 排序操作
        sorted_data = sorted(data)
        
        # 统计计算
        avg = sum(data) / len(data)
        max_val = max(data)
        min_val = min(data)
        
        # 搜索操作
        search_value = random.choice(data)
        count = data.count(search_value)
```

### 磁盘压力测试

```python
class DiskStressTest(BaseStressTest):
    """磁盘压力测试"""
    
    def __init__(self, intensity=1, test_dir='/tmp'):
        super().__init__(intensity)
        self.test_dir = test_dir
        self.test_files = []
    
    def execute_test(self):
        """执行磁盘压力测试"""
        # 创建测试文件
        self.create_test_files()
        
        # 执行文件操作
        self.perform_file_operations()
        
        # 清理测试文件
        self.cleanup_test_files()
    
    def create_test_files(self):
        """创建测试文件"""
        file_size = 1024 * 40 * (2 ** (self.intensity - 1))  # 40KB * 2^(intensity-1)
        file_count = self.intensity * 5
        
        for i in range(file_count):
            filename = os.path.join(self.test_dir, f'stress_test_{i}.dat')
            
            # 写入随机数据
            with open(filename, 'wb') as f:
                f.write(os.urandom(file_size))
            
            self.test_files.append(filename)
    
    def perform_file_operations(self):
        """执行文件操作"""
        for filename in self.test_files:
            # 读取文件
            with open(filename, 'rb') as f:
                content = f.read()
            
            # 修改内容
            modified_content = content[::-1]
            
            # 写回文件
            with open(filename, 'wb') as f:
                f.write(modified_content)
            
            # 复制文件
            copy_filename = filename + '.copy'
            shutil.copy2(filename, copy_filename)
            
            # 验证复制
            with open(filename, 'rb') as f1, open(copy_filename, 'rb') as f2:
                assert f1.read() == f2.read()
            
            # 删除复制文件
            os.remove(copy_filename)
    
    def cleanup_test_files(self):
        """清理测试文件"""
        for filename in self.test_files:
            if os.path.exists(filename):
                os.remove(filename)
        self.test_files.clear()
```

## 🚀 启动脚本设计

### 一键启动脚本 (start_monitor.sh)

```bash
#!/bin/bash
# Matrix FAT温度监控系统启动脚本

# 默认参数
DURATION=300
INTERVAL=2
STRESS_LEVEL="medium"
OUTPUT_FILE=""
LOG_DIR="logs"
BACKGROUND=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --duration|-d)
            DURATION="$2"
            shift 2
            ;;
        --interval|-i)
            INTERVAL="$2"
            shift 2
            ;;
        --stress-level|-s)
            STRESS_LEVEL="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --background|-b)
            BACKGROUND=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "错误: 未知参数 '$1'"
            show_help
            exit 1
            ;;
    esac
done

# 创建日志目录
mkdir -p "$LOG_DIR"

# 构建命令
COMMAND="python3 temperature_monitor.py \
    --duration $DURATION \
    --interval $INTERVAL \
    --stress-level $STRESS_LEVEL"

if [[ -n "$OUTPUT_FILE" ]]; then
    COMMAND="$COMMAND --output $OUTPUT_FILE"
fi

if [[ -n "$LOG_DIR" ]]; then
    COMMAND="$COMMAND --log-dir $LOG_DIR"
fi

# 执行命令
if [[ "$BACKGROUND" == true ]]; then
    # 后台运行
    LOG_FILE="$LOG_DIR/temperature_monitor_$(date +%Y%m%d_%H%M%S).log"
    nohup $COMMAND > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "🚀 监控系统已在后台启动！"
    echo "📝 PID: $PID"
    echo "📊 日志文件: $LOG_FILE"
else
    # 前台运行
    echo "🚀 启动温度监控系统..."
    echo "⏱️  运行时长: $DURATION 秒"
    echo "🔄 刷新间隔: $INTERVAL 秒"
    echo "⚡ 压力测试: $STRESS_LEVEL"
    echo ""
    
    $COMMAND
fi
```

## 📊 性能优化

### 1. 多线程设计

```python
import threading
import queue

class ThreadedMonitor:
    """多线程监控器"""
    
    def __init__(self):
        self.data_queue = queue.Queue()
        self.threads = []
        self.stop_event = threading.Event()
    
    def start_monitoring(self):
        """启动多线程监控"""
        # 启动CAN读取线程
        can_thread = threading.Thread(target=self.can_monitor)
        can_thread.start()
        self.threads.append(can_thread)
        
        # 启动网络监控线程
        network_thread = threading.Thread(target=self.network_monitor)
        network_thread.start()
        self.threads.append(network_thread)
        
        # 启动资源监控线程
        resource_thread = threading.Thread(target=self.resource_monitor)
        resource_thread.start()
        self.threads.append(resource_thread)
    
    def stop_monitoring(self):
        """停止监控"""
        self.stop_event.set()
        for thread in self.threads:
            thread.join()
```

### 2. 缓存优化

```python
import functools
import time

class CachedMonitor:
    """缓存优化的监控器"""
    
    def __init__(self, cache_timeout=1):
        self.cache_timeout = cache_timeout
        self.cache = {}
    
    def cached_method(self, method, *args, **kwargs):
        """缓存方法调用"""
        cache_key = f"{method.__name__}:{args}:{kwargs}"
        current_time = time.time()
        
        # 检查缓存是否有效
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_timeout:
                return cached_result
        
        # 执行方法并缓存结果
        result = method(*args, **kwargs)
        self.cache[cache_key] = (result, current_time)
        return result
```

## 🧪 测试策略

### 单元测试

```python
import unittest
from unittest.mock import Mock, patch

class TestTemperatureMonitor(unittest.TestCase):
    """温度监控器单元测试"""
    
    def setUp(self):
        """测试设置"""
        self.monitor = TemperatureMonitor(duration=10, interval=1)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.monitor.duration, 10)
        self.assertEqual(self.monitor.interval, 1)
        self.assertIsNotNone(self.monitor.can_reader)
        self.assertIsNotNone(self.monitor.network_monitor)
    
    @patch('psutil.cpu_percent')
    def test_resource_monitoring(self, mock_cpu_percent):
        """测试资源监控"""
        mock_cpu_percent.return_value = 45.0
        
        resources = self.monitor.resource_monitor.get_resources()
        
        self.assertEqual(resources['cpu_percent'], 45.0)
    
    def test_temperature_bar_creation(self):
        """测试温度进度条创建"""
        bar = self.monitor.display_manager.create_temp_bar(50, max_temp=100, bar_length=10)
        
        self.assertEqual(len(bar), 10)
        self.assertIn('🟡', bar)  # 中温显示黄色
```

### 集成测试

```python
class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""
    
    def test_full_monitoring_cycle(self):
        """测试完整监控周期"""
        monitor = TemperatureMonitor(duration=5, interval=1)
        
        # 运行监控
        monitor.run_monitoring()
        
        # 验证数据记录
        self.assertTrue(os.path.exists(monitor.data_logger.filename))
        
        # 验证日志文件
        with open(monitor.data_logger.filename, 'r') as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 1)  # 至少包含表头和一行数据
```

## 📈 扩展开发

### 添加新的监控类型

```python
class CustomMonitor(BaseMonitor):
    """自定义监控器"""
    
    def __init__(self, config):
        """初始化自定义监控器"""
        super().__init__(config)
        
    def collect_data(self):
        """收集自定义数据"""
        # 实现数据收集逻辑
        return self.custom_data_collection()
    
    def display_data(self, data):
        """显示自定义数据"""
        # 实现数据显示逻辑
        return self.custom_display_format(data)
```

### 添加新的压力测试

```python
class CustomStressTest(BaseStressTest):
    """自定义压力测试"""
    
    def execute_test(self):
        """执行自定义压力测试"""
        # 实现具体的压力测试逻辑
        self.perform_custom_operations()
```

## 🔍 调试指南

### 日志系统

```python
import logging

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('temperature_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用日志
logger.info("监控系统启动")
logger.warning("CAN设备连接失败")
logger.error("网络监控异常")
```

### 调试模式

```python
class DebugMonitor(TemperatureMonitor):
    """调试模式监控器"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.debug_mode = True
        
    def run_monitoring(self):
        """调试模式运行"""
        if self.debug_mode:
            # 启用详细日志
            logging.getLogger().setLevel(logging.DEBUG)
            
            # 模拟数据
            self.use_mock_data = True
            
        super().run_monitoring()
```

## 📚 相关文档

- [README.md](./README.md) - 用户使用指南
- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API文档
- [PERFORMANCE.md](./PERFORMANCE.md) - 性能优化指南
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - 故障排除指南

## 🔄 版本控制

- **v1.0.0** - 初始版本，基础温度监控
- **v1.1.0** - 添加网络设备监控
- **v1.2.0** - 添加压力测试功能
- **v1.3.0** - 优化显示界面
- **v1.4.0** - 添加数据记录功能
- **v2.0.0** - 重构架构，模块化设计

## 🤝 贡献指南

1. Fork项目仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件。