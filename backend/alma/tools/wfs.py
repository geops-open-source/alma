# pyright: basic
import sys
from io import BytesIO
from logging import getLogger
from tempfile import NamedTemporaryFile
from typing import Any

import fiona
import httpx2
from osgeo import ogr
from owslib.util import ResponseWrapper
from owslib.wfs import WebFeatureService
from pydantic import HttpUrl
from shapely import MultiPolygon, Polygon, to_wkt

from alma.exceptions import WfsError
from alma.settings import WfsSettings, settings

logger = getLogger(__name__)


class WfsClient:
    def __init__(self, wfs_config: WfsSettings, name: str) -> None:
        self.wfs_config = wfs_config
        self.name = name
        self.ows_client = WebFeatureService(
            url=self.wfs_config.url,
            version=self.wfs_config.version,
            headers=self.wfs_config.auth_headers,
        )

    def query(
        self,
        *,
        bbox: tuple[float, float, float, float] | None = None,
        filter_gml: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            if bbox and filter_gml:
                raise WfsError("BBox and filter are mutually exclusive.")
            assert self.ows_client
            if filter_gml:
                result = []
                for layer in self.wfs_config.layers or list(self.ows_client.contents):
                    response = self.ows_client.getfeature(
                        typename=layer,
                        filter=filter_gml,
                        method="post",
                    )
                    result.extend(self._parse_response(response, [layer]))
            elif bbox:
                layers = self.wfs_config.layers or list(self.ows_client.contents)
                response = self.ows_client.getfeature(
                    typename=self.wfs_config.layers or list(self.ows_client.contents),
                    bbox=bbox,
                    method="get",
                )
                return self._parse_response(response, layers)
            else:
                raise WfsError("Either bbox or filter_gml must be provided.")

        except Exception as e:
            logger.error(
                "Error occurred querying wfs. BBOX %s and filter_gml %s",
                bbox,
                filter_gml,
            )
            raise WfsError(f"Error occurred updating WFS {self.wfs_config.url}: {e}.")
        return result

    def _parse_response(
        self, response: BytesIO | ResponseWrapper, layers: list[str]
    ) -> list[dict[str, Any]]:
        result = []
        assert self.ows_client
        if isinstance(response, ResponseWrapper):
            output = BytesIO(response.read()).getvalue()
        elif isinstance(response, BytesIO):
            output = response.getvalue()

        for layer in layers:
            # we have to remove the namespace, because fiona ignores it
            coll = fiona.open(BytesIO(output), layer=layer.split(":")[-1])
            for feature in coll:
                row: dict[str, Any] = {}
                for field_def in self.wfs_config.wfs_fields:
                    cache_table_field = self.wfs_config.field_mappings_lut[field_def]
                    row[cache_table_field] = feature.properties[field_def]
                    if feature.geometry.type == "Polygon":
                        rings = feature.geometry.coordinates
                        polygon = Polygon(rings[0], rings[1:])
                        row["wkb_geometry"] = (
                            f"SRID={coll.crs.to_epsg()};{to_wkt(polygon)}"
                        )
                    elif feature.geometry.type == "MultiPolygon":
                        polygons = [
                            Polygon(part[0], part[1:])
                            for part in feature.geometry.coordinates
                        ]
                        row["wkb_geometry"] = (
                            f"SRID={coll.crs.to_epsg()};{to_wkt(MultiPolygon(polygons))}"
                        )
                    else:
                        raise Exception(
                            f"Geometry Type {feature.geometry.type} not supported."
                        )
                if row:
                    result.append(row)
        return result


def get_wfs_client(wfs_service_name: str) -> WfsClient:
    try:
        return WfsClient(
            wfs_config=settings.wfs_config[wfs_service_name], name=wfs_service_name
        )
    except Exception as e:
        raise WfsError(f"Error occurred instantiating WFS client: {e}")


def fetch_wfs_gml(
    wfsurl: str, layername: str, targetfile, proxyurl: HttpUrl | None
) -> None:
    wfsparams = {
        "request": "getfeature",
        "service": "WFS",
        "version": "1.0.0",
        "typename": layername,
        "map": "units",
    }
    headers = {"User-Agent": "pull-gemeindenservice"}

    """if proxyurl is defined, requests are routed through proxy"""
    kwargs = {}
    if proxyurl:
        kwargs["proxy"] = str(proxyurl)
        if (
            wfsurl == "https://units.geops.io/?map=units"
            and settings.gemeinde_service.ignore_certs
        ):
            kwargs["verify"] = False

    size_read = 0
    chunksize = 20 * 1024
    with httpx2.stream(
        "GET", wfsurl, params=wfsparams, headers=headers, **kwargs
    ) as response:
        for chunk in response.iter_bytes(chunksize):
            if not chunk:
                break
            targetfile.write(chunk)
            size_read += len(chunk)
            sys.stdout.write(
                "\rDownloaded %d kbytes for layer %s." % ((size_read / 1024), layername)
            )
            sys.stdout.flush()
        sys.stdout.write("\n")
        targetfile.flush()


def feature_iterator(wfsurl: str, layername: str, proxyurl: HttpUrl | None = None):
    """generator to iterate over all features in wfs layer"""
    with NamedTemporaryFile(delete=True, suffix=".xml") as gmlfile:
        fetch_wfs_gml(wfsurl, layername, gmlfile, proxyurl)
        ds = ogr.Open(gmlfile.name)

        layer = ds.GetLayerByName(layername)
        assert layer
        print("Layer %s contains %d features." % (layername, layer.GetFeatureCount()))

        # collect field indices
        featureDefn = layer.GetLayerDefn()
        assert featureDefn
        fieldIndices = {}
        idx = 0
        while idx < featureDefn.GetFieldCount():
            fieldDefn = featureDefn.GetFieldDefn(idx)
            assert fieldDefn
            fieldIndices[fieldDefn.GetName()] = idx
            idx += 1

        # get spatial reference code
        spatialref = layer.GetSpatialRef()
        srid = 2056
        if spatialref:
            srid = spatialref.GetAuthorityCode("PROJCS")
        else:
            print(
                "Got no spatial reference in layer %s - using default %d"
                % (layername, srid)
            )

        # return features
        for feature in layer:
            row: dict[str, Any] = {}
            for fieldName, fieldIdx in fieldIndices.items():
                row[fieldName] = str(feature.GetFieldAsString(fieldIdx))

            row["_geom_"] = feature.GetGeometryRef()
            row["_srid_"] = srid
            yield row
