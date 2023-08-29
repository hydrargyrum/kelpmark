# KelpMark

KelpMark helps creating watermarks on images or PDFs.

## Example

Suppose you have your passport: ![sample passport](https://github.com/hydrargyrum/kelpmark/blob/main/kelpmark_before.jpg?raw=true)

And need to send it to some company, but don't trust them because they might have security breaches and might leak your data.
So you want to watermark it to make it harder to reuse in case of data leak.

![kelpmark screenshot](https://github.com/hydrargyrum/kelpmark/blob/main/kelpmark_screenshot.jpg?raw=true)

Then you can save the resulting image/PDF: ![watermarked passport](https://github.com/hydrargyrum/kelpmark/blob/main/kelpmark_after.jpg?raw=true)

## Features

- Import multiple images at once
- Import multi-page PDF
- Export to single image
- Export to multi-page PDF
- Watermark text tiling
- Various graphical features

## Requirements

- PyQt5
- python-poppler-qt5

[requirements.txt](requirements.txt)

## Install

[`pipx install KelpMark`](https://pypi.org/project/KelpMark/)

## License

KelpMark is licensed under the [Unlicense](UNLICENSE).

