# 📚 API文档 - Matrix FAT 温度测试系统

## 🔗 类和方法参考

### TemperatureMonitor 类

**描述**: 温度监控系统的核心类，负责协调所有监控组件

**位置**: `temperature_monitor.py`

#### 构造函数

```python
TemperatureMonitor(duration=300, interval=2, stress_level='medium')
```

**参数**:
- `duration` (int): 监控运行时长，单位秒，默认300秒
- `interval` (int): 数据刷新间隔，单位秒，默认2秒
- `stress_level` (str): 压力测试强度 ('low'/'medium'/'high'/'extreme'/'auto')，默认'medium'

**示例**:
```python
# 创建4小时监控系统
monitor = TemperatureMonitor(duration=14400, interval=2, stress_level='high')
```

#### 主要方法

##### run_monitoring()

**描述**: 启动温度监控系统的主循环

**返回**: None

**异常**: 可能抛出监控过程中的各种异常

**示例**:
```python
monitor = TemperatureMonitor(duration=3600)
monitor.run_monitoring()
```

##### stop_monitoring()

**描述**: 停止监控循环

**返回**: None

**示例**:
```python
monitor.stop_monitoring()
```

#### 属性

- `duration`: 监控运行时长
- `interval`: 数据刷新间隔
- `stress_level`: 压力测试强度
- `can_reader`: CAN温度读取器实例
- `network_monitor`: 网络设备监控器实例
- `resource_monitor`: 硬件资源监控器实例
- `stress_manager`: 压力测试管理器实例
- `display_manager`: 显示管理器实例
- `data_logger`: 数据记录器实例

---

### CANTemperatureReader 类

**描述**: 负责从Vulcan设备读取CAN总线温度数据

**位置**: `temperature_monitor.py`

#### 构造函数

```python
CANTemperatureReader(can_interface='can0', can_id=0x510)
```

**参数**:
- `can_interface` (str): CAN接口名称，默认'can0'
- `can_id` (int): CAN消息ID，默认0x510

**示例**:
```python
reader = CANTemperatureReader(can_interface='can0', can_id=0x510)
```

#### 主要方法

##### read_temperatures()

**描述**: 读取CAN总线温度数据

**返回**: dict - 包含温度和状态信息的字典

**返回格式**:
```python
{
    'vulcan_s1': 59.2,      # Vulcan S1温度（摄氏度）
    'vulcan_s2': 60.0,      # Vulcan S2温度（摄氏度）
    'status': '正常'         # 状态信息
}
```

**异常**: 捕获所有CAN相关异常，返回错误状态

**示例**:
```python
temps = reader.read_temperatures()
print(f"Vulcan S1: {temps['vulcan_s1']}°C")
print(f"Vulcan S2: {temps['vulcan_s2']}°C")
```

##### is_available()

**描述**: 检查CAN接口是否可用

**返回**: bool - True表示可用，False表示不可用

**示例**:
```python
if reader.is_available():
    temps = reader.read_temperatures()
```

---

### NetworkMonitor 类

**描述**: 监控11个网络设备的连通性状态

**位置**: `temperature_monitor.py`

#### 构造函数

```python
NetworkMonitor()
```

**参数**: 无

#### 主要方法

##### check_all_devices()

**描述**: 检查所有网络设备的状态

**返回**: list - 包含所有设备状态信息的列表

**返回格式**:
```python
[
    {
        'name': 'hazard_cam',
        'ip': '192.168.11.9',
        'type': '📹',
        'status': 'UP',
        'response_time': 0.260
    },
    {
        'name': 'nav_pc',
        'ip': '192.168.11.88',
        'type': '💻',
        'status': 'DOWN',
        'response_time': None
    }
    # ... 更多设备
]
```

**示例**:
```python
network_monitor = NetworkMonitor()
status = network_monitor.check_all_devices()
for device in status:
    print(f"{device['name']}: {device['status']}")
```

##### check_device(device_info)

**描述**: 检查单个设备的状态

