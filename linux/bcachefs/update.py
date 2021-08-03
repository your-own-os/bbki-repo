#!/usr/bin/python3

import os
import io
import gzip
import time
import tarfile
import lxml.html
import urllib.request
import robust_layer.wget
import robust_layer.simple_git
import robust_layer.simple_fops


kernelUrl = "https://www.kernel.org"
typename = "stable"

# get kernel version from internet
ver = None
while True:
    try:
        with urllib.request.urlopen(kernelUrl, timeout=robust_layer.TIMEOUT) as resp:
            if resp.info().get('Content-Encoding') is None:
                fakef = resp
            elif resp.info().get('Content-Encoding') == 'gzip':
                fakef = io.BytesIO(resp.read())
                fakef = gzip.GzipFile(fileobj=fakef)
            else:
                assert False
            root = lxml.html.parse(fakef)

            td = root.xpath(".//td[text()='%s:']" % (typename))[0]
            td = td.getnext()
            while len(td) > 0:
                td = td[0]
            ver = td.text
            break
    except OSError as e:
        print("Failed to acces %s, %s" % (kernelUrl, e))
        time.sleep(robust_layer.RETRY_TIMEOUT)

# download
kernelFile = "linux-%s.tar.xz" % (ver)
signFile = "linux-%s.tar.sign" % (ver)
if not os.path.exists(kernelFile) or not os.path.exists(signFile):
    robust_layer.simple_fops.rm(signFile)                              # delete the complete flag file
    kernelFile, signFile = _getRemoteFiles(kernelUrl, ver, kernelFile, signFile)
    robust_layer.wget.exec(os.path.join(kernelUrl, kernelFile), "-O", kernelFile)
    robust_layer.wget.exec(os.path.join(kernelUrl, signFile), "-O", signFile)

# extract
for fn in os.listdir("."):                      # remove old files
    if fn != kernelFile and fn != signFile:
        robust_layer.simple_fops.rm(fn)
with tarfile.open(kernelFile, mode="r:xz") as tarf:
    tarf.extractall(".")
