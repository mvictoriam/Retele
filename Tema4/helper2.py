import struct
import requests
from bitstring import BitArray


def crc_check(input_bitstring, polynomial_bitstring, check_value):
    """
    Calculates the CRC check of a string of bits using a chosen polynomial.
    """
    # acest while rezolva o eroare in care schimbarea din int in string binar sterge 0 de la inceput
    while len(polynomial_bitstring) - 1 > len(check_value):
        check_value = '0' + check_value
    # elimin 0-urile din partea stanga deparece nu sunt necesare
    polynomial_bitstring = polynomial_bitstring.lstrip('0')
    # retin lungimea datelor binare
    len_input = len(input_bitstring)
    # initializez padding-ul
    initial_padding = check_value
    # creaza lista de biti pe care se fac calculele formate din bitii datelor si cel al padding-ului
    input_padded_array = list(input_bitstring + initial_padding)
    # while-ul functioneaza cat timp macar un bit din afara padding-ului e nenul
    while '1' in input_padded_array[:len_input]:
        # iau pozitia primului bit de 1 din lista de biti
        cur_shift = input_padded_array.index('1')
        # parcurg pe toate pozitiile bitilor care vor fi xorati
        for i in range(len(polynomial_bitstring)):
            # se face operatia de xor
            input_padded_array[cur_shift + i] = str(int(polynomial_bitstring[i] != input_padded_array[cur_shift + i]))
    # daca raspunsul este 0 adica toti bitii sunt nuli atunci raspunsul e True, altfel e False
    return '1' not in ''.join(input_padded_array)[len_input:]

if _name_ == '_main_':
    pol_seed = 666
    header = {'Content-Type': 'application/octet-stream'}
    data = struct.pack('!L', pol_seed) # primii 32 de biti sunt unsigned long restul sunt octetii care reprezinta mesajul
    data += b'Salutari de la helper!'
    url = 'http://ec2-34-239-255-229.compute-1.amazonaws.com:8001/crc' # link-ul catre serverul AWS
    response = requests.post(url, headers=header, data=data)
    print(response.content)
    crc = struct.unpack('!L', response.content[:4])[0] # raspunsul trebuie si el despachetat in funcie de cum a fost calculat
    print ('CRC calculat: ', crc)
    data = response.content[4:]
    bin_data = BitArray(data)
    if crc_check(bin_data.bin, "{0:b}".format(pol_seed), "{0:b}".format(crc)):
        print("Mesaj trimis cu succes! (:")
    else:
        print("Mesaj netrimis cu succes! :[")