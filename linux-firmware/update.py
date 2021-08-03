#!/usr/bin/python3

import os
import re
import time
import tarfile
import lxml.html
import urllib.request
import robust_layer.wget
import robust_layer.simple_git
import robust_layer.simple_fops


firmwareUrl = "https://www.kernel.org/pub/linux/kernel/firmware"

# get firmware version version from internet
ver = None
while True:
    try:
        with urllib.request.urlopen(firmwareUrl, timeout=robust_layer.TIMEOUT) as resp:
            root = lxml.html.parse(resp)
            for atag in root.xpath(".//a"):
                m = re.fullmatch("linux-firmware-(.*)\\.tar\\.xz", atag.text)
                if m is not None:
                    if ver is None or ver < m.group(1):
                        ver = m.group(1)
            assert ver is not None
        break
    except OSError as e:
        print("Failed to acces %s, %s" % (firmwareUrl, e))
        time.sleep(robust_layer.RETRY_TIMEOUT)

# download
firmwareFile = "linux-firmware-%s.tar.xz" % (ver)
signFile = "linux-firmware-%s.tar.sign" % (ver)
if not os.path.exists(firmwareFile) or not os.path.exists(signFile):
    robust_layer.simple_fops.rm(signFile)                                               # delete the complete flag file
    robust_layer.wget.exec(os.path.join(firmwareUrl, firmwareFile), "-O", firmwareFile)
    robust_layer.wget.exec(os.path.join(firmwareUrl, signFile), "-O", signFile)

# extract
for fn in os.listdir("."):                      # remove old files
    if fn != firmwareFile and fn != signFile:
        robust_layer.simple_fops.rm(fn)
with tarfile.open(firmwareFile, mode="r:xz") as tarf:
    tarf.extractall(".")
