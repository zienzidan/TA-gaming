from plaso.parsers import interface
from plaso.parsers import manager
from plaso.containers import events
from dfdatetime import posix_time as dfdatetime_posix_time
import struct
import math
from enum import Enum

# CRC64 Table (sama dengan acuan)
crc64Table = [0x0,
    0x7AD870C830358979, 0xF5B0E190606B12F2, 0x8F689158505E9B8B,
    0xC038E5739841B68F, 0xBAE095BBA8743FF6, 0x358804E3F82AA47D,
    0x4F50742BC81F2D04, 0xAB28ECB46814FE75, 0xD1F09C7C5821770C,
    0x5E980D24087FEC87, 0x24407DEC384A65FE, 0x6B1009C7F05548FA,
    0x11C8790FC060C183, 0x9EA0E857903E5A08, 0xE478989FA00BD371,
    0x7D08FF3B88BE6F81, 0x7D08FF3B88BE6F8, 0x88B81EABE8D57D73,
    0xF2606E63D8E0F40A, 0xBD301A4810FFD90E, 0xC7E86A8020CA5077,
    0x4880FBD87094CBFC, 0x32588B1040A14285, 0xD620138FE0AA91F4,
    0xACF86347D09F188D, 0x2390F21F80C18306, 0x594882D7B0F40A7F,
    0x1618F6FC78EB277B, 0x6CC0863448DEAE02, 0xE3A8176C18803589,
    0x997067A428B5BCF0, 0xFA11FE77117CDF02, 0x80C98EBF2149567B,
    0xFA11FE77117CDF0, 0x75796F2F41224489, 0x3A291B04893D698D,
    0x40F16BCCB908E0F4, 0xCF99FA94E9567B7F, 0xB5418A5CD963F206,
    0x513912C379682177, 0x2BE1620B495DA80E, 0xA489F35319033385,
    0xDE51839B2936BAFC, 0x9101F7B0E12997F8, 0xEBD98778D11C1E81,
    0x64B116208142850A, 0x1E6966E8B1770C73, 0x8719014C99C2B083,
    0xFDC17184A9F739FA, 0x72A9E0DCF9A9A271, 0x8719014C99C2B08,
    0x4721E43F0183060C, 0x3DF994F731B68F75, 0xB29105AF61E814FE,
    0xC849756751DD9D87, 0x2C31EDF8F1D64EF6, 0x56E99D30C1E3C78F,
    0xD9810C6891BD5C04, 0xA3597CA0A188D57D, 0xEC09088B6997F879,
    0x96D1784359A27100, 0x19B9E91B09FCEA8B, 0x636199D339C963F2,
    0xDF7ADABD7A6E2D6F, 0xA5A2AA754A5BA416, 0x2ACA3B2D1A053F9D,
    0x50124BE52A30B6E4, 0x1F423FCEE22F9BE0, 0x659A4F06D21A1299,
    0xEAF2DE5E82448912, 0x902AAE96B271006B, 0x74523609127AD31A,
    0xE8A46C1224F5A63, 0x81E2D7997211C1E8, 0xFB3AA75142244891,
    0xB46AD37A8A3B6595, 0xCEB2A3B2BA0EECEC, 0x41DA32EAEA507767,
    0x3B024222DA65FE1E, 0xA2722586F2D042EE, 0xD8AA554EC2E5CB97,
    0x57C2C41692BB501C, 0x2D1AB4DEA28ED965, 0x624AC0F56A91F461,
    0x1892B03D5AA47D18, 0x97FA21650AFAE693, 0xED2251AD3ACF6FEA,
    0x95AC9329AC4BC9B, 0x7382B9FAAAF135E2, 0xFCEA28A2FAAFAE69,
    0x8632586ACA9A2710, 0xC9622C4102850A14, 0xB3BA5C8932B0836D,
    0x3CD2CDD162EE18E6, 0x460ABD1952DB919F, 0x256B24CA6B12F26D,
    0x5FB354025B277B14, 0xD0DBC55A0B79E09F, 0xAA03B5923B4C69E6,
    0xE553C1B9F35344E2, 0x9F8BB171C366CD9B, 0x10E3202993385610,
    0x6A3B50E1A30DDF69, 0x8E43C87E03060C18, 0xF49BB8B633338561,
    0x7BF329EE636D1EEA, 0x12B592653589793, 0x4E7B2D0D9B47BA97,
    0x34A35DC5AB7233EE, 0xBBCBCC9DFB2CA865, 0xC113BC55CB19211C,
    0x5863DBF1E3AC9DEC, 0x22BBAB39D3991495, 0xADD33A6183C78F1E,
    0xD70B4AA9B3F20667, 0x985B3E827BED2B63, 0xE2834E4A4BD8A21A,
    0x6DEBDF121B863991, 0x1733AFDA2BB3B0E8, 0xF34B37458BB86399,
    0x8993478DBB8DEAE0, 0x6FBD6D5EBD3716B, 0x7C23A61DDBE6F812,
    0x3373D23613F9D516, 0x49ABA2FE23CC5C6F, 0xC6C333A67392C7E4,
    0xBC1B436E43A74E9D, 0x95AC9329AC4BC9B5, 0xEF74E3E19C7E40CC,
    0x601C72B9CC20DB47, 0x1AC40271FC15523E, 0x5594765A340A7F3A,
    0x2F4C0692043FF643, 0xA02497CA54616DC8, 0xDAFCE7026454E4B1,
    0x3E847F9DC45F37C0, 0x445C0F55F46ABEB9, 0xCB349E0DA4342532,
    0xB1ECEEC59401AC4B, 0xFEBC9AEE5C1E814F, 0x8464EA266C2B0836,
    0xB0C7B7E3C7593BD, 0x71D40BB60C401AC4, 0xE8A46C1224F5A634,
    0x927C1CDA14C02F4D, 0x1D148D82449EB4C6, 0x67CCFD4A74AB3DBF,
    0x289C8961BCB410BB, 0x5244F9A98C8199C2, 0xDD2C68F1DCDF0249,
    0xA7F41839ECEA8B30, 0x438C80A64CE15841, 0x3954F06E7CD4D138,
    0xB63C61362C8A4AB3, 0xCCE411FE1CBFC3CA, 0x83B465D5D4A0EECE,
    0xF96C151DE49567B7, 0x76048445B4CBFC3C, 0xCDCF48D84FE7545,
    0x6FBD6D5EBD3716B7, 0x15651D968D029FCE, 0x9A0D8CCEDD5C0445,
    0xE0D5FC06ED698D3C, 0xAF85882D2576A038, 0xD55DF8E515432941,
    0x5A3569BD451DB2CA, 0x20ED197575283BB3, 0xC49581EAD523E8C2,
    0xBE4DF122E51661BB, 0x3125607AB548FA30, 0x4BFD10B2857D7349,
    0x4AD64994D625E4D, 0x7E7514517D57D734, 0xF11D85092D094CBF,
    0x8BC5F5C11D3CC5C6, 0x12B5926535897936, 0x686DE2AD05BCF04F,
    0xE70573F555E26BC4, 0x9DDD033D65D7E2BD, 0xD28D7716ADC8CFB9,
    0xA85507DE9DFD46C0, 0x273D9686CDA3DD4B, 0x5DE5E64EFD965432,
    0xB99D7ED15D9D8743, 0xC3450E196DA80E3A, 0x4C2D9F413DF695B1,
    0x36F5EF890DC31CC8, 0x79A59BA2C5DC31CC, 0x37DEB6AF5E9B8B5,
    0x8C157A32A5B7233E, 0xF6CD0AFA9582AA47, 0x4AD64994D625E4DA,
    0x300E395CE6106DA3, 0xBF66A804B64EF628, 0xC5BED8CC867B7F51,
    0x8AEEACE74E645255, 0xF036DC2F7E51DB2C, 0x7F5E4D772E0F40A7,
    0x5863DBF1E3AC9DE, 0xE1FEA520BE311AAF, 0x9B26D5E88E0493D6,
    0x144E44B0DE5A085D, 0x6E963478EE6F8124, 0x21C640532670AC20,
    0x5B1E309B16452559, 0xD476A1C3461BBED2, 0xAEAED10B762E37AB,
    0x37DEB6AF5E9B8B5B, 0x4D06C6676EAE0222, 0xC26E573F3EF099A9,
    0xB8B627F70EC510D0, 0xF7E653DCC6DA3DD4, 0x8D3E2314F6EFB4AD,
    0x256B24CA6B12F26, 0x788EC2849684A65F, 0x9CF65A1B368F752E,
    0xE62E2AD306BAFC57, 0x6946BB8B56E467DC, 0x139ECB4366D1EEA5,
    0x5CCEBF68AECEC3A1, 0x2616CFA09EFB4AD8, 0xA97E5EF8CEA5D153,
    0xD3A62E30FE90582A, 0xB0C7B7E3C7593BD8, 0xCA1FC72BF76CB2A1,
    0x45775673A732292A, 0x3FAF26BB9707A053, 0x70FF52905F188D57,
    0xA2722586F2D042E, 0x854FB3003F739FA5, 0xFF97C3C80F4616DC,
    0x1BEF5B57AF4DC5AD, 0x61372B9F9F784CD4, 0xEE5FBAC7CF26D75F,
    0x9487CA0FFF135E26, 0xDBD7BE24370C7322, 0xA10FCEEC0739FA5B,
    0x2E675FB4576761D0, 0x54BF2F7C6752E8A9, 0xCDCF48D84FE75459,
    0xB71738107FD2DD20, 0x387FA9482F8C46AB, 0x42A7D9801FB9CFD2,
    0xDF7ADABD7A6E2D6, 0x772FDD63E7936BAF, 0xF8474C3BB7CDF024,
    0x829F3CF387F8795D, 0x66E7A46C27F3AA2C, 0x1C3FD4A417C62355,
    0x935745FC4798B8DE, 0xE98F353477AD31A7, 0xA6DF411FBFB21CA3,
    0xDC0731D78F8795DA, 0x536FA08FDFD90E51, 0x29B7D047EFEC8728]

