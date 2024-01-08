# Red Pitaya IQ Acquisition (RPIQA)
Use a [Red Pitaya FPGA board](https://redpitaya.com/) to acquire long continuous time traces of IQ-demodulated signals.
A simple straight-forward Python API is provided to configure the acquisition and transfer data from the board to another computer.
# What does it do?
* An analog signal arriving at the board is digitized at 125MSa/s.
* The now digital signal is demodulated at a user-set frequency using the CORDIC method.
* The demodulated signals, I and Q, are sampled at a slower rate (configurable by the user) and stored in a buffer.
* The buffer is periodically stored in the board's [SoC](https://en.wikipedia.org/wiki/System_on_a_chip)'s RAM while ensuring that no data is lost.
# How is it implemented?
As of now, this project piggy-backs on [Pavel Demin's SDR Transceiver bitfile](https://pavel-demin.github.io/red-pitaya-notes/sdr-transceiver/). Instead of running Pavel's software, which streams data over the network, the software provided in this project stores it in RAM, assuring continuous acquisition. In the future, a custom bitfile will be provided.
# Installation
* Follow [Pavel's instructions](https://pavel-demin.github.io/red-pitaya-notes/alpine/) to install his custom Linux distribution on the Red Pitaya. 
* Install the required Python modules using `pip install numpy paramiko`. The software has been tested using Python 3.7.12. It should work with newer versions of Python.
* Download this repository by either cloning it `git clone https://github.com/DanielAllepuz/RPIQA.git` or [downloading the repository as a ZIP file](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives).
* Navigate to the your local copy's root folder and run `pip install .`
  
