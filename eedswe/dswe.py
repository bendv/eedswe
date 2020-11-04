'''
DSWE v1
=======

author: Ben DeVries
email:  bdv@uoguelph.ca

Algorithm description
---------------------
https://www.usgs.gov/media/files/landsat-dynamic-surface-water-extent-add

Reference
--------
Jones, J. W. (2015). Efficient wetland surface water detection and monitoring via Landsat: 
    Comparison with in situ data from the Everglades Depth Estimation Network. 
    Remote Sensing, 7(9), 12503-12538. http://dx.doi.org/10.3390/rs70912503.
'''

import ee


def _renameBands(x):
    bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'pixel_qa']
    new_bands = ['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2', 'pixel_qa']
    return x.select(bands).rename(new_bands)

def _createCloudAndShadowBand(x):
    qa = x.select('pixel_qa');
    cloudBitMask = ee.Number(2).pow(5).int();
    cloudShadowBitMask = ee.Number(2).pow(3).int();
    cloud = qa.bitwiseAnd(cloudBitMask).neq(0);
    cloudShadow = qa.bitwiseAnd(cloudShadowBitMask).neq(0);
    mask = ee.Image(0).where(cloud.eq(1), 1) \
        .where(cloudShadow.eq(1), 1)\
        .rename('cloud_mask');
    return x.addBands(mask)


def dswe(image):
    '''
    DSWE
    ====

    Apply DSWE algorithm to a single image

    Arguments:
    ----------
    image:  ee.Image object (must be Landsat-5 or Landsat-7)
    '''
    if not image.get('SATELLITE').getInfo() in ['LANDSAT_5', 'LANDSAT_7']:
        raise ValueError("This function is only available for Landsat 5 and 7")

    img = _createCloudAndShadowBand( _renameBands(image) )
    indices = calc_indices(img)
    tests = addTests(indices)
    dswe = ee.Image(-1) \
        .where(isDSWE0(tests), 0) \
        .where(isDSWE1(tests), 1) \
        .where(isDSWE2(tests), 2) \
        .where(isDSWE3(tests), 3) \
        .where(isDSWE9(tests), 9) \
        .updateMask(image.select('pixel_qa').mask()) \
        .rename("DSWE")

    return dswe
    

def cdswe(bounds = None, filters = None):
    '''
    Composite DSWE
    ==============

    Generates a temporal DSWE composite by computing Landsat-5 and Landsat-7 DSWE probabilies for a given time frame and geographical region.

    Arguments:
    ----------
    bounds:  List indicating bounds --> [xmin, ymin, xmax, ymax] (Default: None)
    filters: List of additional ee.Filter objects to apply to input Landsat data (Default: None)
    '''

    tm = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR');
    etm = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR');  

    if bounds is not None:
        xmin, ymin, xmax, ymax = bounds
        poly = ee.Geometry.Polygon(((xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)))
        tm = tm.filterBounds(poly)
        etm = etm.filterBounds(poly)

    if filters is not None:
        tm = tm.filter(filters)
        etm = etm.filter(filters)

    landsat = ee.ImageCollection(tm.merge(etm).sort('system:time_start')) \
        .map(_renameBands) \
        .map(_createCloudAndShadowBand)

    indices = landsat.map(calc_indices)

    tests = indices.map(addTests)

    dswe0 = tests.map(isDSWE0)
    dswe1 = tests.map(isDSWE1)
    dswe2 = tests.map(isDSWE2)
    dswe3 = tests.map(isDSWE3)
    dswe9 = tests.map(isDSWE9)

    # CLASS PROBABILITIES
    csp = tests.count().subtract(dswe9.sum());
    pdswe0 = dswe0.sum().divide(csp).multiply(100).toUint8()
    pdswe1 = dswe1.sum().divide(csp).multiply(100).toUint8()
    pdswe2 = dswe2.sum().divide(csp).multiply(100).toUint8()
    pdswe3 = dswe3.sum().divide(csp).multiply(100).toUint8()

    return ee.Image([pdswe0, pdswe1, pdswe2, pdswe3]) \
        .rename(['pDSWE0', 'pDSWE1', 'pDSWE2', 'pDSWE3'])






# INDICES
def calc_mndwi(image):
    mndwi = ee.Image(0).expression(
        '((g - swir1)/(g + swir1)) * 10000',
            {
                'g': image.select("G"),
                'swir1': image.select("SWIR1")
            })
    return mndwi.toInt16().rename("MNDWI")

