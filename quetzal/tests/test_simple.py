import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Path:", sys.path)
print("Working directory:", __file__)

import unittest

class SimpleTest(unittest.TestCase):
    def test_simple(self):
        print("Running simple test")
        self.assertEqual(1, 1)

if __name__ == "__main__":
    print("Running unittest.main()")
    unittest.main() 