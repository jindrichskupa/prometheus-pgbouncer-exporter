import unittest
import os
from prometheus_pgbouncer_exporter.config import *

CURR_DIR=os.path.dirname(os.path.realpath(__file__))

class TestConfig(unittest.TestCase):

    #
    # read()
    #

    def testReadShouldRaiseErrorOnUnexistingFile(self):
        config = Config()

        with self.assertRaises(Exception):
            config.read("/path/to/none.yml")

    def testReadShouldSupportAnEmptyConfigFile(self):
        config = Config()
        config.read(CURR_DIR + "/fixtures/config-empty.yml")

        self.assertEqual(config.getExporterHost(), "127.0.0.1")
        self.assertEqual(config.getExporterPort(), 9100)
        self.assertEqual(config.getPgbouncers(), [])

    def testReadShouldParseConfigFileWithOnePgbouncer(self):
        config = Config()
        config.read(CURR_DIR + "/fixtures/config-with-one-pgbouncer.yml")

        self.assertEqual(config.getExporterHost(), "0.0.0.0")
        self.assertEqual(config.getExporterPort(), 1234)
        self.assertEqual(len(config.getPgbouncers()), 1)

        self.assertEqual(config.getPgbouncers()[0].getKeyValueConnection(), 'host=host port=6431 user=user password=password dbname=pgbouncer connect_timeout=2')
        self.assertEqual(config.getPgbouncers()[0].getKeyValueConnection(remove_password=True), 'host=host port=6431 user=user password=**** dbname=pgbouncer connect_timeout=2')
        self.assertEqual(config.getPgbouncers()[0].getConnectTimeout(), 2)
        self.assertEqual(config.getPgbouncers()[0].getIncludeDatabases(), ["one", "two"])
        self.assertEqual(config.getPgbouncers()[0].getExcludeDatabases(), ["three"])
        self.assertEqual(config.getPgbouncers()[0].getExtraLabels(), {"first": "1", "second": "2"})

    def testReadShouldParseConfigFileWithTwoPgbouncer(self):
        config = Config()
        config.read(CURR_DIR + "/fixtures/config-with-two-pgbouncer.yml")

        self.assertEqual(config.getExporterHost(), "0.0.0.0")
        self.assertEqual(config.getExporterPort(), 1234)
        self.assertEqual(len(config.getPgbouncers()), 2)

        self.assertEqual(config.getPgbouncers()[0].getKeyValueConnection(), 'host=host port=6431 user=user password=password dbname=pgbouncer connect_timeout=2')
        self.assertEqual(config.getPgbouncers()[0].getKeyValueConnection(remove_password=True), 'host=host port=6431 user=user password=**** dbname=pgbouncer connect_timeout=2') 
        self.assertEqual(config.getPgbouncers()[0].getConnectTimeout(), 2)
        self.assertEqual(config.getPgbouncers()[0].getIncludeDatabases(), ["one", "two"])
        self.assertEqual(config.getPgbouncers()[0].getExcludeDatabases(), ["three"])
        self.assertEqual(config.getPgbouncers()[0].getExtraLabels(), {"first": "1", "second": "2"})

        self.assertEqual(config.getPgbouncers()[1].getKeyValueConnection(), 'host=host port=6432 user=user password=password dbname=pgbouncer connect_timeout=5')
        self.assertEqual(config.getPgbouncers()[1].getKeyValueConnection(remove_password=True), 'host=host port=6432 user=user password=**** dbname=pgbouncer connect_timeout=5')
        self.assertEqual(config.getPgbouncers()[1].getConnectTimeout(), 5)
        self.assertEqual(config.getPgbouncers()[1].getIncludeDatabases(), [])
        self.assertEqual(config.getPgbouncers()[1].getExcludeDatabases(), [])
        self.assertEqual(config.getPgbouncers()[1].getExtraLabels(), {})

    def testReadShouldInjectEnvironmentVariablesOnParsing(self):
        os.environ["TEST_USERNAME"] = "marco"
        os.environ["TEST_PASSWORD"] = "secret"
        os.environ["TEST_INCLUDE_DATABASE"] = "production"
        os.environ["TEST_EXTRA_LABEL_NAME"] = "cluster"
        os.environ["TEST_EXTRA_LABEL_VALUE"] = "users-1-1000"

        config = Config()
        config.read(CURR_DIR + "/fixtures/config-with-env-vars.yml")

        self.assertEqual(len(config.getPgbouncers()), 1)
        self.assertEqual(config.getPgbouncers()[0].getKeyValueConnection(), 'host=host port=6431 user=marco password=secret dbname=pgbouncer connect_timeout=2')
        self.assertEqual(config.getPgbouncers()[0].getIncludeDatabases(), ["production"])
        self.assertEqual(config.getPgbouncers()[0].getExtraLabels(), {"cluster": "users-1-1000"})

    def testReadShouldInjectEnvironmentVariablesOnParsingEvenIfEmpty(self):
        os.environ["TEST_USERNAME"] = "marco"
        os.environ["TEST_PASSWORD"] = ""
        os.environ["TEST_INCLUDE_DATABASE"] = "production"
        os.environ["TEST_EXTRA_LABEL_NAME"] = "cluster"
        os.environ["TEST_EXTRA_LABEL_VALUE"] = "users-1-1000"

        config = Config()
        config.read(CURR_DIR + "/fixtures/config-with-env-vars.yml")

        self.assertEqual(len(config.getPgbouncers()), 1)
        self.assertEqual(config.getPgbouncers()[0].getKeyValueConnection(), 'host=host port=6431 user=marco password= dbname=pgbouncer connect_timeout=5')

    def testReadShouldKeepOriginalConfigOnMissingEnvironmentVariables(self):
        del os.environ["TEST_USERNAME"]
        os.environ["TEST_PASSWORD"] = "secret"
        del os.environ["TEST_INCLUDE_DATABASE"]
        os.environ["TEST_EXTRA_LABEL_NAME"] = "cluster"
        os.environ["TEST_EXTRA_LABEL_VALUE"] = "users-1-1000"

        config = Config()
        config.read(CURR_DIR + "/fixtures/config-with-env-vars.yml")

        self.assertEqual(len(config.getPgbouncers()), 1)
        self.assertEqual(config.getPgbouncers()[0].getKeyValueConnection(), 'host=host port=6431 user=$(TEST_USERNAME) password=secret dbname=pgbouncer connect_timeout=2')
        self.assertEqual(config.getPgbouncers()[0].getIncludeDatabases(), ["$(TEST_INCLUDE_DATABASE)"])
        self.assertEqual(config.getPgbouncers()[0].getExtraLabels(), {"cluster": "users-1-1000"})

    #
    # validate()
    #

    def testValidateShouldPassOnConfigContainingOnePgbouncer(self):
        config = Config()
        config.read(CURR_DIR + "/fixtures/config-with-one-pgbouncer.yml")
        config.validate()

    def testValidateShouldPassOnConfigContainingTwoPgbouncer(self):
        config = Config()
        config.read(CURR_DIR + "/fixtures/config-with-two-pgbouncer.yml")
        config.validate()

    def testValidateShouldRaiseExceptionOnNoPgbouncerConfigured(self):
        config = Config({})

        with self.assertRaisesRegex(Exception, "no pgbouncer instance configured"):
            config.validate()

    def testValidateShouldRaiseExceptionOnTwoPgbouncersWithNoLabels(self):
        config = Config({"pgbouncers": [
            {"dsn": "postgresql://"},
            {"dsn": "postgresql://"}
        ]})

        with self.assertRaisesRegex(Exception, "extra_labels configured for each pgbouncer must be unique"):
            config.validate()

    def testValidateShouldRaiseExceptionOnTwoPgbouncersWithSameExtraLabels(self):
        config = Config({"pgbouncers": [
            {"dsn": "postgresql://", "extra_labels": {"pool_id": 1, "another_id": 5}},
            {"dsn": "postgresql://", "extra_labels": {"pool_id": 1, "another_id": 5}}
        ]})

        with self.assertRaisesRegex(Exception, "extra_labels configured for each pgbouncer must be unique"):
            config.validate()

    def testValidateShouldPassOnTwoPgbouncersWithDifferentExtraLabels(self):
        config = Config({"pgbouncers": [
            {"dsn": "postgresql://", "extra_labels": {"pool_id": 1, "another_id": 5}},
            {"dsn": "postgresql://", "extra_labels": {"pool_id": 2, "another_id": 5}}
        ]})

        config.validate()


