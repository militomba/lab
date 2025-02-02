import argparse
import socket
import pickle
import time
import ipaddress


def client():
    parser = argparse.ArgumentParser()
    #declaro los args para la conexion
    parser.add_argument("-i", "--ip", help="ip", type=str)
    parser.add_argument("-p", "--port", help="port", type=int)
    parser.add_argument("-u", "--tipoUsuario", help="tipoUsuario", type=str)

    args = parser.parse_args()
    ip = ipaddress.ip_network(args.ip)
    if ip.version ==6:
        client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:    
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    
    try:
        #creacion el socket

        client_socket.connect((args.ip, args.port))
        if args.tipoUsuario:
            user= args.tipoUsuario.lower()
            client_socket.sendall(user.encode())

        if user == "cliente":
            print(f"[INFO] Conexión establecida con el servidor PILATES UMA en {args.ip}:{args.port}")
            #string de datos de dias disponibles
            print("\n---!BIENVENIDO A NUESTRO SISTEMA DE RESERVA DE TURNOS!---\nESTAS SON NUESTRAS ACTIVIDADES:")
            validateActividad= True
            while validateActividad:
                print("\n1.SACAR TURNO\n2.CANCELAR TURNO\n3.SALIR DEL SISTEMA")
                opcion = int(input("\nSeleccione el indice de una de las actividades: "))
                client_socket.send(str(opcion).encode())
                if opcion == 1:
                    
                    print("\nUSTED HA ELEIGO LA ACTIVIDAD SACAR TURNO\n")
                    time.sleep(1)
                    validateOpcion1 = True
                    while validateOpcion1:
                        print("\nDIAS DE LA SEMANA DISPONIBLES:")
                        dias_disponibles = client_socket.recv(1024).decode()
                        listaDias= eval(dias_disponibles)
                        for index, dia in enumerate(listaDias):
                            print(str(index+1) + "-" + str(dia[1]))
                        validate = True

                        while validate:
                            try: 
                                selected_dias = int(input("Seleccione el indice del dia: "))-1
                                listaDias[(selected_dias)]
                                validate = False
                            except:
                                print("Indice incorrecto") 
                                
                        client_socket.send(str(selected_dias).encode())
                    
                    #string de horarios de dias disponibles
                        time.sleep(1)
                        print("\nHORARIOS DE LA SEMANA DISPONIBLES: ")
                        horarios_disponibles = client_socket.recv(1024).decode()
                        listaHorarios = eval(horarios_disponibles)
                        for index, hora in enumerate(listaHorarios):
                            print(str(index+1) + "-" + str(hora[1]))
                        validate = True

                        while validate:
                            try: 
                                selected_hora = int(input("Seleccione el indice del horario: "))-1
                                listaHorarios[(selected_hora)]
                                validate = False
                            except:
                                print("Indice incorrecto")

                        client_socket.send(str(selected_hora).encode())
                        

                        #veo disponibilidad
                        mensajeDisponibilidad = client_socket.recv(1024).decode()
                        if mensajeDisponibilidad.startswith("Si hay"):
                            # print(mensajeDisponibilidad)
                            validateOpcion1 = False
                        else:
                            print("---- "+mensajeDisponibilidad+" ----")
                    time.sleep(1)
                    #Pedimos datos personales para completar la reserva    
                    preguntaNombre = client_socket.recv(1024).decode()
                    respuestaNombre = input(preguntaNombre)
                    client_socket.send(str(respuestaNombre).encode())
                    time.sleep(1)
                    preguntaDni = client_socket.recv(1024).decode()
                    respuestaDni = input(preguntaDni)
                    dniSinPuntos = respuestaDni.replace('.', '')
                    client_socket.send(str(dniSinPuntos).encode())
                
                        
                    listaReserva = client_socket.recv(4096)
                    receivedList = pickle.loads((listaReserva))
                    
                    print("\nRESERVA CONFIRMADA: ")
                    for reserva in receivedList:
                        print("Nombre:", reserva['Nombre'])
                        print("DNI:", reserva['Dni'])
                        print("Día:", reserva['Dia'])
                        print("Horario:", reserva['Horario'])
                        print()  
                    validateActividad = False
                if opcion == 2:
                    
                    print("\nUSTED HA ELEIGO LA OPCION CANCELAR TURNO\n")
                    n = True
                    while n:
                    #1. pido y mando dni
                        time.sleep(1)
                        dni = str(input("Porfavor ingrese su dni para ver sus turnos: "))
                        dniSinPuntos = dni.replace('.', '')
                        client_socket.send(str(dniSinPuntos).encode())
                        #2. Recibo si existe o no el dni
                        existe = client_socket.recv(1024).decode()
                        # print("existe?: " + existe)
                        #2.1 existe dni?
                        if existe == "True": 
                            #3.1 recibo las reseervas del servidor
                            turno = client_socket.recv(1024).decode()
                            listaTurnos = eval(turno)
                            # print(listaTurnos)
                            time.sleep(1)
                            print("\n"+str(listaTurnos[0][4]).upper()+" ESTOS SON TUS TURNOS:")
                            for index, t in enumerate(listaTurnos):
                                    print(str(index+1) + "-" +"Dia: " +str(t[2])+ " -" +"Hora: " +str(t[1]))

                            validate = True
                            #El cliente elige el turno para eliminar
                            while validate:
                                try: 
                                    selected_turno = int(input("\nSeleccione el indice del turno que quiera eliminar: "))-1
                                    idReserva = listaTurnos[selected_turno][0]
                                    listaTurnos[(selected_turno)]
                                    validate = False
                                except:
                                    print("Indice incorrecto. Elija otro")
                            #4. cliente manda el indie de reserva
                            client_socket.send(str(idReserva).encode())
                            respuestaCancelacion = client_socket.recv(1024).decode()
                            print(respuestaCancelacion)
                            n=False

                        else: 
                            print("Dni invalido. Seleccione otro!")
                    validateActividad = False
    

                if opcion == 3:
                    # print("\nUsted va a salir del sistema! Que tenga buen dia!")
                    validateActividad = False
        elif user == "admin":
            validate = True
            while validate:
                print("\n1.AGREGAR HORARIO\n2.DAR DE BAJA UN HORARIO\n3.VER RESERVAS CLIENTES\n4.SALIR")
                opcion = int(input("Seleccione el indice correspondiente: "))
                client_socket.send(str(opcion).encode())
                if opcion == 1:
                    horarios = int(input("Cuantos horarios quiere agregar: "))
                    client_socket.send(str(horarios).encode())
                    for i in range(horarios):
                        validateHora = True
                        while validateHora:
                            horario=input(f"Ingrese horario {i+1} (formato: 14:00): ")
                            hora, minuto = map(int, horario.split(':'))
                            if hora < 0 or hora > 23 or minuto < 0 or minuto > 59:
                                validateHora=True
                            else:
                                validateHora = False    
                        client_socket.send(str(horario).encode())
                if opcion == 2:
                    print("HORARIOS DISPONIBLES: \n")
                    horarios = client_socket.recv(1024).decode()
                    listaHorarios = eval(horarios)
                    for index, hora in enumerate(listaHorarios):
                        print(str(index+1) + "-" + str(hora[1]))
                    validateHorario = True

                    while validateHorario:
                        try: 
                            selected_hora = int(input("Seleccione el indice del horario: "))-1
                            listaHorarios[(selected_hora)]
                            validateHorario = False
                        except:
                            print("Indice incorrecto")

                    client_socket.send(str(selected_hora).encode())
                if opcion == 3:
                    print("LISTA DE RESERVAS: \n")
                    reservas = client_socket.recv(1024).decode()
                    listaReservas = eval(reservas)
                    for index, res in enumerate(listaReservas):
                        print(str(index+1) + "-Horario: " + str(res[1]) +  " -Dia: " + str(res[2]) +" -Nombre: " + str(res[4]) + " -Dni: " + str(res[3]))

                if opcion == 4:
                    validate = False
            # else:
            #     print("Esa no es una opcion!, Elegir otra..")
    except ConnectionRefusedError:
        print("[ERROR] No se pudo conectar al servidor. Asegúrate de que el servidor esté en ejecución.")
    except BrokenPipeError:
        print("[ERROR] La conexión con el servidor se cerró inesperadamente.")
    finally:
        
        print("\nGracias por utilizar nuestro servicio de reservas!")
        time.sleep(1)
        client_socket.close()

if __name__ == "__main__":
    client()