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
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <dirent.h>
#include <errno.h>
#include <c-list.h>
#include <sys/mount.h>
#include <blkid/blkid.h>
#include <uuid/uuid.h>


/*UUID_DEFINE(BCACHE_MAGIC, 0xf6, 0x73, 0x85, 0xc6, 0x1a, 0x4e, 0xca, 0x45, 0x82, 0x65, 0xf5, 0x7f, 0x48, 0xba, 0x6d, 0x81);*/

UUID_DEFINE(BCACHE_MAGIC, 0xc6, 0x85, 0x73, 0xf6, 0x4e, 0x1a, 0x45, 0xca, 0x82, 0x65, 0xf5, 0x7f, 0x48, 0xba, 0x6d, 0x81);


struct uuid_map {
    CList link;
    uuid_t uu;
    char devpath[PATH_MAX];
};

static CList uuid_map_list;


static int read_line(const char *path, FILE *fp, int line_no, char *buf, int buflen)
{
    int i;
    for (i = 0; i < buflen; i++) {
        size_t rc = fread(&buf[i], 1, 1, fp);
        if (rc == 0) {
            if (feof(fp)) {
                buf[i] = '\0';
                return i;
            } else {
                fprintf(stderr, "bcachefs-mount: error occured when reading line %d of %s", line_no, path);
                return -2;
            }
        }
        if (buf[i] == '\n') {
            buf[i] = '\0';
            return i;
        }
    }
    fprintf(stderr, "bcachefs-mount: line %d of %s is too long", line_no, path);
    return -1;
}

static int read_buf(const char *path, int fd, int offset, char *buf, int buflen)
{
    if (lseek(fd, offset, SEEK_SET) < 0) {
        fprintf(stderr, "bcachefs-mount: error occured when seeking device %s", path);
        return -1;
    }

    if (read(fd, buf, buflen) != buflen) {
        fprintf(stderr, "bcachefs-mount: error reading device %s", path);
        return -1;
    }

    return 0;
}

static int get_bcachefs_uuid(const char *path, uuid_t uu)
{
    int fd;

    fd = open(path, O_RDONLY, 0);
    if (fd == 0) {
        fprintf(stderr, "bcachefs-mount: error %d when opening device %s", errno, path);
        return -1;
    }

    /* read magic and compare */
    if (read_buf(path, fd, 24, uu, sizeof(*uu))) {
        close(fd);
        return -1;
    }
	if (uuid_compare(uu, BCACHE_MAGIC) != 0) {
        /* not a bcachefs filesystem, that's ok */
        close(fd);
        return 1;
    }

    /* read uuid */
    if (read_buf(path, fd, 40, uu, sizeof(*uu))) {
        close(fd);
        return -1;
    }

    close(fd);
    return 0;
}

static int parse() {
    const char *path = "/proc/partitions";
    struct uuid_map *node;
    FILE *fp;
    int i;

    c_list_init(&uuid_map_list);

    fp = fopen(path, "r");
    for (i = 0; ; i++) {
        char line[4096];
        int rc;
        char *p;

        /* read line */
        rc = read_line(path, fp, i + 1, line, 4096);
        if (rc < 0) {
            fclose(fp);
            return rc;
        }
        if (feof(fp)) {
            break;
        }

        /* jump over the first two lines */
        if (i == 0 || i == 1) {
            continue;
        }

        /* find dev part */
        p = strrchr(line, ' ');
        if (p == NULL) {
            fprintf(stderr, "bcachefs-mount: error parsing /proc/partitions");
            fclose(fp);
            return -1;
        }
        p++;

        node = malloc(sizeof(*node));
        c_list_init(&node->link);

        strcpy(node->devpath, "/dev/");
        strcat(node->devpath, p);

        printf("debug1: %s\n", node->devpath);

        rc = get_bcachefs_uuid(node->devpath, node->uu);
        if (rc < 0) {
            free(node);
            fclose(fp);
            return rc;
        }
        if (rc > 0) {
            /* no bcachefs uuid found */
            free(node);
            continue;
        }

        c_list_link_tail(&uuid_map_list, &node->link);
        printf("debug2: %s\n", node->devpath);
    }

    fclose(fp);
    return 0;
}

int main(int argc, char **argv)
{
    char devices[16384] = "";
    char *uuidList, *mntPoint, *pu;

    /* arguments */
    if (argc < 3) {
        fprintf(stderr, "bcachefs-mount: too few arguments\n");
        return 1;
    }
    uuidList = argv[1];
    mntPoint = argv[2];

    /* argument check */
    if (uuidList[0] == 0) {
        fprintf(stderr, "bcachefs-mount: invalid uuid-list parameter\n");
        return 1;
    }
    if (mntPoint[0] == 0) {
        fprintf(stderr, "bcachefs-mount: invalid mount-point parameter\n");
        return 1;
    }

    /* parse /proc/partitions and get bcachefs uuids */
    if (parse()) {
        return 1;
    }

    /* fill variable devices according to uuidList */
    pu = uuidList;
    while (*pu != '\0') {
        size_t devices_len = strlen(devices);
        uuid_t uu;
        char *pu2;
        struct uuid_map *node;

        if (*pu == ':') pu++;
        pu2 = strchr(pu, ':');
        pu2 = (pu2 != NULL) ? pu2 : (pu + strlen(pu));

        if (uuid_parse_range(pu, pu2, uu)) {
            fprintf(stderr, "bcachefs-mount: invalid UUID \"%.*s\" found\n", (int)(pu2 - pu), pu);
            return 1;
        }

        c_list_for_each_entry(node, &uuid_map_list, link) {
            if (uuid_compare(node->uu, uu) == 0) {
                strcat(devices, node->devpath);
                strcat(devices, ":");
            }
        }

        if (devices_len == strlen(devices)) {
            fprintf(stderr, "bcachefs-mount: no device found for UUID \"%.*s\"\n", (int)(pu2 - pu), pu);
            return 1;
        }

        pu = pu2;
    }

    devices[strlen(devices) - 1] = '\0';

    if (mount(devices, mntPoint, "bcachefs", 0, "")) {
        fprintf(stderr, "bcachefs-mount: error %d mounting %s\n", errno, "bcachefs");
        return 1;
    }

    return 0;
}
