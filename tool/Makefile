WINUSER=$(USER)
python=/mnt/c/Users/$(WINUSER)/Downloads/python-3.12.9-embed-amd64/python.exe
mpremote=/mnt/c/Users/$(WINUSER)/Downloads/python-3.12.9-embed-amd64/Scripts/mpremote.exe
peco=peco #like fzf

# ボードのmicropythonインタプリタと対話する
sh::
	$(mpremote) repl

# ボードのファイル使用量をみる
df::
	$(mpremote) df

# ボードのファイル一覧をみる
ls::
	#$(mpremote) fs ls
	$(mpremote) run tree.py exec 'lsR(".")'

# ボードからsinetstream-upythonを消す
rm::
	$(mpremote) run tree.py exec 'rmR("/lib/sinetstream")'
	$(mpremote) run tree.py exec 'rmR("/lib/uavro")'
	$(mpremote) run tree.py exec 'rmR("/lib/sinetstreamplugin")'
	#$(mpremote) fs --recursive rm /lib/sinetstream
	#$(mpremote) fs --recursive rm /lib/uavro
	#$(mpremote) fs --recursive rm /lib/sinetstreamplugin

# ボードの時刻を設定する
rtc time::
	$(mpremote) rtc
	$(mpremote) rtc --set
	$(mpremote) rtc

# ボード上のファイルを編集する
vi:
	#EDITOR=vi $(mpremote) edit `$(mpremote) run tree.py exec 'lsR(".")' | cut -d' ' -f1 | $(peco)`
	./edit.sh $(mpremote) `$(mpremote) run tree.py exec 'lsR(".")' | cut -d' ' -f1 | $(peco)`
# ボード上にファイルを作成する
newvi:
	read -p 'new filename: ' X && ./newfile.sh $(mpremote) $$X

# WindowsのPythonからこのディレクトリがどんなパスでみえるか確認する
cwd::
	$(python) -c 'import os; print(os.path.realpath("."))'

# WindowsのPythonインタプリタと対話する
py::
	$(python)

# ボード上でテストを実行する
test::
	for X in ../test/test_*.py; do $(mpremote) run $$X; done
