import paramiko
import os
import math
import numpy as np
import struct
import time

PACKAGE_ROOT = os.path.dirname(__file__)

def print_C_sources():
    print(__file__)
    files_to_move = ["acquire.c", "configure.c", "Makefile"]

    for filename in files_to_move:
        print(f"{filename}:" + "~"*12)
        with open(os.path.join(PACKAGE_ROOT, "rp_src", filename), "r") as f:
            print(f.read(-1))
        print("~"*12)

class RPIQA:
    """
    API to configure system and acquire data.
    """
    SAMPLE_RATE_50KSPS = 1250
    SAMPLE_RATE_100KSPS = 625
    SAMPLE_RATE_250KSPS = 250
    SAMPLE_RATE_500KSPS = 125
    SAMPLE_RATE_1250KSPS = 50

    actual_samplerate = {SAMPLE_RATE_50KSPS: 50e3, SAMPLE_RATE_100KSPS: 100e3,
                         SAMPLE_RATE_250KSPS: 250e3, SAMPLE_RATE_500KSPS: 500e3, SAMPLE_RATE_1250KSPS: 1250e3}

    RAM_DISK_PATH = "/mnt/RPIQA"


    def __init__(self, rp_address: str, input_channel: int, username: str = "root", password: str = "changeme", verbose: bool = False, sleep_function=time.sleep):
        """
        :param rp_address: IP address of the Red Pitaya, can be *.*.*.* or RP-******.local
        :param input_channel: Input channel from which to acquire data. Either 1 or 2.
        :param username: User name to use to connect, default is "root".
        :param password: Password of the user, default is "changeme"
        :param verbose: if True, details about the init process will be printed. Default is False
        :param sleep_function: custom function to block execution. Default is Python's time.sleep
        """
        if (int(input_channel) == 1 or int(input_channel) == 2):
            self.input_channel = input_channel
        else:
            raise RuntimeError("Input channel should be 1 or 2")
        
        if verbose:
            vprint = print
        else:
            def vprint(_): return 0

        self.sleep = sleep_function

        # Open SSH and SFTP connection
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(rp_address, username=username, password=password)
        self.sftp = self.ssh.open_sftp()

        # Check that the bit file for the Pavel's SDR transceiver is there:
        bitfile_path = "/media/mmcblk0p1/apps/sdr_transceiver/sdr_transceiver.bit"
        check_command = f"test -f {bitfile_path} && echo 'exists' || echo 'not exists'"
        stdin, stdout, stderr = self.ssh.exec_command(check_command)
        file_status = stdout.read().decode('utf-8').strip()

        if file_status == 'not-exists':
            raise RuntimeError(
                "SDR transceiver bitfile not found, have you installed Pavel's Alpine Linux distribution? https://pavel-demin.github.io/red-pitaya-notes/alpine/")

        # Load sdr_transceiver bit file to the FPGA
        self.ssh.exec_command(f"cat {bitfile_path} > /dev/xdevcfg")

        # Mount a disk on RAM to put our executables and where data will be written
        # First check if it's already present
        stdin, stdout, stderr = self.ssh.exec_command(
            f"test -d {self.RAM_DISK_PATH} && echo 'exists' || echo 'not exists'")

        # Read the result of the check
        folder_status = stdout.read().decode('utf-8').strip()

        if folder_status == 'not exists':
            # Mount ram disk
            self.ssh.exec_command(f"mkdir -p {self.RAM_DISK_PATH}")
            stdin, stdout, stderr = self.ssh.exec_command(
                f"mount -t tmpfs -o size=128m tmpfs {self.RAM_DISK_PATH}")

            # Check for errors during command execution
            if stderr.read():
                raise RuntimeError(
                    f"Error mounting RAM disk on RedPitaya: {stderr.read().decode('utf-8')}")
            else:
                vprint(
                    f"RAM disk '{self.RAM_DISK_PATH}' created successfully.")

        # Move executable files
        files_to_move = ["acquire", "configure"]

        vprint("Transfering executable files...")
        for filename in files_to_move:
            self.sftp.put(os.path.join(PACKAGE_ROOT, "rp_src", filename),
                        self.RAM_DISK_PATH+"/"+filename)
            self.ssh.exec_command(f"chmod u+x {self.RAM_DISK_PATH}"+"/"+filename)
            vprint(f"Transferred {filename}")

        # Once everything is set up, configure some default values
        self._rate = self.SAMPLE_RATE_250KSPS
        self._mod_freq = 1e6
        self.update_configuration()

    def update_configuration(self):
        """
        Updates the hardware implementation running on the Red Pitaya with the set modulation frequency and sample rate
        """
        self.ssh.exec_command(
            f"cd {self.RAM_DISK_PATH} && ./configure {self.input_channel} {self._mod_freq} {self._rate}")

    def set_modulation_frequency(self, mod_freq: float):
        """
        Sets the demodulation frequency.
        :param mod_freq: demodulation frequency in Hertz (float) 
        """
        self._mod_freq = mod_freq
        self.update_configuration()

    def set_sample_rate(self, sample_rate: int):
        """
        Sets the sample rate.
        :param sample_rate: one of the defined smaple rates, such as RPIQA.SAMPLE_RATE_50KSPS. Run `help(RPIQA)` to see options.
        """
        self._rate = sample_rate
        self.update_configuration()

    def acquire(self, duration: float):
        """
        Starts acquisition for the duration given.
        :param duration: duration in seconds, the resulting duration will NOT be the specified duration, as it might not be a multiple of the buffer size. Checked the returned time array for actual duration.
        :returns: Three numpy arrays: t, I, Q. Containing time labels in seconds, I and Q quadrature. 
        """
        # Calculate number of FIFOs to record
        number_of_fifos: int = math.ceil(
            8 * duration * self.actual_samplerate[self._rate] / 16384)  # this is the size of the FIFO
        t0 = time.time()
        self.ssh.exec_command(
            f"cd {self.RAM_DISK_PATH} && ./acquire {self.input_channel} {number_of_fifos}")
        self.sleep(duration-(time.time()-t0))

        # Get raw data through sftp
        with self.sftp.file(f"{self.RAM_DISK_PATH}/output.bin", "rb") as f:
            bindata = f.read(-1)

        chunks = [(bindata[i:i+4]) for i in range(0, len(bindata), 4)]
        I = np.array([struct.unpack('f', chunks[i])
                     for i in range(0, len(chunks), 2)])[:, 0]
        Q = np.array(([struct.unpack('f', chunks[i])
                     for i in range(1, len(chunks), 2)]))[:, 0]

        return np.arange(I.shape[0])/self.actual_samplerate[self._rate], I, Q

    def get_maximum_duration(self) -> float:
        """
        Check what is the maximum acquisition duration at the current sample rate
        :returns: duration in seconds
        """
        return 100e6/(8 * self.actual_samplerate[self._rate])

    def get_modulation_frequency(self) -> float:
        """
        Get current modulation frequency
        :returns: modulation frequency
        """
        return self._mod_freq

    def close(self):
        """
        Disconnects from the Red Pitaya. Run this at the end of your experiments.
        """
        self.ssh.close()
