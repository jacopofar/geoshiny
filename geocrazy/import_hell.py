import logging
import subprocess
import time


def import_gdal_shapely(wait: bool = False):
    """Handle the case of an import order error.

    The order of import for gdal and shapely causes very strange issues,
    because some native library is shared and depending on the python version
    and what was installed and how it gives errors upon importing.

    It's tricky.

    Running another interpreter it's possible to check if that's the case.
    If so, an error is shown and these modules are imported in the other order.

    This function does just that. It doesn't return anything, but as a side
    effect of calling it the import of the two libraries will work on the
    current interpreter.

    """
    proc = subprocess.Popen(
        "python3 -c 'from shapely.geometry import shape;import osgeo'",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True,
    )
    std_out, std_err = proc.communicate()
    if "ModuleNotFoundError: No module named '_gdal'" in std_err:
        logger = logging.getLogger(__name__)
        logger.warning("Error importing shapely BEFORE osgeo :(")
        logger.warning("As a workaround, the other order will be used")
        if wait:
            time.sleep(5)
        logger.warning(std_err)
        if wait:
            time.sleep(5)
        import osgeo
        from shapely.geometry import shape
