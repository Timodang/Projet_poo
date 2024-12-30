# use PowerShell instead of sh:
set shell := ["powershell.exe", "-c"]
#set shell := ["cmd.exe", "/c"]

live_echo_test:
  watchexec -r -e echo -i "./temp/**" just echo_test

echo_test:
  cat ./temp/echo.echo

live_python_poo:
  watchexec -r -e py -i "./src/" just _python_poo

_python_poo:
  cd ./src/ ; \
  python ./main.py
