
'''
Write Information to OTP area
'''
import sys
import argparse
import binascii
import serial
import struct
import json
import zlib
import base64
import time
import array
import os
import binascii
import crcmod
import zlib

from sys import platform as _platform
'''
OTP partitions:
#1 Manufacturer Information(String)
#2 Machine Information(String)
#3 Manufacturing Information(String)
#3 Date of Testing(String)
#4 Time of Testing(String)
#5 Factory Accel Offsets and Scale Factors(6 Floats packed)
'''
'''
COMMAND EXAMPLES:
Manufacturer Info:      python otp_program.py --port /dev/ttyxxx
Machine Information:    python otp_program.py --port /dev/ttyxxx --info-seg 2 --info "Sid's MAC"
Manufacturing Info:     python otp_program.py --port /dev/ttyxxx --info-seg 3 --info "PH11A5500887"
Date of Testing:        python otp_program.py --port /dev/ttyxxx --info-seg 4 --info "Wed 9 Sep 2015"
Time of Testing:        python otp_program.py --port /dev/ttyxxx --info-seg 5 --info "11:28:00 AM"
Accel Calib data:       python otp_program.py --port /dev/ttyxxx --info-seg 6 --info "1.0,1.0,1.0,0.02341,0.023451,0.023552"

Display only:
                        python otp_program.py --port /dev/ttyxxx --only-display
                        
Lock:
                        python otp_program.py --port /dev/ttyxxx --info-seg INFO_SEG --lock
'''
crc32_tab = [
  0x00000000, 0x77073096, 0xee0e612c, 0x990951ba, 0x076dc419, 0x706af48f, 0xe963a535, 0x9e6495a3,
  0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988, 0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91,
  0x1db71064, 0x6ab020f2, 0xf3b97148, 0x84be41de, 0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
  0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec, 0x14015c4f, 0x63066cd9, 0xfa0f3d63, 0x8d080df5,
  0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172, 0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b,
  0x35b5a8fa, 0x42b2986c, 0xdbbbc9d6, 0xacbcf940, 0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
  0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116, 0x21b4f4b5, 0x56b3c423, 0xcfba9599, 0xb8bda50f,
  0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924, 0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d,
  0x76dc4190, 0x01db7106, 0x98d220bc, 0xefd5102a, 0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
  0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818, 0x7f6a0dbb, 0x086d3d2d, 0x91646c97, 0xe6635c01,
  0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e, 0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457,
  0x65b0d9c6, 0x12b7e950, 0x8bbeb8ea, 0xfcb9887c, 0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
  0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2, 0x4adfa541, 0x3dd895d7, 0xa4d1c46d, 0xd3d6f4fb,
  0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0, 0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9,
  0x5005713c, 0x270241aa, 0xbe0b1010, 0xc90c2086, 0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
  0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4, 0x59b33d17, 0x2eb40d81, 0xb7bd5c3b, 0xc0ba6cad,
  0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a, 0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683,
  0xe3630b12, 0x94643b84, 0x0d6d6a3e, 0x7a6a5aa8, 0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
  0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe, 0xf762575d, 0x806567cb, 0x196c3671, 0x6e6b06e7,
  0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc, 0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5,
  0xd6d6a3e8, 0xa1d1937e, 0x38d8c2c4, 0x4fdff252, 0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
  0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60, 0xdf60efc3, 0xa867df55, 0x316e8eef, 0x4669be79,
  0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236, 0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f,
  0xc5ba3bbe, 0xb2bd0b28, 0x2bb45a92, 0x5cb36a04, 0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
  0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a, 0x9c0906a9, 0xeb0e363f, 0x72076785, 0x05005713,
  0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38, 0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21,
  0x86d3d2d4, 0xf1d4e242, 0x68ddb3f8, 0x1fda836e, 0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
  0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c, 0x8f659eff, 0xf862ae69, 0x616bffd3, 0x166ccf45,
  0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2, 0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db,
  0xaed16a4a, 0xd9d65adc, 0x40df0b66, 0x37d83bf0, 0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
  0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6, 0xbad03605, 0xcdd70693, 0x54de5729, 0x23d967bf,
  0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94, 0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d
]

