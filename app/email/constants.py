from enum import Enum


class PublishAction(Enum):
    REQUEST = "request"
    APPROVE = "approve"
    DENY = "deny"
    FINISH = "finish"


class PublishSubject(Enum):
    REQUEST = "Publication Request"
    APPROVE = "Publication Approved"
    DENY = "Publication Denied"
    FINISH = "Publication Finished"


class PublishTemplateName(Enum):
    REQUEST = "email_publish_request.txt"
