#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <math.h>
#include <sys/mman.h>



uint8_t buffer[16384];

int main(int argc, char *argv[]) {
	int fd;
  	volatile void *cfg, *sts;
  	char *endptr;
	volatile uint64_t *fifo;
	volatile uint32_t *rx_freq;
	volatile uint16_t *rx_rate, *rx_cntr;
	volatile uint8_t *gpio, *rx_rst, *rx_sync;
	int channel;
	float user_modulation_frequency;
	uint16_t user_rx_rate;
	
	if (argc != 4) {
        printf("Usage: %s [input channel: 1|2] [modulation frequency: float number from 0 to 60e6] [rx_rate: integer]\n", argv[0]);
        return EXIT_FAILURE;
    }

	if ((fd = open("/dev/mem", O_RDWR)) < 0)
	{
        printf("Couldn't open memory.");
		perror("open");
		return EXIT_FAILURE;
	}

    // Parse the arguments
    errno = 0;
	channel = strtol(argv[1], &endptr, 10);

	switch (channel) {
	case 1:
		cfg = mmap(NULL, sysconf(_SC_PAGESIZE), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0x40000000);
		sts = mmap(NULL, sysconf(_SC_PAGESIZE), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0x41000000);
		fifo = mmap(NULL, 8 * sysconf(_SC_PAGESIZE), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0x42000000);
		break;
	case 2:
		cfg = mmap(NULL, sysconf(_SC_PAGESIZE), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0x80000000);
		sts = mmap(NULL, sysconf(_SC_PAGESIZE), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0x81000000);
		fifo = mmap(NULL, 8 * sysconf(_SC_PAGESIZE), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0x82000000);
		break;
	}

	// Check for errors during conversion
    if (errno != 0 || *endptr != '\0') {
        perror("Error converting channel number, it should be 1 or 2");
        return EXIT_FAILURE;
    }

    user_modulation_frequency = strtof(argv[2], &endptr);

    // Check for errors during conversion
    if (errno != 0 || *endptr != '\0') {
        perror("Error converting modulation frequency");
        return EXIT_FAILURE;
    }

    user_rx_rate = strtol(argv[3], &endptr, 10);

    // Check for errors during conversion
    if (errno != 0 || *endptr != '\0') {
        perror("Error converting RX rate");
        return EXIT_FAILURE;
    }

	rx_rst = (uint8_t *)(cfg + 0);
	rx_freq = (uint32_t *)(cfg + 4);
	rx_sync = (uint8_t *)(cfg + 8);
	rx_rate = (uint16_t *)(cfg + 10);
	rx_cntr = (uint16_t *)(sts + 0);

	/* set default rx phase increment */
	*rx_freq = (uint32_t)floor(user_modulation_frequency / 125.0e6 * (1 << 30) + 0.5);
	*rx_sync = 0;
    *rx_rate = user_rx_rate;

	/* Tested values for rx_rate */
	//*rx_rate = 50;  //  1250 ksPS
	//*rx_rate = 125; //   500 kSPS
	//*rx_rate = 250; //   250 kSPS
	//*rx_rate = 625; //   100 kSPS
	//*rx_rate = 1250;//    50 kSPS
	return EXIT_SUCCESS;
}