def calc_mbsr(image):
    mbsr = ee.Image(0).expression(
        '(g + r) - (nir + swir1)',
        {
            'g': image.select("G"),
            'r': image.select("R"),
            'nir': image.select("NIR"),
            'swir1': image.select("SWIR1")
        })
    return mbsr.toInt16().rename("MBSR")

def calc_ndvi(image):
    ndvi = ee.Image(0).expression(
        '((nir - r)/(nir + r)) * 10000',
        {
          'nir': image.select("NIR"),
          'r': image.select("R")
        })
    return ndvi.toInt16().rename("NDVI")

def calc_awesh(image):
    awesh = ee.Image(0).expression(
        'blue + A*g - B*(nir+swir1) - C*swir2',
        {
            'blue': image.select('B'),
            'g': image.select('G'),
            'nir': image.select('NIR'),
            'swir1': image.select('SWIR1'),
            'swir2': image.select('SWIR2'),
            'A': 2.5,
            'B': 1.5,
            'C': 0.25
        })
    return awesh.toInt16().rename("AWESH")

# wrapper
def calc_indices(image):
    bands = ee.Image([
        calc_mndwi(image),
        calc_mbsr(image),
        calc_ndvi(image),
        calc_awesh(image),
        image.select("B"),
        image.select("NIR"),
        image.select("SWIR1"),
        image.select("SWIR2"),
        image.select("cloud_mask")
    ])
    return bands.set('system:time_start', image.get('system:time_start'))



# DSWE test functions
def test1(image):
    return image.select("MNDWI").gt(123)

def test2(image):
    return image.select("MBSR").gt(0)

def test3(image):
    return image.select("AWESH").gt(0)

def test4(image):
    x = image.select("MNDWI").gt(-5000) \
        .add(image.select("SWIR1").lt(1000)) \
        .add(image.select("NIR").lt(2000))
    return x.eq(3)

def test5(image):
    x = image.select("MNDWI").gt(-5000) \
        .add(image.select("SWIR2").lt(1000)) \
        .add(image.select("NIR").lt(2000))
    return x.eq(3)

def cloudTest(image):
    return image.select('cloud_mask').eq(1)

# wrapper/multiplier function
def addTests(image):
    x1 = test1(image)
    x2 = test2(image).multiply(10);
    x3 = test3(image).multiply(100);
    x4 = test4(image).multiply(1000);
    x5 = test5(image).multiply(10000);
    cld = cloudTest(image);
    res = x1.add(x2).add(x3).add(x4).add(x5).rename('test') \
        .where(cld.eq(1), -1) \
        .set('system:time_start', image.get('system:time_start'));
    return res


# DSWE CLASSES
def isDSWE0(image):
    y = image.lt(10).add(image.gte(0)).eq(2) \
        .rename("DSWE0") \
        .set('system:time_start', image.get('system:time_start'))
    return y

def isDSWE1(image):
    y1 = image.gt(11000).add(image.lte(11111)).eq(2)
    y2 = image.gte(10111).add(image.lt(11000)).eq(2)
    y3 = image.eq(1111)
    y = y1.add(y2).add(y3).gt(0) \
        .rename("DSWE1") \
        .set('system:time_start', image.get('system:time_start'))
    return y

def isDSWE2(image):
    y1 = image.gte(10011).add(image.lte(10110)).eq(2)
    y2 = image.gte(10001).add(image.lt(10010)).eq(2)
    y3 = image.gte(1001).add(image.lt(1110)).eq(2)
    y4 = image.gte(10).add(image.lt(111)).eq(2)
    y = y1.add(y2).add(y3).add(y4).gt(0) \
        .rename("DSWE2") \
        .set('system:time_start', image.get('system:time_start'))
    return y

def isDSWE3(image):
    y1 = image.eq(11000)
    y2 = image.eq(10000)
    y3 = image.eq(1000)
    y = y1.add(y2).add(y3).gt(0) \
        .rename("DSWE3") \
        .set('system:time_start', image.get('system:time_start'))
    return y

def isDSWE9(image):
    y = image.eq(-1) \
        .rename("DSWE9") \
        .set('system:time_start', image.get('system:time_start'))
    return y
