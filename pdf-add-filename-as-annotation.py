#!/usr/bin/env python3

import sys, pathlib, subprocess
# https://github.com/plangrid/pdf-annotate
from pdf_annotate import PdfAnnotator, Location, Appearance, Metadata
from pdf_annotate.config.metadata import Flags

for fn in sys.argv[1:]:
	input_file = pathlib.Path(fn)
	assert input_file.exists(), input_file

	annotation_text = input_file.stem

	if input_file.suffix == ".pdf":
		output_file = input_file.parent / (input_file.stem + ".annotated.pdf")
		assert not output_file.exists(), output_file
	else:
		output_file = input_file.parent / (input_file.stem + ".pdf")
		assert not output_file.exists(), output_file
		subprocess.run(
			[
				# Imagemagick
				"convert", "-units", "PixelsPerInch", "-density", "72",
				input_file.as_posix(),
				output_file.as_posix(),
			],
			shell=False,
			check=True,
		)
		input_file = output_file


	top, left = 1 * 72, 6.5 * 72
	width, height = 3 * 72, 1 * 72

	annotator = PdfAnnotator(input_file.as_posix())
	annotator.add_annotation(
		annotation_type="text",
		location=Location(x1=left, y1=top, x2=(left + width), y2=(top + height), page=0),
		appearance=Appearance(
			content=annotation_text,
			fill=(0, 150/255.0, 255/255.0),
			font_size=24,
			stroke_width=1,
			line_spacing=1,
			text_align="left",
			text_baseline="bottom",
			# fonts="Helvetica"
		),
		metadata=Metadata(
			flags=Flags.Print | Flags.LockedContents | Flags.Locked | Flags.ReadOnly
		)
	)
	annotator.write(output_file.as_posix())
