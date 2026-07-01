from dataclasses import dataclass
from io import BufferedIOBase, BytesIO
from enum import Enum
from pathlib import Path
from struct import pack
import lz4.block

from lib.io.utils import IO
from lib.dvpx.data_classes import FolderMeta


class CompressionTypes(Enum):
    NONE = 0
    LZ4 = 1
    LZ4_HC = 2
    RFC1951 = 3


@dataclass
class DVPMMeta:
    meta_mark: str
    '''
    ### magic string encoded in UTF-8 (met3 or met2)
    '''
    files_count: int
    '''
    ### number of files in the DVPD file
    '''
    dvpd_count: int
    '''
    ### number of DVPD files
    '''
    file_path_string_length: int
    '''
    ### length of file path string
    '''
    file_path_string: str
    '''
    ### null separated file path strings
    '''
    pack_string_raw_size: int
    '''
    ### file paths in bytes
    '''
    pack_string_compressed_size: int
    '''
    ### list of file paths
    '''


@dataclass
class DVPMFileTableItem:
    file_offset: int
    '''
    ### 16 bytes of file offset inside the DVPD data block
    '''
    compressed_size: int
    '''
    ### compressed file size in bytes
    '''
    raw_size: int
    '''
    ### uncompressed file size in bytes
    '''
    compressed_crc32: int
    '''
    ### CRC32 of compressed data
    '''
    compression_type: CompressionTypes
    '''
    ### Compression type, see CompressionTypes
    '''
    uncompressed_crc32: int
    '''
    ### CRC32 of uncompressed data
    '''
    meta_reference: int
    '''
    ### reference to meta section
    '''


@dataclass
class DVPMFileTable:
    files: list[DVPMFileTableItem]
    file_paths: list[str]


@dataclass
class DVPMFooter:
    meta_section_crc32: int
    '''
    ### CRC32 of meta section
    '''
    meta_section_size: int
    '''
    ### size of meta section in bytes
    '''
    files_count: int
    '''
    ### number of files in the DVPD file
    '''
    file_table_paths_compressed_size: int
    '''
    ### size of file table paths in bytes
    '''
    file_table_paths_raw_size: int
    '''
    ### size of file table paths in bytes
    '''
    file_table_size: int
    '''
    ### size of file table in bytes
    '''
    file_table_crc32: int
    '''
    ### CRC32 of file table
    '''
    footer_label: str
    '''
    ### magic string encoded in UTF-8
    '''


@dataclass
class DVPLFooter:
    input_file_size: int
    '''
    ### input file size (in bytes)
    '''
    compressed_block_size: int
    '''
    ### compressed block size (in bytes)
    '''
    compressed_block_crc32: int
    '''
    ### CRC32 of compressed block
    '''
    compression_type: CompressionTypes
    '''
    ### Compression type, see CompressionTypes
    '''
    footer_label: str
    '''
    ### magic string encoded in UTF-8
    '''


class Folder:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.glob_files = self.path.glob("**/*")
        
        dvpl_paths: list[Path] = []
        file_paths: list[Path] = []
        folder_paths: list[Path] = []
        
        for i in self.glob_files:
            file_path = Path(i)
            
            if not file_path.is_file():
                folder_paths.append(file_path)
                continue
            
            if file_path.suffix == ".dvpl":
                dvpl_paths.append(file_path)
            else:
                file_paths.append(file_path)
        
        self.dvpl_file_list = dvpl_paths
        self.file_list = file_paths
        self.folder_paths = folder_paths
        
        self.files_count = len(self.file_list)
        self.dvpl_count = len(self.dvpl_file_list)
        self.folders_count = len(self.folder_paths)
        
        self.folder_meta = FolderMeta(self.path, self.files_count, self.dvpl_count, self.folders_count)

