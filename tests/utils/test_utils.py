from unittest import TestCase

from autoscaler.utils.validation import validate_label_value, validate_label_key


# label value validation
class ValidateLabelValuePositiveTestCase(TestCase):
    def test_valid_empty_value(self):
        self.assertEqual(validate_label_value(""), [])

    def test_valid_value(self):
        self.assertEqual(validate_label_value("label-value"), [])


class ValidateLabelValueNegativeTestCase(TestCase):

    def test_long_value(self):
        self.assertEqual(validate_label_value(f'{"a" * 64}'), ['must be no more than 63 characters'])

    def test_non_qualified_value(self):
        errors_messages_expected = ['a valid label must be an empty string or consist of alphanumeric characters, '
                                    "'-', '_' or '.', and must start and end with an alphanumeric character"]
        self.assertEqual(validate_label_value("@@@###!!!111"), errors_messages_expected)

    def test_long_non_qualified_value(self):
        errors_messages_expected = ['must be no more than 63 characters',
                                    'a valid label must be an empty string or consist of alphanumeric characters, '
                                    "'-', '_' or '.', and must start and end with an alphanumeric character"]
        self.assertEqual(validate_label_value(f'{"a@#1" * 64}'), errors_messages_expected)


# label key validation
class ValidateLabelKeyPositiveTestCase(TestCase):
    def test_valid_one_part_key(self):
        self.assertEqual(validate_label_key("key"), [])

    def test_valid_two_parts_key(self):
        self.assertEqual(validate_label_key("app.kubernetes.io/version"), [])


class ValidateLabelKeyNegativeTestCase(TestCase):

    def test_empty_key(self):
        errors_messages_expected = ['name part must be non-empty',
                                    "name part must consist of alphanumeric characters, '-', '_' or '.', and must "
                                    'start and end with an alphanumeric character (e.g. MyName or my.name or '
                                    '123-abc) (regex used for validation is '
                                    "'([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9]')"]
        self.assertEqual(validate_label_key(""), errors_messages_expected)

    def test_long_key(self):
        errors_messages_expected = ['name part must be no more than 63 characters']
        self.assertEqual(validate_label_key(f"{'key' * 64}"), errors_messages_expected)

    def test_empty_second_part_key(self):
        errors_messages_expected = [
                                    'name part must be non-empty',
                                    "name part must consist of alphanumeric characters, '-', '_' or '.', and must "
                                    'start and end with an alphanumeric character (e.g. MyName or my.name or '
                                    '123-abc) (regex used for validation is '
                                    "'([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9]')"]
        self.assertEqual(validate_label_key("app.kubernetes.io/"), errors_messages_expected)

    def test_three_parts_key(self):
        errors_messages_expected = ["a qualified name must consist of alphanumeric characters, '-', '_' or '.', "
                                    'and must start and end with an alphanumeric character (e.g. MyName or '
                                    'my.name or 123-abc) (regex used for validation is '
                                    "'([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9]') with an optional DNS subdomain "
                                    "prefix and '/' (e.g. 'example.com/MyName')"]
        self.assertEqual(validate_label_key("app.kubernetes.io/version/three"), errors_messages_expected)

    def test_non_qualified_key(self):
        errors_messages_expected = ["name part must consist of alphanumeric characters, '-', '_' or '.', and must "
                                    'start and end with an alphanumeric character (e.g. MyName or my.name or '
                                    '123-abc) (regex used for validation is '
                                    "'([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9]')"]
        self.assertEqual(validate_label_key("@@@###111"), errors_messages_expected)

    def test_non_qualified_with_empty_second_part_key(self):
        errors_messages_expected = [['prefix part a lowercase RFC 1123 subdomain must consist of lower case '
                                     "alphanumeric characters, '-' or '.', and must start and end with an "
                                     'alphanumeric character (e.g. example.com) (regex used for validation is '
                                     "'[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*')"],
                                    'name part must be non-empty',
                                    "name part must consist of alphanumeric characters, '-', '_' or '.', and must "
                                    'start and end with an alphanumeric character (e.g. MyName or my.name or '
                                    '123-abc) (regex used for validation is '
                                    "'([A-Za-z0-9][-A-Za-z0-9_.]*)?[A-Za-z0-9]')"]
        self.assertEqual(validate_label_key("@@@###111/"), errors_messages_expected)
