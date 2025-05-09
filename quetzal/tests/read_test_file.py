import os

test_file_path = os.path.join('tests', 'test_web_crawler.py')
print(f"Reading file: {test_file_path}")
print(f"File exists: {os.path.exists(test_file_path)}")
print(f"File size: {os.path.getsize(test_file_path)} bytes")

try:
    with open(test_file_path, 'r') as f:
        content = f.read()
        print(f"File content length: {len(content)} characters")
        print("First 50 characters:")
        print(content[:50])
        
        # Save content to a new file
        with open('test_file_content.txt', 'w') as out_f:
            out_f.write(content)
        print("Content saved to test_file_content.txt")
except Exception as e:
    print(f"Error reading file: {e}") 