class TestPgbouncerConfig(unittest.TestCase):

    def testGetDsnWithMaskedPasswordShouldReturnDsnWithThreeAsterisksInsteadOfThePassword(self):
        config = PgbouncerConfig({"dsn": "postgresql://pgbouncer:secret@localhost:6431/pgbouncer"})
        self.assertEqual(config.getKeyValueConnection(remove_password=True), 'host=localhost port=6431 user=pgbouncer password=**** dbname=pgbouncer connect_timeout=5')

    def testGetDsnWithMaskedPasswordShouldWorkEvenIfThePasswordIsEmpty(self):
        config = PgbouncerConfig({"dsn": "postgresql://pgbouncer:@localhost:6431/pgbouncer"})
        self.assertEqual(config.getKeyValueConnection(remove_password=True), 'host=localhost port=6431 user=pgbouncer password=**** dbname=pgbouncer connect_timeout=5')

    def testValidateShouldPassOnConfigContainingOnlyDsn(self):
        config = PgbouncerConfig({"dsn": "postgresql://"})
        config.validate()

    def testValidateShouldRaiseExceptionOnEmptyDsn(self):
        config = PgbouncerConfig({"dsn": ""})

        with self.assertRaisesRegex(Exception, "The DSN is required"):
            config.validate()


if __name__ == '__main__':
    unittest.main()
