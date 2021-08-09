import setuptools

with open('requirements.txt') as f:
    install_requires = f.readlines()

setuptools.setup(
    name="aurum-datadiscovery", # Replace with your own username
    version="0.0.1",
    author="Example Author",
    author_email="author@example.com",
    description="aurum dod (short) description",
    install_requires=install_requires,
    long_description="aurum dod long description",
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    project_urls={
        "Bug Tracker": "https://github.com/pypa/sampleproject/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    py_modules=["algebra", "config", "server_config"],
    python_requires=">=3.6",
)
