@echo off
echo 正在打包为可执行文件...

:: 安装依赖
pip install -r requirements.txt

:: 清理旧文件
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist release rd /s /q release
if exist backup_system.spec del /q backup_system.spec

:: 创建发布目录结构
mkdir release
mkdir release\logs
mkdir release\config
mkdir release\static
mkdir release\templates

:: 打包程序
pyinstaller --noconfirm ^
            --clean ^
            --name backup_system ^
            --add-data "src/templates;templates" ^
            --add-data "src/static;static" ^
            --add-data "config;config" ^
            --hidden-import yaml ^
            --hidden-import flask ^
            --hidden-import paramiko ^
            --hidden-import schedule ^
            --hidden-import psutil ^
            main.py

:: 复制文件到发布目录
xcopy /E /I /Y dist\backup_system\* release\
xcopy /E /I /Y config\*.* release\config\
xcopy /E /I /Y src\templates\*.* release\templates\
xcopy /E /I /Y src\static\*.* release\static\

:: 确保目录存在并验证文件
dir release\templates\index.html
dir release\static
dir release\config\config.yaml

:: 如果验证失败则暂停
if errorlevel 1 (
    echo 文件复制验证失败！
    pause
    exit /b 1
)

:: 创建日志文件
type nul > release\logs\backup.log

:: 创建启动脚本
echo @echo off > release\start.bat
echo cd /d %%~dp0 >> release\start.bat
echo backup_system.exe >> release\start.bat
echo pause >> release\start.bat

:: 清理临时文件
rd /s /q build
rd /s /q dist
del /q backup_system.spec

echo 打包完成！
echo 可执行文件在 release 目录中
pause 