import unittest, os

from tests.shared import *
from tests.stub.shared import *
from nutkit.frontend import Driver, AuthorizationToken
import nutkit.protocol as types


class SessionRunDisconnected(unittest.TestCase):
    def setUp(self):
        self._backend = new_backend()
        self._server = StubServer(9001)
        self._driverName = get_driver_name()
        auth = AuthorizationToken(scheme="basic", principal="neo4j", credentials="pass")
        self._driver = Driver(self._backend, "bolt://%s" % self._server.address, auth)
        self._session = self._driver.session("r")

    def tearDown(self):
        self._session.close()
        self._driver.close()
        self._backend.close()
        # If test raised an exception this will make sure that the stub server
        # is killed and it's output is dumped for analys.
        self._server.reset()

    # Helper function that runs the sequence and returns the name of the step at which the
    # error happened.
    def _run(self):
        try:
            result = self._session.run("RETURN 1 as n")
        except types.DriverError:
            return "after run"

        try:
            record = result.next()
        except types.DriverError:
            return "after first next"

        try:
            nullRecord = result.next()
        except types.DriverError:
            return "after last next"

        return "success"

    def test_disconnect_on_hello(self):
        # Verifies how the driver handles when server disconnects right after driver sent bolt
        # hello message.
        if not self._driverName in ["go"]:
            self.skipTest("Need support for specifying user agent in stub server")
        self._server.start(os.path.join(scripts_path, "disconnect_on_hello.script"))
        step = self._run()
        self._server.done()

        expectedStep = "after first next"
        if self._driverName in ["go"]:
            # Go reports this error earlier
            expectedStep = "after run"
        self.assertEqual(step, expectedStep)

    def test_disconnect_on_run(self):
        # Verifies how the driver handles when server disconnects right after driver sent bolt
        # run message.
        script = "disconnect_on_run.script"
        # Until Go is updated to use PULL with n
        if self._driverName in ["go"]:
            script = "disconnect_on_run_pull_all.script"
        # Java (and Go) doesn't rely on default access mode
        if self._driverName in ["java"]:
            script = "disconnect_on_run_explicit_mode.script"

        self._server.start(os.path.join(scripts_path, script))
        step = self._run()
        self._server.done()

        expectedStep = "after first next"
        if self._driverName in ["go"]:
            # Go reports this error earlier
            expectedStep = "after run"
        self.assertEqual(step, expectedStep)

    def test_disconnect_on_pull(self):
        # Verifies how the driver handles when server disconnects right after driver sent bolt
        # pull message.
        script = "disconnect_on_pull.script"
        # Until Go is updated to use PULL with n
        if self._driverName in ["go"]:
            script = "disconnect_on_pull_pull_all.script"
        # Java (and Go) doesn't rely on default access mode
        if self._driverName in ["java"]:
            script = "disconnect_on_pull_explicit_mode.script"

        self._server.start(os.path.join(scripts_path, script))
        step = self._run()
        self._server.done()

        expectedStep = "after first next"
        if self._driverName in ["go"]:
            # Go reports this error earlier
            expectedStep = "after run"
        self.assertEqual(step, expectedStep)

