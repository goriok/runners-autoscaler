# Simplified implementation of labels keys and values validation inspired by apimachinery Kubernetes
# https://github.com/kubernetes/apimachinery/blob/master/pkg/util/validation/validation.go

import re


qnameCharFmt = "[A-Za-z0-9]"
qnameExtCharFmt = "[-A-Za-z0-9_.]"
qualifiedNameFmt = "(" + qnameCharFmt + qnameExtCharFmt + "*)?" + qnameCharFmt
qualifiedNameErrMsg = "must consist of alphanumeric characters, '-', '_' or '.', and must start and end with an alphanumeric character"
qualifiedNameMaxLength = 63
qualified_name_pattern = f"^{qualifiedNameFmt}$"


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
                "a qualified name " + regex_error(qualifiedNameErrMsg, qualifiedNameFmt, ["MyName", "my.name", "123-abc"]) +
                " with an optional DNS subdomain prefix and '/' (e.g. 'example.com/MyName')")
            return errors

    if len(name) == 0:
        errors.append("name part must be non-empty")
    elif len(name) > qualifiedNameMaxLength:
        errors.append(f"name part must be no more than {qualifiedNameMaxLength} characters")

    if not re.match(qualified_name_pattern, name):
        errors.append("name part " + regex_error(qualifiedNameErrMsg, qualifiedNameFmt, ["MyName", "my.name", "123-abc"]))

    return errors


labelValueFmt = "(" + qualifiedNameFmt + ")?"
label_value_pattern = f"^{labelValueFmt}$"
labelValueErrMsg = "a valid label must be an empty string or consist of alphanumeric characters, '-', '_' or '.', and must start and end with an alphanumeric character"
LabelValueMaxLength = 63


def validate_label_value(label_value):
    errors = []
    if len(label_value) > LabelValueMaxLength:
        errors.append(f"must be no more than {LabelValueMaxLength} characters")
    if not re.match(label_value_pattern, label_value):
        errors.append(labelValueErrMsg)

    return errors


dns1123LabelFmt = "[a-z0-9]([-a-z0-9]*[a-z0-9])?"
dns1123SubdomainFmt = dns1123LabelFmt + "(\\." + dns1123LabelFmt + ")*"
dns1123SubdomainErrorMsg = "a lowercase RFC 1123 subdomain must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character"
# DNS1123SubdomainMaxLength is a subdomain's max length in DNS (RFC 1123)
DNS1123SubdomainMaxLength = 253
dns1123SubdomainRegexp_pattern = f"^{dns1123SubdomainFmt}$"


# IsDNS1123Subdomain tests for a string that conforms to the definition of a
# subdomain in DNS (RFC 1123)
def is_dns1123_subdomain(value):
    errors = []
    if len(value) > DNS1123SubdomainMaxLength:
        errors.append(f"must be no more than {DNS1123SubdomainMaxLength} characters")
    if not re.match(dns1123SubdomainRegexp_pattern, value):
        errors.append(regex_error(dns1123SubdomainErrorMsg, dns1123SubdomainFmt, ["example.com"]))

    return errors


# RegexError returns a string explanation of a regex validation failure
def regex_error(msg, fmt, examples):
    if len(examples) == 0:
        return f"{msg} (regex used for validation is '{fmt}')"

    return f"{msg} (e.g. {' or '.join(examples)}) (regex used for validation is '{fmt}')"
