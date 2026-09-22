@echo off
REM 快速测试脚本 - 独立测试各个 Agent
REM 使用方法：双击运行此脚本，或在命令行中执行

echo ============================================================
echo ScenePilot Fast - 独立测试脚本
echo ============================================================
echo.

REM 检查测试数据
echo [1/5] 检查测试数据...
if not exist "data\img\img1.jpg" (
    echo [错误] 未找到测试图片: data\img\img1.jpg
    echo 请确保 data\img\ 目录下有图片文件
    pause
    exit /b 1
)

if not exist "data\video\test_video1.mp4" (
    echo [错误] 未找到测试视频: data\video\test_video1.mp4
    echo 请确保 data\video\ 目录下有视频文件
    pause
    exit /b 1
)

echo [OK] 测试数据准备完毕
echo.

REM 测试 SkillsManager
echo ============================================================
echo [2/5] 测试 SkillsManager Agent
echo ============================================================
python test_agents.py skills --mode bailian --text "我想拍自然的人像短片" --stage director
if errorlevel 1 (
    echo [错误] SkillsManager 测试失败
    pause
    exit /b 1
)
echo.

REM 测试 Director
echo ============================================================
echo [3/5] 测试 Director Agent
echo ============================================================
python test_agents.py director --mode bailian --text "请拍摄一组自然的人像短片" --image data\img\img1.jpg
if errorlevel 1 (
    echo [错误] Director 测试失败
    pause
    exit /b 1
)
echo.

REM 测试 Cinematographer
echo ============================================================
echo [4/5] 测试 Cinematographer Agent
echo ============================================================
python test_agents.py cinematographer --mode bailian --text "拍摄自然人像，注意构图和光线" --video data\video\test_video1.mp4
if errorlevel 1 (
    echo [错误] Cinematographer 测试失败
    pause
    exit /b 1
)
echo.

REM 测试 Editor
echo ============================================================
echo [5/5] 测试 Editor Agent
echo ============================================================
python test_agents.py editor --mode bailian --video data\video\test_video1.mp4 --image data\img\img1.jpg
if errorlevel 1 (
    echo [错误] Editor 测试失败
    pause
    exit /b 1
)
echo.

REM 测试完成
echo ============================================================
echo 所有测试完成！
echo ============================================================
echo.
echo 输出目录：
echo   - outputs\skills_manager\
echo   - outputs\director\
echo   - outputs\cinematographer\
echo   - outputs\editor\
echo.

REM 显示输出文件
echo 生成的文件：
if exist "outputs\skills_manager\skills_director.json" echo   [OK] outputs\skills_manager\skills_director.json
if exist "outputs\director\director.json" echo   [OK] outputs\director\director.json
if exist "outputs\cinematographer\filming.json" echo   [OK] outputs\cinematographer\filming.json
if exist "outputs\editor\edit_plan.json" echo   [OK] outputs\editor\edit_plan.json
if exist "outputs\editor\preview.mp4" echo   [OK] outputs\editor\preview.mp4
echo.

echo 按任意键打开输出目录...
pause > nul
explorer outputs

echo.
echo 测试脚本执行完毕
pause
