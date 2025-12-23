#!/bin/bash
# 高级温度监控系统启动脚本
# 一键启动完整的温度监控解决方案

echo "🚀 启动高级温度监控系统..."
echo "=" * 60

# 默认参数
DURATION=14400  # 4小时
INTERVAL=2      # 2秒刷新
STRESS_LEVEL="medium"  # 中等强度压力测试

# 检查参数
if [ $# -eq 0 ]; then
    echo "使用默认参数: 运行4小时，每2秒刷新，中等强度压力测试"
    echo "如需自定义参数，请使用: $0 --duration 3600 --interval 2 --stress-level high"
else
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
            --help|-h)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --duration, -d <秒数>      运行时长（默认: 14400 = 4小时）"
                echo "  --interval, -i <秒数>      刷新间隔（默认: 2秒）"
                echo "  --stress-level, -s <级别>  压力测试强度（low/medium/high/extreme/auto，默认: medium）"
                echo "  --help, -h                 显示帮助信息"
                exit 0
                ;;
            *)
                echo "未知参数: $1"
                echo "使用 --help 查看帮助信息"
                exit 1
                ;;
        esac
    done
fi

echo "📊 运行参数:"
echo "  运行时长: $DURATION 秒 ($(($DURATION / 3600)) 小时 $(($DURATION % 3600 / 60)) 分钟)"
echo "  刷新间隔: $INTERVAL 秒"
echo "  压力强度: $STRESS_LEVEL"
echo ""

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"

# 检查依赖模块
echo "🔍 检查依赖模块..."
required_modules=("psutil" "can")
missing_modules=()

for module in "${required_modules[@]}"; do
    if ! python3 -c "import $module" 2>/dev/null; then
        missing_modules+=("$module")
    fi
done

if [ ${#missing_modules[@]} -ne 0 ]; then
    echo "❌ 缺少依赖模块: ${missing_modules[*]}"
    echo "请安装缺失的模块:"
    for module in "${missing_modules[@]}"; do
        echo "  pip3 install $module"
    done
    exit 1
fi

echo "✅ 所有依赖模块已安装"

# 检查系统权限
echo "🔍 检查系统权限..."
if ! groups | grep -qE '(sudo|wheel)'; then
    echo "⚠️  警告: 当前用户没有sudo权限，可能影响某些功能"
fi

# 检查CAN接口
echo "🔍 检查CAN接口..."
if ip link show | grep -q can; then
    echo "✅ 发现CAN接口"
else
    echo "⚠️  警告: 未检测到CAN接口，CAN温度功能将不可用"
fi

# 创建日志目录
mkdir -p logs

echo ""
echo "🚀 开始温度监控..."
echo "=" * 60
echo "💡 提示:"
echo "  - 按 Ctrl+C 可中断监控"
echo "  - 日志文件将保存在: logs/"
echo "  - 温度数据将保存在: temperature_log_*.csv"
echo "  - 网络连通性基于network_test.sh的11个设备"
echo "  - CAN温度读取基于can_temperature_reader.py"
echo ""

# 启动监控
echo "🌡️  启动温度监控系统..."
python3 temperature_monitor.py \
    --duration "$DURATION" \
    --interval "$INTERVAL" \
    --stress-level "$STRESS_LEVEL" \
    --log-dir "logs"

echo ""
echo "✅ 温度监控系统已停止"
echo "📁 请查看生成的日志文件和数据文件"