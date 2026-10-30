# Crea la tarea de Windows "Monitor Massa - X": busca menciones en X cada 30 minutos (con la PC prendida).
# Uso:  powershell -ExecutionPolicy Bypass -File .\programar_x.ps1
$ErrorActionPreference = 'Stop'
$dir = $PSScriptRoot
$accion = New-ScheduledTaskAction -Execute "$dir\.venv\Scripts\pythonw.exe" -Argument "`"$dir\x_buscar.py`"" -WorkingDirectory $dir
$disparo = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(30) -RepetitionInterval (New-TimeSpan -Minutes 30)
$ajustes = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "Monitor Massa - X" -Action $accion -Trigger $disparo -Settings $ajustes -Force `
  -Description "Busca menciones a Massa en X cada 30 minutos y las sube al monitor" | Out-Null
$prox = (Get-ScheduledTask -TaskName "Monitor Massa - X" | Get-ScheduledTaskInfo).NextRunTime
Write-Host "Listo. Próxima búsqueda en X: $prox"
