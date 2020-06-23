import struct
from flask import Flask
from flask import request
from bitstring import BitArray
app = Flask(_name_)


@app.route('/')
def hello():
    '''
    Scrieti aici numele voastre
    '''
    return "CRC API de la echipa PS!"


def calculeaza_CRC(input_bitstring, polynomial_bitstring, initial_filler):
    '''
    Calculates the CRC remainder of a string of bits using a chosen polynomial.
    initial_filler should be '1' or '0'.
    '''
    #stochez toate zero urile in string binar
    polynomial_bitstring = polynomial_bitstring.lstrip('0')
    #lungimea datelor din int in binar
    len_input = len(input_bitstring)
    #inializez padding-ul cu 0 pana ajung la numarul lungimii polinomului -1
    initial_padding = initial_filler * (len(polynomial_bitstring) - 1)
    #fac lista unde adun biti strinf ului cu 0 urile din padding
    input_padded_array = list(input_bitstring + initial_padding)
    #cat timp macar dinafara padding ului nu e null
    while '1' in input_padded_array[:len_input]:
        #stochez prima pozitie a bitului
        cur_shift = input_padded_array.index('1')
        #iau fiecare pozitie  bitilor 
        for i in range(len(polynomial_bitstring)):
            #operatia de xotare a bitilor
            input_padded_array[cur_shift + i] = str(int(polynomial_bitstring[i] != input_padded_array[cur_shift + i]))
    #returnez crc ul 
    return ''.join(input_padded_array)[len_input:]


@app.route('/crc', methods=['POST'])
def post_method():
    '''
    print("Got from user: ", request.get_json())
    print(request.get_json()['value']*2)
    return jsonify({'got_it': 'yes'})
    simple flask function
    TODO: implementati aici un endpoint care calculeaza CRC
    '''
    #struct.unpack(....)
    #CRC = calculeaza_CRC()
    data = request.data
    polinom = struct.unpack('!L', data[:4])[0]
    only_data = data[4:]
    bin_data = BitArray(only_data)
    crc = calculeaza_CRC(bin_data.bin, "{0:b}".format(polinom), '0')
    crc = int(crc, 2)
    print ('CRC calculat: ', crc)
    data = struct.pack('!L', crc)
    data += only_data
    return request.data
    #return CRC


if _name_ == '_main_':
    app.run(host='0.0.0.0', port=8001)