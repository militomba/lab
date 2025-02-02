import argparse
import socket
import threading
from postgres import *
from celeryApp import *
import socketserver
import time
import pickle
import ipaddress


def handleClient(client_socket):
    #le doy una conexion a cada cliente para que no se interfiera con otra conexion
        #le doy una conexion a cada cliente para que no se interfiera con otra conexion
    conexDB = conexionDB()
    client_address = client_socket.getpeername()
    tipoUsuario = client_socket.recv(1024).decode().strip()
    if tipoUsuario == "cliente":
        validateActividad = True
        while validateActividad:
            opcion = client_socket.recv(1024).decode().strip()
            selectedOpcion = int(opcion)
            #opcion: SACAR TURNO
            if selectedOpcion == 1:
                reserva=[]
                #traigo los dias de la semana
                validateOpcion1 = True
                while validateOpcion1:
                    dias = getDias(conexDB)
                    client_socket.send(str(dias).encode())
                    dataDia = client_socket.recv(1024).decode().strip()
                    selected_dia = dias[int(dataDia)]
                    indiceDia_db = selected_dia[0]
                    print("Dia elegido:\n","-Id Dia: "+str(indiceDia_db), "\n-Dia Semana: " + str(selected_dia[1]))
                
                #traigo horarios
                
                    horario = getHorarios(conexDB)
                    client_socket.send(str(horario).encode())
                    dataHorario= client_socket.recv(1024).decode().strip()
                    selected_hora = horario[int(dataHorario)]
                    indiceHorario_db = selected_hora[0]
                    print("Horario elegido:\n", "-Id Hora: "+str(indiceHorario_db), "\n-Horario " + str(selected_hora[1]))
                
                #veo disponibilidad en ese dia y horario

                    disp = getDisponibilidad(conexDB, indiceDia_db, indiceHorario_db)
                    # client_socket.send(str(disp).encode())
                    lugares = int(disp[0])
                    
                    if lugares < 15:
                        nuevo_valor = addCantidad(conexDB,indiceDia_db, indiceHorario_db)
                        message = f"Si hay lugares disponibles\n"
                        client_socket.sendall(message.encode())
                        time.sleep(1)
                        #client_socket.send(b"\nAhora le pediremos algunos datos personales para terminar con la reserva\n")
                        nombre, dni = agregarReserva(client_socket, indiceHorario_db, indiceDia_db)
                        reserva.append({"Nombre":nombre, "Dni": dni, "Dia":selected_dia[1], "Horario":selected_hora[1]})
                        validateOpcion1 = False
                        
                    else:  
                        client_socket.sendall(b"No hay lugares disponibles, elija otro!\n")  
                if reserva:
                    #uso pickle para serializar mi lista
                    serializedReserva = pickle.dumps(reserva)
                    client_socket.sendall(serializedReserva)
                client_socket.close()
                validateActividad=False

            #opcion: CANCELAR TURNO
            if selectedOpcion == 2:
                validate = True
                while validate:
                    #1. recibo dni del servidor
                    dniCliente = client_socket.recv(1024).decode().strip()
                    #2. me fijo que exista el dni
                    existeDni = dniExiste(conexDB, dniCliente)
                    client_socket.send(str(existeDni).encode())
                    #2.1 existe dni?
                    if existeDni == True:
                        #3. llamo funcion para obtener reservas del cliente
                        turno = getReservasDni(conexDB, dniCliente)
                        
                        #3.1 mando las reservas al cliente
                        client_socket.send(str(turno).encode())
                    
                        #4. cliente manda el id de la reserva para eliminar
                        dataTurno = client_socket.recv(1024).decode().strip()
                        print("Id reserva ha eliminar "+ dataTurno)
                        cancelarReserva(client_socket, dataTurno)
                        client_socket.send(b"Turno cancelado!")
                        print("Turno eliminado correctamente")
                        eliminarCantidad(conexDB, dataTurno)
                        validate = False
                    # else:
                    #     print("dni no existe")
                validateActividad=False  
                    #cancelarReserva(client_socket)
            if selectedOpcion == 3: 
                print(f"\nCLIENTE {client_socket.getpeername()[1]} SALIENDO DEL SISTEMA!!!")
                validateActividad=False

    else:
        validate= True
        while validate:
            #recibo la actividad
            act=client_socket.recv(1024).decode().strip()
            #actividad 1.Agregar horario
            if act == "1":
                cantHorarios = client_socket.recv(1024).decode().strip()
                print(cantHorarios)
                for i in range(int(cantHorarios)):
                    horaRecibida = client_socket.recv(1024).decode().strip()
                    addHorario(conexDB, horaRecibida)
                    print("Horario: "+ horaRecibida)
                    addHoraInCantidad(conexDB, horaRecibida)
            if act == "2":
                getHorario = getHorarios(conexDB)
                client_socket.send(str(getHorario).encode())
                dataHorario= client_socket.recv(1024).decode().strip()
                selected_hora = getHorario[int(dataHorario)]
                indiceHorario_db = selected_hora[0]
                print("Horario elegido:\n", "-Id Hora: "+str(indiceHorario_db), "\n-Horario " + str(selected_hora[1]))
                deleteHoraInCantidad(conexDB, indiceHorario_db)
            if act == "3":
                reservas = getReservas(conexDB)
                client_socket.send(str(reservas).encode())
                print(reservas)

            if act =="4":
                print(f"\nCLIENTE {client_socket.getpeername()[1]} SALIENDO DEL SISTEMA!!!")
                validate=False

            
                
        
def agregarReserva(client_socket, idHora, idDia):
    client_socket.sendall(b"Ingrese su nombre: ")
    nombreCliente = client_socket.recv(1024).decode().strip()
    print("Nombre del cliente: "+ nombreCliente)
    client_socket.sendall(b"Ingrese su dni: ")
    dniCliente = client_socket.recv(1024).decode().strip()
    print("Dni del cliente: " + dniCliente)
    nuevaReserva.delay(idHora, idDia, dniCliente, nombreCliente)
    return nombreCliente, dniCliente

def cancelarReserva(client_socket, id_reserva):
    cancelarTurno.delay(id_reserva)

    
def start_server(host, port):
    ip = ipaddress.ip_network(host)
    if ip.version ==6:
        server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        server.bind((host, port))
        
    else:    
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        
        
    #vincula el host con el puerto
    
    server.listen(5)
    print(f"[INFO] Servidor escuchando en {host}:{port}...")

    while True:
        client_socket, _ = server.accept()
        print(f"[INFO] Conexión establecida desde {client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}")
        client_handler = threading.Thread(target=handleClient, args=(client_socket,))
        client_handler.start()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #declaro los args para la conexion
    parser.add_argument("-i", "--ip", help="ip", type=str)
    parser.add_argument("-p", "--port", help="port", type=int)
    args = parser.parse_args()
    conexDB = conexionDB()
    # if conexDB:
    #     crear_tablas(conexDB)
    #     conexDB.close()
    start_server(args.ip, args.port)

   


