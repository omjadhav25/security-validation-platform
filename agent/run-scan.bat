@echo off
REM Security Validation Platform - double-click launcher for Windows
REM Downloads nothing permanent, installs nothing. Just runs the agent
REM script in-memory via PowerShell, the same way "curl | bash" works on Linux.

powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://security-validation-platform.onrender.com/public/agent-windows.ps1 | iex"

pause