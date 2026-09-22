@echo off
chcp 65001 > nul
echo ============================================================
echo 测试所有 4 个 Agent
echo ============================================================
echo.

echo [1/4] 测试 SkillsManager...
python test_agents.py skills_manager --mode bailian --text "拍摄自然人像视频"
echo.

echo [2/4] 测试 Director...
python test_agents.py director --mode bailian --text "拍摄自然人像" --image data/img/img1.jpg
echo.

echo [3/4] 测试 Cinematographer...
python test_agents.py cinematographer --mode bailian --text "拍摄自然人像" --video data/video/test_video1.mp4
echo.

echo [4/4] 测试 Editor...
python test_agents.py editor --mode bailian --video data/video/test_video1.mp4
echo.

echo ============================================================
echo 测试完成！查看输出目录：
echo ============================================================
dir /b outputs
echo.
echo 按任意键打开输出目录...
pause > nul
explorer outputs
