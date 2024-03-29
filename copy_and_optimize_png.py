import os
import shutil
import subprocess
import sys

from PIL import Image, ImageChops
from pathlib import Path

# These formats must be both openable by PIL and optimizeable by ect
optimizable_formats = ['.png', '.jpg', '.jpeg']

class CopyingReport:
	def __init__(self):
		self.dst_update = 0
		self.new_file = 0
		self.same_content = 0
		self.non_optimizeable = 0

	def validate(self, expected_count):
		return expected_count == (self.dst_update + self.new_file + self.same_content + self.non_optimizeable)


# https://github.com/shssoichiro/oxipng
def oxipng(path):
	subprocess.run(['oxipng', '-o', '4', '--strip', 'safe', path])


# https://github.com/fhanau/Efficient-Compression-Tool
def ect(path):
	subprocess.run(['ect', '-9', path])

# Overlay the input image on a background with R, G, B all set to background_value
def composite_image_on_background_as_RGB(img_any_format: Image, background_value: int):
	img = img_any_format.convert('RGBA')
	background = Image.new('RGBA', img.size, (background_value, background_value, background_value))

	return Image.alpha_composite(background, img).convert('RGB')

# Check if two images are identical when alpha composited over the same background
# The background will have R, G, B all set to background_value
def images_same_on_background(src_image, dst_image, background_value):
	src_image = composite_image_on_background_as_RGB(src_image, background_value)
	dst_image = composite_image_on_background_as_RGB(dst_image, background_value)

	diff = ImageChops.difference(src_image, dst_image)

	return diff.getbbox() == None

# If the image has an alpha channel, we only care about the non-zero alpha pixels
# Overlaying the image on a solid background before comparison achieves this effect
#
# Need to use two different backgrounds in case there is part of the image with
# exactly the same color as the background
#
# See https://stackoverflow.com/questions/35176639/compare-images-python-pil/56280735
# See https://stackoverflow.com/a/33507138/848627
def images_are_same(src_path, dst_path) -> bool:
	src_image = Image.open(src_path)
	dst_image = Image.open(dst_path)

	if not images_same_on_background(src_image, dst_image, 0):
		return False

	if not images_same_on_background(src_image, dst_image, 255):
		return False

	return True

# Returns a tuple of (needs_copy, needs_optimize)
def image_needs_update(src_path: Path, dst_path, report: CopyingReport) -> bool:
	if src_path.suffix.lower() not in optimizable_formats:
		print(f"  > Warning: detected non-optmizable/non-comparable file {src_path} - will overwrite {dst_path} even if same")
		report.non_optimizeable += 1
		return True, False
	elif not os.path.exists(dst_path):
		print(f"  > Warning: new file detected {src_path} as no file at {dst_path}")
		report.new_file += 1
		return True, True
	elif not images_are_same(src_path, dst_path):
		print("  > Image is different - copying and optimizing with ect")
		report.dst_update += 1
		return True, True
	else:
		report.same_content += 1
		return False, False


def main(src_folder, dst_folder):
	src_paths = list(Path(src_folder).rglob('**/*.*'))

	copying_report = CopyingReport()
	for i, src_path in enumerate(src_paths):
		src_rel_path = os.path.relpath(src_path, src_folder)
		dst_path = os.path.join(dst_folder, src_rel_path)

		print(f"Processing {i}/{len(src_paths)} [{src_rel_path}]")
		need_copy, need_optimize = image_needs_update(src_path, dst_path, copying_report)
		if need_copy:
			Path(os.path.dirname(dst_path)).mkdir(parents=True, exist_ok=True)
			shutil.copyfile(src_path, dst_path)

			if need_optimize:
				ect(dst_path)

	print(f"Got {len(src_paths)} src images")
	print(f"Updated: {copying_report.dst_update}")
	print(f"New    : {copying_report.new_file}")
	print(f"Same   : {copying_report.same_content}")
	print(f"No Opt : {copying_report.non_optimizeable}")

	if not copying_report.validate(len(src_paths)):
		raise Exception("ERROR: number of files processed doesn't match expected num files!")


if __name__ == '__main__':
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
