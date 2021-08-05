#!/usr/bin/python3

import os
import io
import glob
import gzip
import time
import subprocess
import lxml.html
import urllib.request
import robust_layer


def update_linux_vanilla():
    selfDir = os.path.dirname(os.path.realpath(__file__))
    kernelUrl = "https://www.kernel.org"
    typename = "stable"

    # get latest kernel version from internet
    kernelVersion = None
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
                kernelVersion = td.text
                break
        except OSError as e:
            print("Failed to acces %s, %s" % (kernelUrl, e))
            time.sleep(robust_layer.RETRY_TIMEOUT)

    # get remote file
    remoteFile = None
    while True:
        # we support two mirror file structure:
        # 1. all files placed under /: a simple structure suitable for local mirrors
        # 2. /{v3.x,v4.x,...}/*:       an overly complicated structure used by official kernel mirrors

        kernelFile = "linux-%s.tar.xz" % kernelVersion
        signFile = "linux-%s.tar.sign" % kernelVersion

        # try file structure 1
        good = True
        for fn in (kernelFile, signFile):
            if not util.cmdCallTestSuccess("/usr/bin/wget", "--spider", "%s/%s" % (kernelUrl, fn)):
                good = False
                break
        if good:
            remoteFile = os.path.join(kernelUrl, kernelFile)
            break

        # try file structure 2
        subdir = None
        for i in range(3, 9):
            if kernelVersion.startswith(str(i)):
                subdir = "v%d.x" % (i)
        assert subdir is not None

        good = True
        for fn in (kernelFile, signFile):
            if not util.cmdCallTestSuccess("/usr/bin/wget", "--spider", "%s/%s/%s" % (kernelUrl, subdir, fn)):
                good = False
                break
        if good:
            remoteFile = os.path.join(kernelUrl, subdir, kernelFile)
            break

        # invalid
        assert False

    # rename bbki file
    targetFile = os.path.join(selfDir, "linux", "vanilla", "%s.bbki" % (kernelVersion))
    util.renameTo(targetFile)

    # change SRC_URI
    subprocess.run(["sed", "-i", r's/SRC_URI=.*/SRC_URI="' + remoteFile + r'"/g', targetFile])


class util:

    @staticmethod
    def renameTo(targetFile):
        bFound = False
        for fullfn in glob.glob(os.path.join(os.path.dirname(targetFile), "*.bbki")):
            bFound = True
            if fullfn != targetFile:
                os.rename(fullfn, targetFile)
                break
        assert bFound

    @staticmethod
    def cmdCallTestSuccess(cmd, *kargs):
        ret = subprocess.run([cmd] + list(kargs),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True)
        if ret.returncode > 128:
            time.sleep(1.0)
        return (ret.returncode == 0)


if __name__ == "__main__":
    update_linux_vanilla()
