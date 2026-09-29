import io
from unittest.mock import patch

import pytest
from PIL import Image
from sqlalchemy import delete, select

from alma.models.documents import Asset


@pytest.mark.skip(reason="Permission issues on saving files.")
def test_file_upload_creates_new_entry_in_database(client, session):
    image = Image.new("RGB", (256, 256), (256, 256, 256))
    bytestream = io.BytesIO()
    image.save(bytestream, "jpeg")
    image.seek(0)

    session.execute(delete(Asset))
    response = client.post(
        "/api/documents/",
        data={"title": "foo"},
        files={"file": ("foo.jpeg", bytestream.getvalue())},
    )
    assert response.status_code == 200
    assert session.scalars(select(Asset)).all()


@pytest.mark.skip(reason="Permission issues on saving files.")
def test_file_upload_creates_preview(client, session):
    image = Image.new("RGB", (256, 256), (256, 256, 256))
    bytestream = io.BytesIO()
    image.save(bytestream, "jpeg")
    image.seek(0)

    session.execute(delete(Asset))
    response = client.post(
        "/api/documents/",
        data={"title": "foo"},
        files={"file": ("foo.jpeg", bytestream.getvalue())},
    )
    assert response.status_code == 200
    asset = session.scalars(select(Asset)).first()
    assert asset.preview_path


@pytest.mark.skip(reason="Permission issues on saving files.")
def test_file_upload_sets_metadata(client, session):
    image = Image.new("RGB", (256, 256), (256, 256, 256))
    bytestream = io.BytesIO()
    image.save(bytestream, "jpeg")
    image.seek(0)

    session.execute(delete(Asset))
    response = client.post(
        "/api/documents/",
        data={"title": "foo"},
        files={"file": ("foo.jpeg", bytestream.getvalue())},
    )
    assert response.status_code == 200
    asset = session.scalars(select(Asset)).first()
    assert asset.file_size == len(bytestream.getvalue())
    assert asset.file_type == "image/jpeg"
    assert asset.original_file_name == "foo.jpeg"
    assert asset.title == "foo"


@pytest.mark.skip(reason="Permission issues on saving files.")
def test_lucky_path_upload_and_download(client):
    image = Image.new("RGB", (256, 256), (256, 256, 256))
    bytestream = io.BytesIO()
    image.save(bytestream, "jpeg")
    image.seek(0)

    response = client.post(
        "/api/documents/",
        data={"title": "foo"},
        files={"file": ("foo.jpeg", bytestream.getvalue())},
    )
    assert response.status_code == 200
    document_ref = response.text

    file_response = client.get(f"/api/documents/{document_ref}/file")
    assert file_response.status_code == 200

    meta_data_response = client.get(f"/api/documents/{document_ref}")
    assert meta_data_response.status_code == 200

    preview_response = client.get(f"/api/documents/{document_ref}/preview")
    assert preview_response.status_code == 200


@pytest.mark.skip(reason="Permission issues on saving files.")
@patch("preview_generator.manager.PreviewManager.get_jpeg_preview")
def test_preview_generator_raises_error_does_not_generate_preview(
    mocked_preview_fun, client
):
    from preview_generator.exception import (
        PreviewGeneratorException,
    )

    mocked_preview_fun.side_effect = PreviewGeneratorException("foo")
    image = Image.new("RGB", (256, 256), (256, 256, 256))
    bytestream = io.BytesIO()
    image.save(bytestream, "jpeg")
    image.seek(0)

    response = client.post(
        "/api/documents/",
        data={"title": "foo"},
        files={"file": ("foo.jpeg", bytestream.getvalue())},
    )
    assert response.status_code == 200
    document_ref = response.text

    preview_response = client.get(f"/api/documents/{document_ref}/preview")
    assert preview_response.json() == {"detail": {"error": "preview does not exist"}}
    assert preview_response.status_code == 404