def crc64(seed, buffer):
    """Hitung CRC64 untuk data (diperlukan dalam proses unscramble)."""
    crc = seed
    for i in buffer:
        table_index = i ^ (crc & 0xFF)
        crc = crc64Table[table_index] ^ (crc >> 8)
    return crc

class RecordType(Enum):
    OSD = 0x01
    HOME = 0x02
    GIMBAL = 0x03
    RC = 0x04
    CUSTOM = 0x05
    DEFORM = 0x06
    CENTER_BATTERY = 0x07
    SMART_BATTERY = 0x08
    APP_TIP = 0x09
    APP_WARN = 0x0A
    RC_GPS = 0x0B
    RC_DEBUG = 0x0C
    RECOVER = 0x0D
    APP_GPS = 0x0E
    FIRMWARE = 0x0F
    OFDM_DEBUG = 0x10
    VISION_GROUP = 0x11
    VISION_WARN = 0x12
    MC_PARAM = 0x13
    APP_OPERATION = 0x14
    APP_SER_WARN = 0x18
    COMPONENT = 0x28
    JPEG = 0x39
    OTHER = 0xFE

def GetScrambleBytes(recordType, keyByte):
    """Menghasilkan 8 byte untuk XOR unscramble berdasarkan tipe record dan keyByte."""
    data_for_buffer = (0x123456789ABCDEF0 * keyByte) & 0xFFFFFFFFFFFFFFFF
    buffer_to_crc = struct.pack("<Q", data_for_buffer)
    # Menghasilkan scramble bytes dengan CRC64 seperti pada txt_parser.py
    return struct.pack("<Q", crc64((recordType + keyByte) & 0xFF, buffer_to_crc))

