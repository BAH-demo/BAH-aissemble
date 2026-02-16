import sys
import os
import types
from unittest.mock import MagicMock

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

py4j_pkg = types.ModuleType("py4j")
py4j_pkg.__path__ = []

java_gateway_mod = MagicMock()
java_gateway_mod.JavaGateway = MagicMock()
java_gateway_mod.GatewayParameters = MagicMock()
java_gateway_mod.CallbackServerParameters = MagicMock()
java_gateway_mod.launch_gateway = MagicMock(return_value=25333)
java_gateway_mod.find_jar_path = MagicMock(return_value="/fake/py4j.jar")

version_mod = types.ModuleType("py4j.version")
version_mod.__version__ = "0.10.9.7"

protocol_mod = MagicMock()
protocol_mod.Py4JError = type("Py4JError", (Exception,), {})

sys.modules["py4j"] = py4j_pkg
sys.modules["py4j.java_gateway"] = java_gateway_mod
sys.modules["py4j.version"] = version_mod
sys.modules["py4j.protocol"] = protocol_mod
