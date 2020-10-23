# wire_interface.py
# Get keys from wg Write wireguard config files
# Author: Tim Schlottmann

from os import path
from typing import NamedTuple
from typing import Optional

# from .io_ import JSONDecodeError

from .config import delete_config
from .config import write_config

from .io_ import read_file
from .io_ import write_file

from .keys import get_keys

from .typedefs import JSONDecodeError
from .typedefs import PeerItems
from .typedefs import PeerDoesExistError
from .typedefs import PeerDoesNotExistError
from .typedefs import Peers
from .typedefs import Settings
from .typedefs import SettingDoesNotExistError
from .typedefs import SiteItems
from .typedefs import SiteDoesExistError
from .typedefs import SiteDoesNotExistError
from .typedefs import Sites


class Site(NamedTuple):
  name: str
  config_version: str
  ip_networks: str
  peers: list


class Peer(NamedTuple):
  name: str
  additional_allowed_ips: list
  outgoing_connected_peers: list
  main_peer: str
  ingoing_connected_peers: list
  endpoint: str
  port: int
  persistent_keep_alive: int
  redirect_all_traffic: bool


class WireUI():
  """ Class for managing wireguard config files """

  def __init__(self, settings_path: Optional[str] = None):
    default_settings = {
        "verbosity": 0,
        "sites_file_path": "./sites.json",
        "wg_config_path": "./wg",
        "editor": "editor",
    }
    if settings_path:
      self.settings_path = settings_path
      try:
        self._settings = Settings(read_file(settings_path), default_settings)
      except JSONDecodeError as e:
        raise e
    else:
      self._settings = Settings(defaults=default_settings)

    self._sites = Sites(read_file(self._settings.get("sites_file_path")))

  def get_sites(self) -> list:
    """ Get all existing sites """

    return list(self._sites)

  def add_site(self, site: Site):
    """ Add a new site and creates its config files """

    if site.name in self._sites:
      raise SiteDoesExistError(site.name)

    peers = Peers()
    for p in site.peers:
      try:
        peers[p.name] = PeerItems({
          "keys": get_keys(),
          "additional_allowed_ips": p.additional_allowed_ips,
          "outgoing_connected_peers": p.outgoing_connected_peers,
          "main_peer": p.main_peer,
          "ingoing_connected_peers": p.ingoing_connected_peers,
          "endpoint": p.endpoint,
          "port": p.port,
          "persistent_keep_alive": p.persistent_keep_alive,
          "redirect_all_traffic": p.redirect_all_traffic,
        })
      except PeerDoesExistError as e:
        raise e

    self._sites[site.name] = SiteItems({
        "config_version": site.config_version,
        "ip_networks": site.ip_networks,
        "peers": peers
    })

  def delete_site(self, name: str):
    """ Delete a site """

    if name not in self._sites:
      raise SiteDoesNotExistError(name)

    del self._sites[name]

  def site_exists(self, name: str) -> bool:
    """ Check if a site does exist """

    return name in self._sites

  def get_number_of_sites(self) -> int:
    """ Get the number of existing sites """

    return len(self._sites)

  def get_peer_names(self, site_name: str) -> list:
    """ Get name of all existing peers from a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    return list(self._sites[site_name]["peers"])

  def add_peer(self, site_name: str, peer: Peer):
    """ Add a peer to a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    if peer.name in self._sites[site_name]["peers"]:
      raise PeerDoesExistError(peer.name)

    self._sites[site_name]["peers"][peer.name] = PeerItems({
        "keys": get_keys(),
        "additional_allowed_ips": peer.additional_allowed_ips,
        "outgoing_connected_peers": peer.outgoing_connected_peers,
        "main_peer": peer.main_peer,
        "ingoing_connected_peers": peer.ingoing_connected_peers,
        "endpoint": peer.endpoint,
        "port": peer.port,
        "persistent_keep_alive": peer.persistent_keep_alive,
        "redirect_all_traffic": peer.redirect_all_traffic,
    })

  def get_peer(self, site_name: str, peer_name: str) -> Peer:
    """ Get a peer from a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    if peer_name not in self._sites[site_name]["peers"]:
      raise PeerDoesNotExistError(peer_name)

    return Peer(
      peer_name,
      self._sites[site_name]["peers"][peer_name]["additional_allowed_ips"],
      self._sites[site_name]["peers"][peer_name]["outgoing_connected_peers"],
      self._sites[site_name]["peers"][peer_name]["main_peer"],
      self._sites[site_name]["peers"][peer_name]["ingoing_connected_peers"],
      self._sites[site_name]["peers"][peer_name]["endpoint"],
      self._sites[site_name]["peers"][peer_name]["port"],
      self._sites[site_name]["peers"][peer_name]["persistent_keep_alive"],
      self._sites[site_name]["peers"][peer_name]["redirect_all_traffic"],
    )

  def set_peer(self, site_name: str, peer: Peer):
    """ Set a peer in a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    if peer.name not in self._sites[site_name]["peers"]:
      raise PeerDoesNotExistError(peer.name)

    self._sites[site_name]["peers"][peer.name] = PeerItems({
        "keys": self._sites[site_name]["peers"][peer.name]["keys"],
        "additional_allowed_ips": peer.additional_allowed_ips,
        "outgoing_connected_peers": peer.outgoing_connected_peers,
        "main_peer": peer.main_peer,
        "ingoing_connected_peers": peer.ingoing_connected_peers,
        "endpoint": peer.endpoint,
        "port": peer.port,
        "persistent_keep_alive": peer.persistent_keep_alive,
        "redirect_all_traffic": peer.redirect_all_traffic,
    })

  def delete_peer(self, site_name: str, peer_name: str):
    """ Delete a peer from a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    if peer_name not in self._sites[site_name]["peers"]:
      raise PeerDoesNotExistError(peer_name)

    del self._sites[site_name]["peers"][peer_name]

  def rekey_peer(self, site_name: str, peer_name: str):
    """ Create new keys for a peer from a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    if peer_name not in self._sites[site_name]["peers"]:
      raise PeerDoesNotExistError(peer_name)

    self._sites[site_name]["peers"][peer_name] = PeerItems({
        "keys": get_keys()
    })

  def peer_exists(self, site_name: str, peer_name: str) -> bool:
    """ Check if a peer exists in a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    return peer_name in self._sites[site_name]["peers"]

  def get_number_of_peers(self, site_name: str) -> int:
    """ Get the number of peers in a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)
    return len(self._sites[site_name]["peers"])

  def create_wireguard_config(self, site_name: str) -> list:
    """ Write the wireguard config files """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    return write_config(self._sites[site_name],
                        path.join(self._settings["wg_config_path"], site_name))

  def delete_wireguard_config(self, site_name: str):
    """ Check if a peer exists in a site """

    if site_name not in self._sites:
      raise SiteDoesNotExistError(site_name)

    delete_config(site_name,
                  path.join(self._settings.get("wg_config_path"), site_name))

  def get_setting_names(self, setting: str) -> list:
    """ Get names of all existing settings """

    return list(self._settings)

  def get_setting(self, setting: str):
    """ Get a setting """

    if setting not in self._settings:
      raise SettingDoesNotExistError

    return self._settings[setting]

  def write_settings_to_file(self):
    write_file(self.settings_path, str(self._settings))

  def write_sites_to_file(self):
    write_file(self._settings["sites_file_path"], str(self._sites))
