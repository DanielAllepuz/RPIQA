CFLAGS = -O3 -march=armv7-a -mtune=cortex-a9 -mfpu=neon -mfloat-abi=hard

all: acquire configure

acquire: acquire.c
	gcc $(CFLAGS) -o $@ $^ -lm

configure: configure.c
	gcc $(CFLAGS) -o $@ $^ -lm

clean:
	rm -f acquire configure