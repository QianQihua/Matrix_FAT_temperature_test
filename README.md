# 🌡️ Matrix FAT 温度测试系统

高级温度监控系统，专为Matrix FAT环境设计，集成11个网络设备监控、Vulcan CAN温度读取、硬件资源监控和智能压力测试。

## 🎯 系统特色

- ✅ **11网络设备监控** - 基于network_test.sh的完整设备列表
- ✅ **Vulcan CAN温度** - 基于can_temperature_reader.py的专业读取
- ✅ **硬件资源可视化** - CPU/内存/磁盘使用率+彩色进度条
- ✅ **智能压力测试** - 根据硬件自动调节强度（低/中/高/极限）
- ✅ **实时仪表板** - 每2秒刷新，彩色温度指示
- ✅ **长时间运行** - 支持4小时+持续监控
- ✅ **数据记录** - CSV格式，便于后续绘图分析

## 📋 系统架构

```
temperature_monitoring_system/
├── temperature_monitor.py      # 主监控程序
├── start_monitor.sh           # 一键启动脚本
├── README.md                  # 本文档
├── LICENSE                    # 许可证
└── logs/                      # 日志文件目录
    └── temperature_monitor_*.log
```

## 🚀 快速开始

### 一键启动（推荐）
```bash
# 启动4小时监控（默认参数）
./start_monitor.sh

# 自定义参数
./start_monitor.sh --duration 14400 --interval 2 --stress-level medium
```

### 直接运行
```bash
# 基础运行
python3 temperature_monitor.py --duration 3600 --interval 2

# 完整参数
python3 temperature_monitor.py --duration 14400 --interval 2 --stress-level high
```

## 📊 实时监控界面

```
🏠 高级温度监控系统 - 2025-12-23 18:10:54 - 间隔: 2s
================================================================================
🌡️  温度监控:
  CPU:  83.0°C [🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴▫▫▫]
  Vulcan S1:  59.2°C [🟢🟢🟢🟢🟢🟢🟢🟢▫▫▫▫▫▫▫]
  Vulcan S2:  60.0°C [🟡🟡🟡🟡🟡🟡🟡🟡🟡▫▫▫▫▫▫]

💻 硬件资源:
  CPU使用率:  18.6% [🟢🟢🟢🟢🟢🟢🟢🟢🟢▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫]  18.6%
  内存使用率:   8.9% [🟢🟢🟢🟢▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫]   8.9%
  磁盘使用率:  26.3% [🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫▫]  26.3%

🌐 网络设备连通性 (11个设备):
  🟢 📹 hazard_cam: UP | 192.168.11.9 (0.260ms)
  🟢 📹 dock_cam: UP | 192.168.11.10 (0.281ms)
  🟢 📹 ptz_cam: UP | 192.168.11.68 (0.360ms)
  🟢 📹 ptz_ir_cam: UP | 192.168.11.69 (0.907ms)
  🟢 📹 bosch_cam: UP | 192.168.11.65 (0.225ms)
  🟢 📡 airy_front: UP | 10.7.5.152 (0.072ms)
  🟢 📡 airy_rear: UP | 10.7.5.153 (0.185ms)
  🟢 📡 e1r_left: UP | 10.7.5.103 (0.173ms)
  🟢 📡 e1r_right: UP | 10.7.5.104 (0.091ms)
  🟢 💻 va_pc: UP | 192.168.140.75 (0.348ms)
  🔴 💻 nav_pc: DOWN | 192.168.11.88 

  📊 统计: 10/11 设备在线, 1 设备离线

🟢 Vulcan CAN状态: 正常
================================================================================
```

## 🎛️ 命令参数

### 基础参数
- `--duration, -d <秒数>`: 运行时长（默认: 300秒 = 5分钟）
- `--interval, -i <秒数>`: 刷新间隔（1/2/5/10/30秒，默认: 2秒）
- `--stress-level, -s <级别>`: 压力测试强度（low/medium/high/extreme/auto，默认: medium）

### 高级参数
- `--output, -o <文件名>`: 温度数据输出文件名
- `--log-dir <目录>`: 日志文件目录
- `--no-stress`: 禁用后台压力测试
- `--no-network`: 禁用后台网络测试

## 🌐 网络设备列表

基于`network_test.sh`的完整11个设备：

