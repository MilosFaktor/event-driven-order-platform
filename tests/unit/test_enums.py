from app.models.enums import OrderFailureStep


def test_failure_step_capture_payment_value():
    assert OrderFailureStep.CAPTURE_PAYMENT == "CAPTURE_PAYMENT"
