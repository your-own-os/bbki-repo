#!/usr/bin/python3


import re
import time
import robust_layer
import urllib.request


wirelessRegDbDirUrl = "https://www.kernel.org/pub/software/network/wireless-regdb"

# get wireless-regdb from internet
ver = None
while True:
    try:
        with urllib.request.urlopen(wirelessRegDbDirUrl, timeout=robust_layer.TIMEOUT) as resp:
            out = resp.read().decode("iso8859-1")
            for m in re.finditer("wireless-regdb-([0-9]+\\.[0-9]+\\.[0-9]+)\\.tar\\.xz", out, re.M):
                if ver is None or m.group(1) > ver:
                    ver = m.group(1)
            assert ver is not None
        break
    except OSError as e:
        print("Failed to acces %s, %s" % (wirelessRegDbDirUrl, e))
        time.sleep(robust_layer.RETRY_TIMEOUT)

# download
localFile = "wireless-regdb-%s.tar.xz" % (ver)

if not os.path.exists(localFile):
    print("File already downloaded.")
    return

# download the target file
FmUtil.wgetDownload("%s/%s" % (self.wirelessRegDbDirUrl, filename), localFile)
