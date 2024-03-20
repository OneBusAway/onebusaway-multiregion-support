from xml.dom.minidom import getDOMImplementation
import json

class BaseSerializer(object):
    _open311BaseUrls = ''
    _open311JurisdictionIds = ''

    def __init__(self, **kwargs):
        self.pretty = kwargs.get('pretty')

    def _normalize_float(self, val):
        return round(float(val), 12)

    def _bounds(self, bounds_str):
        def _map_bound(bound):
            lat, lon, latSpan, lonSpan = bound.split(':')
            return {
                'lat': self._normalize_float(lat),
                'lon': self._normalize_float(lon),
                'latSpan': self._normalize_float(latSpan),
                'lonSpan': self._normalize_float(lonSpan)
            }

        if not bounds_str:
            return []

        bounds = bounds_str.split('|')
        return [_map_bound(b) for b in bounds]

    def _open311ApiKeys(self, apikeys_str):
        def _map_api_keys(apiKey, endpoint, jurisdiction):
            return {
                'juridisctionId': jurisdiction or None,
                'apiKey': apiKey,
                'baseUrl': endpoint
            }

        if not apikeys_str:
            return []
        endpoints = self._open311BaseUrls.split('|')
        apikeys = apikeys_str.split('|')

        if not self._open311JurisdictionIds:
            return [_map_api_keys(a, e, None) for (a,e) in zip(apikeys, endpoints)]
        else:
            jurisdictionIds = self._open311JurisdictionIds.split('|')
            return [_map_api_keys(a, e, j) for (a,e,j) in zip(apikeys, endpoints, jurisdictionIds)]

    def region_id(self, bundle, value):
        bundle['id'] = int(value)

    def active(self, bundle, value):
        bundle['active'] = self._bool(value)

    def bounds(self, bundle, value):
        bundle['bounds'] = self._bounds(value)

    def open311BaseUrls(self, bundle, value):
        self._open311BaseUrls = value

    def open311JurisdictionId(self, bundle, value):
        self._open311JurisdictionIds =value

    def open311ApiKeys(self, bundle, value):
        bundle['open311Servers'] = self._open311ApiKeys(value)

    def supportsSiriRealtimeApis(self, bundle, value):
        bundle['supportsSiriRealtimeApis'] = self._bool(value)

    def supportsObaDiscoveryApis(self, bundle, value):
        bundle['supportsObaDiscoveryApis'] = self._bool(value)

    def supportsObaRealtimeApis(self, bundle, value):
        bundle['supportsObaRealtimeApis'] = self._bool(value)

    def experimental(self, bundle, value):
        bundle['experimental'] = self._bool(value)

    def alter_bundle(self, bundle):
        return bundle

    def supportsEmbeddedSocial(self, bundle, value):
        bundle['supportsEmbeddedSocial'] = self._bool(value)

    def supportsOtpBikeshare(self, bundle, value):
        bundle['supportsOtpBikeshare'] = self._bool(value)

    def travelBehaviorDataCollectionEnabled(self, bundle, value):
        bundle['travelBehaviorDataCollectionEnabled'] = self._bool(value)

    def enrollParticipantsInStudy(self, bundle, value):
        bundle['enrollParticipantsInStudy'] = self._bool(value)

class JSONSerializer(BaseSerializer):
    def __init__(self, **kwargs):
        super(JSONSerializer, self).__init__(**kwargs)

    def _bool(self, value):
        if value == 'TRUE':
            return True
        elif value == 'FALSE':
            return False
        else:
            raise ValueError("Invalid value for active")

    # The base URLs want to be serialized as null in JSON,
    # not the empty string.

    def obaBaseUrl(self, bundle, value):
        bundle['obaBaseUrl'] = value or None

    def siriBaseUrl(self, bundle, value):
        bundle['siriBaseUrl'] = value or None

    def stopInfoUrl(self, bundle, value):
        bundle['stopInfoUrl'] = value or None

    def otpBaseUrl(self, bundle, value):
        bundle['otpBaseUrl'] = value or None

    def otpContactEmail(self, bundle, value):
        bundle['otpContactEmail'] = value or None

    def paymentAndroidAppId(self, bundle, value):
        bundle['paymentAndroidAppId'] = value or None

    def paymentWarningTitle(self, bundle, value):
        bundle['paymentWarningTitle'] = value or None

    def paymentWarningBody(self, bundle, value):
        bundle['paymentWarningBody'] = value or None

    def paymentiOSAppStoreIdentifier(self, bundle, value):
        bundle['paymentiOSAppStoreIdentifier'] = value or None

    def paymentiOSAppUrlScheme(self, bundle, value):
        bundle['paymentiOSAppUrlScheme'] = value or None

    def alter_list_bundle(self, list_bundle, version):
        return {
            'version': version,
            'code': 200,
            'text': 'OK',
            'data': {'list': list_bundle}
        }

    def serialize(self, list_bundle):
        if self.pretty:
            return json.dumps(list_bundle, indent=2)
        else:
            return json.dumps(list_bundle)


