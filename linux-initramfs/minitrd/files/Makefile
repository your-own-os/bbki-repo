PACKAGE_VERSION="1.0"
CFLAGS=-Wall -Wextra -Werror -Wno-unused-function -Wno-unused-parameter -Wno-sign-compare -Wno-pointer-sign -Wno-unused-but-set-variable -Wno-format-zero-length -Wno-format-truncation -DVERSION=\"$(PACKAGE_VERSION)\" -g
LIBS=`pkg-config --libs blkid kmod`

all: init

init: init.o
	$(CC) $(LDFLAGS) $^ $(LIBS) -o $@

clean:
	rm -f init $(MINILIBC) *.o