def ParseOSD(data):
    """
    Parsing record OSD: ekspektasi 24 byte dengan format "<ddhhhh".
    Mengembalikan list [longitude (derajat), latitude (derajat), height].
    """
    if len(data) < 24:
        return None
    longitude, latitude, height, xSpeed, ySpeed, zSpeed = struct.unpack("<ddhhhh", data[:24])
    # Konversi longitude & latitude dari radian ke derajat untuk sesuai format derajat
    # Height dibiarkan dalam satuan aslinya (kemungkinan decimeter, sesuai jurnal)
    longitude_deg = longitude * (180.0 / math.pi)
    latitude_deg = latitude * (180.0 / math.pi)
    return [longitude_deg, latitude_deg, height]

def ParseCustom(data):
    """
    Parsing record CUSTOM: ekspektasi 18 byte dengan format:
    Lewati 2 byte pertama, kemudian 4 byte h_speed, 4 byte distance, dan 8 byte update_time.
    Mengembalikan tuple (timestamp sebagai dfdatetime, h_speed, distance).
    """
    if len(data) < 18:
        return (None, None, None)
    # Skip 2-byte header inside CUSTOM data and unpack the rest
    h_speed, distance, update_time = struct.unpack("<ffQ", data[2:18])
    # Konversi timestamp (epoch dalam ms) ke dfdatetime dengan presisi milidetik
    #timestamp = dfdatetime_posix_time.PosixTime(timestamp=update_time / 1000.0)
    timestamp = dfdatetime_posix_time.PosixTimeInMilliseconds(timestamp=update_time)
    return (timestamp, h_speed, distance)

