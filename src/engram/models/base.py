from enum import Enum


class EntityType(str, Enum):
    COMMIT = "commit"
    BRANCH = "branch"
    PULL_REQUEST = "pull_request"
    CODE_REVIEW = "code_review"
    ISSUE = "issue"

    DECISION = "decision"
    DESIGN_RATIONALE = "design_rationale"
    BUG_REPORT = "bug_report"
    FAILED_ATTEMPT = "failed_attempt"

    CONVERSATION = "conversation"
    MESSAGE = "message"
    MEETING_NOTE = "meeting_note"
    SLACK_THREAD = "slack_thread"

    DOCUMENT = "document"
    SNIPPET = "snippet"

    BENCHMARK = "benchmark"
    EXPERIMENT = "experiment"

    PERSON = "person"
    PROJECT = "project"
    COMPONENT = "component"
    CONCEPT = "concept"


class RelationType(str, Enum):
    CAUSED_BY = "caused_by"
    RESULTED_IN = "resulted_in"
    PRECEDED_BY = "preceded_by"
    FOLLOWED_BY = "followed_by"

    PART_OF = "part_of"
    CONTAINS = "contains"
    DEPENDS_ON = "depends_on"

    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    CONTRADICTS = "contradicts"
    SUPERSEDES = "supersedes"
    IMPLEMENTS = "implements"
    REVERTS = "reverts"

    AUTHORED_BY = "authored_by"
    REVIEWED_BY = "reviewed_by"
    ASSIGNED_TO = "assigned_to"
    MENTIONED_BY = "mentioned_by"

    MODIFIES = "modifies"
    REFERENCES = "references"

    DISCUSSED_IN = "discussed_in"
    DECIDED_IN = "decided_in"
    DOCUMENTED_IN = "documented_in"


class EntityStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ProvenanceAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    REFERENCED = "referenced"
    CONTRADICTED = "contradicted"
    SUPERSEDED = "superseded"
    MERGED = "merged"
