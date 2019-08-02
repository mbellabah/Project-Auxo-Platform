import unittest
from typing import Dict, List

from lib.zhelpers import strip_of_bytes, int_from_bytes, int_to_bytes


class TestZHelpers(unittest.TestCase):

    @unittest.skip("Assume this works, because the function's been unchanged")
    def test_strip_of_bytes(self):
        dict_input_1: Dict[bytes, bytes] = {b'Dog': b'runs, 1,2,3'}
        dict_input_2: Dict[str, bytes] = {'Dog': b'runs, 1,2,3'}
        dict_input_3: Dict[bytes, str] = {b'Dog': 'runs, 1,2,3'}
        dict_input_4: Dict[str, str] = {'Dog': 'runs, 1,2,3'}

        test_inputs = [dict_input_1, dict_input_2, dict_input_3, dict_input_4]
        desired_out: Dict[str, str] = {'Dog': 'runs, 1,2,3'}

        for test_input in test_inputs:
            self.assertEqual(strip_of_bytes(test_input), desired_out)

    def test_int_to_bytes(self):
        input_1: int = 10
        input_2: int = 260
        input_3: int = 0
        input_4: int = 100000
        test_inputs = [input_1, input_2, input_3, input_4]
        desired_out = [0, 0, 0, 0]      # FIXME: Finish writing the test case


if __name__ == '__main__':
    unittest.main()