class DVPMStruct:
    def __init__(self, file: BufferedIOBase) -> None:
        self.data = file.read()
        self.footer: DVPMFooter = self._get_footer_data()
        self.meta: DVPMMeta = self._get_meta_section_data(self.footer)
        self.file_table: DVPMFileTable = self._get_file_table_data(self.footer)
        file.close()

    def __str__(self) -> str:
        data = \
            f'DVPM Meta:\n'\
            f'-|  Meta mark: {self.meta.meta_mark}\n'\
            f'-|  Files count: {self.meta.files_count}\n'\
            f'-|  DVPD count: {self.meta.dvpd_count}\n'\
            f'-|  File path string length: {self.meta.file_path_string_length}\n'\
            f'-|  Pack string raw size: {self.meta.pack_string_raw_size}\n'\
            f'-|  Pack string compressed size: {self.meta.pack_string_compressed_size}\n'\
            f'-|  File path string: {self.meta.file_path_string}\n\n'\
            f'DVPM Footer:\n'\
            f'-|  Meta section crc32: {hex(self.footer.meta_section_crc32).replace("0x", "")}\n'\
            f'-|  Meta section size: {self.footer.meta_section_size} bytes\n'\
            f'-|  Files count: {self.footer.files_count}\n'\
            f'-|  File table paths compressed size: {self.footer.file_table_paths_compressed_size} bytes\n'\
            f'-|  File table paths raw size: {self.footer.file_table_paths_raw_size} bytes\n'\
            f'-|  File table size: {self.footer.file_table_size} bytes\n'\
            f'-|  File table crc32: {hex(self.footer.file_table_crc32).replace("0x", "")}\n'\
            f'-|  Footer label: {self.footer.footer_label}\n\n'\
            f'File Table:\n'\
        
        data += '-| '+ '\n-| '.join(self.file_table.file_paths)[:-4]
            
        return data
    
    def _get_footer_data(self) -> DVPMFooter:
        buffer = BytesIO(self.data[-44:])
        
        # skip unknown bytes
        IO.skip_bytes(buffer, 8)
        
        meta_crc32 = IO.int32(buffer, signed=False)
        meta_size = IO.int32(buffer, signed=False)
        
        # skip unknown bytes
        IO.skip_bytes(buffer, 4)
        
        files_count = IO.int32(buffer, signed=False)
        file_table_compressed_size = IO.int32(buffer, signed=False)
        file_table_uncompressed_size = IO.int32(buffer, signed=False)
        file_table_size = IO.int32(buffer, signed=False)
        file_table_crc32 = IO.int32(buffer, signed=False)
        
        footer_label = IO.string(buffer, 4)
        
        buffer.close()
        return DVPMFooter(
            meta_section_crc32=meta_crc32,
            meta_section_size=meta_size,
            files_count=files_count,
            file_table_paths_compressed_size=file_table_compressed_size,
            file_table_paths_raw_size=file_table_uncompressed_size,
            file_table_size=file_table_size,
            file_table_crc32=file_table_crc32,
            footer_label=footer_label
        )
        
    def _get_meta_section_data(self, footer_data: DVPMFooter) -> DVPMMeta:
        buffer = IO.buffer_from_bytes(self.data[:footer_data.meta_section_size])
        meta_label = IO.string(buffer, 4)
        
        if meta_label not in ['met2', 'met3']:
            raise ValueError(f'Unknown meta label: {meta_label}')
        
        files_count = IO.int32(buffer, signed=False)
        
        # skip unknown bytes
        IO.skip_bytes(buffer, 4 * (files_count * 2))
        
        dvpd_files_count = IO.int32(buffer, signed=False)

        # skip unknown bytes
        IO.skip_bytes(buffer, 16 * dvpd_files_count)
        
        file_path_string_length = IO.int32(buffer, signed=False)
        file_path_sting = IO.string(buffer, file_path_string_length).split('\x00')[0]
        
        pack_string_raw_size = IO.int32(buffer, signed=False)
        pack_string_compressed_size = IO.int32(buffer, signed=False)
        
        buffer.close()
        return DVPMMeta(
            meta_mark=meta_label,
            files_count=files_count,
            dvpd_count=dvpd_files_count,
            file_path_string_length=file_path_string_length,
            file_path_string=file_path_sting,
            pack_string_raw_size=pack_string_raw_size,
            pack_string_compressed_size=pack_string_compressed_size
        )
        
    def _encode_file_paths(self, buffer: BytesIO) -> list[str]:
        paths = buffer.read(self.footer.file_table_paths_compressed_size)
        if self.footer.file_table_paths_raw_size == self.footer.file_table_paths_compressed_size:
            return [path.decode('utf-8') for path in paths.split(b'\x00')]
        else:
            paths_data: bytes = lz4.block.decompress(paths, uncompressed_size=self.footer.file_table_paths_raw_size)
            return [path.decode('utf-8') for path in paths_data.split(b'\x00')]
        
    def _get_file_table_data(self, footer_data: DVPMFooter) -> DVPMFileTable:
        buffer = IO.buffer_from_bytes(
            self.data[
                footer_data.meta_section_size:
                footer_data.meta_section_size + footer_data.file_table_size
            ]
        )
        
        files: list[DVPMFileTableItem] = []
        
        for _ in range(footer_data.files_count):
            file_offset = IO.int64(buffer, signed=False)
            compressed_size = IO.int32(buffer, signed=False)
            raw_size = IO.int32(buffer, signed=False)
            compressed_crc32 = IO.int32(buffer, signed=False)
            compression_type = CompressionTypes(IO.int32(buffer, signed=False))
            uncompressed_crc32 = IO.int32(buffer, signed=False)
            meta_reference = IO.int32(buffer, signed=False)
            
            files.append(
                DVPMFileTableItem(
                    file_offset=file_offset,
                    compressed_size=compressed_size,
                    raw_size=raw_size,
                    compressed_crc32=compressed_crc32,
                    compression_type=compression_type,
                    uncompressed_crc32=uncompressed_crc32,
                    meta_reference=meta_reference
                )
            )
        
        file_paths = self._encode_file_paths(buffer)
        buffer.close()
        
        return DVPMFileTable(files=files, file_paths=file_paths)
    
