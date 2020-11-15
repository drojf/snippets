import os
import subprocess
import sys
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"

def call(args, **kwargs):
	print("running: {}".format(args))
	retcode = subprocess.call(args, shell=IS_WINDOWS, **kwargs) # use shell on windows
	if retcode != 0:
		exit(retcode)

#when calling this function, use named arguments to avoid confusion!
def aria(downloadDir=None, inputFile=None, url=None, followMetaLink=False, useIPV6=False, outputFile=None):
	"""
	Calls aria2c with some default arguments:

	Note about continuing downloads/control file save frequency
	By default, aria2c saves the control file every 60s, or when aria2c is closed non-forcefully.
	This means that if you close aria2c forcefully, you will lose up to the last 1 minute of download.
	This value can be changed with --auto-save-interval=<SEC>, but we have left it as the default here.

	:param downloadDir: The directory to store the downloaded file(s)
	:param inputFile: The path to a file containing multiple URLS to download (see aria2c documentation)
	:param outputFile: When downloading a single file, if this is specified, it will be downloaded with the given name
	:return Returns the exit code of the aria2c call
	"""
	arguments = [
		"aria2c",
		"--file-allocation=none", # Pre-allocate space where the downloaded file will be saved
		'--continue=true', # Allow continuing the download of a partially downloaded file (is this flag actually necessary?)
		'--retry-wait=5',  # Seconds to wait between retries
		'-m 0', # max number of retries (0=unlimited). In some cases, like server rejects download, aria2c won't retry.
		'-x 8', # max connections to the same server
		'-s 8', # Split - Try to use N connections per each download item
		'-j 1', # max concurrent download items (eg number of separate urls which can be downloaded in parallel)
		'--auto-file-renaming=false',
		# By default, if aria2c detects a file already exists with the same name, and is different size to the file
		# being downloaded (lets call this 'test.zip'), it will save to a different name ('test.2.zip', 'test.3.zip' etc)
		# This option prevents this from happening. Continuing existing downloads where the file size is the same is still supported.
		'--allow-overwrite=true',
		# By default, aria2c will just error out if auto-renaming is disabled. Enabling this option allows aria2c to overwrite existing files,
		# if they cannot be continued (by the --continue argument)
	]

	if followMetaLink:
		arguments.append('--follow-metalink=mem')
		arguments.append('--check-integrity=true')  # check integrity when using metalink
	else:
		arguments.append('--follow-metalink=false')

	if not useIPV6:
		arguments.append('--disable-ipv6=true')

	#Add an extra command line argument if the function argument has been provided
	if downloadDir:
		arguments.append('-d ' + downloadDir)

	if inputFile:
		arguments.append('--input-file=' + inputFile)

	if url:
		arguments.append(url)

	if outputFile:
		arguments.append("--out=" + outputFile)

	return call(arguments)

def try_remove_tree(path):
	try:
		if os.path.isdir(path):
			shutil.rmtree(path)
		else:
			os.remove(path)
	except FileNotFoundError:
		pass


def try_remove_tree_repeat_attempt(folder_to_remove, num_attempts=5):
	last_exception = None
	for attempt in range(num_attempts):
		print(f'Attempt {attempt} to remove {folder_to_remove}')
		try:
			try_remove_tree(folder_to_remove)
			return
		except Exception as e:
			last_exception = e
			traceback.print_exc()
			time.sleep(1)

	raise last_exception


# Long options: 7z a -m0=lzma2 -mmt=3 -mx=9 -mfb=64 -md=256m -ms=on out.7z HigurashiEp04_Data
# Short options: 7z a -m0=lzma2 -mx=9 -md=256m -mmt=3 out.7z HigurashiEp04_Data
def archive(input_path, output_filename):
	try_remove_tree(output_filename)
	call(["7z", "a",
		  "-mx=9",     # max compression level
		  "-md=256m",  # 256m dictionary size (memory used for compression is much higher than this)
		  "-mmt=3",    # use 3 threads (using > 3 threads results in increased archive size)
		  output_filename, input_path])

def extract(input_path, output_folder):
	call(["7z", "x",
		  f"-o{output_folder}",
		  input_path])

temp_dir = "python_repack_dir"
python_extract_dir = os.path.join(temp_dir, "python")
url = "https://www.python.org/ftp/python/3.7.7/python-3.7.7-embed-win32.zip"
filename = url.split("/")[-1]
filepath = os.path.join(temp_dir, filename)

# Ensure temp dir exists
Path(temp_dir).mkdir(exist_ok=True)

# Download the file
aria(temp_dir, url="https://www.python.org/ftp/python/3.7.7/python-3.7.7-embed-win32.zip")

# Extract the file
extract(filepath, python_extract_dir)

# Delete the file
# try_remove_tree_repeat_attempt(filepath)

# Re-compress the file
archive(python_extract_dir, "python_archive.7z")
