import json

import pytest

from program.services.downloaders import alldebrid
from program.services.downloaders.alldebrid import (
    AllDebridDownloader,
    AllDebridRequestHandler,
)
from program.services.downloaders.models import (
    DebridFile,
    TorrentContainer,
)
from program.settings.manager import settings_manager as settings
from program.utils.request import HttpMethod


@pytest.fixture
def downloader(user, upload, status, status_all, files, delete):
    """Instance of AllDebridDownloader with API calls mocked"""
    _execute = alldebrid.AllDebridRequestHandler.execute

    # mock API calls
    def execute(self, method: HttpMethod, endpoint: str, **kwargs) -> dict:
        params = kwargs.get("params", {})
        match endpoint:
            case "user":
                return user()["data"]
            case "magnet/upload":
                return upload(endpoint, **params)["data"]
            case "magnet/delete":
                return delete(endpoint, **params)["data"]
            case "magnet/status":
                if params.get("id", False):
                    return status(endpoint, **params)["data"]
                else:
                    return status_all(endpoint, **params)["data"]
            case "magnet/files":
                return files(endpoint, **params)["data"]
            case _:
                raise Exception("unmatched api call %s" % endpoint)

    alldebrid.AllDebridRequestHandler.execute = execute

    alldebrid_settings = settings.settings.downloaders.all_debrid
    alldebrid_settings.enabled = True
    alldebrid_settings.api_key = "key"

    downloader = AllDebridDownloader()
    assert downloader.initialized
    yield downloader

    # tear down mock
    alldebrid.AllDebridRequestHandler.execute = _execute


## DownloaderBase tests
def test_validate(downloader):
    assert downloader.validate() == True


def test_get_instant_availability(downloader):
    assert downloader.get_instant_availability(UBUNTU, "movie") == TorrentContainer(
        infohash=UBUNTU,
        files=[DebridFile.create(filename="foo", filesize_bytes=123, filetype="movie")],
    )


def test_add_torrent(downloader):
    assert downloader.add_torrent(UBUNTU) == MAGNET_ID


def test_select_files(downloader):
    assert downloader.select_files(MAGNET_ID, [1, 2, 3]) == None


def test_get_torrent_info(downloader):
    torrent_info = downloader.get_torrent_info(MAGNET_ID)


def test_delete_torrent(downloader):
    assert (
        downloader.delete_torrent(MAGNET_ID) == None
    )  # TODO: assert that delete was called


# Example requests - taken from real API calls
UBUNTU = "3648baf850d5930510c1f172b534200ebb5496e6"
MAGNET_ID = "251993753"


@pytest.fixture
def user():
    """GET /user"""
    with open("src/tests/test_data/alldebrid_user.json") as f:
        body = json.load(f)
    return lambda: body


@pytest.fixture
def upload():
    """GET /magnet/upload?magnets[]=infohash (torrent not ready yet)"""
    with open("src/tests/test_data/alldebrid_magnet_upload_not_ready.json") as f:
        body = json.load(f)
    return lambda url, **params: body


@pytest.fixture
def upload_ready():
    """GET /magnet/upload?magnets[]=infohash (torrent ready)"""
    with open("src/tests/test_data/alldebrid_magnet_upload_ready.json") as f:
        body = json.load(f)
    return lambda url, **params: body


@pytest.fixture
def status():
    """GET /magnet/status?id=123 (debrid links ready)"""
    with open("src/tests/test_data/alldebrid_magnet_status_one_ready.json") as f:
        body = json.load(f)
    return lambda url, **params: body


@pytest.fixture
def status_downloading():
    """GET /magnet/status?id=123 (debrid links not ready yet)"""
    with open("src/tests/test_data/alldebrid_magnet_status_one_downloading.json") as f:
        body = json.load(f)
    return lambda url, **params: body


@pytest.fixture
def status_all():
    """GET /magnet/status (gets a list of all links instead of a single object)"""
    # The body is the same as a single item, but with all your magnets in a list.
    with open("src/tests/test_data/alldebrid_magnet_status_one_ready.json") as f:
        body = json.load(f)
    return lambda url, **params: {
        "status": "success",
        "data": {"magnets": [body["data"]["magnets"]]},
    }


@pytest.fixture
def files():
    """GET /magnet/files (gets files and links for a magnet)"""
    with open("src/tests/test_data/alldebrid_magnet_files.json") as f:
        body = json.load(f)
    return lambda url, **params: body


@pytest.fixture
def delete():
    """GET /delete"""
    with open("src/tests/test_data/alldebrid_magnet_delete.json") as f:
        body = json.load(f)
    return lambda url, **params: body
