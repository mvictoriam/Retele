# receptor Reiable UDP
import random

from helper import *
from argparse import ArgumentParser
import socket
import logging

logging.basicConfig(format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level=logging.NOTSET)


def main():
    parser = ArgumentParser(usage=_file_ + ' '
                                             '-p/--port PORT'
                                             '-f/--fisier file_descriptor_PATH',
                            description='Reliable UDP Receptor')

    parser.add_argument('-p', '--port',
                        dest='port',
                        default=10000,
                        help='Portul pe care sa porneasca receptorul pentru a primi mesaje')

    parser.add_argument('-f', '--fisier',
                        dest='fisier',
                        help='Calea catre fisierul in care se vor scrie octetii primiti')

    # Parse arguments
    args = vars(parser.parse_args())
    port = int(args['port'])
    fisier = args['fisier']
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)

    adresa = '0.0.0.0'
    server_address = (adresa, port)
    sock.bind(server_address)
    logging.info("Serverul a pornit pe %s si portul %d", adresa, port)
    # acest dictionar este folosit pentru a retine mesajele primite anterior, iar dupa ce sunt scrise in fisier sunt
    # sterse din memorie
    processed_seq_nr = {}
    file_descriptor = None
    # LAS-ul este o variabila in care este retinut pana unde a fost citit fisierul curent (ultimul seq_nr/ack_nr)
    LAS = 0
    window = random.randint(1, 10)
    # started e folosit doar pentru a  nu inchide un fisier dupa ce a fost deja inchis
    started = False
    while True:
        logging.info('Asteptam mesaje...')
        data, address = sock.recvfrom(MAX_SEGMENT + 8)
        seq_nr, _, flags = parse_header_emitator(data[:8])
        # daca mesajul nu este corect este complet ignorat
        if not verifica_checksum(data):
            continue
        checksum = 0
        if flags == 'S':
            # initializarile specifice primei conexiuni
            started = True
            ack_nr = seq_nr + 1
            LAS = ack_nr
            file_descriptor = open(fisier, "wb")
        elif flags == 'P':
            ack_nr = seq_nr
            # pasii specifici fiecarui mesaj transmis in parte
            # daca mesajul a fost deja primit, este ignorat in cadrul procesarii
            if seq_nr not in processed_seq_nr:
                processed_seq_nr[seq_nr] = data[8:]
                window -= 1
                # sunt citite toate mesajele consecutive cu primul din fereastra, updatand window si golind memoria
                while LAS + len(data) - 8 == seq_nr:
                    file_descriptor.write(processed_seq_nr[seq_nr])
                    processed_seq_nr[seq_nr] = None
                    LAS = seq_nr
                    seq_nr = next_in_dict(processed_seq_nr, seq_nr)
                    window += 1
        elif flags == 'F':
            ack_nr = seq_nr + 1
        else:
            ack_nr = 0
        # este trimisa confirmarea primirii mesajului catre emitator
        mesaj = create_header_receptor(ack_nr, checksum, window)
        checksum = calculeaza_checksum(mesaj)
        mesaj = create_header_receptor(ack_nr, checksum, window)
        sock.sendto(mesaj, address)
        # daca primeste un mesaj de finalizare si inca nu a fost finalizat totul, fisierul este inchis si verificarea
        # fisierelor este facuta
        if flags == 'F' and started:
            started = False
            file_descriptor.close()
            if verificare_fisiere(fisier, "/elocal/tema3/src/layers.jpg"):
                print("Fisier copiat cu succes! ^.^")
            else:
                print("Fisier necopiat cu succes! :c")


if _name_ == '_main_':
    main()

# docker-compose exec receptor bash -c "python3 /elocal/tema3/src/receptor.py -p 10000 -f /elocal/tema3/src/layers_copy.jpg"