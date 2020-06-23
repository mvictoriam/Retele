# emitator Reliable UDP
import traceback
import random
from helper import *
from argparse import ArgumentParser
import socket
import logging

logging.basicConfig(format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level=logging.NOTSET)


def connect(sock, adresa_receptor):
    """
    Functie care initializeaza conexiunea cu receptorul.
    Returneaza ack_nr de la receptor si window
    """
    seq_nr = random.randint(0, MAX_UINT32)
    flags = 'S'
    checksum = 0
    mesaj = create_header_emitator(seq_nr, checksum, flags)
    checksum = calculeaza_checksum(mesaj)
    mesaj = create_header_emitator(seq_nr, checksum, flags)

    # pe parcursul codului vor mai exista astfel de initializari, ele nu au niciun rost real in cod, doar ajuta la
    # disparitia unor warning-uri
    did_connect = False
    data = None
    # in acest while se incearca crearea conectarii, in cazul in care nu primeste vreo confirmare, se reincearca
    # pana cand o primeste; se procedeaza similar si la finalizare
    while not did_connect:
        try:
            sock.sendto(mesaj, adresa_receptor)
            data, _ = sock.recvfrom(MAX_SEGMENT)
            did_connect = verifica_checksum(data)
        except socket.timeout:
            logging.info("Timeout la connect, retrying...")

    ack_nr, _, window = parse_header_receptor(data)

    logging.info('Ack Nr: "%d"', ack_nr)
    logging.info('Checksum: "%d"', checksum)
    logging.info('Window: "%d"', window)

    return ack_nr, window


def finalize(sock, adresa_receptor, seq_nr):
    """
    Functie care trimite mesajul de finalizare
    cu seq_nr dat ca parametru.
    """
    flags = 'F'
    checksum = 0
    mesaj = create_header_emitator(seq_nr, checksum, flags)
    checksum = calculeaza_checksum(mesaj)
    mesaj = create_header_emitator(seq_nr, checksum, flags)

    did_finalize = False
    data = None
    while not did_finalize:
        try:
            sock.sendto(mesaj, adresa_receptor)
            data, _ = sock.recvfrom(MAX_SEGMENT + 8)
            did_finalize = verifica_checksum(data)
        except socket.timeout:
            logging.info("Timeout la finalize, retrying...")

    ack_nr, _, window = parse_header_receptor(data)

    logging.info('Ack Nr: "%d"', ack_nr)
    logging.info('Checksum: "%d"', checksum)
    logging.info('Window: "%d"', window)

    return ack_nr, window


def send(sock, adresa_receptor, seq_nr, window, octeti_payload):
    # se retin mesajele din fereastra curenta intr-un dictionar pentru accesare si stergere usoara in functie de seq_nr
    mesaje = {}
    ack_nr = seq_nr
    while True:
        # sunt adaugate mesajele ce mai pot fi adaugate pentru a ajunge la numarul potrivit de spatii goale din receptor
        if len(mesaje) < window:
            for i in range(len(mesaje), window):
                segment = next(citeste_segment(octeti_payload))
                if len(segment) == 0:
                    break
                flags = 'P'
                checksum = 0
                seq_nr += len(segment)
                octeti_header_fara_checksum = create_header_emitator(seq_nr, checksum, flags)
                mesaj = octeti_header_fara_checksum + segment
                checksum = calculeaza_checksum(mesaj)
                octeti_header_cu_checksum = create_header_emitator(seq_nr, checksum, flags)
                mesaj = octeti_header_cu_checksum + segment
                mesaje[seq_nr] = mesaj
        # daca nu mai sunt meesaje de trimis inseamna ca tot fisierul s-a terminat
        if len(mesaje) == 0:
            return ack_nr, window
        # sunt trimise toate mesajele, se asteapta o confirmare pentru fiecare in parte, iar daca este primit este scos
        # mesajul specific din dictionar-ul emitatorului
        for msg_key in list(mesaje.keys()):
            try:
                mesaj = mesaje[msg_key]
                sock.sendto(mesaj, adresa_receptor)
                data, _ = sock.recvfrom(MAX_SEGMENT + 8)
                ack_nr, checksum, window = parse_header_receptor(data[:8])
                if verifica_checksum(data) and ack_nr in mesaje:
                    del mesaje[ack_nr]
                    logging.info('Ack Nr: "%d"', ack_nr)
                    logging.info('Checksum: "%d"', checksum)
                    logging.info('Window: "%d"', window)
            except socket.timeout:
                logging.info("Timeout la send, retrying...")


def main():
    parser = ArgumentParser(usage=_file_ + ' '
                                             '-a/--adresa IP '
                                             '-p/--port PORT'
                                             '-f/--fisier FILE_PATH',
                            description='Reliable UDP Emitter')

    parser.add_argument('-a', '--adresa',
                        dest='adresa',
                        default='receptor',
                        # default='198.8.0.2',
                        help='Adresa IP a receptorului (IP-ul containerului, localhost sau altceva)')

    parser.add_argument('-p', '--port',
                        dest='port',
                        default=10000,
                        help='Portul pe care asculta receptorul pentru mesaje')

    parser.add_argument('-f', '--fisier',
                        dest='fisier',
                        # default='layers.jpg',
                        help='Calea catre fisierul care urmeaza a fi trimis')

    # Parse arguments
    args = vars(parser.parse_args())
    ip_receptor = args['adresa']
    port_receptor = int(args['port'])
    fisier = args['fisier']
    adresa_receptor = (ip_receptor, port_receptor)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
    # setam timeout pe socket in cazul in care recvfrom nu primeste nimic in 0.05 secunde
    sock.settimeout(0.05)
    file_descriptor = None
    try:
        ack_nr, window = connect(sock, adresa_receptor)
        file_descriptor = open(fisier, 'rb')
        send(sock, adresa_receptor, ack_nr, window, file_descriptor)
        finalize(sock, adresa_receptor, ack_nr)
    except Exception:
        logging.exception(traceback.format_exc())
        sock.close()
        file_descriptor.close()


if _name_ == '_main_':
    main()

# docker-compose exec emitator bash -c "python3 /elocal/tema3/src/emitator.py -a 198.8.0.2 -p 10000 -f /elocal/tema3/src/layers.jpg"