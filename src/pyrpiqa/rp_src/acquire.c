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

#define OUTPUT_FILE "/mnt/RPIQA/output.bin"

volatile uint64_t *fifo;
volatile uint16_t *rx_cntr;
volatile uint8_t *gpio, *rx_rst, *rx_sync;

uint8_t buffer[16384];

int main(int argc, char *argv[])
{
    int fd;
    volatile void *cfg, *sts;
    char *endptr;
    unsigned int channel;
    uint16_t target_fifo_reads;

    if (argc != 3)
    {
        printf("Usage: %s [input channel: 1|2] [number of fifo reads: integer]\n", argv[0]);
        return EXIT_FAILURE;
    }

    if ((fd = open("/dev/mem", O_RDWR)) < 0)
    {
        printf("Couldn't open memory.");
        perror("open");
        return EXIT_FAILURE;
    }

    errno = 0;
    channel = strtol(argv[1], &endptr, 10);

    switch (channel)
    {
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
    if (errno != 0 || *endptr != '\0')
    {
        perror("Error converting channel number, it should be 1 or 2");
        return EXIT_FAILURE;
    }

    target_fifo_reads = strtol(argv[2], &endptr, 10);

    // Check for errors during conversion
    if (errno != 0 || *endptr != '\0')
    {
        perror("Error converting RX rate");
        return EXIT_FAILURE;
    }

    gpio = (uint8_t *)(cfg + 2);
    *gpio = 0;

    rx_rst = (uint8_t *)(cfg + 0);
    rx_cntr = (uint16_t *)(sts + 0);
    rx_sync = (uint8_t *)(cfg + 8);

    FILE *file = fopen(OUTPUT_FILE, "wb");

    *rx_rst &= ~1;
    *rx_rst |= 1;
    for (size_t i = 0; i < target_fifo_reads; i++)
    {
        if (*rx_cntr >= 8192)
        {
            *rx_rst &= ~1;
            *rx_rst |= 1;
        }

        while (*rx_cntr < 4096)
            usleep(500);

        memcpy(buffer, fifo, 16384);
        fwrite(buffer, sizeof(unsigned char), 16384, file);
    }
    fclose(file);

    return EXIT_SUCCESS;
}