class XMLSerializer(BaseSerializer):
    def __init__(self, **kwargs):
        super(XMLSerializer, self).__init__(**kwargs)
        self.dom = getDOMImplementation()
        self.doc = self.dom.createDocument(None, "response", None)

    def _bool(self, value):
        if value in ('TRUE', 'FALSE'):
            return value.lower()
        else:
            raise ValueError("Invalid value for active")

    def _node(self, tag, text):
        elem = self.doc.createElement(tag)
        text_elem = self.doc.createTextNode(str(text))
        elem.appendChild(text_elem)
        return elem

    def bounds(self, bundle, value):
        bounds = self._bounds(value)
        # We need to convert this to a element here
        l = self.doc.createElement('bounds')

        for b in bounds:
            elem = self.doc.createElement('bound')
            for key, value in b.items():
                child = self._node(key, value)
                elem.appendChild(child)
            l.appendChild(elem)

        bundle['bounds'] = l

    def open311ApiKeys(self, bundle, value):
        open311ApiKeys = self._open311ApiKeys(value)
        # We need to convert this to a element here
        l = self.doc.createElement('open311Servers')

        for o in open311ApiKeys:
            elem = self.doc.createElement('open311Server')
            for key, value in o.items():
                if not value:
                    value = ''

                child = self._node(key, value)
                elem.appendChild(child)

            l.appendChild(elem)

        bundle['open311ApiKeys'] = l

    def alter_bundle(self, bundle):
        # Each item in the bundle should be converted to a text
        # node, if it isn't already a node (which it would be for bounds)
        elem = self.doc.createElement('region')
        for key, value in bundle.items():
            if key == 'bounds' or key == 'open311ApiKeys':
                elem.appendChild(value)
            else:
                child = self._node(key, value)
                elem.appendChild(child)

        return elem

    def alter_list_bundle(self, list_bundle, version):
        top = self.doc.documentElement
        top.appendChild(self._node('version', version))
        top.appendChild(self._node('code', 200))
        top.appendChild(self._node('text', 'OK'))

        # Create the data and list nodes
        data = self.doc.createElement('data')
        l = self.doc.createElement('list')
        for elem in list_bundle:
            l.appendChild(elem)

        data.appendChild(l)
        top.appendChild(data)
        return list_bundle

    def serialize(self, list_bundle):
        if self.pretty:
            return self.doc.toprettyxml(indent='  ')
        else:
            return self.doc.toxml()


def serialize(regions, serializer, version):
    """
    This does the following:
    1. Map each spreadsheet name into a suitable python function.
    2. Use the serializer class to bundle up the spreadhsheet values
        into a serializable form (with proper typing, etc)
    3. Allow the serializer to add any other header information, etc.
    4. Convert to the serialized format.
    """
    def _key(name):
        # Remove the '?' and replace _ with a space, convert to title
        name = name.replace('?', '').replace('_', ' ').title()
        # Convert to lower camel
        name = name[0].lower() + name[1:]
        # Keep "iOS"
        name = name.replace('Ios', 'iOS')
        # Remove spaces
        return name.replace(' ', '')

    def _to_bundle(index, region):
        bundle = {}
        serializer.region_id(bundle, index)
        for k, v in region.items():
            key = _key(k)
            f = getattr(serializer, key, None)
            if f:
                f(bundle, v)
            else:
                # Convenience for strings, and things that need no conversion
                bundle[key] = v
        bundle = serializer.alter_bundle(bundle)
        return bundle

    list_bundle = []
    for i, region in enumerate(regions):
        try:
            # For v2, don't include experimental servers
            if version == 2:
                if region["Experimental?"] == 'TRUE':
                    print("Skipping %s as experimental for v2" % (region["Region_Name"]))
                else:
                    list_bundle.append(_to_bundle(i, region))
            else:
                 list_bundle.append(_to_bundle(i, region))
        except ValueError:
            print("*** ERROR: Invalid region specification: " + str(region), file=sys.stderr)
            raise

    list_bundle = serializer.alter_list_bundle(list_bundle, version)
    serialized = serializer.serialize(list_bundle)
    return serialized
