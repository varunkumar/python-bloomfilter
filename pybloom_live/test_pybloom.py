from __future__ import absolute_import
from pybloom_live.pybloom import (BloomFilter, ScalableBloomFilter,
                                  make_hashfuncs)
from pybloom_live.utils import running_python_3, range_fn

try:
    from StringIO import StringIO
    import cStringIO
except ImportError:
    from io import BytesIO as StringIO

from io import BytesIO

import unittest
import random
import tempfile


class TestMakeHashFuncs(unittest.TestCase):
    def test_make_hashfuncs_returns_hashfn(self):
        make_hashes, hashfn = make_hashfuncs(100, 20)
        self.assertEquals('openssl_sha512', hashfn.__name__)
        make_hashes, hashfn = make_hashfuncs(20, 3)
        self.assertEquals('openssl_sha384', hashfn.__name__)
        make_hashes, hashfn = make_hashfuncs(15, 2)
        self.assertEquals('openssl_sha256', hashfn.__name__)
        make_hashes, hashfn = make_hashfuncs(10, 2)
        self.assertEquals('openssl_sha1', hashfn.__name__)
        make_hashes, hashfn = make_hashfuncs(5, 1)
        self.assertEquals('openssl_md5', hashfn.__name__)


class TestUnionIntersection(unittest.TestCase):
    def test_union(self):
        bloom_one = BloomFilter(100, 0.001)
        bloom_two = BloomFilter(100, 0.001)
        chars = [chr(i) for i in range_fn(97, 123)]
        for char in chars[int(len(chars)/2):]:
            bloom_one.add(char)
        for char in chars[:int(len(chars)/2)]:
            bloom_two.add(char)
        new_bloom = bloom_one.union(bloom_two)
        for char in chars:
            self.assertTrue(char in new_bloom)

    def test_intersection(self):
        bloom_one = BloomFilter(100, 0.001)
        bloom_two = BloomFilter(100, 0.001)
        chars = [chr(i) for i in range_fn(97, 123)]
        for char in chars:
            bloom_one.add(char)
        for char in chars[:int(len(chars)/2)]:
            bloom_two.add(char)
        new_bloom = bloom_one.intersection(bloom_two)
        for char in chars[:int(len(chars)/2)]:
            self.assertTrue(char in new_bloom)
        for char in chars[int(len(chars)/2):]:
            self.assertTrue(char not in new_bloom)

    def test_intersection_capacity_fail(self):
        bloom_one = BloomFilter(1000, 0.001)
        bloom_two = BloomFilter(100, 0.001)
        def _run():
            bloom_one.intersection(bloom_two)
        self.assertRaises(ValueError, _run)

    def test_union_capacity_fail(self):
        bloom_one = BloomFilter(1000, 0.001)
        bloom_two = BloomFilter(100, 0.001)
        def _run():
            bloom_one.union(bloom_two)
        self.assertRaises(ValueError, _run)

    def test_intersection_k_fail(self):
        bloom_one = BloomFilter(100, 0.001)
        bloom_two = BloomFilter(100, 0.01)
        def _run():
            bloom_one.intersection(bloom_two)
        self.assertRaises(ValueError, _run)

    def test_union_k_fail(self):
        bloom_one = BloomFilter(100, 0.01)
        bloom_two = BloomFilter(100, 0.001)
        def _run():
            bloom_one.union(bloom_two)
        self.assertRaises(ValueError, _run)

    def test_union_scalable_bloom_filter(self):
        bloom_one = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
        bloom_two = ScalableBloomFilter(mode=ScalableBloomFilter.SMALL_SET_GROWTH)
        numbers = [i for i in range_fn(1, 10000)]
        middle = int(len(numbers) / 2)
        for number in numbers[middle:]:
            bloom_one.add(number)
        for number in numbers[:middle]:
            bloom_two.add(number)
        new_bloom = bloom_one.union(bloom_two)
        for number in numbers:
            self.assertTrue(number in new_bloom)

class Serialization(unittest.TestCase):
    SIZE = 12345
    EXPECTED = set([random.randint(0, 10000100) for _ in range_fn(0, SIZE)])

    def test_serialization(self):
        for klass, args in [(BloomFilter, (self.SIZE,)),
                            (ScalableBloomFilter, ())]:
            filter = klass(*args)
            for item in self.EXPECTED:
                filter.add(item)

            f = tempfile.TemporaryFile()
            filter.tofile(f)
            stringio = StringIO()
            filter.tofile(stringio)
            streams_to_test = [f, stringio]
            if not running_python_3:
                cstringio = cStringIO.StringIO()
                filter.tofile(cstringio)
                streams_to_test.append(cstringio)

            del filter

            for stream in streams_to_test:
                stream.seek(0)
                filter = klass.fromfile(stream)
                for item in self.EXPECTED:
                    self.assertTrue(item in filter)
                del(filter)
                stream.close()

    def test_bytes_io(self):
        filter = BloomFilter(self.SIZE)
        for item in self.EXPECTED:
            filter.add(item)

        stream = BytesIO()
        filter.tofile(stream)
        del filter
        stream.seek(0)
        filter = BloomFilter.fromfile(stream)
        for item in self.EXPECTED:
            assert item in filter


if __name__ == '__main__':
    unittest.main()
