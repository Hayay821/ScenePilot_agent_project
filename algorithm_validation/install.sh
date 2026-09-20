#!/bin/bash
# 快速安装脚本 - 在 conda scenepilot 环境中运行

echo "=== ScenePilot 算法验证环境安装 ==="
echo ""

# 检查是否在 conda 环境中
if [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "❌ 错误: 请先激活 conda 环境"
    echo "运行: conda activate scenepilot"
    exit 1
fi

echo "✓ 当前 conda 环境: $CONDA_DEFAULT_ENV"
echo ""

# 安装核心依赖
echo "正在安装核心依赖..."
pip install --upgrade pip

pip install fastapi==0.104.0 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    opencv-python-headless==4.8.0.76 \
    av==11.0.0 \
    ffmpeg-python==0.2.0 \
    openai==1.6.0 \
    httpx==0.25.0 \
    tenacity==8.2.0 \
    diskcache==5.6.0 \
    ultralytics==8.0.0 \
    imagehash==4.3.0 \
    pillow==10.1.0 \
    numpy==1.24.0 \
    click==8.1.0 \
    rich==13.7.0 \
    loguru==0.7.0

echo ""
echo "正在安装开发工具..."
pip install pytest==7.4.0 \
    pytest-asyncio==0.21.0

echo ""
echo "✅ 安装完成!"
echo ""
echo "验证安装:"
python -c "
from app.core.schemas import FramePacket
print('✓ Schema 导入成功')
"
