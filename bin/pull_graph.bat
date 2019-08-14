:: Resources:
::https://stackoverflow.com/questions/28197540/best-way-to-script-remote-ssh-commands-in-batch-windows

::*path_to_putty/putty.exe -ssh *auth using key file* -m *path_to_pull_graph.txt*

:: pull_graph.txt ==
:: cd prod_env
::python3 HMI.py *args e.g. epic_ccy=GBPUSD timestep=3600 stdev=2 
:: scp -i 'path/to/graph/graph.pickle' '/local/path/graph.pickle'
:: exit

pause