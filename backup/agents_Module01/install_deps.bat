@echo off
REM Install dependencies in current conda environment
echo Installing dependencies for agents_Module...
pip install pydantic==2.13.5 PyYAML==6.0.1 dashscope==1.24.1
echo.
echo Installation complete!
echo.
echo Now you can run:
echo   python -m agents_Module list
echo   python -m agents_Module run "your request" --mock
echo   python examples/real_skills_demo.py
pause
