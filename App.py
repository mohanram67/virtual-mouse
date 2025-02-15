import os

# Check if the dist folder exists and list its contents
if os.path.isdir('dist'):
    files = os.listdir('dist')
    print('Files in the dist folder:')
    for file in files:
        print(file)
else:
    print('dist directory does not exist.')

print('done')