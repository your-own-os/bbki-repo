#!/usr/bin/python3

import os
import io
import re
import glob
import gzip
import time
import pathlib
import subprocess
import lxml.html
import urllib.request
import robust_layer


def update_linux_vanilla():
    myName = "linux/vanilla"
    selfDir = os.path.dirname(os.path.realpath(__file__))

    # get latest kernel version from internet
    kernelVersion = None
    if True:
        root = util.fetchAndParseHtmlPage("https://www.kernel.org")
        td = root.xpath(".//td[text()='%s:']" % ("stable"))[0]
        td = td.getnext()
        while len(td) > 0:
            td = td[0]
        kernelVersion = td.text

    # get remote file
    remoteFile = None
    while True:
        kernelUrl = "https://www.kernel.org/pub/linux/kernel"
        kernelFile = "linux-%s.tar.xz" % (kernelVersion)
        signFile = "linux-%s.tar.sign" % (kernelVersion)

        # try mirror file structure 1: all files placed under / (a simple structure suitable for local mirrors)
        good = True
        for fn in [kernelFile, signFile]:
            if not util.cmdCallTestSuccess("wget", "--spider", "%s/%s" % (kernelUrl, fn)):
                good = False
                break
        if good:
            remoteFile = os.path.join(kernelUrl, kernelFile)
            break

        # try mirror file structure 2: /{v3.x,v4.x,...}/* (an overly complicated structure used by official kernel mirrors)
        subdir = None
        for i in range(3, 9):
            if kernelVersion.startswith(str(i)):
                subdir = "v%d.x" % (i)
        assert subdir is not None

        good = True
        for fn in [kernelFile, signFile]:
            if not util.cmdCallTestSuccess("wget", "--spider", "%s/%s/%s" % (kernelUrl, subdir, fn)):
                good = False
                break
        if good:
            remoteFile = os.path.join(kernelUrl, subdir, kernelFile)
            break

        # invalid
        print("%s: Can not find remote file." % myName)
        return

    # rename bbki file
    targetFile = os.path.join(myName, "%s.bbki" % (kernelVersion))
    util.renameTo(os.path.join(selfDir, targetFile))

    # change SRC_URI
    util.sed(targetFile, "SRC_URI=.*", "SRC_URI=\"%s\"" % (remoteFile))

    # print result
    print("%s: %s updated." % (myName, targetFile))


class util:

    @staticmethod
    def fetchAndParseHtmlPage(myName, url):
        while True:
            try:
                with urllib.request.urlopen(url, timeout=robust_layer.TIMEOUT) as resp:
                    if resp.info().get('Content-Encoding') is None:
                        fakef = resp
                    elif resp.info().get('Content-Encoding') == 'gzip':
                        fakef = io.BytesIO(resp.read())
                        fakef = gzip.GzipFile(fileobj=fakef)
                    else:
                        assert False
                    return lxml.html.parse(fakef)
            except OSError as e:
                print("%s: Failed to acces %s, %s" % (myName, url, e))
                time.sleep(robust_layer.RETRY_TIMEOUT)

    @staticmethod
    def renameTo(targetFile):
        bFound = False
        for fullfn in glob.glob(os.path.join(os.path.dirname(targetFile), "*.bbki")):
            bFound = True
            if fullfn != targetFile:
                os.rename(fullfn, targetFile)
                return True
        assert bFound
        return False

    @staticmethod
    def cmdCallTestSuccess(cmd, *kargs):
        ret = subprocess.run([cmd] + list(kargs),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True)
        if ret.returncode > 128:
            time.sleep(1.0)
        return (ret.returncode == 0)

    @staticmethod
    def sed(fn, pattern, repl):
        buf = pathlib.Path(fn).read_text()
        buf = re.sub(pattern, repl, buf)
        with open(fn, "w") as f:
            f.write(buf)


if __name__ == "__main__":
    update_linux_vanilla()