if __name__ == '__main__':
    # Parse commandline arguments
    parser = argparse.ArgumentParser(description="OTP Programmer for the PX autopilot system.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--port', action="store", required=True, help="Serial port(s) to which the FMU may be attached")
    parser.add_argument('--baud', action="store", type=int, default=57600, help="Baud rate of the serial port (default is 115200), only required for true serial ports.")
    parser.add_argument('--info-seg', action="store", type=int, default=1, help="OTP partitions:\n"
                                                                               "#1 Manufacturer Information\n"
                                                                               "#2 Machine Information\n"
                                                                               "#3 Manufacturing Information\n"
                                                                               "#3 Date of Testing\n"
                                                                               "#4 Time of Testing\n"
                                                                               "#5 Factory Accel Offsets and Scale Factors\n")
    parser.add_argument('--info', action="store", default="3D Robotics, Inc, \xA9 2015", help='Information')
    parser.add_argument('--only-display', action='store_true', default=False, help="specify if you want to only display otp space")
    parser.add_argument('--lock', action='store_true', default=False, help="specify if you want to lock the mentioned portion of otp space")
    args = parser.parse_args()

    #Connect to the port
    port = args.port
    print("Trying %s" % port)

    # attach to the port
    try:
            if "linux" in _platform:
                    # Linux, don't open Mac OS and Win ports
                    if not "COM" in port and not "tty.usb" in port:
                            conn = serial.Serial(port, args.baud, timeout=0.5)
            elif "darwin" in _platform:
                    # OS X, don't open Windows and Linux ports
                    if not "COM" in port and not "ACM" in port:
                            conn = serial.Serial(port, args.baud, timeout=0.5)
            elif "win" in _platform:
                    # Windows, don't open POSIX ports
                    if not "/" in port:
                            conn = serial.Serial(port, args.baud, timeout=0.5)
    except Exception:
        # open failed, rate-limit our attempts
        print "Port Not Found!"
        sys.exit()

    conn.close()
    conn.open()

    #Display Information
    conn.write("otp show\r\n".encode())

    count = 0
    print "Data in OTP segments:"
    while True:
        line  = conn.readline()
        if count == 2:
            info = line.split()
            if info[1] == 'U':
                lock = "Unlocked\t"
            else:
                lock = "Locked\t"
            string = info[2].decode('hex')
            print "Segment", info[0], lock, "Manufacturer Info:\t", string[:string.index('\xff')]
        elif count == 3:
            info = line.split()
            if info[1] == 'U':
                lock = "Unlockedt\t"
            else:
                lock = "Locked\t"
            string = info[2].decode('hex')
            print "Segment", info[0], lock, "Test Machine Info:\t", string[:string.index('\xff')]
        elif count == 4:
            info = line.split()
            if info[1] == 'U':
                lock = "Unlocked\t"
            else:
                lock = "Locked\t"
            string = info[2].decode('hex')
            print "Segment", info[0], lock, "Manufacturing Info:\t", string[:string.index('\xff')]
        elif count == 5:
            info = line.split()
            if info[1] == 'U':
                lock = "Unlocked\t"
            else:
                lock = "Locked\t"
            string = info[2].decode('hex')
            print "Segment", info[0], lock, "Date of Testing:\t", string[:string.index('\xff')]
        elif count == 6:
            info = line.split()
            if info[1] == 'U':
                lock = "Unlocked\t"
            else:
                lock = "Locked\t"
            string = info[2].decode('hex')
            print "Segment", info[0], lock, "Time of Testing:\t", string[:string.index('\xff')]
        elif count == 7:
            info = line.split()
            if info[1] == 'U':
                lock = "Unlocked\t"
            else:
                lock = "Locked\t"
            accel_data = struct.unpack('6f', bytearray.fromhex(info[2][:48]))
            print "Segment", info[0], lock, "Accel :\t", accel_data

        count = count+1
        if count == 17:
            break;

    if args.only_display:
        conn.close()    
        sys.exit()

    if args.lock:
        cmd = "otp lock "+str(args.info_seg)+" "+str(args.info_seg)+"\r\n"
        conn.write(cmd)
        print "\nSegment " + str(args.info_seg) + " locked!"
        time.sleep(1)
        conn.close()
        sys.exit()

    #Write Information
    print "Writing..."
    if args.info_seg == 6:
        accel_data = [float(x) for x in args.info.split(',') if x]
        packed_accel_data = struct.pack('%sf' % len(accel_data), *accel_data)
        hexarray = binascii.hexlify(packed_accel_data)
        information = hexarray
        data = struct.unpack('6f', bytearray.fromhex(hexarray))
    elif args.info_seg < 6:
        information = str(str(args.info).encode('hex'))
    else:
        print "Segment is unavailable or reserved for future!!\n"
        conn.close()
        sys.exit()

    if len(information) > 64:
        print "ERROR: Single information cannot be larger that 64 Bytes!!"
        conn.close()
        sys.exit()

    information = information + 'f'*(64-len(information))
    src = bytearray.fromhex(information)
    crc32val = 0
    for i in range (0,32):
        crc32val = crc32_tab[(crc32val ^ src[i]) & 0xff] ^ (crc32val >> 8);
    crc = hex(crc32val)
    cmd = "otp write " + str(args.info_seg) + " " + information + " " + crc + "\r\n"
    conn.write(cmd)
    time.sleep(1)

    #Verify Information
    print "Verifying..." 
    conn.write("otp show\r\n".encode())
    count = 0
    first_line_detected = False
    while True:
        line = conn.readline()
        if first_line_detected == False:
            if(line[1] == '0'):
                count = 0
                first_line_detected = True
            else:
                continue
        if count == args.info_seg:
            info = line.split()
            if(info[2] == information):
                print "Verification Successful!!"
            else:
                print "Verification Failed!"
        count = count+1
        if count == 17:
            break;
        
    conn.close()