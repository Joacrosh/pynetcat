# NetCat Tool in Python

## Descripcion General
Esta herramienta es una implementacion modular en Python de la utilidad clasica Netcat. Permite establecer conexiones TCP bidireccionales, actuar como servidor a la escucha de conexiones entrantes, ejecutar comandos del sistema operativo de forma remota y transferir archivos mediante la manipulacion directa de sockets e hilos de ejecucion concurrente.

## Caracteristicas Principales
- Modo Servidor y Modo Cliente unificados bajo una misma interfaz de comandos.
- Soporte para multiples conexiones concurrentes utilizando hilos (threading).
- Ejecucion segura de procesos del sistema operativo mediante el modulo subprocess y shlex.
- Capacidad de shell interactivo completo enviando comandos y recibiendo flujos de bytes.
- Transferencia y almacenamiento de archivos recibidos en bloques de red binarios.
- Reutilizacion de puertos mediante la opcion de socket SO_REUSEADDR.

## Requisitos del Sistema
- Python 3.8 o superior.
- Sistema operativo compatible con interfaces de red TCP/IP (Linux, macOS, Windows).

## Uso y Ejemplos

El script se ejecuta desde la linea de comandos utilizando argparse. Para ver el menu de ayuda completo:

    python netcat.py --help

Ejemplos de uso:

1. Activar un servidor interactivo de comandos:
    python netcat.py -t 0.0.0.0 -p 5555 -l -c

2. Activar un servidor para recibir un archivo:
    python netcat.py -t 0.0.0.0 -p 5555 -l -u archivo_destino.txt

3. Ejecutar un comando unico de forma remota al conectar:
    python netcat.py -t 192.168.1.108 -p 5555 -e "whoami"

4. Conectarse como cliente interactivo:
    python netcat.py -t 192.168.1.108 -p 5555
