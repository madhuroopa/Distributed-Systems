import struct
import socket
import datetime
from array import array

def deserialize_price(data: bytes) -> float:
    """
    Deserializes a byte array into a floating-point number.

    Args:
        data (bytes): The byte array to be deserialized.

    Returns:
        float: The deserialized floating-point number.
    """
    deserialized_data = struct.unpack("f", data)  # Unpack bytes and convert to float
    return round(deserialized_data[0], 4)

def serialize_address(ip, port) -> bytes:
    """
    Serializes an IP address and port into a bytes object.

    Args:
        ip (str): The IP address.
        port (int): The port number.

    Returns:
        bytes: The serialized IP address and port.
    """
    ip_address = socket.gethostbyname(ip)  
    ip_packed = struct.pack("!I", struct.unpack("!I", socket.inet_aton(ip_address))[0])  # Packing IP address to bytes
    port_packed = struct.pack("!H", port)  # Packing port to bytes
    return ip_packed + port_packed

def deserialize_utcdatetime(bytes_data: bytes) -> datetime.datetime:
    """
    Deserializes a bytes object into a datetime.datetime object.

    Args:
        bytes_data (bytes): The bytes object to be deserialized.

    Returns:
        datetime.datetime: The deserialized datetime object.
    """
    
    array_q = array("Q")
    array_q.frombytes(bytes_data)
    array_q.byteswap()
    microseconds = array_q[0]
    epoch = datetime.datetime(1970, 1, 1)
    return epoch + datetime.timedelta(microseconds=microseconds)

def unmarshal_message(data: bytes) -> list:
    """
    Unmarshals a byte array of quote data into a list of dictionaries.

    Args:
        data (bytes): The byte array containing quote data.

    Returns:
        list: A list of dictionaries representing quotes with keys 'cross', 'price', and 'time'.
    """
    quotes_list = []
    quote_size = 32  # Expected size of quote structure in bytes

    for i in range(0, len(data), quote_size):
        each_quote = data[i : i + quote_size]

        currency_pair = each_quote[0:6].decode("ascii")
        price_bytes = each_quote[6:10]
        time_bytes = each_quote[10:18]

        price = deserialize_price(price_bytes)
        timestamp = deserialize_utcdatetime(time_bytes)
        formatted_currency_pair = f"{currency_pair[:3]}/{currency_pair[3:]}"

        quote_dict = {"cross": formatted_currency_pair, "price": price, "time": timestamp}
        quotes_list.append(quote_dict)

    return quotes_list
