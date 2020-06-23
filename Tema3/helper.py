import os
import struct

MAX_UINT32 = 0xFFFFFFFF
MAX_BITI_CHECKSUM = 16
MAX_SEGMENT = 4088


def compara_endianness(numar):
    """
    https://en.m.wikipedia.org/wiki/Endianness#Etymology
        numarul 16 se scrie in binar 10000 (2^4)
        pe 8 biti, adaugam 0 pe pozitiile mai mari: 00010000
        pe 16 biti, mai adauga un octet de 0 pe pozitiile mai mari: 00000000 00010000
        daca numaratoarea incepe de la dreapta la stanga:
            reprezentarea Big Endian (Network Order) este: 00000000 00010000
                - cel mai semnificativ bit are adresa cea mai mica
            reprezentarea Little Endian este: 00010000 00000000
                - cel mai semnificativ bit are adresa cea mai mare
    """
    print("Numarul: ", numar)
    print("Network Order (Big Endian): ", [bin(byte) for byte in struct.pack('!H', numar)])
    print("Little Endian: ", [bin(byte) for byte in struct.pack('<H', numar)])


def create_header_emitator(seq_nr, checksum, flags='S'):
    if flags == 'S':
        flags = 0b100
    elif flags == 'F':
        flags = 0b001
    elif flags == 'P':
        flags = 0b010
    flags <<= 13
    octeti = struct.pack('!LHH', seq_nr, checksum, flags)
    return octeti


def parse_header_emitator(octeti):
    seq_nr, checksum, spf = struct.unpack('!LHH', octeti)
    flags = ''
    spf >>= 13
    if spf & 0b100:
        # inseamna ca am primit S
        flags = 'S'
    elif spf & 0b001:
        # inseamna ca am primit F
        flags = 'F'
    elif spf & 0b010:
        # inseamna ca am primit P
        flags = 'P'
    return seq_nr, checksum, flags


def create_header_receptor(ack_nr, checksum, window):
    octeti = struct.pack('!LHH', ack_nr, checksum, window)
    return octeti


def parse_header_receptor(octeti):
    ack_nr, checksum, window = struct.unpack('!LHH', octeti)
    return ack_nr, checksum, window


def citeste_segment(file_descriptor):
    yield file_descriptor.read(MAX_SEGMENT)


def calculeaza_checksum(octeti):
    header = octeti[:8]
    _, checksum, _ = parse_header_emitator(header)
    if len(octeti) % 2 == 1:
        octeti += b'\x00'
    for i in range(0, len(octeti), 2):
        two_bytes = octeti[i] * 256 + octeti[i + 1]
        checksum = (checksum + two_bytes) % 65536
    checksum = ~(-checksum)
    return checksum


def verifica_checksum(octeti):
    header = octeti[:8]
    ack_nr, checksum, window = parse_header_receptor(header)
    if calculeaza_checksum(create_header_receptor(ack_nr, 0, window) + octeti[8:]) == checksum:
        return True
    return False


# aceasta functie obtine urmatoarea cheie dintr-un dictionat, primind o cheie reper (se presupune ca cheile pot fi
# comparate, probabil int-uri)
def next_in_dict(dict, key):
    lista = sorted(dict.keys())
    for i in range(len(lista)):
        if lista[i] == key:
            if i == len(lista) - 1:
                return lista[0]
            else:
                return lista[i + 1]
    return None


# aceasta functie verifica daca doua fisiere sunt compelt identitce
def verificare_fisiere(fisier1, fisier2):
    if os.path.getsize(fisier1) != os.path.getsize(fisier2):
        return False
    f = open(fisier1, "rb")
    g = open(fisier2, "rb")
    segment1 = f.read(1000)
    segment2 = g.read(1000)
    while len(segment1) != 0:
        if segment1 != segment2:
            return False
        segment1 = f.read(1000)
        segment2 = g.read(1000)
    return True


if _name_ == '_main_':
    compara_endianness(16)