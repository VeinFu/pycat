#! /usr/bin/python
import binascii

def binary_to_ascii(binary_str):
    str=""
    if binary_str=="" or binary_str==None:
        raise ValueError("Error: Input binary string cannot be empty!")
    temp=binary_str.strip('\r')
    temp=binary_str.strip('\n')

    bins=temp.split(' ')
    for bin in bins:
        str=str+binascii.a2b_hex(bin)
    return str	
def binary_to_int(binary_str):
    if (binary_str=="" or binary_str==None):
        raise ValueError("Error: Input binary string cannot be empry!")
    if len(binary_str.split(' ')) > 2:
        raise ValueError("Error: Input binary string cannot be more than 1 byte!")
    if (len(binary_str)>2) and (binary_str[1]=='x' or binary_str[1]=='X'):
        lastchar=len(binary_str)	    
        binary_str=binary_str[2:lastchar]	  
    print binary_str	
    ret=int(binary_str,16)
    return ret
