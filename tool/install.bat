SET PYTHON=%USERPROFILE%\Downloads\python-3.12.9-embed-amd64\python.exe
SET MPREMOTE=%USERPROFILE%\Downloads\python-3.12.9-embed-amd64\Scripts\mpremote.exe

%PYTHON% install-deps.py
%PYTHON% install-sinetstream.py
%MPREMOTE% df
