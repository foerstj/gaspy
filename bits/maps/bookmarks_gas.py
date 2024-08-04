from __future__ import annotations

from gas.gas import Section, Attribute, Gas
from gas.gas_file import GasFile
from gas.molecules import Position


class Camera:
    def __init__(self, azimuth, distance, orbit):
        self.azimuth: float = azimuth
        self.distance: float = distance
        self.orbit: float = orbit

    @classmethod
    def from_gas(cls, section: Section):
        assert section.header == 'camera'
        azimuth = section.get_attr_value('azimuth')
        distance = section.get_attr_value('distance')
        orbit = section.get_attr_value('orbit')
        return Camera(azimuth, distance, orbit)

    def to_gas(self):
        return Section('camera', [
            Attribute('azimuth', self.azimuth),
            Attribute('distance', self.distance),
            Attribute('orbit', self.orbit)
        ])


class Bookmark:
    def __init__(self, description: str, position, camera):
        self.description = description
        self.position = position
        self.camera = camera

    @classmethod
    def from_gas(cls, section: Section):
        bookmark_type, bookmark_key = section.get_t_n_header()
        assert bookmark_type == 'bookmark'
        description = section.get_attr_value('description')
        position = Position.parse(section.get_attr_value('position'))
        camera = Camera.from_gas(section.get_section('camera'))
        return bookmark_key, Bookmark(description, position, camera)

    def to_gas(self, bookmark_key: str):
        return Section(Section.make_t_n_header('bookmark', bookmark_key), [
            Attribute('description', self.description),
            Attribute('position', self.position),
            self.camera.to_gas()
        ])


# Handler for bookmarks.gas files
class BookmarksGas:
    def __init__(self, bookmarks: dict[str, Bookmark]):
        self.bookmarks = bookmarks

    @classmethod
    def load(cls, gas_file: GasFile) -> BookmarksGas:
        bookmarks: dict[str, Bookmark] = dict()
        if gas_file is not None:
            bookmarks_section = gas_file.get_gas().get_section('bookmarks')
            assert bookmarks_section, 'bookmarks.gas file has no [bookmarks] section, wtf'
            for section in bookmarks_section.get_sections():
                bookmark_key, bookmark = Bookmark.from_gas(section)
                bookmarks[bookmark_key] = bookmark
        return BookmarksGas(bookmarks)

    def write_gas(self) -> Gas:
        return Gas([
            Section('bookmarks', [
                bookmark.to_gas(bookmark_key) for bookmark_key, bookmark in self.bookmarks.items()
            ])
        ])