### 相机设备（5个）
- `hazard_cam`: 192.168.11.9
- `dock_cam`: 192.168.11.10
- `ptz_cam`: 192.168.11.68
- `ptz_ir_cam`: 192.168.11.69
- `bosch_cam`: 192.168.11.65

### 雷达设备（4个）
- `airy_front`: 10.7.5.152
- `airy_rear`: 10.7.5.153
- `e1r_left`: 10.7.5.103
- `e1r_right`: 10.7.5.104

### PC设备（2个）
- `va_pc`: 192.168.140.75
- `nav_pc`: 192.168.11.88（额外添加）

## 🌡️ 温度监控

### CPU温度
- 使用`psutil`库读取系统CPU温度
- 支持多种温度传感器类型

### Vulcan CAN温度
- **CAN ID**: 0x510（基于can_temperature_reader.py）
- **数据格式**: int16_t温度值 × 10
- **硬件过滤**: 已启用，避免软件过滤开销
- **双传感器**: S1和S2，分别解析前4字节数据

## 📊 数据记录

### CSV格式
```csv
timestamp,datetime,cpu_temp,vulcan_s1_temp,vulcan_s2_temp
1736478393.309,2025-12-23 18:10:57,83.0,59.2,60.0
```

### 文件位置
- **温度数据**: `temperature_log_YYYYMMDD_HHMMSS.csv`
- **运行日志**: `logs/temperature_monitor_YYYYMMDD_HHMMSS.log`
- **结果汇总**: `monitor_results_YYYYMMDD_HHMMSS/`

## 🔧 压力测试强度

### 低强度
- **CPU**: 单线程，轻量级计算
- **内存**: 约4MB数据，简单访问
- **磁盘**: 小文件读写

### 中等强度（默认）
- **CPU**: 4线程，中等复杂度运算
- **内存**: 约20MB数据块，频繁访问
- **磁盘**: 160KB文件，多次读写

### 高强度
- **CPU**: 8线程，复杂数学运算+矩阵运算
- **内存**: 约800MB大数据块，高强度访问
- **磁盘**: 780KB文件，20次读写+复制验证

### 极限强度
- **CPU**: 16线程，极限复杂运算+大矩阵
- **内存**: 约2GB巨大数据块，复杂统计计算
- **磁盘**: 5MB大文件，多次读写追加修改

### 自动模式
根据硬件自动选择：
- CPU≥8核+内存≥16GB → 极限强度
- CPU≥4核+内存≥8GB → 高强度
- CPU≥2核+内存≥4GB → 中等强度
- 其他 → 低强度

## 📈 后续绘图

生成的CSV文件可直接用于绘图分析：

```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取数据
df = pd.read_csv('temperature_log_20251223_173652.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# 绘图
plt.figure(figsize=(12, 8))
plt.plot(df['datetime'], df['cpu_temp'], label='CPU温度', color='red')
plt.plot(df['datetime'], df['vulcan_s1_temp'], label='Vulcan S1', color='blue')
plt.plot(df['datetime'], df['vulcan_s2_temp'], label='Vulcan S2', color='green')
plt.xlabel('时间')
plt.ylabel('温度 (°C)')
plt.title('温度监控数据')
plt.legend()
plt.grid(True)
plt.show()
```

## 🛠️ 系统要求

### 必需模块
```bash
pip3 install psutil can
```

### 系统环境
- Python 3.6+
- Linux系统（支持CAN接口）
- sudo权限（可选，用于某些网络操作）

### CAN接口
- 需要CAN硬件支持
- 已配置CAN0接口
- 支持socketcan

## 🚨 故障排除

### 无显示输出
```bash
# 使用过滤查看仪表板
python3 temperature_monitor.py --duration 60 --interval 2 2>&1 | grep -v "INFO"

# 或者直接运行简化版本
python3 temperature_monitor.py --duration 60 --interval 2 --no-stress
```

### CAN温度显示为-999
- 检查CAN接口是否启用: `ip link show can0`
- 验证CAN总线连接: `candump can0`
- 确认设备发送CAN ID 0x510

### 网络设备全部离线
- 检查网络配置
- 验证IP地址可达性
- 检查防火墙设置

## 📞 技术支持

系统完全开源，基于以下标准实现：
- network_test.sh - 网络连通性测试标准
- can_temperature_reader.py - CAN温度读取标准
- psutil - 系统资源监控标准

任何问题都可以通过查看日志文件进行调试。