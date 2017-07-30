@echo off
title HTTP scraping for Used Car Statistics

echo Executing 'runHttpScraping.py'
echo ------------------------------

echo changing Environment to Python 3.5
call activate ipykernel_py3
echo activated

echo Run Scraping script
python runHttpScraping.py

echo deactivate Environment
call deactivate
echo done
pause
