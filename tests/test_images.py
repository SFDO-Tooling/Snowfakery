from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import check_output
from unittest import mock
import gvgen

import pytest

from snowfakery.cli import generate_cli
from snowfakery.output_streams import GraphvizOutputStream, ImageOutputStream
from snowfakery.data_generator import generate

sample_yaml = Path(__file__).parent.parent / "examples/family.recipe.yml"


class MockGraph(gvgen.GvGen):
    def __init__(self):
        self.nodes = []
        self.links = []
        self.properties = []

    def styleDefaultAppend(self, *args, **kwargs):
        pass

    def newItem(self, nodename):
        self.nodes.append(nodename)
        return nodename

    def newLink(self, node1, node2):
        self.links.append((node1, node2))
        return (node1, node2)

    def propertyAppend(self, link, propname, value):
        self.properties.append((link, propname, value))

    def dot(self, filename):
        pass


class TestGraphvizOutputStream:
    def test_image_outputs(self):
        with TemporaryDirectory() as t:
            dot = Path(t) / "out.dot"
            generate_cli.main(
                [str(sample_yaml), "--output-file", dot],
                standalone_mode=False,
            )
            assert dot.exists()

    @mock.patch("gvgen.GvGen")
    def test_nodes_and_edges(self, mock_graph_class):
        with TemporaryDirectory() as t, sample_yaml.open() as yaml:
            dot = Path(t) / "out.dot"

            mock_graph = MockGraph()
            mock_graph_class.return_value = mock_graph
            output_stream = GraphvizOutputStream(dot)
            generate(yaml, {}, output_stream)
            output_stream.close()
            assert mock_graph.nodes == [
                "Duke(1, Leto I Atreides)",
                "Duke(2, Muad'Dib)",
                "Lady(1, Lady Jessica)",
            ]
            assert mock_graph.links == [
                ("Duke(1, Leto I Atreides)", "Duke(2, Muad'Dib)"),
                ("Duke(1, Leto I Atreides)", "Lady(1, Lady Jessica)"),
                ("Duke(2, Muad'Dib)", "Duke(1, Leto I Atreides)"),
                ("Duke(2, Muad'Dib)", "Lady(1, Lady Jessica)"),
                ("Lady(1, Lady Jessica)", "Duke(1, Leto I Atreides)"),
                ("Lady(1, Lady Jessica)", "Duke(2, Muad'Dib)"),
            ]
            assert mock_graph.properties == [
                (
                    ("Duke(1, Leto I Atreides)", "Duke(2, Muad'Dib)"),
                    "label",
                    "son",
                ),
                (
                    ("Duke(1, Leto I Atreides)", "Lady(1, Lady Jessica)"),
                    "label",
                    "wife",
                ),
                (
                    ("Duke(2, Muad'Dib)", "Duke(1, Leto I Atreides)"),
                    "label",
                    "father",
                ),
                (
                    ("Duke(2, Muad'Dib)", "Lady(1, Lady Jessica)"),
                    "label",
                    "mother",
                ),
                (
                    ("Lady(1, Lady Jessica)", "Duke(1, Leto I Atreides)"),
                    "label",
                    "husband",
                ),
                (("Lady(1, Lady Jessica)", "Duke(2, Muad'Dib)"), "label", "son"),
            ]

    @mock.patch("gvgen.GvGen")
    def test_no_label(self, mock_graph_class):
        with TemporaryDirectory() as t, sample_yaml.open() as yaml:
            dot = Path(t) / "out.dot"

            mock_graph = MockGraph()
            mock_graph_class.return_value = mock_graph
            output_stream = GraphvizOutputStream(dot)
            yaml = (
                yaml.read()
                .replace("name", "REPLACEDNOMX")
                .replace("nickREPLACEDNOMX", "nickname")
            )
            generate(StringIO(yaml), {}, output_stream)
            output_stream.close()
            assert mock_graph.nodes == [
                "Duke(1)",
                "Duke(2)",
                "Lady(1, Lady Jessica)",
            ]


def graphviz_available():
    try:
        return bool(check_output(["dot", "-?"]))
    except FileNotFoundError:
        return False


class TestImageOuputStreams:
    @mock.patch("subprocess.Popen")
    def test_image_outputs_mocked(self, popen):
        png = "out.png"
        svg = "out.svg"
        txt = "out.txt"
        dot = "out.dot"
        popen.return_value.communicate = lambda: (mock.Mock(), mock.Mock())
        generate_cli.main(
            [
                str(sample_yaml),
                "--output-file",
                png,
                "--output-file",
                svg,
                "--output-file",
                txt,
                "--output-file",
                dot,
            ],
            standalone_mode=False,
        )
        for call in popen.mock_calls:
            assert call[1][0][0] == "dot"

    def test_image_outputs(self):
        if not graphviz_available():
            pytest.skip("Graphviz is not installed")

        with TemporaryDirectory() as t:
            png = Path(t) / "out.png"
            svg = Path(t) / "out.svg"
            txt = Path(t) / "out.txt"
            dot = Path(t) / "out.dot"
            generate_cli.main(
                [
                    str(sample_yaml),
                    "--output-file",
                    png,
                    "--output-file",
                    svg,
                    "--output-file",
                    txt,
                    "--output-file",
                    dot,
                ],
                standalone_mode=False,
            )
            assert png.read_bytes().startswith(b"\x89PNG"), png.read_bytes()[0:10]
            assert svg.read_bytes().startswith(b"<?xml"), svg.read_bytes()[0:5]
            assert svg.read_bytes().startswith(b"<?xml"), svg.read_bytes()[0:5]
            assert dot.read_bytes().startswith(b"/* Ge"), dot.read_bytes()[0:5]
            assert txt.exists()

    @mock.patch("subprocess.Popen", side_effect=FileNotFoundError)
    def test_dot_missing(self, popen):
        with TemporaryDirectory() as t, sample_yaml.open() as yaml:
            dot = Path(t) / "out.dot"

            output_stream = ImageOutputStream(dot, "png")
            generate(yaml, {}, output_stream)
            rc = output_stream.close()
            assert "Could not find `dot` executable." in rc[0]
