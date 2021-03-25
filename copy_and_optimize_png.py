import os
import shutil
import subprocess
import sys

from PIL import Image, ImageChops
from pathlib import Path


class CopyingReport:
	def __init__(self):
		self.dst_update = 0
		self.new_file = 0
		self.same_content = 0

	def validate(self, expected_count):
		return expected_count == (self.dst_update + self.new_file + self.same_content)


# https://github.com/shssoichiro/oxipng
def oxipng(path):
	subprocess.run(['oxipng', '-o', '4', '--strip', 'safe', path])


# https://github.com/fhanau/Efficient-Compression-Tool
def ect(path):
	subprocess.run(['ect', '-9', path])


# See https://stackoverflow.com/questions/35176639/compare-images-python-pil/56280735
def images_are_same(src_path, dst_path) -> bool:
	# Note: PIL will silently fail if mode is RGBA, so covert to RGB image before processing
	# TODO: support proper alpha channel comparison
	src_image = Image.open(src_path).convert('RGB')
	dst_image = Image.open(dst_path).convert('RGB')

	diff = ImageChops.difference(src_image, dst_image)

	return diff.getbbox() == None


def image_needs_update(src_path, dst_path, report: CopyingReport) -> bool:
	if not os.path.exists(dst_path):
		print(f"  > Warning: new file detected {src_path} as no file at {dst_path}")
		report.new_file += 1
		return True
	elif not images_are_same(src_path, dst_path):
		print("  > Image is different - copying and optimizing with ect")
		report.dst_update += 1
		return True
	else:
		report.same_content += 1
		return False


def main(src_folder, dst_folder):
	src_paths = list(Path(src_folder).rglob('**/*.png'))

	copying_report = CopyingReport()
	for src_path in src_paths:
		src_rel_path = os.path.relpath(src_path, src_folder)
		dst_path = os.path.join(dst_folder, src_rel_path)

		print(f"Processing [{src_rel_path}]")
		if image_needs_update(src_path, dst_path, copying_report):
			Path(os.path.dirname(dst_path)).mkdir(parents=True, exist_ok=True)
			shutil.copyfile(src_path, dst_path)
			ect(dst_path)

	print(f"Got {len(src_paths)} src images")
	print(f"Updated: {copying_report.dst_update}")
	print(f"New    : {copying_report.new_file}")
	print(f"Same   : {copying_report.same_content}")

	if not copying_report.validate(len(src_paths)):
		raise Exception("ERROR: number of files processed doesn't match expected num files!")


if __name__ == '__main__':
	print("Warning: this script does not properly support images with alpha - will convert to RGB image first.")

	if len(sys.argv) < 3:
		print("Need 2 arguments: python copy_and_optimize_png [src_folder] [dst_folder]")
		raise SystemExit(-1)

	src_folder = sys.argv[1]
	dst_folder = sys.argv[2]

	if not os.path.exists(src_folder):
		print(f"Error: Source folder \"{src_folder}\" does not exist!")
		raise SystemExit(-2)

	if not os.path.exists(src_folder):
		print(f"Warning: Destination folder \"{src_folder}\" does not exist! It will be created.")

	print(f"Updating [{src_folder}] -> [{dst_folder}]")
	main(src_folder, dst_folder)