class DVPLFooterStruct:
    def __init__(self, file: BufferedIOBase) -> None:
        self.data = file.read()
        footer = self.data[-20:]
        
        if len(footer) != 20:
            raise ValueError('Invalid last bytes length')
        
        self.last_bytes = footer
        self.footer_data = self._get_footer_metadata()
        file.close()
        '''
        ### 20 last bytes of DVPL file
        '''

    def __str__(self) -> str:
        data = \
            f'DVPL Footer metadata:\n'\
            f'-|  Input file size: {self.footer_data.input_file_size} bytes\n'\
            f'-|  Compressed block size: {self.footer_data.compressed_block_size} bytes\n'\
            f'-|  Compressed block crc32: {hex(self.footer_data.compressed_block_crc32).replace("0x", "")}\n'\
            f'-|  Compression type: {self.footer_data.compression_type.name}\n'\
            f'-|  Footer label: {self.footer_data.footer_label}\n'\
            f'-|  Compression: {round(abs((self.footer_data.compressed_block_size / self.footer_data.input_file_size * 100) - 100), 2)}%\n'
        
        return data

    def _get_footer_metadata(self) -> DVPLFooter:
        input_file_size = int.from_bytes(self.last_bytes[0:4], 'little')
        compressed_block_size = int.from_bytes(self.last_bytes[4:8], 'little')
        compressed_block_crc32 = int.from_bytes(self.last_bytes[8:12], 'little')
        compression_type = CompressionTypes(int.from_bytes(self.last_bytes[12:16], 'little'))
        file_descriptor = self.last_bytes[16:20].decode('utf-8')

        return DVPLFooter(
            input_file_size=input_file_size,
            compressed_block_size=compressed_block_size,
            compressed_block_crc32=compressed_block_crc32,
            compression_type=compression_type,
            footer_label=file_descriptor
        )
    
    @staticmethod
    def generate_footer(input_file_size: int, compressed_block_size: int, compressed_block_crc32: int, compression_type: int, footer_label: str = 'DVPL') -> bytes:
        """
        Generate the footer for a DVPL file.

        Args:
            input_file_size (int): The size of the input file in bytes.
            compressed_block_size (int): The size of the compressed block in bytes.
            compressed_block_crc32 (int): The CRC32 checksum of the compressed block.
            compression_type (CompressionTypes): The type of compression used.
            footer_label (str, optional): The label for the footer. Defaults to 'DVPL'.

        Returns:
            bytes: The generated footer as a byte array. 20 bytes long.
        """
        bytes = bytearray()
        bytes += pack('<I', input_file_size)
        bytes += pack('<I', compressed_block_size)
        bytes += pack('<I', compressed_block_crc32)
        bytes += pack('<I', compression_type)
        bytes += footer_label.encode('utf-8')
        
        return bytes
        
    def get_footer_data(self) -> DVPLFooter:
        return self.footer_data
