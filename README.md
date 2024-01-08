# Red Pitaya IQ Acquisition (RPIQA)
Use a [Red Pitaya FPGA board](https://redpitaya.com/) to acquire long, continuous time traces of IQ-demodulated signals.

## Features
* Demodulation at custom frequencies, from DC up to 62.5MHz. 
* Sample rates down to 50 kSa/s and up to 1.25MSa/s have been tested.
* A simple, straight-forward Python API is provided to configure the acquisition and transfer data from the board to another computer.

# What does it do?
* An analog signal arriving at the board is digitized at 125MSa/s.
* The digital signal is demodulated at a user-set frequency using the CORDIC method.
* The demodulated signals, I and Q, are sampled at a slower rate (configurable by the user) and stored in a buffer.
* The buffer is periodically stored in the board's [SoC](https://en.wikipedia.org/wiki/System_on_a_chip)'s RAM while ensuring that no data is lost.

# How is it implemented?
As of now, this project piggybacks on [Pavel Demin's SDR Transceiver bitfile](https://pavel-demin.github.io/red-pitaya-notes/sdr-transceiver/). Instead of running Pavel's software, which streams data over the network, the software provided in this project stores it in RAM, ensuring continuous acquisition. In the future, a custom bitfile will be provided.

# Installation
* Follow [Pavel's instructions](https://pavel-demin.github.io/red-pitaya-notes/alpine/) to install a custom Linux distribution on the Red Pitaya. 
* Install the required Python modules using `pip install numpy paramiko`. The software has been tested using Python 3.7.12. It should work with newer versions of Python.
* Download this repository by either cloning it `git clone https://github.com/DanielAllepuz/RPIQA.git` or [downloading the repository as a ZIP file](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives).
* Navigate to the root folder of your local copy and run `pip install .`
  
# Usage
```python
from pyrpiqa import RPIQA

rpiqa = RPIQA("your Red Pitaya IP address", 1) # This can take a few seconds, 1 means IN1; use 2 for IN2

rpiqa.set_modulation_frequency(1.001e6) # Set the demodulation frequency 1kHz away from the signal
rpiqa.set_sample_rate(rpiqa.SAMPLE_RATE_100KSPS) # Set the sample rate to 100kHz
t, I, Q = rpiqa.acquire(2.5) # Acquire 2.5 seconds of data
```

# Known issues
* When the Red Pitaya is rebooted, Pavel's Linux distribution generates new ssh keys. The program will not run and complain with `ValueError: ('Invalid private key',...`. A quick fix when using Windows is to delete the stored keys found in `C:\Users\(your user name)\.shh\known_hosts`