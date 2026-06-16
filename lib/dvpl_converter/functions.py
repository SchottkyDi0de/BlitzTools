from typing import Literal
from lz4.block import compress, decompress

def block_compress(
    data: bytes, 
    mode: Literal['default', 'fast', 'high_compression'] = 'default',
    acceleration: int = 1,
    store_size: bool = True, 
    return_bytearray: bool = False,
) -> bytes:
    """
    Compress data using LZ4-block compression.

    Args:
        data: The data to compress.
        mode: The compression mode to use.
        acceleration: The acceleration level to use.
        store_size: If True, store the size of the compressed data.
        return_bytearray: If True, return a bytearray instead of a bytes object.

    Returns:
        The compressed data.
    """
    return compress(data, mode=mode, acceleration=acceleration, store_size=store_size, return_bytearray=return_bytearray)

def block_decompress(
    data: bytes, 
    uncompressed_size: int, 
    return_bytearray: bool = False, 
) -> bytes:
    """
    Decompress LZ4-compressed data.

    Args:
        data: The data to decompress.
        uncompressed_size: The size of the uncompressed data.
        return_bytearray: If True, return a bytearray instead of a bytes object.

    Returns:
        The decompressed data.
    """
    return decompress(data, uncompressed_size=uncompressed_size, return_bytearray=return_bytearray)
