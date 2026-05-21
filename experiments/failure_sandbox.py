class MyError(Exception):
    pass


def payment_success():
    print("payment captured")


def payment_failure():
    raise MyError("payment capture failed")


failure_step = None
failure_reason = None

try:
    payment_success()
except MyError as error:
    failure_step = "CAPTURE_PAYMENT"
    failure_reason = str(error)

print(failure_step)
print(failure_reason)

try:
    payment_failure()
except MyError as error:
    failure_step = "CAPTURE_PAYMENT"
    failure_reason = str(error)

print(failure_step)
print(failure_reason)