**参数**:
- `device_info` (dict): 设备信息字典，包含'name', 'ip', 'type'键

**返回**: dict - 设备状态信息

**示例**:
```python
device = {'name': 'test_device', 'ip': '192.168.1.1', 'type': '💻'}
status = network_monitor.check_device(device)
```

##### get_device_list()

**描述**: 获取所有监控的设备列表

**返回**: list - 设备信息列表

**示例**:
```python
devices = network_monitor.get_device_list()
print(f"监控 {len(devices)} 个设备")
```

---

### ResourceMonitor 类

**描述**: 监控系统硬件资源使用情况

**位置**: `temperature_monitor.py`

#### 构造函数

```python
ResourceMonitor()
```

**参数**: 无

#### 主要方法

##### get_resources()

**描述**: 获取当前系统资源使用情况

**返回**: dict - 资源使用信息

**返回格式**:
```python
{
    'cpu_percent': 25.3,        # CPU使用率百分比
    'memory_percent': 45.7,     # 内存使用率百分比
    'disk_percent': 67.2,       # 磁盘使用率百分比
    'cpu_temp': 65.8            # CPU温度（摄氏度）
}
```

**示例**:
```python
resource_monitor = ResourceMonitor()
resources = resource_monitor.get_resources()
print(f"CPU使用率: {resources['cpu_percent']}%")
```

##### get_cpu_temperature()

**描述**: 获取CPU温度

**返回**: float - CPU温度（摄氏度）

**示例**:
```python
cpu_temp = resource_monitor.get_cpu_temperature()
print(f"CPU温度: {cpu_temp}°C")
```

---

### StressTestManager 类

**描述**: 管理4级压力测试，根据硬件自动调节强度

**位置**: `temperature_monitor.py`

#### 构造函数

```python
StressTestManager(stress_level='medium')
```

**参数**:
- `stress_level` (str): 压力测试强度 ('low'/'medium'/'high'/'extreme'/'auto')，默认'medium'

**示例**:
```python
stress_manager = StressTestManager(stress_level='high')
```

#### 主要方法

##### run_tests()

**描述**: 运行所有压力测试

**返回**: dict - 测试结果

**返回格式**:
```python
{
    'cpu_test': {
        'status': 'success',
        'duration': 2.5,
        'threads': 8
    },
    'memory_test': {
        'status': 'success',
        'duration': 1.8,
        'memory_used': '800MB'
    },
    'disk_test': {
        'status': 'success',
        'duration': 3.2,
        'files_processed': 20
    }
}
```

**示例**:
```python
results = stress_manager.run_tests()
print(f"CPU测试状态: {results['cpu_test']['status']}")
```

##### auto_detect_level()

**描述**: 根据硬件配置自动检测合适的压力测试强度

**返回**: str - 检测到的压力测试强度

**示例**:
```python
level = stress_manager.auto_detect_level()
print(f"自动检测到的强度: {level}")
```

##### set_stress_level(level)

**描述**: 设置压力测试强度

**参数**:
- `level` (str): 新的压力测试强度

**示例**:
```python
stress_manager.set_stress_level('extreme')
```

---

### DisplayManager 类

**描述**: 管理实时仪表板显示

**位置**: `temperature_monitor.py`

#### 构造函数

```python
DisplayManager()
```

**参数**: 无

#### 主要方法

##### update_display(temps, network_status, resources, stress_tests)

**描述**: 更新显示内容

**参数**:
- `temps` (dict): 温度数据
- `network_status` (list): 网络设备状态
- `resources` (dict): 硬件资源数据
- `stress_tests` (dict): 压力测试结果

**返回**: None

**示例**:
```python
display_manager = DisplayManager()
display_manager.update_display(temps, network_status, resources, stress_tests)
```

##### create_temp_bar(temp, max_temp=100, bar_length=20)

**描述**: 创建温度彩色进度条

**参数**:
- `temp` (float): 温度值
- `max_temp` (float): 最大温度值，默认100
- `bar_length` (int): 进度条长度，默认20

