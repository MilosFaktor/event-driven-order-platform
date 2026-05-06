def payment_captured_mock(order):
    # payment mock
    order["steps"]["payment"] = "CAPTURED"
    print("Payment captured successfully")


def is_payment_captured(order):
    return order["steps"]["payment"] == "CAPTURED"
