@echo off

echo HKCU\Environment
echo.
reg query "HKCU\Environment"                                                  | C:\msys64\usr\bin\grep -e "^[[:space:]]" | C:\msys64\usr\bin\sed "s/[[:space:]]*\(REG[a-zA-Z0-9_]*_SZ\)[[:space:]]*/||||\1||||/;" | C:\msys64\usr\bin\column.exe -t -o " " -c 3 -s "||||"
echo.
echo.

echo HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment
echo.
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" | C:\msys64\usr\bin\grep -e "^[[:space:]]" | C:\msys64\usr\bin\sed "s/[[:space:]]*\(REG[a-zA-Z0-9_]*_SZ\)[[:space:]]*/||||\1||||/;" | C:\msys64\usr\bin\column.exe -t -o " " -c 3 -s "||||"
echo.
echo.