**返回**: str - 彩色进度条字符串

**示例**:
```python
bar = display_manager.create_temp_bar(65.5)
print(f"温度进度条: [{bar}]")
```

##### clear_screen()

**描述**: 清除屏幕内容

**返回**: None

**示例**:
```python
display_manager.clear_screen()
```

---

### DataLogger 类

**描述**: 负责数据记录到CSV文件

**位置**: `temperature_monitor.py`

#### 构造函数

```python
DataLogger(filename=None)
```

**参数**:
- `filename` (str): CSV文件名，如果为None则自动生成

**示例**:
```python
logger = DataLogger('my_temperature_data.csv')
```

#### 主要方法

##### log_data(temps, network_status, resources)

**描述**: 记录数据到CSV文件

**参数**:
- `temps` (dict): 温度数据
- `network_status` (list): 网络设备状态
- `resources` (dict): 硬件资源数据

**返回**: None

**示例**:
```python
logger.log_data(temps, network_status, resources)
```

##### get_filename()

**描述**: 获取当前使用的CSV文件名

**返回**: str - CSV文件名

**示例**:
```python
filename = logger.get_filename()
print(f"数据记录在文件: {filename}")
```

---

### BaseStressTest 类

**描述**: 压力测试基类，所有压力测试类都继承此类

**位置**: `temperature_monitor.py`

#### 构造函数

```python
BaseStressTest(intensity=1)
```

**参数**:
- `intensity` (int): 测试强度等级 (1-4)，默认1

#### 主要方法

##### run()

**描述**: 运行压力测试

**返回**: dict - 测试结果

**返回格式**:
```python
{
    'status': 'success',    # 或 'failed'
    'duration': 2.5,        # 测试持续时间
    'error': None           # 错误信息（如果有）
}
```

##### execute_test()

**描述**: 执行具体的压力测试，子类必须实现此方法

**返回**: None

---

### CPUStressTest 类

**描述**: CPU压力测试

**位置**: `temperature_monitor.py`

#### 构造函数

```python
CPUStressTest(intensity=1)
```

**参数**:
- `intensity` (int): 测试强度等级 (1-4)，默认1

#### 主要方法

##### execute_test()

**描述**: 执行CPU压力测试

**返回**: None

---

### MemoryStressTest 类

**描述**: 内存压力测试

**位置**: `temperature_monitor.py`

#### 构造函数

```python
MemoryStressTest(intensity=1)
```

**参数**:
- `intensity` (int): 测试强度等级 (1-4)，默认1

#### 主要方法

##### execute_test()

**描述**: 执行内存压力测试

**返回**: None

---

### DiskStressTest 类

**描述**: 磁盘压力测试

**位置**: `temperature_monitor.py`

#### 构造函数

```python
DiskStressTest(intensity=1, test_dir='/tmp')
```

**参数**:
- `intensity` (int): 测试强度等级 (1-4)，默认1
- `test_dir` (str): 测试目录，默认'/tmp'

#### 主要方法

##### execute_test()

**描述**: 执行磁盘压力测试

**返回**: None

---

## 🛠️ 实用函数

### parse_arguments()

**描述**: 解析命令行参数

**位置**: `temperature_monitor.py`

**返回**: argparse.Namespace - 解析后的参数

**示例**:
```python
args = parse_arguments()
print(f"运行时长: {args.duration}秒")
```

### setup_logging()

**描述**: 设置日志系统

**位置**: `temperature_monitor.py`

**参数**:
- `log_level` (str): 日志级别，默认'INFO'
- `log_file` (str): 日志文件路径，可选

**返回**: None

**示例**:
```python
setup_logging(log_level='DEBUG', log_file='monitor.log')
```

### validate_duration(duration)

**描述**: 验证运行时长参数

**位置**: `temperature_monitor.py`

**参数**:
- `duration` (int): 运行时长

**返回**: bool - 验证结果

**示例**:
```python
if validate_duration(3600):
    print("时长参数有效")
```

