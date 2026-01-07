# Copyright (C) 2022 National Institute of Informatics
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import copy
"""#if sinetstream-python
import zlib
"""#if sinetstream-upython
import deflate
#endif
from io import BytesIO

"""#if sinetstream-python
import zstandard as zstd
"""#endif

from sinetstream.spi import PluginCompression
from sinetstream.utils import Registry


GZIP = "gzip"
"""#if sinetstream-python
ZSTD = "zstd"
"""#endif
compression_registry = Registry('sinetstream.compression', PluginCompression)


class GzipCompression:
    def __init__(self, level=None, params=None):
        if params is None:
            params = {}
        self._level = level
        self._params = params

    def compress(self, data, params):
        """#if sinetstream-python
        cctx = zlib.compressobj(**params)
        return cctx.compress(data) + cctx.flush()
        """#if sinetstream-upython
        bs = BytesIO()
        with deflate.DeflateIO(bs, deflate.ZLIB) as dflt:
            dflt.write(data)
        return bs.getvalue()
        #endif

    @property
    def compressor(self):
        params = copy.deepcopy(self._params)
        if self._level is not None and "level" not in params:
            params["level"] = self._level
        return lambda data: self.compress(data, params)

    def decompress(self, data, params):
        """#if sinetstream-python
        dctx = zlib.decompressobj(**params)
        return dctx.decompress(data) + dctx.flush()
        """#if sinetstream-upython
        with deflate.DeflateIO(BytesIO(data), deflate.ZLIB) as dflt:
            return dflt.read()
        #endif

    @property
    def decompressor(self):
        return lambda data: self.decompress(data, self._params)


"""#if sinetstream-python
class ZstdCompression:
    def __init__(self, level=None, params=None):
        if params is None:
            params = {}
        self._level = level
        self._params = params

    @property
    def compressor(self):
        params = copy.deepcopy(self._params)
        if self._level is not None and "level" not in params:
            params["level"] = self._level
        cctx = zstd.ZstdCompressor(**params)
        return cctx.compress  # = lambda data: cctx.compress(data)

    @property
    def decompressor(self):
        dctx = zstd.ZstdDecompressor(**self._params)
        return lambda data: ZstdCompression._decompress(dctx, data)

    @staticmethod
    def _decompress(dctx, data):
        # import sys
        # print(f"XXX:decomp:data={ZstdCompression._zstd_dump(data)}", file=sys.stderr)
        content_size = zstd.get_frame_parameters(data).content_size
        if content_size >= 0 and content_size < ((1 << 64) - 1):
            return dctx.decompress(data)
        else:
            ifh = BytesIO(data)
            ofh = BytesIO()
            dctx.copy_stream(ifh, ofh)
            return ofh.getvalue()

    @staticmethod
    def _zstd_dump(data):
        frame_params = zstd.get_frame_parameters(data)
        return (   "FrameParameters{"
                + f"content_size={frame_params.content_size}(0x{frame_params.content_size:x})"
                + f",window_size={frame_params.window_size}(0x{frame_params.window_size:x})"
                + f",dict_id={frame_params.dict_id}"
                + f",has_checksum={frame_params.has_checksum}"
                + "}")
"""#endif

class GzipCompressionEntryPoint:
    @classmethod
    def load(cls):
        return GzipCompression


"""#if sinetstream-python
class ZstdCompressionEntryPoint:
    @classmethod
    def load(cls):
        return ZstdCompression
"""#endif


compression_registry.register(GZIP, GzipCompressionEntryPoint)
"""#if sinetstream-python
compression_registry.register(ZSTD, ZstdCompressionEntryPoint)
"""#endif
