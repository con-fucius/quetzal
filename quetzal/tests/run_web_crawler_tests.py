import unittest
import sys
import os
import traceback

# Print diagnostic information
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Script location: {__file__}")
print(f"sys.path: {sys.path}")

# Ensure the module can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)
print(f"Added to sys.path: {script_dir}")

# Check if test file exists
test_file_path = os.path.join(script_dir, 'tests', 'test_web_crawler.py')
print(f"Test file path: {test_file_path}")
print(f"Test file exists: {os.path.exists(test_file_path)}")

# List files in the tests directory
tests_dir = os.path.join(script_dir, 'tests')
if os.path.exists(tests_dir):
    print(f"Files in tests directory: {os.listdir(tests_dir)}")
else:
    print(f"Tests directory not found: {tests_dir}")

try:
    # Import the test module
    print("Attempting to import TestWebCrawler...")
    from tests.test_web_crawler import TestWebCrawler
    print("Successfully imported TestWebCrawler")
    
    def run_tests():
        print("Creating web crawler test suite")
        
        # Create a test suite with all tests from TestWebCrawler
        suite = unittest.TestSuite()
        for test_method in [
            'test_is_valid_url',
            'test_fetch_url',
            'test_extract_text',
            'test_extract_links',
            'test_crawl_url',
            'test_crawl_multiple_urls'
        ]:
            suite.addTest(TestWebCrawler(test_method))
        
        print("Running web crawler test suite")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        print("Tests completed")
        print(f"Ran {result.testsRun} tests")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for failure in result.failures:
                print(f"- {failure[0]}")
                print(f"  {failure[1]}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"- {error[0]}")
                print(f"  {error[1]}")
        
        return result

    if __name__ == "__main__":
        print("Starting web crawler tests...")
        with open("web_crawler_test_results.txt", "w") as f:
            # Save the original stdout
            original_stdout = sys.stdout
            # Redirect stdout to file
            sys.stdout = f
            try:
                result = run_tests()
            except Exception as e:
                print(f"Exception during test execution: {e}")
                traceback.print_exc(file=f)
            finally:
                # Restore stdout
                sys.stdout = original_stdout
        
        print("Web crawler tests completed. Check web_crawler_test_results.txt for details.")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc() 