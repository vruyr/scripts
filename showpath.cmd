@echo off

reg query "HKCU\Environment" /v PATH | C:\msys64\usr\bin\sed "s/_SZ[[:space:]]*/_SZ\n\t/; s/;/\n\t/g"
reg query "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH | C:\msys64\usr\bin\sed "s/_SZ[[:space:]]*/_SZ\n\t/; s/;/\n\t/g"
