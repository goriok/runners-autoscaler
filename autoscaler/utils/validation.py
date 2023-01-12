# Simplified implementation of labels keys and values validation inspired by apimachinery Kubernetes
# https://github.com/kubernetes/apimachinery/blob/master/pkg/util/validation/validation.go

import re


qname_char_fmt = "[A-Za-z0-9]"
qname_ext_char_fmt = "[-A-Za-z0-9_.]"
qualified_name_fmt = "(" + qname_char_fmt + qname_ext_char_fmt + "*)?" + qname_char_fmt
qualified_name_err_msg = "must consist of alphanumeric characters, '-', '_' or '.', and must start and end with an alphanumeric character"
qualified_name_max_length = 63
qualified_name_pattern = f"^{qualified_name_fmt}$"


def validate_label_key(label_key):
    errors = []
    parts = label_key.split('/')

    match len(parts):
        case 1:
            name = parts[0]
        case 2:
            prefix, name = parts[0], parts[1]
            if len(prefix) == 0:
                errors.append("prefix part must be non-empty")

            # validate if prefix is_dns1123_subdomain and get errors
            messages = is_dns1123_subdomain(prefix)
            messages = [f"prefix part {item}" for item in messages]
            if messages:
                errors.append(messages)
        case _:
            errors.append(
                "a qualified name " + regex_error(qualified_name_err_msg, qualified_name_fmt, ["MyName", "my.name", "123-abc"]) +
                " with an optional DNS subdomain prefix and '/' (e.g. 'example.com/MyName')")
            return errors

    if len(name) == 0:
        errors.append("name part must be non-empty")
    elif len(name) > qualified_name_max_length:
        errors.append(f"name part must be no more than {qualified_name_max_length} characters")

    if not re.match(qualified_name_pattern, name):
        errors.append("name part " + regex_error(qualified_name_err_msg, qualified_name_fmt, ["MyName", "my.name", "123-abc"]))

    return errors


label_value_fmt = "(" + qualified_name_fmt + ")?"
label_value_pattern = f"^{label_value_fmt}$"
label_value_err_msg = "a valid label must be an empty string or consist of alphanumeric characters, '-', '_' or '.', and must start and end with an alphanumeric character"
label_value_max_length = 63


def validate_label_value(label_value):
    errors = []
    if len(label_value) > label_value_max_length:
        errors.append(f"must be no more than {label_value_max_length} characters")
    if not re.match(label_value_pattern, label_value):
        errors.append(label_value_err_msg)

    return errors


dns1123_label_fmt = "[a-z0-9]([-a-z0-9]*[a-z0-9])?"
dns1123_subdomain_fmt = dns1123_label_fmt + "(\\." + dns1123_label_fmt + ")*"
dns1123_subdomain_error_msg = "a lowercase RFC 1123 subdomain must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character"
# dns1123_subdomain_max_length is a subdomain's max length in DNS (RFC 1123)
dns1123_subdomain_max_length = 253
dns1123_subdomain_regexp_pattern = f"^{dns1123_subdomain_fmt}$"


# is_dns1123_subdomain tests for a string that conforms to the definition of a
# subdomain in DNS (RFC 1123)
def is_dns1123_subdomain(value):
    errors = []
    if len(value) > dns1123_subdomain_max_length:
        errors.append(f"must be no more than {dns1123_subdomain_max_length} characters")
    if not re.match(dns1123_subdomain_regexp_pattern, value):
        errors.append(regex_error(dns1123_subdomain_error_msg, dns1123_subdomain_fmt, ["example.com"]))

    return errors


# RegexError returns a string explanation of a regex validation failure
def regex_error(msg, fmt, examples):
    if len(examples) == 0:
        return f"{msg} (regex used for validation is '{fmt}')"

    return f"{msg} (e.g. {' or '.join(examples)}) (regex used for validation is '{fmt}')"
