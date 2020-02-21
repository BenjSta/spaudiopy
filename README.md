# spaudiopy

Spatial Audio Python Package.

The focus (so far) is on spatial audio encoders and decoders.
The package includes e.g. spherical harmonics processing and (binaural renderings of) loudspeaker decoders, such as VBAP and AllRAD.

## Documentation

You can find the latest package documentation here:  
https://spaudiopy.readthedocs.io/

Some details about the implementation can be found in my [thesis](https://doi.org/10.13140/RG.2.2.11905.20323), or just contact me.

## Quickstart

It's easiest to start with something like [Anaconda](https://www.anaconda.com/distribution/) as a Python distribution.
You'll need Python >= 3.6 .

You can simply install via pip:  
  `pip install spaudiopy`

Or if you want to go into detail and install from source:

1. Create a conda environment, called e.g. 'spaudio':  
  `conda create --name spaudio python=3.6 anaconda joblib portaudio`
2. Activate this new environment:  
  `conda activate spaudio`
  
Get the latest source code from GitHub:
  `git clone https://github.com/chris-hld/spaudiopy.git && cd spaudiopy`

Install the package and remaining dependencies:  
  `pip install -e . ` 

## Contributions

This is meant to be an open project and contributions or feature requests are always welcome!

Some functions are also (heavily) inspired by other packages, e.g. https://github.com/polarch/Spherical-Harmonic-Transform, https://github.com/spatialaudio/sfa-numpy, https://github.com/AppliedAcousticsChalmers/sound_field_analysis-py .

## Licence

MIT -- see the file LICENSE for details.
