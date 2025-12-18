@echo off
REM ===== yt-dlp URL extraction for all boiler keywords with headers =====
REM Make sure keywords.txt is in the same folder as this .bat

setlocal enabledelayedexpansion
mkdir urls_output

REM Clear previous output
echo. > urls_output\all_urls3.txt

for /f "usebackq tokens=*" %%k in ("keywords3.txt") do (
    set "line=%%k"

    REM If the line starts with #, it's a header
    echo !line! | findstr /b "#" >nul
    if !errorlevel! == 0 (
        echo. >> urls_output\all_urls3.txt
        echo !line! >> urls_output\all_urls3.txt
        echo. >> urls_output\all_urls3.txt
    ) else (
        REM Otherwise, it's a keyword line
        if not "!line!"=="" (
            echo Processing: !line!
            for /f "tokens=*" %%i in ('python -m yt_dlp "ytsearch10:!line!" --get-id --skip-download') do (
                echo https://www.youtube.com/watch?v=%%i >> urls_output\all_urls3.txt
            )
        )
    )
)

echo.
echo Done! All URLs saved in urls_output\all_urls3.txt
pause
