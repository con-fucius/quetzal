import unittest
import sys

# Print diagnostic info
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Working directory:", __file__)

# Define a simple test case
class SimpleTest(unittest.TestCase):
    def setUp(self):
        print("Test setup")
    
    def test_simple(self):
        print("Running simple test")
        self.assertEqual(1, 1)
        
    def test_another(self):
        print("Running another test")
        self.assertTrue(True)

# Manually create and run a test suite
def run_tests():
    print("Creating test suite")
    suite = unittest.TestSuite()
    suite.addTest(SimpleTest("test_simple"))
    suite.addTest(SimpleTest("test_another"))
    
    print("Running test suite")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("Tests completed")
    print(f"Ran {result.testsRun} tests")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    return result

if __name__ == "__main__":
    print("Starting direct test...")
    with open("test_results.txt", "w") as f:
        sys.stdout = f
        result = run_tests()
        sys.stdout = sys.__stdout__
    
    print("Tests completed. Check test_results.txt for details.") 