class DroneFlightEventData(events.EventData):
    DATA_TYPE = 'drone:flight:event'

    def __init__(self):
        """Inisialisasi event data untuk log penerbangan drone."""
        super(DroneFlightEventData, self).__init__(data_type=self.DATA_TYPE)
        self.timestamp = None   # dfdatetime objek waktu (YYYY-MM-DD HH:MM:SS.sss)
        self.longitude = None   # Longitude dalam derajat
        self.latitude = None    # Latitude dalam derajat
        self.height = None      # Ketinggian (height), satuan sesuai log (decimeter jika sesuai jurnal)
        self.distance = None    # Jarak (distance), satuan meter
        self.speed = None            # (horizontal speed)


class DroneBinaryParser(interface.FileObjectParser):
    NAME = 'drone_binary'
    DESCRIPTION = 'Parser untuk catatan penerbangan drone format biner (mengikuti logika txt_parser.py).'

    def ParseFileObject(self, parser_mediator, file_object):
        data = file_object.read()
        if len(data) < 11:
            parser_mediator.ProduceExtractionWarning("File terlalu kecil, tidak dapat diparsing.")
            return

        # Baca header file (11 byte pertama: records_area_end (QWord), details_area_size (HWord), file_version (Byte))
        records_area_end, details_area_size, file_version = struct.unpack("<QHB", data[:11])

        header_size = 100
        is_scrambled = True
        if file_version < 0x06:
            header_size = 12
            is_scrambled = False

        # Menentukan urutan area berdasarkan versi file
        if file_version >= 0x0C:
            # Urutan: header; area detail; area records
            records_area_start = header_size + details_area_size
        else:
            # Urutan: header; area records; area detail
            records_area_start = header_size

        # Ekstrak hanya bagian data record (sesuai penentuan di atas)
        record_data = data[records_area_start:records_area_end]
        offset = 0
        last_gps = None  # akan menyimpan [lon, lat, height] terakhir dari record OSD

        # Loop parsing semua record hingga selesai
        while offset < len(record_data):
            if offset + 2 > len(record_data):
                parser_mediator.ProduceExtractionWarning(
                    f"Data record tidak cukup pada offset {offset}")
                break

            record_type = record_data[offset]
            record_length = record_data[offset + 1]
            offset += 2  # maju melewati byte tipe dan panjang

            # Validasi apakah panjang record valid (cukup hingga akhir data record)
            if offset + record_length > len(record_data):
                parser_mediator.ProduceExtractionWarning(
                    f"Record tipe {record_type} dengan panjang {record_length} tidak valid pada offset {offset}")
                break

            # Tangani record JPEG (jika ditemukan, hentikan parsing karena sisanya adalah data gambar)
            if record_type == RecordType.JPEG.value or (record_type == 0xFF and record_length == 0xD8):
                parser_mediator.ProduceExtractionWarning(
                    f"Record JPEG tidak ditangani pada offset {offset}")
                break

            # Validasi end marker: seharusnya ada byte 0xFF setelah data record
            if offset + record_length < len(record_data) and record_data[offset + record_length] != 0xFF:
                # Jika byte setelahnya adalah 0xFF (misal dua 0xFF berturut), anggap tambahan 1 byte ke panjang
                if offset + record_length + 1 < len(record_data) and record_data[offset + record_length + 1] == 0xFF:
                    record_length += 1
                else:
                    parser_mediator.ProduceExtractionWarning(
                        f"End marker 0xFF tidak ditemukan untuk record tipe {record_type} pada offset {offset}")
                    break

            # Ambil data record sesuai panjang yang ditentukan (tanpa menyertakan end marker 0xFF)
            rec_data = record_data[offset: offset + record_length]

            # Jika data di-scramble (file_version >= 0x06), lakukan XOR unscramble mengikuti metode txt_parser.py
            if is_scrambled and len(rec_data) > 0:
                scramble_bytes = GetScrambleBytes(record_type, rec_data[0])
                if len(rec_data) >= 2:
                    raw_record_data = rec_data[1:]
                    # XOR setiap byte dengan scramble_bytes berulang tiap 8 byte
                    rec_data = bytes([b ^ scramble_bytes[i % 8] for i, b in enumerate(raw_record_data)])

            # Proses record berdasarkan tipe
            if record_type == RecordType.OSD.value:
                # Simpan data GPS terakhir (longitude, latitude, height) jika record OSD valid
                if len(rec_data) >= 24:
                    last_gps = ParseOSD(rec_data)
            elif record_type == RecordType.CUSTOM.value:
                # Record custom menyimpan timestamp, speed, distance
                if len(rec_data) >= 18:
                    timestamp, h_speed, distance = ParseCustom(rec_data)
                    # Jika GPS terakhir tersedia dan timestamp berhasil didapat
                    if last_gps is not None and timestamp is not None:
                        # Buat objek event data dan isi dengan nilai yang diekstraksi
                        event_data = DroneFlightEventData()
                        event_data.timestamp = timestamp            # format waktu dfdatetime (dengan milidetik)
                        event_data.longitude = last_gps[0]          # derajat
                        event_data.latitude = last_gps[1]           # derajat
                        event_data.height = last_gps[2]             # ketinggian (int, 0.1 m jika sesuai jurnal)
                        event_data.distance = distance              # jarak (float, meter)
                        event_data.speed = h_speed
                        # (Kecepatan h_speed tidak dimasukkan ke event_data karena output tabel hanya memerlukan jarak)
                        parser_mediator.ProduceEventData(event_data)
            # Maju ke record berikutnya (lewati data record yang diproses dan 1 byte end marker 0xFF)
            offset += (record_length + 1)

        # (Opsional) Tidak ada pengurangan jumlah record: loop berjalan sampai habis atau break jika ada masalah di atas.
        # Jika break terjadi sebelum semua data terbaca, peringatan sudah dikeluarkan melalui ProduceExtractionWarning.
        return

# Daftarkan parser ke manager
manager.ParsersManager.RegisterParser(DroneBinaryParser)