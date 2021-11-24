/*
 * bcachefs-mount.c
 * 
 * Simple code to mount bcachefs filesystem.
 *
 * Copyright 2014-2014 fpemud@sina.com
 *
 * This software may be freely redistributed under the terms of the GNU
 * public license.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 *
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <glob.h>
#include <errno.h>
#include "lvm2app.h"


static char * partitions[1024] = {NULL};
static char * uuids[1024] = {NULL};
static int max_parti = -1;


static char *get_bcachefs_uuid(const char *devpath) {

}

static int parse() {
    int fd;
    char line[4096];
    int i, j;

    max_parti = 0;
    fd = open("/proc/partitions");
    for (i = 0; ; i++) {
        char *p;

        /* read line into variable "line" */
        for (j = 0; j < 4096; j++) {
            int rc = read(fd, &line[j], 1);
            if (rc < 0) {
                fprintf(stderr, "bcachefs-mount: error reading line %d of /proc/partitions", i + 1);
                close(fd);
                return 1;
            }
            if (rc == 0) {
                close(fd);
                return 0;
            }
            if (line[j] == '\n') {
                break;
            }
        }
        if (j == 4096) {
            fprintf(stderr, "bcachefs-mount: line %d of /proc/partitions is too long", i + 1);
            close(fd);
            return 1;
        }

        /* jump over the first two lines */
        if (i == 0 || i == 1) {
            continue;
        }

        /* find dev part */
        p = strrchr(line, ' ');
        if (p == NULL) {
            fprintf(stderr, "bcachefs-mount: error parsing /proc/partitions");
            close(fd);
            return 1;
        }
        p++;

        /* add a device path and bcachefs uuid */
        if (max_parti >= 1024) {
            fprintf(stderr, "bcachefs-mount: too many partitions in /proc/partitions");
            close(fd);
            return 1;
        }
        partitions[max_parti] = (char*)malloc(strlen(p) + 1);
        strcpy(partitions[max_parti], "/dev/");
        strcat(partitions[max_parti], p);
        uuids[max_parti] = get_bcachefs_uuid(partitions[max_parti]);

        max_parti++;
    }
}

int main(int argc, char **argv) {
    char *uuidList;
    char *mntPoint;
    char devices[16384] = "";
    char *pu, *pd;
    int i;

    /* arguments */
    if (argc < 3) {
        fprintf(stderr, "bcachefs-mount: too few arguments\n");
        return 1;
    }
    uuidList = argv[1];
    mntPoint = argv[2];

    /* parse /proc/partitions and get bcachefs uuid */
    if (parse() == NULL) {
        return 1;
    }

    pu = uuidList;
    pd = devices;
    while (1) {
        char *pu2 = strchr(pu, ':');
        if ((pu2 != NULL && strlen(pu) != 36) || (pu2 == NULL && strlen(pu) != 36)) {
            fprintf(stderr, "bcachefs-mount: invalid UUID found\n");
            return 1;
        }

        for (i = 0; i < max_parti; i++) {
            if (uuids[i] != NULL && strncmp(pu, uuids[i], 36) == 0) {
                strcat(pd, partitions[i]);
                strcat(pd, ":");
                break;
            }
        }
        if (i == max_parti) {
            fprintf(stderr, "bcachefs-mount: UUID %s not found\n");
            return 1;
        }

        if (pu2 == NULL) {
            break;
        }
    }





    if (mount(device, mntPoint, "bcachefs", 0, "")) {
        fprintf(stderr, "mount: error %d mounting %s\n", errno, "bcachefs");
        return 1;
    }

    return 0;
}
