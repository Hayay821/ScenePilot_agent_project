@echo off
chcp 65001 >nul
REM 专家技能创作功能测试脚本 (Windows)

echo ============================================================
echo 🎓 SkillsManager - 专家技能创作功能测试
echo ============================================================
echo.

echo 测试 1: 人像拍摄技能提取
echo ------------------------------------------------------------
python test_agents.py skills-author --mode bailian --expert-input "拍摄人像时，我喜欢在黄金时刻拍摄，光线柔和，画面温暖。我会让模特面向光源，确保眼神有光。构图时会留出视线方向的空间，让画面更有呼吸感。"

echo.
echo ============================================================
echo 测试完成
echo ============================================================
echo.
echo 📁 查看输出：
echo    - 提取结果: outputs\skills_manager\
echo    - 待审核技能: skills\repository\pending_review\
echo    - 技能索引: skills\repository\skill_index.json
echo.

pause
