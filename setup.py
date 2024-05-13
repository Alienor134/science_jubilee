import setuptools

setuptools.setup(
    name="science_jubilee",
    version="0.1.0",
    author="Machine Agency, Pozzo Research Group",
    author_email="b1air@uw.edu, politim@uw.edu, bgpelkie@uw.edu",

    description="Make science with Jubilee",
    long_description= open('README.md', 'r', encoding = 'utf-8').read(),
    long_description_content_type='text/markdown; charset=UTF-8; variant=GFM',
    url="https://github.com/machineagency/science_jubilee",
    license="MIT",
    keywords= ['jubilee', 'science'],
    include_package_data=True,
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=['pyserial==3.5',
                       'requests',
                       'ipykernel',
                       'numpy',
                       'opencv_contrib_python==4.5.3.56',
                       'matplotlib',
                       'Jinja2',
                       'sphinx',
                       'sphinx-design',
                       'pydata_sphinx_theme',
                       'sphinx-autoapi',
                       "picamera;platform_machine=='aarch64'",
                       'adafruit-mcp4725',
                       'Adafruit-Blinka',
                       ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)