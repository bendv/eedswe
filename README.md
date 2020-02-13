DSWE on the GEE
===============

Apply the Dynamic Surface Water Extent (DSWE) v1 algorithm (Jones, 2015) to Landsat-5 and Landsat-7 ImageCollections on the Google Earth Engine.

Installation
------------

First, install the earthengine API: https://developers.google.com/earth-engine/python_install_manual.

When you have sorted your authentication token out, install `eedswe`:
```bash
git clone https://github.com/bendv/eedswe
cd eedswe
pip install .
```

Algorithm description
---------------------
https://www.usgs.gov/media/files/landsat-dynamic-surface-water-extent-add

Reference
---------
Jones, J. W. (2015). Efficient wetland surface water detection and monitoring via Landsat: 
    Comparison with in situ data from the Everglades Depth Estimation Network. 
    Remote Sensing, 7(9), 12503-12538. http://dx.doi.org/10.3390/rs70912503.

