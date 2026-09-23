import unittest

from app.schemas import DeviceCreate, DeviceUpdate, InterfaceCreate
from app.services.gns3_service import _infer_device_type, _infer_status, _match_site_or_backbone


class FakeEntity:
    def __init__(self, entity_id: int, name: str):
        self.id = entity_id
        self.name = name


class CoreBehaviorTests(unittest.TestCase):
    def test_gns3_mapping_is_case_and_separator_insensitive(self):
        site_id, backbone_id = _match_site_or_backbone(
            "RTR_SITE-Paris_01",
            [FakeEntity(7, "Site Paris")],
            [FakeEntity(9, "CORE")],
        )
        self.assertEqual(site_id, 7)
        self.assertIsNone(backbone_id)

    def test_gns3_type_and_status_mapping(self):
        self.assertEqual(_infer_device_type("dynamips", "EDGE-01"), "router")
        self.assertEqual(_infer_device_type("qemu", "Main Firewall"), "firewall")
        self.assertEqual(_infer_status("started"), "online")
        self.assertEqual(_infer_status("unexpected"), "unknown")

    def test_device_creation_requires_exactly_one_location(self):
        with self.assertRaises(ValueError):
            DeviceCreate(name="r1", device_type="router")
        with self.assertRaises(ValueError):
            DeviceCreate(name="r1", device_type="router", site_id=1, backbone_id=2)

    def test_device_update_can_clear_location_but_not_duplicate_it(self):
        self.assertIsNone(DeviceUpdate(name="r1", device_type="router").site_id)
        with self.assertRaises(ValueError):
            DeviceUpdate(name="r1", device_type="router", site_id=1, backbone_id=2)

    def test_interface_status_is_validated(self):
        with self.assertRaises(ValueError):
            InterfaceCreate(device_id=1, name="eth0", status="broken")


if __name__ == "__main__":
    unittest.main()