### validate_interval(interval)

**描述**: 验证刷新间隔参数

**位置**: `temperature_monitor.py`

**参数**:
- `interval` (int): 刷新间隔

**返回**: bool - 验证结果

**示例**:
```python
if validate_interval(2):
    print("间隔参数有效")
```

---

## 📊 数据格式规范

### 温度数据格式

```python
{
    'cpu_temp': 65.8,           # CPU温度
    'vulcan_s1': 59.2,          # Vulcan S1温度
    'vulcan_s2': 60.0,          # Vulcan S2温度
    'timestamp': 1736478393.309 # 时间戳
}
```

### 网络设备状态格式

```python
[
    {
        'name': 'device_name',      # 设备名称
        'ip': '192.168.1.1',        # IP地址
        'type': '📹',               # 设备类型图标
        'status': 'UP',             # 状态 (UP/DOWN)
        'response_time': 0.123      # 响应时间（毫秒）
    }
]
```

### 资源数据格式

```python
{
    'cpu_percent': 25.3,        # CPU使用率
    'memory_percent': 45.7,     # 内存使用率
    'disk_percent': 67.2,       # 磁盘使用率
    'cpu_temp': 65.8            # CPU温度
}
```

### CSV文件格式

```csv
timestamp,datetime,cpu_temp,vulcan_s1_temp,vulcan_s2_temp,cpu_percent,memory_percent,disk_percent,online_devices,total_devices
1736478393.309,2025-12-23 18:10:57,83.0,59.2,60.0,18.6,8.9,26.3,10,11
```

---

## 🔧 配置选项

### 监控参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| duration | int | 300 | 监控运行时长（秒） |
| interval | int | 2 | 数据刷新间隔（秒） |
| stress_level | str | 'medium' | 压力测试强度 |
| output_file | str | None | 输出文件名 |
| log_dir | str | 'logs' | 日志目录 |

### 网络设备配置

系统监控以下11个设备：

```python
DEVICES = [
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
```

### 压力测试配置

| 强度级别 | CPU线程数 | 内存使用 | 磁盘文件大小 | 适用场景 |
|----------|-----------|----------|--------------|----------|
| low | 2 | 4MB | 40KB | 轻量级测试 |
| medium | 4 | 20MB | 160KB | 标准测试 |
| high | 8 | 800MB | 780KB | 高强度测试 |
| extreme | 16 | 2GB | 5MB | 极限测试 |

---

## 🚨 错误处理

### 异常类型

```python
class MonitorError(Exception):
    """监控系统基础异常"""
    pass

class CANError(MonitorError):
    """CAN通信异常"""
    pass

class NetworkError(MonitorError):
    """网络监控异常"""
    pass

class StressTestError(MonitorError):
    """压力测试异常"""
    pass
```

### 错误码

| 错误码 | 描述 | 处理方式 |
|--------|------|----------|
| CAN001 | CAN接口不可用 | 返回-999温度值 |
| NET001 | 网络设备不可达 | 标记为DOWN状态 |
| STR001 | 压力测试失败 | 记录错误信息 |
| LOG001 | 日志写入失败 | 输出到控制台 |

---

## 📈 性能指标

### 系统性能

- **监控周期**: 2秒（可配置）
- **数据延迟**: <100ms
- **CPU占用**: <5%（中等强度）
- **内存使用**: <50MB

### 压力测试性能

| 测试类型 | 低强度 | 中等强度 | 高强度 | 极限强度 |
|----------|--------|----------|--------|----------|
| CPU测试 | 2秒 | 5秒 | 10秒 | 20秒 |
| 内存测试 | 1秒 | 3秒 | 8秒 | 15秒 |
| 磁盘测试 | 2秒 | 4秒 | 8秒 | 12秒 |

---

## 🔗 相关链接

- [开发者指南](./DEVELOPER_GUIDE.md)
- [用户使用指南](./README.md)
- [性能优化指南](./PERFORMANCE.md)
- [故障排除指南](./TROUBLESHOOTING.md)