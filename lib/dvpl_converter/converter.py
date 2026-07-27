from io import BytesIO
from pathlib import Path

from zlib import crc32
from typing import Optional, Union

from lib.dvpl_converter.classes import CompressionTypes, DVPLFooterStruct
from lib.dvpl_converter.functions import block_compress, block_decompress

class Converter:
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def pack_file(
            path_or_data: Union[Path, bytes],
            file_name: str,
            pack_path: Optional[Path] = None,
            keep_original: bool = True, 
            compression_type: CompressionTypes = CompressionTypes.NONE,
        ) -> Optional[bytes]:
        
        """
        Pack a file into a DVPL file.

        Args:
            path_or_data: The path to the file to pack or the bytes of the data to pack.
            pack_path: The path to pack the file to. If None, the packed data is returned directly.
            keep_original: If True, the original file is not deleted after packing.
            compression_type: The type of compression to use. Defaults to NONE.

        Returns:
            The packed data if pack_path is None, otherwise None.
        """

        if isinstance(path_or_data, Path):

            if path_or_data.suffix == '.dvpl':
                raise ValueError('Cannot pack a DVPL file')

            if not path_or_data.is_file():
                raise ValueError('Provide a valid path containing the file to pack')

            with open(path_or_data, 'rb') as file:
                data = file.read()
                size = path_or_data.stat().st_size

        elif isinstance(path_or_data, bytes):
            size = len(path_or_data)
            data = path_or_data

        else:
            raise ValueError('Provide a valid path containing the file to pack or bytes of the data to pack')

        if compression_type != CompressionTypes.NONE:
            compressed_data: bytes = block_compress(
                data, 
                mode='high_compression' if compression_type == CompressionTypes.LZ4_HC else 'default', 
                store_size=False
            )
        else:
            compressed_data = data

        footer = DVPLFooterStruct.generate_footer(
            size,
            len(compressed_data),
            crc32(compressed_data),
            compression_type.value
        )

        compressed_data += footer

        if pack_path is None:
            return compressed_data

        else:
            if not pack_path.exists():
                pack_path.mkdir(parents=True)

            with open(pack_path.joinpath(file_name), 'wb') as file:
                file.write(compressed_data)
                file.close()

            if not keep_original and isinstance(path_or_data, Path):
                path_or_data.unlink()

    @staticmethod
    def unpack_file(path_or_data: Union[Path, bytes], file_name: str, unpack_path: Optional[Path], keep_original: bool = True) -> Optional[bytes]:
        """
        Unpacks a DVPL file

        Args:
            path_or_data: The path to the file to unpack or the bytes of the data to unpack
            unpack_path: The path to unpack the file to. If None, the unpacked data is returned directly
            keep_original: If True, the original DVPL file is not deleted after unpacking

        Returns:
            The unpacked data if unpack_path is None, otherwise None
        """
        if isinstance(path_or_data, Path):
            if path_or_data.suffix != '.dvpl':
                raise ValueError('Cannot unpack a non-DVPL file')

            if not path_or_data.is_file():
                raise ValueError('Provide a valid path containing the file to unpack')

            with open(path_or_data, 'rb') as file:
                dvpl = DVPLFooterStruct(file)
                footer = dvpl.get_footer_data()
                data = dvpl.data


        elif isinstance(path_or_data, bytes):
            dvpl = DVPLFooterStruct(BytesIO(path_or_data))
            footer = dvpl.get_footer_data()
            data = dvpl.data

        else:
            raise ValueError('Provide a valid path containing the file to unpack or bytes of the data to unpack')

        if footer.compression_type is CompressionTypes.NONE:
            uncompressed_data = data[:-20]
        else:
            uncompressed_data = block_decompress(data[:-20], uncompressed_size=footer.input_file_size)

        if unpack_path is None:
            return uncompressed_data

        else:
            if not unpack_path.exists():
                unpack_path.mkdir(parents=True)
                
            with open(unpack_path.joinpath(file_name), 'wb') as file:
                file.write(uncompressed_data)

        if not keep_original and isinstance(path_or_data, Path):
            path_or_data.unlink()