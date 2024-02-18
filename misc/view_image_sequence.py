#!/usr/bin/env python3

import argparse
import os

import cv2


def view_images(folder):
    image_files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]

    if not image_files:
        print(f"Error: No PNG files found in the folder '{folder}'.")
        return

    for image_file in sorted(image_files):
        image_path = os.path.join(folder, image_file)
        img = cv2.imread(image_path)
        cv2.imshow('Image Stream', img)
        cv2.waitKey(1)

    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='View PNG images in a folder.')
    parser.add_argument('folder',
                        help='Path to the folder containing PNG images.')
    args = parser.parse_args()
    view_images(args.folder)


if __name__ == '__main__':
    main()
