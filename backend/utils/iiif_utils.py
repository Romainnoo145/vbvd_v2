"""
IIIF Utilities - Parse IIIF Presentation API manifests and extract images
Supports both IIIF Presentation API 2.0 and 3.0
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import httpx

logger = logging.getLogger(__name__)


class IIIFImageURL:
    """
    Constructs IIIF Image API URLs according to spec
    URL Format: {scheme}://{server}{/prefix}/{identifier}/{region}/{size}/{rotation}/{quality}.{format}
    """

    @staticmethod
    def construct_url(
        service_id: str,
        region: str = "full",
        size: str = "max",
        rotation: str = "0",
        quality: str = "default",
        format: str = "jpg"
    ) -> str:
        """
        Construct a IIIF Image API URL

        Args:
            service_id: Base service URL (e.g., https://example.org/iiif/image123)
            region: Image region (full, square, x,y,w,h, pct:x,y,w,h)
            size: Image size (max, w,, ,h, w,h, pct:n, ^max, ^w,h)
            rotation: Rotation degrees (0-359, !0-!359 for mirroring)
            quality: Color quality (color, gray, bitonal, default)
            format: Output format (jpg, png, webp, etc.)

        Returns:
            Complete IIIF Image URL
        """
        # Remove trailing slash from service_id if present
        service_id = service_id.rstrip('/')

        return f"{service_id}/{region}/{size}/{rotation}/{quality}.{format}"


class IIIFManifestParser:
    """
    Parse IIIF Presentation API manifests (versions 2.0 and 3.0)
    Extract image URLs, thumbnails, and metadata
    """

    @staticmethod
    async def fetch_manifest(manifest_url: str, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """Fetch a IIIF manifest from URL"""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(manifest_url)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to fetch manifest from {manifest_url}: status {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching IIIF manifest from {manifest_url}: {e}")
            return None

    @staticmethod
    def detect_version(manifest: Dict[str, Any]) -> str:
        """
        Detect IIIF Presentation API version

        Returns:
            "2.0", "3.0", or "unknown"
        """
        context = manifest.get('@context', '')

        if isinstance(context, str):
            if '/presentation/3' in context:
                return "3.0"
            elif '/presentation/2' in context:
                return "2.0"
        elif isinstance(context, list):
            for ctx in context:
                if isinstance(ctx, str):
                    if '/presentation/3' in ctx:
                        return "3.0"
                    elif '/presentation/2' in ctx:
                        return "2.0"

        # Fallback heuristics
        if 'items' in manifest:  # 3.0 uses 'items'
            return "3.0"
        elif 'sequences' in manifest:  # 2.0 uses 'sequences'
            return "2.0"

        return "unknown"

    @classmethod
    def extract_images_v2(cls, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract images from IIIF Presentation API 2.0 manifest

        Returns:
            List of dicts with 'url', 'service_id', 'width', 'height', 'type'
        """
        images = []

        sequences = manifest.get('sequences', [])
        for sequence in sequences:
            canvases = sequence.get('canvases', [])
            for canvas in canvases:
                canvas_images = canvas.get('images', [])
                for img in canvas_images:
                    resource = img.get('resource', {})

                    image_info = {}

                    # Direct image URL
                    if 'id' in resource or '@id' in resource:
                        image_info['url'] = resource.get('id') or resource.get('@id')

                    # IIIF Image Service
                    if 'service' in resource:
                        service = resource['service']
                        if isinstance(service, dict):
                            service_id = service.get('@id') or service.get('id')
                            if service_id:
                                image_info['service_id'] = service_id
                                # Construct full-size image URL
                                image_info['iiif_url'] = IIIFImageURL.construct_url(
                                    service_id=service_id,
                                    size="max"
                                )
                        elif isinstance(service, list) and len(service) > 0:
                            service_id = service[0].get('@id') or service[0].get('id')
                            if service_id:
                                image_info['service_id'] = service_id
                                image_info['iiif_url'] = IIIFImageURL.construct_url(
                                    service_id=service_id,
                                    size="max"
                                )

                    # Dimensions
                    if 'width' in resource:
                        image_info['width'] = resource['width']
                    if 'height' in resource:
                        image_info['height'] = resource['height']

                    # Type/format
                    image_info['type'] = resource.get('format', 'image/jpeg')

                    if image_info:
                        images.append(image_info)

        return images

    @classmethod
    def extract_images_v3(cls, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract images from IIIF Presentation API 3.0 manifest

        Returns:
            List of dicts with 'url', 'service_id', 'width', 'height', 'type'
        """
        images = []

        items = manifest.get('items', [])
        for item in items:
            # Each item is a Canvas
            if item.get('type') == 'Canvas':
                # Get annotation pages
                annotation_pages = item.get('items', [])
                for page in annotation_pages:
                    # Get annotations
                    annotations = page.get('items', [])
                    for annotation in annotations:
                        # Get the body (the actual content)
                        body = annotation.get('body', {})

                        if isinstance(body, dict):
                            bodies = [body]
                        elif isinstance(body, list):
                            bodies = body
                        else:
                            continue

                        for b in bodies:
                            image_info = {}

                            # Direct image URL
                            if 'id' in b:
                                image_info['url'] = b['id']

                            # IIIF Image Service
                            if 'service' in b:
                                services = b['service']
                                if isinstance(services, dict):
                                    services = [services]

                                for service in services:
                                    if 'id' in service:
                                        service_id = service['id']
                                        image_info['service_id'] = service_id
                                        # Construct full-size image URL
                                        image_info['iiif_url'] = IIIFImageURL.construct_url(
                                            service_id=service_id,
                                            size="max"
                                        )
                                        break

                            # Dimensions
                            if 'width' in b:
                                image_info['width'] = b['width']
                            if 'height' in b:
                                image_info['height'] = b['height']

                            # Type/format
                            image_info['type'] = b.get('format', 'image/jpeg')

                            if image_info:
                                images.append(image_info)

        return images

    @classmethod
    def extract_images(cls, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all images from a IIIF manifest (auto-detects version)

        Returns:
            List of dicts with 'url', 'service_id', 'width', 'height', 'type'
        """
        version = cls.detect_version(manifest)

        if version == "3.0":
            logger.debug("Parsing IIIF Presentation API 3.0 manifest")
            return cls.extract_images_v3(manifest)
        elif version == "2.0":
            logger.debug("Parsing IIIF Presentation API 2.0 manifest")
            return cls.extract_images_v2(manifest)
        else:
            logger.warning(f"Unknown IIIF manifest version, attempting both parsers")
            # Try both
            images = cls.extract_images_v3(manifest)
            if not images:
                images = cls.extract_images_v2(manifest)
            return images

    @classmethod
    def extract_thumbnail(cls, manifest: Dict[str, Any]) -> Optional[str]:
        """Extract thumbnail URL from manifest"""
        thumbnail = manifest.get('thumbnail')

        if isinstance(thumbnail, dict):
            return thumbnail.get('id') or thumbnail.get('@id')
        elif isinstance(thumbnail, list) and len(thumbnail) > 0:
            thumb = thumbnail[0]
            if isinstance(thumb, dict):
                return thumb.get('id') or thumb.get('@id')
            elif isinstance(thumb, str):
                return thumb
        elif isinstance(thumbnail, str):
            return thumbnail

        return None

    @classmethod
    def extract_metadata(cls, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from manifest"""
        metadata = {}

        # Label/Title
        label = manifest.get('label')
        if isinstance(label, dict):
            # 3.0 format: {"en": ["Title"]}
            for lang, values in label.items():
                if isinstance(values, list) and values:
                    metadata['title'] = values[0]
                    break
        elif isinstance(label, str):
            # 2.0 format: simple string
            metadata['title'] = label

        # Description/Summary
        description = manifest.get('description') or manifest.get('summary')
        if isinstance(description, dict):
            for lang, values in description.items():
                if isinstance(values, list) and values:
                    metadata['description'] = values[0]
                    break
        elif isinstance(description, str):
            metadata['description'] = description

        # Metadata pairs
        metadata_pairs = manifest.get('metadata', [])
        for item in metadata_pairs:
            label = item.get('label')
            value = item.get('value')

            if isinstance(label, str) and value:
                if isinstance(value, str):
                    metadata[label.lower()] = value
                elif isinstance(value, list):
                    metadata[label.lower()] = ', '.join(str(v) for v in value)

        # Rights/License
        rights = manifest.get('rights') or manifest.get('license')
        if rights:
            metadata['rights'] = rights

        return metadata


async def fetch_and_parse_manifest(
    manifest_url: str,
    timeout: float = 10.0
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convenience function: fetch manifest and extract images

    Returns:
        Tuple of (metadata_dict, images_list)
    """
    parser = IIIFManifestParser()

    manifest = await parser.fetch_manifest(manifest_url, timeout)
    if not manifest:
        return None, []

    metadata = parser.extract_metadata(manifest)
    images = parser.extract_images(manifest)

    # Add thumbnail to metadata
    thumbnail = parser.extract_thumbnail(manifest)
    if thumbnail:
        metadata['thumbnail'] = thumbnail

    return metadata, images


__all__ = ['IIIFImageURL', 'IIIFManifestParser', 'fetch_and_parse_manifest']
