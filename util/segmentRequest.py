# * This is an implementation of FLiDASH.
# * Copyright (C) 2019  Abhijit Mondal
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <http://www.gnu.org/licenses/>.




class SegmentRequest():
    def __init__(self, qualityIndex, downloadStarted, downloadFinished, segmentDuration, segId, clen, downloader, extraData = None):
        self._qualityIndex = qualityIndex
        self._downloadStarted = downloadStarted
        self._downloadFinished = downloadFinished
        self._segmentDuration = segmentDuration
        self._segId = segId
        self._clen = clen
        self._downloader = downloader
        self._extraData = extraData
        self._syncSeg = False

    @property
    def syncSeg(self):
        return self._syncSeg

    @syncSeg.setter
    def syncSeg(self, p):
        self._syncSeg = p

    @property
    def extraData(self):
        return self._extraData

    @property
    def qualityIndex(self):
        return self._qualityIndex

    @property
    def downloadStarted(self):
        return self._downloadStarted

    @property
    def downloadFinished(self):
        return self._downloadFinished

    @property
    def segmentDuration(self):
        return self._segmentDuration

    @property
    def segId(self):
        return self._segId

    @property
    def clen(self):
        return self._clen

    @property
    def downloader(self):
        return self._downloader

    @property
    def timetaken(self):
        return self.downloadFinished - self.downloadStarted

    @property
    def throughput(self):
        return self.clen*8.0/self.timetaken

