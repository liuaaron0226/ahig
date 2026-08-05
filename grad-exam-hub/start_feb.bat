@echo off
chcp 65001 >nul
title Feb - 本機伺服器（關掉這個視窗網站就停）
cd /d "%~dp0"
echo ============================================
echo  Feb 已啟動： http://localhost:8642/site/
echo  瀏覽器會自動打開；要停止就關掉這個視窗
echo ============================================
start "" "http://localhost:8642/site/"
python -m http.server 8642
