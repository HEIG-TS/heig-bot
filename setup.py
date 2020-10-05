import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="heig-bot", # Replace with your own username
    version="0.4.0",
    author="Gabriel Roch",
    author_email="gabriel.roch@heig-vd.ch",
    description="A telegram bot for access to GAPS website",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HEIG-TS/heig-bot",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
