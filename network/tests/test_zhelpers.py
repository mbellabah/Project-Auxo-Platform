import unittest
from typing import Dict, List

from lib.zhelpers import strip_of_bytes


class TestZHelpers(unittest.TestCase):

    def test_strip_of_bytes(self):
        dict_input_1: Dict[bytes, bytes] = {b'Dog': b'runs, 1,2,3'}
        dict_input_2: Dict[str, bytes] = {'Dog': b'runs, 1,2,3'}
        dict_input_3: Dict[bytes, str] = {b'Dog': 'runs, 1,2,3'}
        dict_input_4: Dict[str, str] = {'Dog': 'runs, 1,2,3'}

        test_inputs = [dict_input_1, dict_input_2, dict_input_3, dict_input_4]
        desired_out: Dict[str, str] = {'Dog': 'runs, 1,2,3'}

        for test_input in test_inputs:
            self.assertEqual(strip_of_bytes(test_input), desired_out)


if __name__ == '__main__':
    unittest.main()