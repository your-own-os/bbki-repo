#!/usr/bin/python3

import os
import io
import gzip
import time
import tarfile
import subprocess
import lxml.html
import urllib.request
import robust_layer.wget
import robust_layer.simple_git
import robust_layer.simple_fops


def _cmdCallTestSuccess(cmd, *kargs):
    ret = subprocess.run([cmd] + list(kargs),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True)
    if ret.returncode > 128:
        time.sleep(1.0)
    return (ret.returncode == 0)


def _getRemoteFiles(kernelUrl, kernelVersion, kernelFile, signFile):
    # we support two mirror file structure:
    # 1. all files placed under /: a simple structure suitable for local mirrors
    # 2. /{v3.x,v4.x,...}/*:       an overly complicated structure used by official kernel mirrors

    # try file structure 1
    good = True
    for fn in (kernelFile, signFile):
        if not _cmdCallTestSuccess("/usr/bin/wget", "--spider", "%s/%s" % (kernelUrl, fn)):
            good = False
            break
    if good:
        return (kernelFile, signFile)

    # try file structure 2
    subdir = None
    for i in range(3, 9):
        if kernelVersion.startswith(str(i)):
            subdir = "v%d.x" % (i)
    assert subdir is not None

    good = True
    for fn in (kernelFile, signFile):
        if not _cmdCallTestSuccess("/usr/bin/wget", "--spider", "%s/%s/%s" % (kernelUrl, subdir, fn)):
            good = False
            break
    if good:
        return (os.path.join(subdir, kernelFile), os.path.join(subdir, signFile))

    # invalid
    assert False


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
