"""Cable sweep paths must not depend on the Windows clipboard."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from sympy import Symbol

from HFSSdrawpy.core.body import Body


class HfssCablePathTests(unittest.TestCase):
    def test_each_conductor_gets_the_same_parametric_path_without_copy(self):
        for radius in (0, Symbol("bend_radius")):
            with self.subTest(radius=radius):
                points = [[0, 0, 0], [Symbol("length"), 0, 0], [1, 1, 0]]
                created = []

                def polyline(vertices, **kwargs):
                    entity = Mock()
                    entity.copy.side_effect = AssertionError("Clipboard copy used")
                    created.append((vertices, kwargs, entity))
                    return entity

                body = SimpleNamespace(
                    mode="hfss", interface=Mock(), polyline=polyline
                )
                port = SimpleNamespace(
                    ori=[1, 0, 0], pos=[0, 0, 0], N=2,
                    offsets=[0, 0.2], widths=[0.1, 0.3],
                    subnames=["track", "gap"], layers=[1, 2],
                )
                with patch("HFSSdrawpy.core.body.check_name", return_value="cable"):
                    result = Body.path.__wrapped__(
                        body, points, port, radius, name="cable"
                    )

                self.assertEqual(len(created), 4)
                for index, subname in enumerate(port.subnames):
                    _, section_args, section = created[2 * index]
                    path_points, path_args, path = created[2 * index + 1]
                    self.assertIs(path_points, points)
                    self.assertEqual(path_args, {
                        "closed": False, "name": "cable_" + subname + "_path"
                    })
                    self.assertEqual(section_args["layer"], port.layers[index])
                    self.assertIs(result[index], section)
                    path.fillet.assert_called_once_with(radius)
                    body.interface.sweep_along_path.assert_any_call(section, path)
                    path.delete.assert_called_once_with()
                    path.copy.assert_not_called()
                    section.delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
